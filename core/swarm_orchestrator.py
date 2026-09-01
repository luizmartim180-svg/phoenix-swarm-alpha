"""
Orquestrador do Swarm Alpha
Coordena o fluxo sequencial Sentinel → Architect → Executor
com estado compartilhado persistido no TiDB.
"""
import logging
from typing import Dict, Any, Optional
from agents.sentinel import SentinelAgent
from agents.architect import ArchitectAgent
from agents.executor import ExecutorAgent

logger = logging.getLogger(__name__)


class SwarmOrchestrator:
    """Orquestra o ciclo completo de auto-curaçãoo de infraestrutura."""

    def __init__(self):
        self.sentinel = SentinelAgent()
        self.architect = ArchitectAgent()
        self.executor = ExecutorAgent()

    def run_cycle(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa ciclo completo do swarm.
        Retorna dicionário com todos os resultados de cada fase.
        """
        logger.info("=" * 60)
        logger.info("🚀 INICIANDO CICLO DO SWARM ALPHA")
        logger.info("=" * 60)

        results = {"phases": {}}

        # Fase 1: Detecção
        try:
            sentinel_out = self.sentinel.detect_anomaly(metrics)
            results["phases"]["sentinel"] = sentinel_out
        except Exception as e:
            logger.error(f"Sentinel falhou: {e}", exc_info=True)
            results["error"] = f"Sentinel: {e}"
            return results

        # Verifica se precisa de intervenção
        if sentinel_out.get("next_agent") != "architect":
            logger.info("⏸️  Anomalia não requer ação automática. Monitorando.")
            results["status"] = "MONITORING_ONLY"
            return results

        # Fase 2: Proposição
        try:
            architect_out = self.architect.propose_solution(sentinel_out)
            results["phases"]["architect"] = architect_out
        except Exception as e:
            logger.error(f"Architect falhou: {e}", exc_info=True)
            results["error"] = f"Architect: {e}"
            return results

        # Fase 3: Execução Segura
        try:
            executor_out = self.executor.execute_safe_fix(architect_out)
            results["phases"]["executor"] = executor_out
        except Exception as e:
            logger.error(f"Executor falhou: {e}", exc_info=True)
            results["error"] = f"Executor: {e}"
            return results

        results["status"] = "COMPLETED"
        results["final_action"] = executor_out.get("action", "UNKNOWN")

        logger.info("=" * 60)
        logger.info(f"✅ CICLO CONCLUÍDO | Ação final: {results['final_action']}")
        logger.info("=" * 60)

        return results
