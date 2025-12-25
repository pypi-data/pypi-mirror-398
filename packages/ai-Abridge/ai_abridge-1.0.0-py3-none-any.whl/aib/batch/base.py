"""Base classes for batch processing."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class BatchStatus(str, Enum):
    """Batch job status."""
    PENDING = "pending"
    VALIDATING = "validating"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass
class BatchJob:
    """
    Batch job information.
    
    Attributes:
        id: Job ID from vendor.
        vendor: Vendor name.
        model: Model used.
        status: Current status.
        created_at: Creation timestamp.
        total_requests: Total number of requests.
        completed_requests: Number of completed requests.
        output_file_id: ID of output file (when completed).
    """
    id: str
    vendor: str
    model: str
    status: BatchStatus = BatchStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    total_requests: int = 0
    completed_requests: int = 0
    output_file_id: Optional[str] = None
    error: Optional[str] = None


class BaseBatchManager(ABC):
    """
    Abstract base class for batch job managers.
    
    Batch processing allows submitting many requests at once for
    significant cost savings (typically 50% off).
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None
    ):
        """
        Initialize batch manager.
        
        Args:
            api_key: Vendor API key.
            base_url: Optional custom API endpoint.
            timeout: Optional request timeout in seconds.
        """
        if not api_key:
            raise ValueError("API key is required")
        
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
    
    @abstractmethod
    def submit(
        self,
        requests: List[Dict[str, Any]],
        model: str,
        **kwargs
    ) -> BatchJob:
        """
        Submit a batch job.
        
        Args:
            requests: List of request dictionaries, each containing:
                - prompt: The prompt text
                - files: Optional list of file paths
            model: Model name to use.
            **kwargs: Additional options.
        
        Returns:
            BatchJob with job ID and initial status.
        """
        ...
    
    @abstractmethod
    def get_status(self, job_id: str) -> BatchJob:
        """
        Get status of a batch job.
        
        Args:
            job_id: Job ID from submit().
        
        Returns:
            BatchJob with current status.
        """
        ...
    
    @abstractmethod
    def get_results(self, job_id: str) -> Dict[str, str]:
        """
        Get results of a completed batch job.
        
        Args:
            job_id: Job ID of a completed job.
        
        Returns:
            Dictionary mapping request ID to response content.
        """
        ...
    
    @abstractmethod
    def cancel(self, job_id: str) -> bool:
        """
        Cancel a running batch job.
        
        Args:
            job_id: Job ID to cancel.
        
        Returns:
            True if cancelled successfully.
        """
        ...
