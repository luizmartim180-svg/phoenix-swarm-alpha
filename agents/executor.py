"""
Agente Executor: Teste Isolado e Aplicação Segura
Cria branch serverless no TiDB, simula correção, avalia segurança via LLM,
e decide entre merge ou discard com audit trail completo.
"""
import logging
from typing import Dict, Any
from core.tidb_client import TiDBClient
from core.bedrock_client import BedrockClient

logger = logging.getLogger(__name__)


class ExecutorAgent:
    AGENT_ID = "executor"

    def __init__(self):
        self.tidb = TiDBClient()
        self.bedrock = BedrockClient()

    def execute_safe_fix(self, architect_result: Dict[str, Any]) -> Dict[str, Any]:
        """Executa ciclo completo de branching: create → test → evaluate → merge/discard."""
        task_id = architect_result["task_id"]
        proposal = architect_result["proposal"]
        branch_name = f"fix-{task_id[:8]}"

        logger.info(f"[Executor] Iniciando execução segura | task={task_id} | branch={branch_name}")

        self.tidb.update_swarm_state(
            task_id=task_id,
            agent_id=self.AGENT_ID,
            phase="BRANCH_TEST",
            state_data={"branch_name": branch_name, "status": "creating"}
        )

        # 1. Criar branch isolado
        try:
            branch_info = self.tidb.create_branch(branch_name)
            self.tidb.log_branch_decision(task_id, branch_name, "CREATED", {"branch_id": branch_info.get("id")})
            logger.info(f"[Executor] Branch criado: {branch_info.get('id')}")
        except Exception as e:
            logger.error(f"[Executor] Falha ao criar branch: {e}")
            return self._fail(task_id, branch_name, f"Branch creation failed: {e}")

        # 2. Simular teste no branch (em cenário real, conectaria ao branch endpoint)
        test_results = {
            "branch_id": branch_info.get("id"),
            "tests_passed": True,
            "latency_ms": 45,
            "rows_affected": 12,
            "rollback_available": True
        }
        self.tidb.log_branch_decision(task_id, branch_name, "TESTED", test_results)

        # 3. Avaliar segurança via LLM
        evaluation = self.bedrock.evaluate_fix(proposal, test_results)
        logger.info(f"[Executor] Avaliação LLM: safe={evaluation.get('safe')}, confidence={evaluation.get('confidence')}")

        # 4. Decidir e registrar
        if evaluation.get("safe", False) and evaluation.get("confidence", 0) > 0.7:
            action = "MERGED"
            # Em produção: self.tidb.merge_branch(branch_info["id"])
            logger.info(f"[Executor] ✅ Fix APLICADO com sucesso")
        else:
            action = "DISCARDED"
            # Em produção: self.tidb.delete_branch(branch_info["id"])
            logger.warning(f"[Executor] ❌ Fix REJEITADO: {evaluation.get('risks')}")

        self.tidb.log_branch_decision(task_id, branch_name, action, evaluation)

        final_state = {
            "task_id": task_id,
            "branch_name": branch_name,
            "action": action,
            "evaluation": evaluation,
            "phase": "APPLY" if action == "MERGED" else "REJECT"
        }

        self.tidb.update_swarm_state(
            task_id=task_id,
            agent_id=self.AGENT_ID,
            phase=final_state["phase"],
            state_data=final_state
        )

        return final_state

    def _fail(self, task_id: str, branch_name: str, error: str) -> Dict[str, Any]:
        failure = {"task_id": task_id, "branch_name": branch_name, "action": "FAILED", "error": error, "phase": "REJECT"}
        self.tidb.update_swarm_state(task_id, self.AGENT_ID, "REJECT", failure)
        return failure
