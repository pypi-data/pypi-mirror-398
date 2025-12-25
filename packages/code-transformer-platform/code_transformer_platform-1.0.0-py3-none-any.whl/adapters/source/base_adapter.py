from abc import ABC, abstractmethod


class SourceParserAdapter(ABC):
    language: str

    @abstractmethod
    def parse(self, file_path: str):
        pass
