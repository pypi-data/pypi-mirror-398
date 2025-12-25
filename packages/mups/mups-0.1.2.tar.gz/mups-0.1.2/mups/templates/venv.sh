#!/usr/bin/env bash
# venv.sh
#
# Recreate a local virtual environment (.venv) for a job directory, using reqs.txt.
# This is meant to be run on another machine that receives a job folder snapshot.

set -euo pipefail

if [[ ! -f "reqs.txt" ]]; then
    echo "reqs.txt not found in current directory." >&2
    exit 1
fi

# Read required python version from reqs.txt comment lines
required_py=""
while IFS= read -r line; do
    line="${line//$'\r'/}"
    if [[ "$line" =~ ^#.*python=([0-9]+\.[0-9]+\.[0-9]+) ]]; then
        required_py="${BASH_REMATCH[1]}"
        break
    fi
done < reqs.txt

if [[ -z "$required_py" ]]; then
    echo "No python version comment found in reqs.txt (expected a line with 'python=X.Y.Z')." >&2
    exit 1
fi

# Query current python version
if ! command -v python >/dev/null 2>&1; then
    echo "'python' command not found in PATH." >&2
    exit 1
fi

current_py=$(python - << 'EOF'
import sys
v = sys.version_info
print(f"{v[0]}.{v[1]}.{v[2]}")
EOF
)

if [[ "$current_py" != "$required_py" ]]; then
    echo "Python version mismatch: reqs.txt expects $required_py but 'python' is $current_py." >&2
    exit 1
fi

echo "Python version matches ($required_py). Creating virtual environment in .venv"

python -m venv .venv

if [[ "$(uname -s)" == MINGW* || "$(uname -s)" == CYGWIN* ]]; then
    venv_python=".venv/Scripts/python.exe"
else
    venv_python=".venv/bin/python"
fi

if [[ ! -x "$venv_python" ]]; then
    echo "Expected venv python not found at $venv_python" >&2
    exit 1
fi

# Upgrade pip
"$venv_python" -m pip install --upgrade pip

"$venv_python" -m pip install -r reqs.txt
echo "Virtual environment created and requirements installed."
