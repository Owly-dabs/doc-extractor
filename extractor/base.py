from abc import ABC, abstractmethod

class DocstringExtractor(ABC):
    @property
    @abstractmethod
    def suffix(self) -> list[str]:
        """File suffix (e.g., '.py')"""
        pass
    
    @abstractmethod
    def extract_docstrings(self, code: str) -> list[dict]:
        """Extract docstrings from a single file"""
        pass