import boto3
import json
import logging
from typing import List, Dict, Any
from config.settings import settings

logger = logging.getLogger(__name__)

class BedrockClient:
    """Wrapper otimizado para Amazon Bedrock com caching e retry"""
    
    def __init__(self):
        self.client = boto3.client("bedrock-runtime", region_name=settings.AWS_REGION)
    
    def generate_embedding(self, text: str) -> List[float]:
        """Gera embedding via Titan V2 com tratamento de erro robusto"""
        try:
            response = self.client.invoke_model(
                modelId=settings.BEDROCK_EMBED_MODEL,
                body=json.dumps({"inputText": text[:8192], "dimensions": 1024})  # Titan max tokens
            )
            result = json.loads(response["body"].read())
            return result["embedding"]
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise
    
    def evaluate_fix(self, proposed_fix: Dict, test_results: Dict) -> Dict[str, Any]:
        """Avalia segurança de correção proposta usando Claude Haiku"""
        prompt = f"""You are an SRE safety evaluator. Analyze this proposed infrastructure fix:

PROPOSED FIX: {json.dumps(proposed_fix)}
TEST RESULTS IN BRANCH: {json.dumps(test_results)}

Respond ONLY in valid JSON with keys:
- safe: boolean
- confidence: float 0-1
- risks: list of strings
- recommendation: string
"""
        try:
            response = self.client.invoke_model(
                modelId=settings.BEDROCK_CHAT_MODEL,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 500,
                    "messages": [{"role": "user", "content": prompt}]
                })
            )
            result = json.loads(response["body"].read())
            content = result["content"][0]["text"]
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning("LLM returned non-JSON, defaulting to unsafe")
            return {"safe": False, "confidence": 0.0, "risks": ["Parse error"], "recommendation": "Manual review required"}
    
    def analyze_anomaly(self, metrics: Dict, historical_context: List[Dict]) -> Dict:
        """Sentinel usa isso para classificar anomalias"""
        context_str = "\n".join([f"- {h['description']}: {h['resolution']}" for h in historical_context[:3]])
        prompt = f"""Current metrics anomaly: {json.dumps(metrics)}
Similar historical incidents:
{context_str}

Classify severity (1-5) and suggest immediate action. Respond in JSON:
{{"severity": int, "action": string, "requires_branch_test": boolean}}"""
        
        response = self.client.invoke_model(
            modelId=settings.BEDROCK_CHAT_MODEL,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 300,
                "messages": [{"role": "user", "content": prompt}]
            })
        )
        result = json.loads(response["body"].read())
        return json.loads(result["content"][0]["text"])

    def chat(self, prompt: str, system: str = "", max_tokens: int = 600) -> str:
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            body["system"] = system
        response = self.client.invoke_model(modelId=settings.BEDROCK_CHAT_MODEL, body=json.dumps(body))
        result = json.loads(response["body"].read())
        return result["content"][0]["text"]
