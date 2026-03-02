import json
from .base import LLMProvider

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


class GroqClient(LLMProvider):
    """Groq LLM provider — ultra-fast LPU inference"""

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        if not GROQ_AVAILABLE:
            raise ImportError(
                "groq not installed. Install with: pip install groq"
            )
        self.client = Groq(api_key=api_key)
        self.model = model
        self.tokens = {"input": 0, "output": 0}

    def generate(self, raw_text: str, system_prompt: str):
        response = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"{raw_text}\n\nOutput ONLY valid JSON.",
                },
            ],
            model=self.model,
            max_tokens=8192,
            temperature=0.7,
            response_format={"type": "json_object"},
        )

        text = response.choices[0].message.content

        if hasattr(response, "usage") and response.usage:
            self.tokens["input"] += getattr(response.usage, "prompt_tokens", 0)
            self.tokens["output"] += getattr(response.usage, "completion_tokens", 0)

        return self._parse(text)

    def _parse(self, text: str):
        clean = text.strip()
        if clean.startswith("```json"):
            clean = clean[7:]
        if clean.startswith("```"):
            clean = clean[3:]
        if clean.endswith("```"):
            clean = clean[:-3]
        return json.loads(clean.strip())

    def get_stats(self):
        return {
            "provider": "groq",
            "model": self.model,
            "total_input_tokens": self.tokens["input"],
            "total_output_tokens": self.tokens["output"],
        }
