import os
import json
from .base import LLMProvider
from google.genai import client as genai_client

class GeminiClient(LLMProvider):
    COST_INPUT = 0.0001
    COST_OUTPUT = 0.0004
    
    def __init__(self, api_key):
        self.client = genai_client.Client(api_key=api_key)
        self.model = "gemini-flash-lite-latest"
        self.tokens = {"input": 0, "output": 0}
        self.cost = 0.0

    def generate(self, raw_text: str, system_prompt: str):
        prompt = f"{system_prompt}\n\nUSER RAW NOTES:\n{raw_text}\n\nOutput ONLY valid JSON."
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={
                "temperature": 0.3, 
                "max_output_tokens": 2048,
                "response_mime_type": "application/json"
            }
        )
        
        if hasattr(response, 'usage_metadata'):
            i = getattr(response.usage_metadata, 'prompt_token_count', 0)
            o = getattr(response.usage_metadata, 'candidates_token_count', 0)
            self._track(i, o)
            
        return self._parse(response.text)

    def _track(self, i, o):
        self.tokens["input"] += i
        self.tokens["output"] += o
        self.cost += (i/1000)*self.COST_INPUT + (o/1000)*self.COST_OUTPUT

    def _parse(self, text):
        clean = text.strip()
        if clean.startswith("```json"): clean = clean[7:]
        if clean.startswith("```"): clean = clean[3:]
        if clean.endswith("```"): clean = clean[:-3]
        return json.loads(clean.strip())

    def get_stats(self):
        return {
            "provider": "gemini",
            "model": self.model,
            "total_input_tokens": self.tokens["input"],
            "total_output_tokens": self.tokens["output"],
            "estimated_cost_usd": round(self.cost, 6)
        }
