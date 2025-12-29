"""
OpenAI Client Service
"""

import json
from openai import OpenAI
from typing import Dict, Any

from app.config.settings import get_settings


class OpenAIClient:
    """OpenAI API Client"""

    def __init__(self):
        settings = get_settings()
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.max_tokens = settings.max_tokens
        self.temperature = settings.temperature

    def evaluate_rule(self, prompt: str) -> Dict[str, Any]:
        """
        Gửi prompt đến GPT và nhận kết quả đánh giá

        Args:
            prompt: Prompt đánh giá rule

        Returns:
            Dict chứa kết quả đánh giá
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Bạn là chuyên gia đánh giá hồ sơ bảo hiểm. Trả lời bằng JSON format."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )

            response_text = response.choices[0].message.content

            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)

            raise ValueError("No valid JSON in response")

        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")


# Singleton instance
_openai_client = None


def get_openai_client() -> OpenAIClient:
    """Get OpenAI client singleton"""
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAIClient()
    return _openai_client
