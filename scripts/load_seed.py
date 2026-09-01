#!/usr/bin/env python3
"""Carrega data/seed_incidents.json no TiDB gerando embeddings (1024 dims) via Bedrock."""
import json, time, platform, os
import pymysql, boto3
from pathlib import Path
from config.settings import settings

SEED_FILE = Path(__file__).parent.parent / "data" / "seed_incidents.json"


def connect():
    default_ca = None if platform.system() == "Windows" else "/etc/ssl/certs/ca-certificates.crt"
    ca = os.getenv("TIDB_SSL_CA", getattr(settings, 'TIDB_SSL_CA', None) or default_ca)
    ssl_arg = {"ca": ca} if ca else {}
    return pymysql.connect(host=settings.TIDB_HOST, user=settings.TIDB_USER,
                           password=settings.TIDB_PASSWORD, database=settings.TIDB_DB,
                           port=settings.TIDB_PORT, ssl=ssl_arg, charset="utf8mb4")


def main():
    records = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    print(f"📦 {len(records)} registros no seed")
    conn = connect()
    bedrock = boto3.client("bedrock-runtime", region_name=settings.AWS_REGION)
    for i, rec in enumerate(records, 1):
        text = f"{rec['description']}. Root cause: {rec['root_cause']}. Resolution: {rec['resolution']}"
        resp = bedrock.invoke_model(modelId=settings.BEDROCK_EMBED_MODEL,
                                    body=json.dumps({"inputText": text[:8192], "dimensions": 1024}))
        embedding = json.loads(resp["body"].read())["embedding"]
        with conn.cursor() as cur:
            cur.execute("""INSERT INTO infra_incidents
                           (id, source_system, severity, description, root_cause, resolution, embedding, metadata)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                           ON DUPLICATE KEY UPDATE embedding=VALUES(embedding)""",
                         (rec["id"], rec["source_system"], rec["severity"], rec["description"],
                          rec["root_cause"], rec["resolution"], str(embedding), json.dumps(rec.get("metadata", {}))))
        conn.commit()
        print(f"  ✅ [{i}/{len(records)}] {rec['id']}")
        time.sleep(0.1)
    conn.close()
    print("🎉 Seed concluído com embeddings de 1024 dims")


if __name__ == "__main__":
    main()
