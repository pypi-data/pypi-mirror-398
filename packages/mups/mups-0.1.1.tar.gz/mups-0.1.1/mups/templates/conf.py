'''conf.py

Configuration for the job launcher.

Variables:
  * ENV_MODE        : how to handle the .venv for each job.
  * JOB_DESCRIPTION : short, directory-safe string describing the job, used in job folder names.
  * INCLUDE / EXCLUDE : control which files/folders are copied into jobs.
  * INHERIT_MODE    : how non-venv files are inherited into jobs (copy vs link).
'''

# How to handle the .venv for each job:
#   "new_venv"      -> create a fresh venv in the job folder and install from reqs.txt
#   "copy_parent"   -> copy the parent .venv into the job folder
#   "link_parent"   -> symlink the parent .venv into the job folder
#   "deferred_venv" -> do not touch .venv; use venv.sh in the job dir to create it later
ENV_MODE = "link_parent"

# Short, directory-compatible job description (no spaces or path separators recommended).
# This string becomes part of the job directory name: <timestamp>-<JOB_DESCRIPTION>
JOB_DESCRIPTION = "my_job"

# How non-venv files are inherited into each job:
#   "copy" -> copy all files into the job directory.
#   "link" -> symlink files from the template into the job directory.
#
# Directory structure is always recreated in the job.
# Core files (main.py, conf.py, reqs.txt, venv.sh) are always copied, never linked.
INHERIT_MODE = "copy"  # or "link"

# Copy filtering:
# Only one of INCLUDE or EXCLUDE should be non-None.
#
# - INCLUDE: list of names (files or top-level folders) that should be copied/linked.
#            Only these will be included, plus core files:
#            main.py, conf.py, reqs.txt, venv.sh.
#
# - EXCLUDE: list of names that should NOT be copied/linked.
#            Everything else will be included, plus the same core files.
#
# NOTE:
#   - main.py is ALWAYS brought into every job (copied).
#   - conf.py, reqs.txt, venv.sh are ALWAYS copied.
#   - boot.py is NEVER copied/linked into jobs, regardless of INCLUDE/EXCLUDE.
#   - The parent README is never copied; each job gets its own README instead.
INCLUDE = None      # e.g. ["main.py", "src", "config"]
EXCLUDE = None      # e.g. ["data", "notes", "tmp"]
