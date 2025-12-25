"""Kimi (Moonshot) adapter using OpenAI SDK."""

from pathlib import Path
from typing import List, Optional

from openai import OpenAI

from .base import VendorAdapter
from ..models import Response, Usage


class KimiAdapter(VendorAdapter):
    """
    Moonshot Kimi adapter using OpenAI SDK.
    
    Supports:
    - Native file processing via Files API (documents)
    - Image input via Files API
    - Custom base_url for proxies
    """
    
    # Default endpoint and model
    DEFAULT_BASE_URL = "https://api.moonshot.cn/v1"
    DEFAULT_MODEL = "moonshot-v1-auto"
    
    def __init__(
        self,
        api_key: str,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        **kwargs
    ):
        super().__init__(
            api_key=api_key,
            model=model or self.DEFAULT_MODEL,
            base_url=base_url or self.DEFAULT_BASE_URL,
            timeout=timeout,
            **kwargs
        )
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout
        )
    
    def upload_file(self, file_path: Path) -> str:
        """
        Upload file to Kimi Files API.
        
        Returns:
            File ID for use in chat requests.
        """
        path = self._validate_file(file_path)
        
        with open(path, "rb") as f:
            uploaded = self.client.files.create(file=f, purpose="file-extract")
        
        return uploaded.id
    
    def chat(
        self,
        prompt: str,
        files: Optional[List[Path]] = None,
        **kwargs
    ) -> Response:
        """
        Send chat request to Kimi.
        
        For files: uploads via File API and includes content in system message.
        """
        messages = []
        
        # Process files - upload and reference by fileid
        if files:
            for file_path in files:
                path = Path(file_path)
                file_id = self.upload_file(path)
                # Use fileid reference - let AI natively process the file
                messages.append({
                    "role": "system",
                    "content": f"fileid://{file_id}"
                })
        
        # Add user prompt
        messages.append({"role": "user", "content": prompt})
        
        # Build request params - let API use its own defaults
        request_kwargs = {
            "model": self.model,
            "messages": messages,
        }
        if "temperature" in kwargs:
            request_kwargs["temperature"] = kwargs.pop("temperature")
        if "max_tokens" in kwargs:
            request_kwargs["max_tokens"] = kwargs.pop("max_tokens")
        request_kwargs.update(kwargs)
        
        # Send request
        completion = self.client.chat.completions.create(**request_kwargs)
        
        # Validate response
        if not completion.choices:
            return Response(
                content="",
                usage=Usage.from_openai(completion.usage),
                raw=completion
            )
        
        # Handle None content (e.g., when using tool_calls)
        content = completion.choices[0].message.content or ""
        
        return Response(
            content=content,
            usage=Usage.from_openai(completion.usage),
            raw=completion
        )
