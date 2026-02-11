import json
from pathlib import Path
from .base import LLMProvider

class MockClient(LLMProvider):
    def generate(self, raw_text: str, system_prompt: str):
        # Locate example file relative to src/core/llm/mock.py -> ../../../examples
        path = Path(__file__).parent.parent.parent.parent / "examples" / "expected_output.json"
        with open(path, "r") as f:
            return json.load(f)

    def get_stats(self):
        return {
            "provider": "mock",
            "model": "mock",
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "estimated_cost_usd": 0.0
        }
