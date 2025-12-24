from abc import ABC, abstractmethod


class BaseSchemaGenerator(ABC):
    def __init__(self, config, messages):
        self.config = config
        self.messages = messages

    @abstractmethod
    def generate(self, renditions, packaging, name: str = ""):
        pass
