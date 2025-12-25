"""
generator.py

Turn the given directory (default: current) into a reproducible "job template" by creating:
  - boot.py   : launcher that snapshots the project and runs jobs
  - reqs.txt  : Python version + package requirements
  - conf.py   : configuration (env mode, job description, include/exclude, inherit mode)
  - venv.sh   : helper script to create a .venv from reqs.txt on another machine
  - README.md : instructions for using THAT FOLDER as a job template
"""

from __future__ import annotations

import os
import sys
import shutil
from pathlib import Path
import sys as _sys

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"


def _copy_template_file(template_name: str, dest_path: str) -> None:
    """Copy a file from mups/templates/<template_name> to dest_path."""
    src_path = TEMPLATES_DIR / template_name
    if not src_path.is_file():
        raise FileNotFoundError(f"Template {src_path!r} not found")
    shutil.copyfile(src_path, dest_path)


def main() -> None:
    """Create boot.py, reqs.txt, conf.py, venv.sh, .gitignore and README.md in the target directory.

    Usage:
        python -m mups            # mupsify current directory
        python -m mups path/to/dir

    Existing reqs.txt, conf.py, venv.sh or README.md are left untouched with a warning.
    boot.py is never overwritten.
    """
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = "."

    template_root = Path(target).resolve()

    if not template_root.exists():
        print(f"Error: target path {str(template_root)!r} does not exist.", file=sys.stderr)
        sys.exit(1)
    if not template_root.is_dir():
        print(f"Error: target path {str(template_root)!r} is not a directory.", file=sys.stderr)
        sys.exit(1)

    boot_path = template_root / "boot.py"
    reqs_path = template_root / "reqs.txt"
    conf_path = template_root / "conf.py"
    venv_sh_path = template_root / "venv.sh"
    readme_path = template_root / "README.md"
    gitignore_path = template_root / "gitignore"

    # boot.py: must not exist (to avoid accidental overwrite)
    if boot_path.exists():
        print(f"Error: boot.py already exists in {str(template_root)!r}.", file=sys.stderr)
        sys.exit(1)

    # Write boot.py from template
    _copy_template_file("boot.py", str(boot_path))
    print(f"Created boot.py in {str(template_root)!r}")

    # reqs.txt: create or warn (generated directly)
    if reqs_path.exists():
        print("Warning: reqs.txt already exists, leaving it untouched.", file=sys.stderr)
    else:
        py_ver = _sys.version_info
        with reqs_path.open("w", encoding="utf-8") as f:
            f.write(f"# python={py_ver.major}.{py_ver.minor}.{py_ver.micro}\n")
            f.write("# IMPORTANT: specify exact versions (e.g. numpy==1.26.4) for reproducibility.\n")
            f.write("# add your package requirements below, one per line\n")
        print("Created reqs.txt")

    # conf.py: create or warn
    if conf_path.exists():
        print("Warning: conf.py already exists, leaving it untouched.", file=sys.stderr)
    else:
        _copy_template_file("conf.py", str(conf_path))
        print("Created conf.py")

    # venv.sh: create or warn
    if venv_sh_path.exists():
        print("Warning: venv.sh already exists, leaving it untouched.", file=sys.stderr)
    else:
        _copy_template_file("venv.sh", str(venv_sh_path))
        try:
            os.chmod(venv_sh_path, 0o755)
        except OSError:
            pass
        print("Created venv.sh")

    # README.md (template-folder README): create or warn
    if readme_path.exists():
        print("Warning: README.md already exists, leaving it untouched.", file=sys.stderr)
    else:
        _copy_template_file("README_TEMPLATE.md", str(readme_path))
        print("Created README.md")

    # .gitignore: create or warn
    if gitignore_path.exists():
        print("Warning: .gitignore already exists, leaving it untouched.", file=sys.stderr)
    else:
        _copy_template_file("gitignore", str(gitignore_path).replace("gitignore", ".gitignore")) # PyPI doesn't lake the template being a dotfile. 
        print("Created .gitignore")


if __name__ == "__main__":
    main()
