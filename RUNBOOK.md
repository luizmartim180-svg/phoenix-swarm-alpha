# RUNBOOK - Phoenix Swarm Alpha

This runbook contains quick steps to run the demo offline and live.

## Offline demo (safe)
1. python -m venv .venv
2. .\.venv\Scripts\python.exe -m pip install -r requirements.txt
3. .\.venv\Scripts\python.exe -m pytest -q tests/test_branching.py
4. .\.venv\Scripts\python.exe run_loop.py --once
5. View outputs/insights_offline.md for insights

## Live demo (requires .env)
1. Copy .env.example to .env and fill credentials (DO NOT commit)
2. .\.venv\Scripts\python.exe -m pip install -r requirements.txt
3. .\.venv\Scripts\python.exe scripts/debug_cycle.py --sanity
4. .\.venv\Scripts\python.exe run_loop.py --once

## Notes
- Do not commit .env or secrets. Use GitHub Secrets for CI.
- To publish CI workflow, use a PAT with 'workflow' scope after the event.
