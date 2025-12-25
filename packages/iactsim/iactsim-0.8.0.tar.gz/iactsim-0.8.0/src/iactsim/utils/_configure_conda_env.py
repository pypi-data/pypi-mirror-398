import os
import sys
from pathlib import Path

def _configure_conda_env():
    if len(sys.argv) < 2:
        print("Usage: python setup_env_scripts.py <target_env_name>", file=sys.stderr)
        sys.exit(1)
    target_env = sys.argv[1]

    conda_prefix_str = os.getenv("CONDA_PREFIX")
    if not conda_prefix_str:
        print("Error: CONDA_PREFIX environment variable not set.", file=sys.stderr)
        print("Ensure you are running this script within an active Conda environment.", file=sys.stderr)
        sys.exit(1)

    conda_prefix = Path(conda_prefix_str)
    current_env = conda_prefix.name

    if current_env != target_env:
        print(f"Error: The target environment '{target_env}' is not active.", file=sys.stderr)
        print(f"Currently active environment: '{current_env}'", file=sys.stderr)
        sys.exit(1)

    # Define activation and deactivation directories
    activate_dir = conda_prefix / "etc" / "conda" / "activate.d"
    deactivate_dir = conda_prefix / "etc" / "conda" / "deactivate.d"

    activate_dir.mkdir(parents=True, exist_ok=True)
    deactivate_dir.mkdir(parents=True, exist_ok=True)

    # NVHPC_ROOT is assumed to be defined when `module load nvhpc` runs
    # CUDA_PATH is assumed to be $NVHPC_ROOT/cuda
    set_vars_script = """\
#!/bin/sh

module load nvhpc

if [ -n "$NVHPC_ROOT" ]; then
  export NVCC="$NVHPC_ROOT/compilers/bin/nvcc"
  export CUDA_PATH="$NVHPC_ROOT/cuda"
else
  echo "Warning: NVHPC_ROOT was not set after 'module load nvhpc'." >&2
fi
"""

    unset_vars_script = """\
#!/bin/sh

unset NVCC
unset CUDA_PATH
module unload nvhpc
"""

    set_vars_path = activate_dir / "set_vars.sh"
    try:
        with open(set_vars_path, "w") as f:
            f.write(set_vars_script)
        os.chmod(set_vars_path, 0o755)
    except IOError as e:
        print(f"Error writing activation script: {e}", file=sys.stderr)
        sys.exit(1)

    unset_vars_path = deactivate_dir / "unset_vars.sh"
    try:
        with open(unset_vars_path, "w") as f:
            f.write(unset_vars_script)
        os.chmod(unset_vars_path, 0o755)
    except IOError as e:
        print(f"Error writing deactivation script: {e}", file=sys.stderr)
        sys.exit(1)