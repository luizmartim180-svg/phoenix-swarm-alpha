"""
Agente Sentinel: Monitoramento e Detecção de Anomalias
Responsável por analisar métricas em tempo real e classificar severidade
usando contexto histórico via vector search no TiDB.
"""
import uuid
import logging
from typing import Dict, Any
from core.tidb_client import TiDBClient
from core.bedrock_client import BedrockClient

logger = logging.getLogger(__name__)


class SentinelAgent:
    AGENT_ID = "sentinel"

    def __init__(self):
        self.tidb = TiDBClient()
        self.bedrock = BedrockClient()

    def detect_anomaly(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analisa métricas atuais, busca contexto histórico similar,
        e classifica a anomalia com recomendação de ação.
        """
        task_id = str(uuid.uuid4())
        logger.info(f"[Sentinel] Nova anomalia detectada | task={task_id}")

        # Atualiza estado inicial
        self.tidb.update_swarm_state(
            task_id=task_id,
            agent_id=self.AGENT_ID,
            phase="DETECT",
            state_data={"metrics": metrics, "status": "analyzing"}
        )

        # Gera embedding da descrição da anomalia para busca contextual
        anomaly_desc = f"{metrics.get('source_system', 'unknown')}: {metrics.get('description', 'no description')}"
        query_embedding = self.bedrock.generate_embedding(anomaly_desc)

        # Busca incidentes históricos similares (vector + filtro relacional)
        historical_context = self.tidb.hybrid_search(
            query_embedding=query_embedding,
            filters={"min_severity": 2},
            limit=3
        )
        logger.info(f"[Sentinel] Encontrados {len(historical_context)} incidentes similares")

        # Classifica com LLM usando contexto histórico
        classification = self.bedrock.analyze_anomaly(metrics, historical_context)

        # Persiste resultado
        result = {
            "task_id": task_id,
            "classification": classification,
            "historical_matches": len(historical_context),
            "next_agent": "architect" if classification.get("requires_branch_test", False) else "monitor"
        }

        self.tidb.update_swarm_state(
            task_id=task_id,
            agent_id=self.AGENT_ID,
            phase="DETECT",
            state_data=result
        )

        logger.info(f"[Sentinel] Classificação completa: severity={classification.get('severity')}")
        return result
