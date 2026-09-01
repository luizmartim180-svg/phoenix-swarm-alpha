import os
import json
import uuid
import pytest

REQUIRED_ENV = ["TIDB_HOST", "TIDB_USER", "TIDB_PASSWORD"]
MODE = "live" if all(os.getenv(k) for k in REQUIRED_ENV) else "mock"
print(f"\n[pytest] Executando em modo: {MODE.upper()}")


class FakeTiDB:
    def __init__(self):
        self.states = {}
        self.decisions = []

    def hybrid_search(self, query_embedding, filters=None, limit=5):
        return [{"id": "inc-001",
                 "description": "Lambda timeout spike in payment processing",
                 "root_cause": "Cold start",
                 "resolution": "Increase memory + connection pooling",
                 "severity": 4, "metadata": "{}", "similarity_score": 0.12}]

    def create_branch(self, branch_name):
        return {"id": f"br-{uuid.uuid4().hex[:8]}", "name": branch_name}

    def update_swarm_state(self, task_id, agent_id, phase, state_data):
        self.states[(task_id, agent_id)] = {"phase": phase, "state_data": state_data}

    def log_branch_decision(self, task_id, branch_name, action, evaluation):
        self.decisions.append({"task_id": task_id, "branch": branch_name, "action": action})

    def close(self):
        pass


class FakeBedrock:
    def generate_embedding(self, text):
        return [0.1] * 1024

    def evaluate_fix(self, proposal, test_results):
        return {"safe": True, "confidence": 0.95, "risks": [], "recommendation": "proceed"}

    def analyze_anomaly(self, metrics, historical_context):
        return {"severity": 3, "action": "scale compute and add pooling", "requires_branch_test": True}

    def chat(self, prompt, system="", max_tokens=600):
        return json.dumps({"fix_type": "config_change",
                           "description": "Increase lambda memory",
                           "parameters": {"memory_mb": 1024},
                           "estimated_risk": "low",
                           "test_plan": "Apply in branch and compare p99 latency"})


@pytest.fixture()
def clients(monkeypatch):
    if MODE == "mock":
        fake_tidb, fake_bedrock = FakeTiDB(), FakeBedrock()
        for mod_name in ("agents.sentinel", "agents.architect", "agents.executor"):
            mod = __import__(mod_name, fromlist=["x"])
            monkeypatch.setattr(mod, "TiDBClient", lambda: fake_tidb)
            monkeypatch.setattr(mod, "BedrockClient", lambda: fake_bedrock)
        return fake_tidb, fake_bedrock
    from core.tidb_client import TiDBClient
    from core.bedrock_client import BedrockClient
    return TiDBClient(), BedrockClient()


def test_embedding_dimension(clients):
    _, bedrock = clients
    assert len(bedrock.generate_embedding("sanity")) == 1024


def test_sentinel_detects_and_classifies(clients):
    from agents.sentinel import SentinelAgent
    out = SentinelAgent().detect_anomaly({"source_system": "aws-lambda", "severity": 3,
                                          "description": "Latency spike in payment pipeline"})
    assert out["task_id"]
    assert out["classification"]["severity"] in (1, 2, 3, 4, 5)
    assert out["next_agent"] in ("architect", "monitor")


def test_architect_proposes_valid_json(clients):
    from agents.architect import ArchitectAgent
    out = ArchitectAgent().propose_solution({"task_id": str(uuid.uuid4()),
                                             "classification": {"severity": 3, "action": "scale compute",
                                                                "requires_branch_test": True}})
    assert out["proposal"]["fix_type"] in ("config_change", "code_patch", "scaling", "rollback")
    assert out["proposal"]["estimated_risk"] in ("low", "medium", "high")


def test_executor_branch_lifecycle(clients):
    from agents.executor import ExecutorAgent
    out = ExecutorAgent().execute_safe_fix({"task_id": str(uuid.uuid4()),
                                            "proposal": {"fix_type": "config_change", "description": "x",
                                                         "parameters": {}, "estimated_risk": "low", "test_plan": "y"}})
    assert out["action"] in ("MERGED", "DISCARDED", "FAILED")
    if MODE == "mock":
        assert out["action"] == "MERGED"
        assert out["branch_name"].startswith("fix-")


def test_full_swarm_cycle(clients):
    from core.swarm_orchestrator import SwarmOrchestrator
    result = SwarmOrchestrator().run_cycle({"source_system": "tidb-cluster", "severity": 3,
                                            "description": "Read latency due to compaction"})
    assert result["status"] == "COMPLETED"
    assert result["final_action"] in ("MERGED", "DISCARDED")
