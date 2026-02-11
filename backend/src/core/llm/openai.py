import json
from openai import OpenAI
from .base import LLMProvider

class OpenAIClient(LLMProvider):
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4-turbo-preview"
        self.tokens = {"input": 0, "output": 0}
        self.cost = 0.0

    def generate(self, raw_text: str, system_prompt: str):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": raw_text}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=2048
        )
        
        if response.usage:
            self._track(response.usage.prompt_tokens, response.usage.completion_tokens)
            
        return json.loads(response.choices[0].message.content)

    def _track(self, i, o):
        self.tokens["input"] += i
        self.tokens["output"] += o
        self.cost += (i/1000)*0.01 + (o/1000)*0.03

    def get_stats(self):
        return {
            "provider": "openai",
            "model": self.model,
            "total_input_tokens": self.tokens["input"],
            "total_output_tokens": self.tokens["output"],
            "estimated_cost_usd": round(self.cost, 6)
        }
