# Phoenix Swarm Alpha 🏗️🤖

> **Infraestrutura Auto-Curável com Agentes Autônomos, TiDB Vector Search e Serverless Branching**

Projeto desenvolvido para o **AWS × TiDB Builders Day: IA em Escala** (São Paulo, 02/09/2026).

## 🎯 O Problema
Agentes de IA autônomos operam em loops contínuos, gerando milhares de operações imprevisíveis. Bancos tradicionais não oferecem isolamento seguro para testes de correções automáticas, nem unificam busca semântica com dados transacionais em escala.

## 💡 A Solução
Um swarm de 3 agentes especializados que:
1. **Detecta** anomalias em tempo real (Sentinel)
2. **Busca** soluções históricas via vector search híbrido (Architect)
3. **Testa** correções em branch isolado antes de aplicar em produção (Executor)

Tudo rodando sobre **TiDB Cloud Serverless na AWS** + **Amazon Bedrock**.

## 🚀 Quick Start (Hackathon Setup < 5 min)
```bash
git clone https://github.com/seu-user/phoenix-swarm-alpha.git
cd phoenix-swarm-alpha
cp .env.example .env  # Preencha com suas credenciais
pip install -r requirements.txt
streamlit run app.py
