"""
Agente Architect: Busca Semântica e Proposição de Soluções
Usa vector search híbrido no TiDB para encontrar resoluções históricas
e gera propostas de correção estruturadas via Bedrock.
"""
import logging
from typing import Dict, Any, List
from core.tidb_client import TiDBClient
from core.bedrock_client import BedrockClient

logger = logging.getLogger(__name__)


class ArchitectAgent:
    AGENT_ID = "architect"

    SYSTEM_PROMPT = """You are an infrastructure architect specializing in AI-native systems.
Given an anomaly classification and historical incident matches, propose a concrete fix.

Respond ONLY in valid JSON:
{
  "fix_type": "config_change|code_patch|scaling|rollback",
  "description": "Human-readable fix description",
  "parameters": {"key": "value"},
  "estimated_risk": "low|medium|high",
  "test_plan": "Steps to validate in isolated branch"
}"""

    def __init__(self):
        self.tidb = TiDBClient()
        self.bedrock = BedrockClient()

    def propose_solution(self, sentinel_result: Dict[str, Any]) -> Dict[str, Any]:
        """Gera proposta de correção baseada em contexto histórico e classificação."""
        task_id = sentinel_result["task_id"]
        classification = sentinel_result["classification"]
        logger.info(f"[Architect] Gerando solução para task={task_id}")

        self.tidb.update_swarm_state(
            task_id=task_id,
            agent_id=self.AGENT_ID,
            phase="ANALYZE",
            state_data={"status": "generating_proposal"}
        )

        # Busca resoluções históricas com maior similaridade
        anomaly_desc = classification.get("action", "infrastructure anomaly")
        embedding = self.bedrock.generate_embedding(anomaly_desc)
        matches = self.tidb.hybrid_search(query_embedding=embedding, limit=5)

        # Formata contexto para LLM
        context_lines = []
        for m in matches:
            context_lines.append(
                f"- [{m['severity']}] {m['description']} → Resolution: {m['resolution']}"
            )
        context_str = "\n".join(context_lines) if context_lines else "No historical matches found."

        prompt = f"""Anomaly Classification: {classification}

Historical Resolutions:
{context_str}

Propose a fix following the JSON schema."""

        # Chama Bedrock para gerar proposta
        import boto3, json
        client = boto3.client("bedrock-runtime", region_name="us-east-1")
        response = client.invoke_model(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 600,
                "system": self.SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": prompt}]
            })
        )
        result_body = json.loads(response["body"].read())
        proposal = json.loads(result_body["content"][0]["text"])

        output = {
            "task_id": task_id,
            "proposal": proposal,
            "context_used": len(matches),
            "next_agent": "executor"
        }

        self.tidb.update_swarm_state(
            task_id=task_id,
            agent_id=self.AGENT_ID,
            phase="ANALYZE",
            state_data=output
        )

        logger.info(f"[Architect] Proposta gerada: type={proposal.get('fix_type')}, risk={proposal.get('estimated_risk')}")
        return output
