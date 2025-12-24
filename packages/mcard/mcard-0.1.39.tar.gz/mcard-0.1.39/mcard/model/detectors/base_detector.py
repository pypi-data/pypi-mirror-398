from abc import ABC, abstractmethod
from typing import List, Optional

class BaseDetector(ABC):
    """
    Abstract base class for content type detectors.
    """

    @property
    @abstractmethod
    def content_type_name(self) -> str:
        """The name of the content type this detector identifies (e.g., 'python', 'json')."""
        pass

    @abstractmethod
    def detect(self, content_sample: str, lines: List[str], first_line: str, file_extension: Optional[str] = None) -> float:
        """
        Analyzes the content and returns a confidence score for this detector's content type.

        Args:
            content_sample: A string sample of the content (typically the first few KB).
            lines: A list of lines from the beginning of the content.
            first_line: The very first line of the content.
            file_extension: The file extension, if available (e.g., '.py', '.txt').

        Returns:
            A float between 0.0 (not this type) and 1.0 (definitely this type).
        """
        pass
