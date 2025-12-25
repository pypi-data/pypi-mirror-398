"""AIBridge - Unified AI model bridge."""

from pathlib import Path
from typing import List, Optional, Union

from .config import load_config, get_vendor_config
from .models import Response, VendorType
from .vendors import get_adapter, VendorAdapter


class AIBridge:
    """
    Main entry point for AI Bridge.
    
    Provides a unified interface to call different AI vendor models.
    
    Example:
        >>> from aib import AIBridge
        >>> bridge = AIBridge(vendor="gemini")
        >>> response = bridge.chat("Hello!")
        >>> print(response.content)
    """
    
    def __init__(
        self,
        vendor: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        config_path: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize AIBridge.
        
        Args:
            vendor: Vendor name (gemini, kimi, qwen, openai). 
                   Defaults to config default_vendor.
            api_key: API key. If not provided, loaded from config/env.
            model: Model name. If not provided, loaded from config.
            base_url: Custom API endpoint (for relays/proxies).
            timeout: Request timeout in seconds. Defaults to None (no timeout).
            config_path: Path to config file.
            **kwargs: Additional vendor-specific options.
        """
        # Load configuration
        self.config = load_config(config_path)
        
        # Determine vendor
        self.vendor = vendor or self.config.get("default_vendor", "gemini")
        
        # Validate vendor
        valid_vendors = ["gemini", "openai", "kimi", "qwen"]
        if self.vendor not in valid_vendors:
            raise ValueError(
                f"Invalid vendor: '{self.vendor}'. "
                f"Must be one of {valid_vendors}"
            )
        
        vendor_config = get_vendor_config(self.config, self.vendor)
        
        # Merge parameters (explicit > config > default)
        self.api_key = api_key or vendor_config.get("api_key")
        self.model = model or vendor_config.get("model")
        self.base_url = base_url or vendor_config.get("base_url")
        self.timeout = timeout or vendor_config.get("timeout")
        
        if not self.api_key:
            raise ValueError(f"No API key found for vendor '{self.vendor}'. "
                           f"Set via AIB_{self.vendor.upper()}_API_KEY env var or config file.")
        
        # Note: model is optional - adapters have DEFAULT_MODEL that will be used if not specified
        
        # Create adapter
        self._adapter: VendorAdapter = get_adapter(
            vendor=self.vendor,
            api_key=self.api_key,
            model=self.model,
            base_url=self.base_url,
            timeout=self.timeout,
            **kwargs
        )
    
    def chat(
        self,
        prompt: str,
        files: Optional[List[Union[str, Path]]] = None,
        **kwargs
    ) -> Response:
        """
        Send a chat request to the AI model.
        
        Args:
            prompt: User prompt text.
            files: Optional list of file paths to include.
                   Files are uploaded to vendor's File API.
            **kwargs: Additional request parameters (temperature, max_tokens, etc.)
        
        Returns:
            Response object containing:
            - content: Raw AI response (unmodified)
            - usage: Token usage statistics
            - raw: Original SDK response object
        
        Example:
            >>> response = bridge.chat("Summarize this document", files=["doc.pdf"])
            >>> print(response.content)
            >>> print(f"Tokens used: {response.usage.total_tokens}")
        """
        # Convert string paths to Path objects
        file_paths = None
        if files:
            file_paths = [Path(f) for f in files]
        
        return self._adapter.chat(prompt=prompt, files=file_paths, **kwargs)
    
    def upload_file(self, file_path: Union[str, Path]) -> str:
        """
        Upload a file to the vendor's File API.
        
        Useful when you need to reference the same file in multiple requests.
        
        Args:
            file_path: Path to the file.
        
        Returns:
            File ID or URI for referencing.
        """
        return self._adapter.upload_file(Path(file_path))
    
    @property
    def adapter(self) -> VendorAdapter:
        """Access the underlying vendor adapter for advanced operations."""
        return self._adapter
