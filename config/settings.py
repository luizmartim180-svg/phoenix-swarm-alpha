import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # TiDB
    TIDB_HOST: str = os.getenv("TIDB_HOST", "")
    TIDB_USER: str = os.getenv("TIDB_USER", "")
    TIDB_PASSWORD: str = os.getenv("TIDB_PASSWORD", "")
    TIDB_DB: str = os.getenv("TIDB_DB", "phoenix_alpha")
    TIDB_PORT: int = int(os.getenv("TIDB_PORT", 4000))
    
    # TiDB Cloud API
    TIDB_PROJECT_ID: str = os.getenv("TIDB_PROJECT_ID", "")
    TIDB_PUBLIC_KEY: str = os.getenv("TIDB_PUBLIC_KEY", "")
    TIDB_PRIVATE_KEY: str = os.getenv("TIDB_PRIVATE_KEY", "")
    
    # AWS
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    BEDROCK_EMBED_MODEL: str = os.getenv("BEDROCK_EMBED_MODEL", "amazon.titan-embed-text-v2")
    BEDROCK_CHAT_MODEL: str = os.getenv("BEDROCK_CHAT_MODEL", "anthropic.claude-3-haiku-20240307-v1:0")
    
    # Validation
    @classmethod
    def validate(cls):
        missing = [k for k,v in cls.__dict__.items() if not v and k.isupper()]
        if missing:
            raise ValueError(f"Missing env vars: {missing}")

settings = Settings()
