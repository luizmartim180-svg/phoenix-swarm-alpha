"""
Phoenix Swarm Alpha - Dashboard Interativo
Demonstração visual do swarm para hackathon e stakeholders.
"""
import streamlit as st
import json
import time
from datetime import datetime
from core.swarm_orchestrator import SwarmOrchestrator
from core.tidb_client import TiDBClient

st.set_page_config(page_title="Phoenix Swarm Alpha", page_icon="🏗️", layout="wide")

# --- Header ---
st.title("🏗️ Phoenix Swarm Alpha")
st.caption("Infraestrutura Auto-Curável com Agentes Autônomos | TiDB Cloud + Amazon Bedrock")

# --- Sidebar: Simulação de Métricas ---
st.sidebar.header("⚙️ Simular Anomalia")
source = st.sidebar.selectbox("Sistema", ["aws-lambda", "tidb-cluster", "bedrock-api", "k8s-pod"])
severity = st.sidebar.slider("Severidade Inicial", 1, 5, 3)
desc = st.sidebar.text_area("Descrição", "Latency spike in payment processing pipeline")

if st.sidebar.button("🚀 Disparar Ciclo do Swarm", type="primary"):
    metrics = {
        "source_system": source,
        "severity": severity,
        "description": desc,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    orchestrator = SwarmOrchestrator()
    
    with st.spinner("Swarm executando ciclo completo..."):
        result = orchestrator.run_cycle(metrics)
    
    st.session_state["last_result"] = result
    st.rerun()

# --- Main Area: Resultados ---
if "last_result" in st.session_state:
    result = st.session_state["last_result"]
    
    # Status Banner
    status = result.get("status", "UNKNOWN")
    color = {"COMPLETED": "green", "MONITORING_ONLY": "orange"}.get(status, "red")
    st.markdown(f"### Status: :{color}[{status}]")
    
    # 3 Colunas para cada agente
    cols = st.columns(3)
    
    agent_configs = [
        ("sentinel", "🔍 Sentinel", "Detecção & Classificação"),
        ("architect", "🏛️ Architect", "Busca Semântica & Proposta"),
        ("executor", "⚡ Executor", "Branching Seguro & Aplicação")
    ]
    
    for col, (key, title, subtitle) in zip(cols, agent_configs):
        with col:
            st.subheader(title)
            st.caption(subtitle)
            phase_data = result.get("phases", {}).get(key, {})
            
            if phase_data:
                st.json(phase_data, expanded=False)
                
                # Indicadores visuais específicos
                if key == "sentinel":
                    sev = phase_data.get("classification", {}).get("severity", "?")
                    st.metric("Severidade Classificada", sev)
                elif key == "architect":
                    st.metric("Contextos Usados", phase_data.get("context_used", 0))
                elif key == "executor":
                    action = phase_data.get("action", "?")
                    emoji = {"MERGED": "✅", "DISCARDED": "❌", "FAILED": "💥"}.get(action, "❓")
                    st.metric("Resultado", f"{emoji} {action}")
            else:
                st.info("Aguardando execução...")
    
    # Erros
    if "error" in result:
        st.error(f"⚠️ Erro no ciclo: {result['error']}")

else:
    st.info("👈 Configure uma anomalia na sidebar e clique em 'Disparar Ciclo do Swarm' para iniciar.")

# --- Footer: Arquitetura ---
st.divider()
with st.expander("📐 Arquitetura do Sistema"):
    st.markdown("""
    ```mermaid
    graph LR
        A[Métricas AWS] --> B[Sentinel Agent]
        B -->|Vector Search| C[(TiDB Cloud)]
        B --> D[Architect Agent]
        D -->|Hybrid Query| C
        D --> E[Executor Agent]
        E -->|Create Branch| F[TiDB Serverless Branch]
        F -->|Test & Evaluate| E
        E -->|Merge/Discard| C
        C --> G[Audit Trail]
    ```
    """)
