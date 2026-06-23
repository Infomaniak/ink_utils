# Copilot Coding Agent Onboarding — ink_utils (Ink)

## Overview
Ink is a Python CLI tool that automates tedious development tasks for Infomaniak Android projects: importing translation strings from Loco, AI-assisted translation, ADB shortcuts, cross-app login config, and more. Entry point: `main.py`. The CLI alias is `ink`.

**Language**: Python 3. **No Android/Gradle**. Dependencies: `pyyaml`, `inquirer`, `requests` (see `requirements.txt`).

## One-Time Setup
```bash
pip install -r requirements.txt          # install dependencies
cp settings.yml.example settings.yml    # copy config template
# Edit settings.yml: fill in project names, Loco API keys, ADB device paths, etc.
```
`settings.yml` is git-ignored — never commit it.

## Run
```bash
python3 main.py                          # interactive menu
# Or via alias (after setup):
ink <command>
```

## Tests & Lint
No automated test suite. No CI workflows. Validate changes by running the relevant command interactively.

## Project Layout
```
main.py                   # Entry point — argparse routing to subcommands
config.py                 # Reads settings.yml, exposes project config
settings.yml.example      # Config template — document new fields here
settings.yml              # Local config (git-ignored)
requirements.txt          # Python runtime dependencies (pyyaml, inquirer, requests)
adb.py / adb_prop.py      # ADB helpers
loco_updater.py           # Loco string import logic
translate/                # AI translation commands
login.py                  # Cross-app login utilities
updater.py                # Self-update / git pull logic
```

## Key Rules
- `settings.yml` is git-ignored — always update `settings.yml.example` when adding new config fields.
- Keep the CLI backwards compatible — `ink` is used as a shell alias in many dev setups.
- Python 3 only; no f-string syntax older than 3.6.
- When adding a new runtime dependency, add it to `requirements.txt` **and** update `LICENSES.md`.
