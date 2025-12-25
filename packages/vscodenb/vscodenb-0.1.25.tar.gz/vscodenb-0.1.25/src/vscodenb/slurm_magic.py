"""
Enhanced Jupyter cell magic for running code in an isolated subprocess with state transfer.

This version can pass the notebook's global scope to the subprocess and retrieve
the updated state back, making isolated cells contribute to the notebook scope.

Usage:
    %%slurm
    # Your code here - behaves like a normal cell but runs in subprocess

    %%slurm --no-state
    # Run truly isolated without state transfer
"""

import ast
import subprocess
import sys
import tempfile
import re
import pickle
import dill  # Better serialization than pickle
import json
import types
import time
from pathlib import Path
from IPython.core.magic import Magics, magics_class, cell_magic
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring
from IPython.core.getipython import get_ipython
from IPython.display import display, HTML
import numpy as np
import pandas as pd
import shutil


def extract_imports_from_code(code):
    """Extract import statements from Python code."""
    imports = []
    
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.append(ast.unparse(node))
            elif isinstance(node, ast.ImportFrom):
                imports.append(ast.unparse(node))
    except SyntaxError:
        # Fallback to regex if AST parsing fails
        import_pattern = r'^\s*(from\s+[\w\.]+\s+import\s+.*|import\s+[\w\.,\s]+)$'
        for line in code.split('\n'):
            if re.match(import_pattern, line.strip()):
                imports.append(line.strip())
    
    return imports


def get_all_previous_imports(ipython):
    """Collect all import statements from cells executed before the current one."""
    all_imports = []
    seen_imports = set()
    
    history = ipython.history_manager
    session_num = history.session_number
    
    for _, _, code in history.get_range(session_num, start=1):
        if code:
            imports = extract_imports_from_code(code)
            for imp in imports:
                normalized = ' '.join(imp.split())
                if normalized not in seen_imports:
                    seen_imports.add(normalized)
                    all_imports.append(imp)
    
    return all_imports


def serialize_globals(globals_dict):
    """
    Serialize the globals dictionary for transfer to subprocess.
    Returns (serializable_dict, failed_items).
    """
    import warnings
    
    # Items to skip - IPython internals and non-serializable objects
    skip_patterns = [
        'In', 'Out', '_', '__', '___', '_i', '_ii', '_iii',
        '_oh', '_dh', 'exit', 'quit', 'get_ipython',
        '__builtins__', '__builtin__', '__package__',
        '__loader__', '__spec__', '__annotations__',
        '__cached__', '__file__', '_ih', '_oh', '_dh'
    ]
    
    serializable = {}
    failed = {}
    
    for key, value in globals_dict.items():
        # Skip IPython internals and private variables
        if key in skip_patterns or key.startswith('_i'):
            continue
            
        # Skip modules, functions from modules, and built-in functions
        if isinstance(value, types.ModuleType):
            continue
        if isinstance(value, types.BuiltinFunctionType):
            continue
        if isinstance(value, type):
            # Skip classes unless they're user-defined
            if value.__module__ not in ['__main__', '__console__']:
                continue
        
        try:
            # Try to serialize with dill (handles more types than pickle)
            serialized = dill.dumps(value)
            # Test deserialization
            dill.loads(serialized)
            serializable[key] = value
        except Exception as e:
            # If dill fails, try to handle specific types
            try:
                if isinstance(value, (np.ndarray, pd.DataFrame, pd.Series)):
                    # These should work with dill, but have a fallback
                    serializable[key] = value
                elif isinstance(value, (int, float, str, bool, list, dict, tuple, set)):
                    # Basic types should always work
                    serializable[key] = value
                else:
                    failed[key] = f"{type(value).__name__}: {str(e)[:50]}"
            except Exception as e2:
                failed[key] = f"{type(value).__name__}: {str(e2)[:50]}"
    
    return serializable, failed


def create_subprocess_script(imports, cell_code, transfer_state=True):
    """Create the Python script that will run in the subprocess."""
    
    script = '''
import sys
import dill
import pickle
import base64
import traceback

# Function to load state
def load_state():
    if len(sys.argv) > 1:
        state_file = sys.argv[1]
        try:
            with open(state_file, 'rb') as f:
                return dill.load(f)
        except Exception as e:
            print(f"Warning: Could not load state: {e}", file=sys.stderr)
            return {}
    return {}

# Function to save state
def save_state(state_dict, output_file):
    try:
        # Filter out non-serializable items for return
        clean_state = {}
        for key, value in state_dict.items():
            # Skip built-ins and internals
            if key.startswith('__') and key.endswith('__'):
                continue
            if key in ['dill', 'pickle', 'sys', 'base64', 'traceback', 
                      'load_state', 'save_state', '_initial_state']:
                continue
            try:
                dill.dumps(value)
                clean_state[key] = value
            except:
                pass  # Skip non-serializable items
        
        with open(output_file, 'wb') as f:
            dill.dump(clean_state, f)
    except Exception as e:
        print(f"Warning: Could not save state: {e}", file=sys.stderr)

'''

    if transfer_state:
        script += '''
# Load initial state
_initial_state = load_state()
globals().update(_initial_state)

'''

    # Add imports
    if imports:
        script += "# Collected imports from previous cells\n"
        script += '\n'.join(imports)
        script += '\n\n'
    
    # Add the cell code
    script += "# Cell code\n"
    script += cell_code
    script += '\n\n'
    
    if transfer_state:
        script += '''
# Save the updated state
if len(sys.argv) > 2:
    # Get the current globals, excluding the initial state variable
    current_globals = {k: v for k, v in globals().items() if k != '_initial_state'}
    save_state(current_globals, sys.argv[2])
'''
    
    return script


