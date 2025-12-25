# Job template directory

This directory has been turned into a *job template* using mups (Multi Use PipelineS).

You develop your code here as usual (starting from `main.py`), and each time you
run `boot.py`, it creates a timestamped job directory under `jobs/` containing a
snapshot of this folder:

- directory structure is recreated in the job
- files are either copied or symlinked depending on `INHERIT_MODE`
- core files are always copied

and then runs `main.py` inside that job.

## Files created by the generator

- `boot.py`  
  Launcher that:
  - creates a job directory under `jobs/`
  - copies or links this project into it (respecting `INCLUDE` / `EXCLUDE`)
  - sets up the environment according to `ENV_MODE`
  - writes a job-specific `README.md`
  - runs `main.py` inside the job directory

- `conf.py`  
  Configuration with:
  - `ENV_MODE`
  - `JOB_DESCRIPTION`
  - `INHERIT_MODE` (copy or link)
  - `INCLUDE` / `EXCLUDE`

  You can also add your own config variables here; they will be copied into
  each job and accessed as:

      import conf as CFG

- `reqs.txt`  
  Contains the Python version used when this template was created plus package
  requirements. For reproducibility, pin exact versions.

- `venv.sh`  
  Script for recreating a `.venv` inside a job (mainly for `deferred_venv` mode).

- `README.md`  
  This file. It is not copied into jobs.

## Copy / link rules

- `main.py`, `conf.py`, `reqs.txt`, `venv.sh` are always copied.
- `boot.py` is never copied or linked.
- Parent `README.md` is never copied.
- Job directory structure is always recreated.
- `INHERIT_MODE` controls non-core files:
  - `"copy"` copies files into the job
  - `"link"` symlinks files into the job
- `INCLUDE` selects only specific names (plus core files).
- `EXCLUDE` removes specific names (but not core files).

## Typical workflow

1. Edit `main.py` and supporting modules.
2. Set `ENV_MODE`, `JOB_DESCRIPTION`, `INHERIT_MODE`, and filters in `conf.py`.
3. Run:

       python boot.py

A new job appears under `jobs/` and runs `main.py` inside it.
