from .Document import factory
from abc import ABC, abstractmethod
definitions = factory()

class LLMClient(ABC):
    @abstractmethod
    def __init__(self):
        self.field_for_answer = definitions.field_for_llm
    @abstractmethod
    def answer(self, _question, _top_k_docs) -> tuple[str, float, int, dict]:
        raise NotImplementedError