@magics_class
class SlurmMagic(Magics):
    """IPython magics for running code in SLURM jobs."""

    @cell_magic
    @magic_arguments()
    @argument('--no-imports', action='store_true',
              help="Don't include previous imports")
    @argument('--no-state', action='store_true',
              help="Don't transfer global state (true isolation)")
    @argument('--python', type=str, default=None,
              help='Path to Python interpreter')
    @argument('--timeout', type=float, default=None,
              help='Timeout for job in seconds')
    @argument('--show-script', action='store_true',
              help='Print the generated script before running')
    @argument('--show-state', action='store_true',
              help='Show what variables are being transferred')
    @argument('--mem', '-m', type=str, default=None,
              help='Memory per CPU (SLURM)')
    @argument('--cores', '-c', type=int, default=None,
              help='CPUs per task (SLURM)')
    @argument('--time', '-t', type=str, default=None,
              help='Walltime limit (SLURM)')
    @argument('--account', '-A', type=str, default=None,
              help='Account to charge (SLURM)')
    def slurm(self, line, cell):
        """
        Run code in a SLURM job with optional state transfer.

        Usage:
            %%slurm
            # your code here

            %%slurm --mem 4G --cores 4 --time 00:10:00
            # your code here with SLURM resources

            %%slurm --no-state
            # run truly isolated without state transfer
        """
        args = parse_argstring(self.slurm, line)

        if not shutil.which("sbatch"):
            print("Not running on SLURM cluster.", file=sys.stderr)
            return

        python_path = args.python if args.python else sys.executable

        # Collect imports
        imports = []
        if not args.no_imports:
            try:
                imports = get_all_previous_imports(self.shell)
            except Exception:
                pass

        # Prepare state transfer
        state_file = None
        output_state_file = None
        serializable = {}

        if not args.no_state:
            # Get current globals
            user_globals = self.shell.user_ns
            serializable, failed = serialize_globals(user_globals)

            if args.show_state:
                print("=" * 50)
                print("Transferring variables:")
                for key in sorted(serializable.keys()):
                    var_type = type(serializable[key]).__name__
                    print(f"  {key}: {var_type}")
                if failed:
                    print("\nNot transferring (non-serializable):")
                    for key, reason in failed.items():
                        print(f"  {key}: {reason}")
                print("=" * 50)
                print()

            # Create temporary files for state transfer
            # Use current directory (shared filesystem) instead of /tmp (local to node)
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.pkl', delete=False, dir='.') as f:
                dill.dump(serializable, f)
                state_file = f.name

            with tempfile.NamedTemporaryFile(mode='wb', suffix='.pkl', delete=False, dir='.') as f:
                output_state_file = f.name

        # Create the script
        script = create_subprocess_script(imports, cell, transfer_state=not args.no_state)

        if args.show_script:
            print("=" * 50)
            print("Generated script:")
            print("=" * 50)
            print(script)
            print("=" * 50)
            print()

        # Write script to temporary file
        # Use current directory (shared filesystem) instead of /tmp (local to node)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, dir='.') as f:
            f.write(script)
            script_file = f.name

        output_file = None
        try:
            # Create output file for stdout/stderr
            with tempfile.NamedTemporaryFile(mode='w', suffix='.out', delete=False, dir='.') as f:
                output_file = f.name

            # Build sbatch command
            sbatch_cmd = ['sbatch', '--parsable']
            if args.mem:
                sbatch_cmd.append(f'--mem={args.mem}')
            if args.cores:
                sbatch_cmd.append(f'--cpus-per-task={args.cores}')
            sbatch_cmd.append('--nodes=1')
            if args.time:
                sbatch_cmd.append(f'--time={args.time}')
            if args.account:
                sbatch_cmd.append(f'--account={args.account}')
            sbatch_cmd.extend([f'--output={output_file}', f'--error={output_file}'])

            # Build the command to run
            run_cmd = [python_path, script_file]
            if not args.no_state:
                run_cmd.extend([state_file, output_state_file])
            sbatch_cmd.append('--wrap=' + ' '.join(run_cmd))

            # Submit the job
            result = subprocess.run(sbatch_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                display(HTML(self._generate_status_html([('Failed', '#666666')])))
                return

            job_id = result.stdout.strip()

            # Initialize HTML status display
            status_stages = []
            status_display = display(HTML(self._generate_status_html(status_stages)), display_id=True)

            # Poll for job state
            poll_interval = 0.5
            prev_state = None
            final_state = None
            start_time = time.time()

            try:
                while True:
                    poll_result = subprocess.run(
                        ['sacct', '-n', '-P', '-X', '-j', job_id,
                         '--state=PENDING,RUNNING,CANCELLED,FAILED,COMPLETED,TIMEOUT,OUT_OF_MEMORY',
                         '--format=state'],
                        capture_output=True, text=True
                    )
                    state = poll_result.stdout.strip()

                    if state and state != prev_state:
                        if state == 'PENDING' and prev_state is None:
                            status_stages.append(('Allocated...', '#666666'))
                            status_display.update(HTML(self._generate_status_html(status_stages)))
                        elif state == 'RUNNING':
                            status_stages.append(('Running...', '#666666'))
                            status_display.update(HTML(self._generate_status_html(status_stages)))
                        prev_state = state

                    if state in ('COMPLETED', 'FAILED', 'CANCELLED', 'TIMEOUT', 'OUT_OF_MEMORY'):
                        final_state = state
                        break

                    if args.timeout and (time.time() - start_time) > args.timeout:
                        # Cancel the job
                        subprocess.run(['scancel', job_id], capture_output=True)
                        final_state = 'TIMEOUT'
                        break

                    time.sleep(poll_interval)

            except KeyboardInterrupt:
                subprocess.run(['scancel', job_id], capture_output=True)
                final_state = 'CANCELLED'

            # Handle final state
            if final_state == 'COMPLETED':
                # Load the updated state back into the notebook
                if not args.no_state and output_state_file:
                    try:
                        with open(output_state_file, 'rb') as f:
                            updated_state = dill.load(f)

                        # Update the notebook's globals with the new state
                        for key, value in updated_state.items():
                            if key not in self.shell.user_ns or \
                               not self._compare_values(self.shell.user_ns.get(key), value):
                                self.shell.user_ns[key] = value
                    except Exception:
                        pass
                status_stages.append(('Completed', '#666666'))
            elif final_state == 'TIMEOUT':
                status_stages.append(('Timeout', '#666666'))
            elif final_state == 'CANCELLED':
                status_stages.append(('Killed', '#666666'))
            elif final_state == 'OUT_OF_MEMORY':
                status_stages.append(('Out of Memory', '#666666'))
            else:
                status_stages.append(('Failed', '#666666'))

            status_display.update(HTML(self._generate_status_html(status_stages)))

            # Print output from job
            if Path(output_file).exists():
                with open(output_file, 'r') as f:
                    output = f.read()
                if output:
                    print(output, end='')

        except KeyboardInterrupt:
            display(HTML(self._generate_status_html([('Killed', '#666666')])))
        except Exception:
            display(HTML(self._generate_status_html([('Failed', '#666666')])))
        finally:
            # Clean up temporary files
            for temp_file in [script_file, state_file, output_state_file, output_file]:
                if temp_file:
                    Path(temp_file).unlink(missing_ok=True)
    
    def _compare_values(self, val1, val2):
        """Compare two values for equality, handling special cases."""
        try:
            if type(val1) != type(val2):
                return False
            if isinstance(val1, (np.ndarray, pd.DataFrame, pd.Series)):
                # Use appropriate comparison for these types
                if isinstance(val1, np.ndarray):
                    return np.array_equal(val1, val2)
                else:
                    return val1.equals(val2)
            else:
                return val1 == val2
        except:
            return False

    def _generate_status_html(self, stages):
        """Generate HTML for status display.

        Args:
            stages: list of (status_text, color) tuples
        """
        # Color mapping for final states
        spans = []
        for text, color in stages:
            spans.append(f'<span style="color: {color};">{text}</span>')

        html = f'''<div style="font-family: monospace; font-size: 10px; padding: 4px;">{''.join(spans)}</div>'''
        return html


# def load_ipython_extension(ipython):
#     """Load the extension in IPython."""
#     ipython.register_magics(SlurmMagic)
#     print("Enhanced slurm magic loaded. Use %%slurm to run cells with state transfer.")


# def unload_ipython_extension(ipython):
#     """Unload the extension."""
#     print("Enhanced slurm magic unloaded.")


# def register_magic():
#     """Manually register the magic if not loading as extension."""
#     ip = get_ipython()
#     if ip:
#         ip.register_magics(SlurmMagic)
#         print("Enhanced slurm magic registered. Use %%slurm for subprocess execution with state transfer.")
#     else:
#         print("No IPython instance found. This must be run in a Jupyter environment.")


# if __name__ == "__main__":
#     print(__doc__)
