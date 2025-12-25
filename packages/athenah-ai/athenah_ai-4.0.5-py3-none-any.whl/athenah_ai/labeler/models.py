"""
Data models for AI Code Labeler.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ProcessingStatus(Enum):
    """Status of file processing"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ProcessingProgress:
    """Progress information for callbacks"""
    file_path: str
    status: ProcessingStatus
    current: int
    total: int
    message: str = ""
    error: Optional[str] = None
