from abc import ABC, abstractmethod
from typing import List, Dict

class LLMService(ABC):
    @abstractmethod
    def chat(self, messages: List[Dict], temperature: float = 0.0) -> str:
        ...

    def generate_sql_json(self, messages: List[Dict], temperature: float = 0.0) -> dict:
        import json
        text = self.chat(messages, temperature)
        return json.loads(text)

    def markdown(self, messages: List[Dict], temperature: float = 0.0) -> str:
        return self.chat(messages, temperature)
