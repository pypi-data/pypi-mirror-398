"""Abstract base class for vendor adapters."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Any

from ..models import Response


class VendorAdapter(ABC):
    """
    Abstract base class for AI vendor adapters.
    
    All vendor implementations must inherit from this class and implement
    the required methods. The adapter is responsible for:
    1. Uploading files to vendor's File API
    2. Sending chat requests
    3. Returning raw, unmodified AI responses
    """
    
    def __init__(
        self,
        api_key: str,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        **kwargs
    ):
        """
        Initialize adapter.
        
        Args:
            api_key: Vendor API key.
            model: Model name to use. If None, adapter's DEFAULT_MODEL is used.
            base_url: Optional custom API endpoint (for relays/proxies).
            timeout: Optional request timeout in seconds.
            **kwargs: Additional vendor-specific options.
        """
        if not api_key:
            raise ValueError("API key is required")
        
        self.api_key = api_key
        self.model = model  # Allow None, subclass will use DEFAULT_MODEL
        self.base_url = base_url
        self.timeout = timeout
        self.options = kwargs
    
    @abstractmethod
    def chat(
        self,
        prompt: str,
        files: Optional[List[Path]] = None,
        **kwargs
    ) -> Response:
        """
        Send a chat request to the AI model.
        
        Args:
            prompt: User prompt text.
            files: Optional list of file paths to include (will be uploaded via File API).
            **kwargs: Additional request parameters (temperature, max_tokens, etc.)
        
        Returns:
            Response object with raw content and usage stats.
        """
        ...
    
    @abstractmethod
    def upload_file(self, file_path: Path) -> str:
        """
        Upload a file to the vendor's File API.
        
        Args:
            file_path: Path to the file to upload.
        
        Returns:
            File ID or URI for referencing in chat requests.
        """
        ...
    
    def _validate_file(self, file_path: Path) -> Path:
        """Validate that file exists and return resolved path."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return path.resolve()
