#!/usr/bin/env python3
"""
Gera embeddings reais via Bedrock para os 50 registros seed do TiDB.
EXECUTE ESTE SCRIPT APÓS RODAR setup_tidb.sql E ANTES DO HACKATHON.
"""
import pymysql
import boto3
import json
import time
from config.settings import settings


def main():
    conn = pymysql.connect(
        host=settings.TIDB_HOST, user=settings.TIDB_USER,
        password=settings.TIDB_PASSWORD, database=settings.TIDB_DB,
        port=settings.TIDB_PORT, ssl={"ca": "/etc/ssl/certs/ca-certificates.crt"}
    )
    bedrock = boto3.client("bedrock-runtime", region_name=settings.AWS_REGION)
    
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute("SELECT id, description, root_cause, resolution FROM infra_incidents WHERE embedding IS NULL")
        rows = cur.fetchall()
    
    print(f"📊 Encontrados {len(rows)} registros sem embedding. Gerando...")
    
    for i, row in enumerate(rows):
        text = f"{row['description']}. Root cause: {row['root_cause']}. Resolution: {row['resolution']}"
        
        try:
            resp = bedrock.invoke_model(
                modelId=settings.BEDROCK_EMBED_MODEL,
                body=json.dumps({"inputText": text[:8192]})
            )
            embedding = json.loads(resp["body"].read())["embedding"]
            
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE infra_incidents SET embedding = %s WHERE id = %s",
                    (str(embedding), row["id"])
                )
                conn.commit()
            
            print(f"  ✅ [{i+1}/{len(rows)}] {row['id']}")
            time.sleep(0.1)  # Rate limiting
            
        except Exception as e:
            print(f"  ❌ [{i+1}/{len(rows)}] {row['id']}: {e}")
    
    conn.close()
    print("🎉 Geração de embeddings concluída!")

if __name__ == "__main__":
    main()
