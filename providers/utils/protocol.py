from typing import Protocol

class GenerationClient(Protocol):
    def __init__(self):
        ...

    def create(self, messages: list[dict], stream: bool = False, async_mode: bool = False, temperature: float = 0.8, top_p: int = 1, **kwargs):
        ...