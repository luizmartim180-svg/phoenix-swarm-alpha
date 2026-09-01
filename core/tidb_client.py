import pymysql
import json
import requests
import logging
import platform
import os
from typing import List, Dict, Any, Optional
from config.settings import settings

logger = logging.getLogger(__name__)

class TiDBClient:
    """Cliente otimizado para TiDB Cloud Serverless com suporte a Vector Search e Branching"""
    
    def __init__(self):
        settings.validate()
        self._conn = None
    
    @property
    def conn(self):
        if self._conn is None or not getattr(self._conn, 'open', True):
            # SSL CA path depends on platform; Windows typically uses the OS store
            default_ca = None if platform.system() == "Windows" else "/etc/ssl/certs/ca-certificates.crt"
            ca = getattr(settings, 'TIDB_SSL_CA', None) or default_ca
            ssl_arg = {"ca": ca} if ca else {}
            self._conn = pymysql.connect(
                host=settings.TIDB_HOST,
                user=settings.TIDB_USER,
                password=settings.TIDB_PASSWORD,
                database=settings.TIDB_DB,
                port=settings.TIDB_PORT,
                ssl=ssl_arg,
                connect_timeout=10,
                charset="utf8mb4"
            )
        return self._conn
    
    def hybrid_search(self, query_embedding: List[float], filters: Optional[Dict] = None, limit: int = 5) -> List[Dict]:
        """Busca vetorial semântica + filtros relacionais em única query HTAP"""
        sql = """
            SELECT id, description, root_cause, resolution, severity, metadata,
                   embedding <=> %s AS similarity_score
            FROM infra_incidents
            WHERE 1=1
        """
        params: list = [str(query_embedding)]
        
        if filters:
            if "min_severity" in filters:
                sql += " AND severity >= %s"
                params.append(filters["min_severity"])
            if "source_system" in filters:
                sql += " AND source_system = %s"
                params.append(filters["source_system"])
        
        sql += " ORDER BY similarity_score ASC LIMIT %s"
        params.append(limit)
        
        with self.conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(sql, params)
            results = cur.fetchall()
            logger.info(f"Hybrid search returned {len(results)} results")
            return results
    
    def create_branch(self, branch_name: str) -> Dict[str, Any]:
        """Cria branch serverless isolado via TiDB Cloud API"""
        url = f"https://api.tidbcloud.com/v1beta/projects/{settings.TIDB_PROJECT_ID}/branches"
        payload = {"name": branch_name, "cluster_id": settings.TIDB_PROJECT_ID}
        
        resp = requests.post(
            url, json=payload,
            auth=(settings.TIDB_PUBLIC_KEY, settings.TIDB_PRIVATE_KEY),
            timeout=30
        )
        resp.raise_for_status()
        branch_data = resp.json()
        logger.info(f"Branch '{branch_name}' created: {branch_data.get('id')}")
        return branch_data
    
    def update_swarm_state(self, task_id: str, agent_id: str, phase: str, state_data: Dict):
        """Atualiza estado compartilhado atomicamente entre agentes"""
        sql = """
            INSERT INTO swarm_state (task_id, agent_id, phase, state_data)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                phase = VALUES(phase),
                state_data = VALUES(state_data),
                updated_at = NOW()
        """
        with self.conn.cursor() as cur:
            cur.execute(sql, (task_id, agent_id, phase, json.dumps(state_data)))
            self.conn.commit()
            logger.debug(f"State updated: {agent_id}@{phase} for task {task_id}")
    
    def log_branch_decision(self, task_id: str, branch_name: str, action: str, evaluation: Dict):
        """Registra auditoria de decisão de branching"""
        sql = """
            INSERT INTO branch_decisions (task_id, branch_name, action, llm_evaluation)
            VALUES (%s, %s, %s, %s)
        """
        with self.conn.cursor() as cur:
            cur.execute(sql, (task_id, branch_name, action, json.dumps(evaluation)))
            self.conn.commit()
    
    def close(self):
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None
