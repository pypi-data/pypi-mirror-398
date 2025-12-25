'''boot.py

Entry point for reproducible jobs.

This script:
  * Validates that main.py and reqs.txt exist.
  * Reads the expected Python version from reqs.txt.
  * Imports configuration from conf.py (ENV_MODE, JOB_DESCRIPTION, INCLUDE, EXCLUDE, INHERIT_MODE).
  * Creates a timestamped job directory under jobs/.
  * Copies or links the current project (with optional include/exclude rules).
  * Handles environment setup according to ENV_MODE.
  * Optionally checks that the job environment's Python matches reqs.txt.
  * Writes a job-local README describing how to run the job.
  * Runs main.py inside the job directory.
'''

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import re
from datetime import datetime, UTC
from typing import Optional

DOTFILE = ".jobdir"


def _read_python_version_from_reqs(reqs_path: str) -> Optional[str]:
    """Return the python version string (e.g. '3.12.11') from reqs.txt or None."""
    if not os.path.isfile(reqs_path):
        print("Error: reqs.txt not found next to boot.py.", file=sys.stderr)
        sys.exit(1)

    with open(reqs_path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line.startswith("#"):
                continue
            m = re.search(r"python=([0-9]+\\.[0-9]+\\.[0-9]+)", line)
            if m:
                return m.group(1)
    return None


def _venv_python_path(venv_path: str) -> str:
    """Return the absolute path to the Python executable inside a venv."""
    if os.name == "nt":
        return os.path.join(venv_path, "Scripts", "python.exe")
    return os.path.join(venv_path, "bin", "python")


def get_timestamp() -> str:
    """Return current time in a filesystem-safe format: YYYY-MM-DD-HH-MM-SS-mmm."""
    return datetime.now(UTC).strftime("%Y-%m-%d-%H-%M-%S-%f")[:-3]


# ---------------------------------------------------------------------------
# Job README generation helpers (inlined here to keep jobs self-contained)
# ---------------------------------------------------------------------------

def _inherit_info_block(inherit_mode: str) -> str:
    """Return a short description of how files were inherited."""
    if inherit_mode == "link":
        return (
            "- Directory structure is recreated in the job.\n"
            "- Core files (main.py, conf.py, reqs.txt, venv.sh) are copied.\n"
            "- Other files may be symlinked back to the template folder.\n"
        )
    return "- Files and directories were fully copied from the template folder.\n"


def _python_line(expected_py: Optional[str]) -> str:
    """Return the 'required Python version' line."""
    if expected_py:
        return f"- **Required Python version:** {expected_py}"
    return "- **Required Python version:** not specified"


def _env_and_run_blocks(env_mode: str) -> tuple[str, str]:
    """Return (ENV_INFO, RUN_INFO) blocks based on ENV_MODE."""
    if env_mode == "deferred_venv":
        env_info = (
            "`ENV_MODE='deferred_venv'`: the environment is **not** created yet.\n\n"
            "1. Ensure your `python` matches the version in `reqs.txt`.\n"
            "2. Run:\n\n"
            "   ```bash\n"
            "   ./venv.sh\n"
            "   ```\n\n"
            "3. Activate the virtual environment:\n\n"
            "- Unix/macOS: `source .venv/bin/activate`\n"
            "- Windows cmd: `.venv\\\\Scripts\\\\activate.bat`\n"
            "- Windows PowerShell: `.venv\\\\Scripts\\\\Activate.ps1`\n\n"
            "To deactivate, run `deactivate`.\n"
        )
        run_info = (
            "After `venv.sh` has completed and `.venv` is activated:\n\n"
            "```bash\n"
            "python main.py\n"
            "```"
        )
    else:
        env_info = (
            "A `.venv` directory should already exist in this folder.\n\n"
            "Activate it using:\n\n"
            "- Unix/macOS: `source .venv/bin/activate`\n"
            "- Windows cmd: `.venv\\\\Scripts\\\\activate.bat`\n"
            "- Windows PowerShell: `.venv\\\\Scripts\\\\Activate.ps1`\n\n"
            "To deactivate, run `deactivate`.\n"
        )
        run_info = (
            "With `.venv` activated:\n\n"
            "```bash\n"
            "python main.py\n"
            "```"
        )
    return env_info, run_info


def _build_readme_text(
    env_mode: str,
    expected_py: Optional[str],
    inherit_mode: str,
) -> str:
    """Return the full README.md text for a job directory."""
    inherit_info = _inherit_info_block(inherit_mode).strip()
    python_line = _python_line(expected_py).strip()
    env_info, run_info = _env_and_run_blocks(env_mode)
    env_info = env_info.strip()
    run_info = run_info.strip()

    parts: list[str] = []

    parts.append("# Job directory")
    parts.append("")
    parts.append("This folder is a self-contained snapshot of a single run.")
    parts.append("The file `.jobdir` marks this as a job directory.")
    parts.append("")
    parts.append(inherit_info)
    parts.append("")
    parts.append(python_line)
    parts.append("")
    parts.append("## Environment setup")
    parts.append("")
    parts.append(env_info)
    parts.append("")
    parts.append("## Running the job")
    parts.append("")
    parts.append(run_info)
    parts.append("")
    parts.append("All paths in your code should be relative to this directory (`./`).")

    return "\n".join(parts)


def write_job_readme(
    jobdir: str,
    env_mode: str,
    expected_py: Optional[str],
    inherit_mode: str,
) -> None:
    """Write README.md into `jobdir` describing how to run the job."""
    text = _build_readme_text(env_mode=env_mode, expected_py=expected_py, inherit_mode=inherit_mode)
    readme_path = os.path.join(jobdir, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(text)


# ---------------------------------------------------------------------------
# Main boot logic
# ---------------------------------------------------------------------------

def main() -> None:
    """Main entry for boot.py.

    Creates a job directory, prepares its environment, writes a job README,
    and runs main.py inside the job directory.
    """
    # Resolve project root as the folder containing this boot.py
    boot_path = os.path.abspath(__file__)
    project_root = os.path.dirname(boot_path)

    # Require main.py before anything else
    main_src = os.path.join(project_root, "main.py")
    if not os.path.isfile(main_src):
        print("Error: main.py not found next to boot.py.", file=sys.stderr)
        sys.exit(1)

    # Require reqs.txt and read expected Python version (if specified)
    reqs_path = os.path.join(project_root, "reqs.txt")
    expected_py = _read_python_version_from_reqs(reqs_path)

    # Import configuration (ENV_MODE, JOB_DESCRIPTION, INCLUDE, EXCLUDE, INHERIT_MODE)
    try:
        import conf as CFG
    except ImportError:
        print("Error: conf.py not found or import failed.", file=sys.stderr)
        sys.exit(1)

    env_mode = getattr(CFG, "ENV_MODE", "link_parent")
    job_desc = getattr(CFG, "JOB_DESCRIPTION", "job")
    include = getattr(CFG, "INCLUDE", None)
    exclude = getattr(CFG, "EXCLUDE", None)
    inherit_mode = getattr(CFG, "INHERIT_MODE", "copy")

    if include and exclude:
        print("Error: Only one of INCLUDE or EXCLUDE may be set in conf.py.", file=sys.stderr)
        sys.exit(1)

    if inherit_mode not in ("copy", "link"):
        print("Error: INHERIT_MODE must be 'copy' or 'link'.", file=sys.stderr)
        sys.exit(1)

    # Files that must always be brought into the job, regardless of INCLUDE/EXCLUDE
    # and always copied (never linked).
    ALWAYS_COPY = {"main.py", "conf.py", "reqs.txt", "venv.sh"}

    # If mode uses parent .venv, it must exist
    project_venv = os.path.join(project_root, ".venv")
    if env_mode in ("copy_parent", "link_parent"):
        if not os.path.isdir(project_venv):
            print(
                f"Error: ENV_MODE={env_mode!r} requires parent .venv at {project_venv!r}.",
                file=sys.stderr,
            )
            sys.exit(1)

    # If deferred mode, venv.sh must exist to be shipped into the job dir
    if env_mode == "deferred_venv":
        venv_script = os.path.join(project_root, "venv.sh")
        if not os.path.isfile(venv_script):
            print(
                "Error: ENV_MODE='deferred_venv' requires venv.sh next to boot.py.",
                file=sys.stderr,
            )
            sys.exit(1)

    # Prepare jobs/<timestamp>-<job_description> directory
    ts = get_timestamp()
    job_label = f"{ts}-{job_desc}" if job_desc else ts

    jobs_root = os.path.join(project_root, "jobs")
    os.makedirs(jobs_root, exist_ok=True)
    jobdir = os.path.join(jobs_root, job_label)
    os.makedirs(jobdir, exist_ok=True)

    print(f"[mups] Created job directory: {jobdir}")

    # Copy or link project into jobdir
    for name in os.listdir(project_root):
        # Skip jobs dir and dotfiles
        if name == "jobs" or name.startswith("."):
            continue

        # Never copy the template README; each job gets its own README
        if name.lower().startswith("readme"):
            continue

        # Never copy boot.py into the job directory
        if name == "boot.py":
            continue

        src = os.path.join(project_root, name)

        # Apply INCLUDE / EXCLUDE filters, but never drop ALWAYS_COPY
        if include is not None:
            if (name not in include) and (name not in ALWAYS_COPY):
                continue
        elif exclude is not None:
            if (name in exclude) and (name not in ALWAYS_COPY):
                continue

        dst = os.path.join(jobdir, name)

        if os.path.isdir(src):
            # Directories: recreate structure, then apply INHERIT_MODE to files inside
            for dirpath, dirnames, filenames in os.walk(src):
                rel_sub = os.path.relpath(dirpath, src)
                if rel_sub == ".":
                    target_dir = dst
                else:
                    target_dir = os.path.join(dst, rel_sub)
                os.makedirs(target_dir, exist_ok=True)

                for fname in filenames:
                    src_file = os.path.join(dirpath, fname)
                    dst_file = os.path.join(target_dir, fname)

                    # Core filenames are always copied, even inside subdirs if they appear
                    if fname in ALWAYS_COPY or inherit_mode == "copy":
                        shutil.copy2(src_file, dst_file)
                    else:
                        try:
                            os.symlink(src_file, dst_file)
                        except (NotImplementedError, OSError):
                            shutil.copy2(src_file, dst_file)
        else:
            # Top-level files: core files always copied, others depend on INHERIT_MODE
            if name in ALWAYS_COPY or inherit_mode == "copy":
                shutil.copy2(src, dst)
            else:
                try:
                    os.symlink(src, dst)
                except (NotImplementedError, OSError):
                    shutil.copy2(src, dst)

    # Mark job directory so code can detect it's inside a run
    open(os.path.join(jobdir, DOTFILE), "w").close()

    # Write a job-specific README
    write_job_readme(jobdir, env_mode=env_mode, expected_py=expected_py, inherit_mode=inherit_mode)

    # Handle env modes that actively manage a .venv
    job_venv = os.path.join(jobdir, ".venv")

    if env_mode == "new_venv":
        completed = subprocess.run([sys.executable, "-m", "venv", job_venv])
        if completed.returncode != 0:
            print("Error: failed to create new venv in jobdir.", file=sys.stderr)
            sys.exit(completed.returncode)

        job_reqs = os.path.join(jobdir, "reqs.txt")
        job_python = _venv_python_path(job_venv)
        completed = subprocess.run(
            [job_python, "-m", "pip", "install", "-r", job_reqs]
        )
        if completed.returncode != 0:
            print("Error: failed to install requirements in job venv.", file=sys.stderr)
            sys.exit(completed.returncode)

    elif env_mode == "copy_parent":
        if os.path.exists(job_venv):
            shutil.rmtree(job_venv)
        shutil.copytree(project_venv, job_venv)

    elif env_mode == "link_parent":
        if os.path.islink(job_venv) or os.path.exists(job_venv):
            if os.path.isdir(job_venv) and not os.path.islink(job_venv):
                print(
                    f"Error: {job_venv!r} exists and is not a symlink; cannot link parent venv.",
                    file=sys.stderr,
                )
                sys.exit(1)
            os.unlink(job_venv)
        try:
            os.symlink(project_venv, job_venv, target_is_directory=True)
        except OSError as e:
            print(f"Error: failed to create symlink to parent venv: {e}", file=sys.stderr)
            sys.exit(1)

    elif env_mode == "deferred_venv":
        job_venv = None

    else:
        print(f"Error: unknown ENV_MODE={env_mode!r}.", file=sys.stderr)
        sys.exit(1)

    # If we actually have a venv, check python version inside it (if requested)
    if env_mode in ("new_venv", "copy_parent", "link_parent"):
        job_python = _venv_python_path(job_venv)
        if not os.path.isfile(job_python):
            print(
                f"Error: Python interpreter not found in job venv at {job_python!r}.",
                file=sys.stderr,
            )
            sys.exit(1)

        if expected_py is not None:
            proc = subprocess.run(
                [
                    job_python,
                    "-c",
                    "import sys; v=sys.version_info; "
                    "print(f'{v[0]}.{v[1]}.{v[2]}')",
                ],
                capture_output=True,
                text=True,
            )
            if proc.returncode != 0:
                print("Error: failed to query Python version in job venv.", file=sys.stderr)
                sys.exit(proc.returncode)

            actual_py = proc.stdout.strip()
            if actual_py != expected_py:
                print(
                    f"Error: reqs.txt expects python={expected_py}, "
                    f"but job venv uses python={actual_py}.",
                    file=sys.stderr),
                sys.exit(1)

        completed = subprocess.run([job_python, "main.py"], cwd=jobdir)
        sys.exit(completed.returncode)

    else:
        completed = subprocess.run([sys.executable, "main.py"], cwd=jobdir)
        sys.exit(completed.returncode)


if __name__ == "__main__":
    main()
