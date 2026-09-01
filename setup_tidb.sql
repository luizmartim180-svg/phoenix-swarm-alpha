-- Phoenix Swarm Alpha - Schema Completo para Hackathon IA em Escala
-- Execute este script ANTES do evento no TiDB Cloud Console > Chat2Query ou SQL Editor

CREATE DATABASE IF NOT EXISTS phoenix_alpha;
USE phoenix_alpha;

-- Tabela principal: incidentes de infraestrutura com embeddings
CREATE TABLE IF NOT EXISTS infra_incidents (
    id VARCHAR(36) PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_system VARCHAR(50) NOT NULL,
    severity TINYINT NOT NULL CHECK (severity BETWEEN 1 AND 5),
    description TEXT NOT NULL,
    root_cause TEXT,
    resolution TEXT,
    embedding VECTOR(1024) COMMENT 'Titan V2 embeddings (1024)',
    metadata JSON COMMENT 'Contexto adicional estruturado',
    INDEX idx_severity (severity),
    INDEX idx_source (source_system)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

ALTER TABLE infra_incidents ADD VECTOR INDEX idx_vec_cosine ((embedding) WITH (DISTANCE=COSINE, TYPE=HNSW));

-- Estado compartilhado do swarm (memória transacional entre agentes)
CREATE TABLE IF NOT EXISTS swarm_state (
    task_id VARCHAR(36) NOT NULL,
    agent_id VARCHAR(50) NOT NULL,
    phase ENUM('DETECT','ANALYZE','BRANCH_TEST','APPLY','REJECT') NOT NULL,
    state_data JSON NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (task_id, agent_id),
    INDEX idx_updated (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Log de decisões do Executor (audit trail para branching)
CREATE TABLE IF NOT EXISTS branch_decisions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    task_id VARCHAR(36) NOT NULL,
    branch_name VARCHAR(100) NOT NULL,
    action ENUM('CREATED','TESTED','MERGED','DISCARDED') NOT NULL,
    llm_evaluation JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_task (task_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
