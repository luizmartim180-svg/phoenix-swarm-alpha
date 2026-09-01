# RUNBOOK - Phoenix Swarm Alpha

## Pre-evento (setup com credenciais reais)
1. Copie .env.example para .env e preencha credenciais reais (NUNCA commitar)
2. Execute setup_tidb.sql no TiDB Cloud Console (SQL Editor)
3. .venv\Scripts\python.exe scripts/load_seed.py (gera 50 embeddings via Bedrock)
4. .venv\Scripts\python.exe -m pytest -q tests/test_branching.py (modo LIVE, esperado 5 passed)
5. .venv\Scripts\python.exe -m streamlit run app.py (demo visual)

## Durante o evento (02/09/2026, State, 14h)
13h30 chegada + Wi-Fi | 14h sessoes tecnicas | 16h mostrar branching aos juizes | 18h pitch | 19h happy hour com QR code do repo

## Fallback se Wi-Fi falhar
- pytest roda em modo MOCK sem .env
- Streamlit funciona com seed ja carregado
- Omega offline: cd ..\phoenix-swarm-omega && .venv\Scripts\python.exe run_loop.py --once

## Emergencia
- Recriar venv: rmdir /s /q .venv & python -m venv .venv & .venv\Scripts\python.exe -m pip install -e ".[dev]"
- Sanity TiDB+Bedrock: .venv\Scripts\python.exe scripts/debug_cycle.py --sanity
