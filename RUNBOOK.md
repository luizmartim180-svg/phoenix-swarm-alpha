# 🏆 Runbook de Execução - Hackathon IA em Escala

## Pré-evento (hoje, até meia-noite)
```powershell
cd D:\phoenix-swarm-alpha

# 1. Preencha o .env com credenciais REAIS
notepad .env

# 2. Execute o schema no TiDB Cloud Console > SQL Editor (cole setup_tidb.sql)

# 3. Carregue o seed com embeddings reais (gera 50 embeddings via Bedrock)
.venv\Scripts\python.exe scripts/load_seed.py

# 4. Valide em modo LIVE (conexão real TiDB + Bedrock)
.venv\Scripts\python.exe -m pytest -q tests/test_branching.py

# 5. Teste a demo visual
.venv\Scripts\python.exe -m streamlit run app.py
```

## Durante o evento (02/09/2026 - 14h no State)
1. **13h30** - Chegue, conecte no Wi-Fi, identifique juízes da AWS/TiDB
2. **14h** - Sessões técnicas: anote palavras-chave dos engenheiros
3. **15h** - `git pull` para pegar qualquer ajuste remoto
4. **16h** - Convide juiz para ver branching funcionando
5. **17h** - Finalize ajustes de prompts baseados em feedback
6. **18h** - Pitch + premiação
7. **19h** - Happy hour: QR code com arquitetura + contatos

## Fallback se Wi-Fi falhar
- Use o modo MOCK dos testes (não requer .env)
- Demo local via Streamlit funciona com dados seed já carregados
- Pitch pode ser feito offline com screenshots do .venv

## Comandos de emergência
```powershell
# Recriar venv do zero
rmdir /s /q .venv
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"

# Testar só conexão TiDB (sem Bedrock)
.venv\Scripts\python.exe -c "from core.tidb_client import TiDBClient; t=TiDBClient(); print('✅ TiDB OK'); t.close()"

# Testar só Bedrock (sem TiDB)
.venv\Scripts\python.exe -c "from core.bedrock_client import BedrockClient; b=BedrockClient(); print('✅ Bedrock client OK')"
```
