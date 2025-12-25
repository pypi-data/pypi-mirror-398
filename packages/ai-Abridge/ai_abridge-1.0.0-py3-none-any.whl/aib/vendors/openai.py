"""OpenAI adapter using official OpenAI SDK."""

import mimetypes
import base64
from pathlib import Path
from typing import List, Optional

from openai import OpenAI

from .base import VendorAdapter
from ..models import Response, Usage


class OpenAIAdapter(VendorAdapter):
    """
    OpenAI adapter using official OpenAI SDK.
    
    Supports:
    - Native file processing via Files API (for assistants)
    - Vision models with base64 images
    - Custom base_url for proxies/relays
    """
    
    # Default endpoint and model
    DEFAULT_BASE_URL = "https://api.openai.com/v1"
    DEFAULT_MODEL = "gpt-4o"
    
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
        Upload file to OpenAI Files API.
        
        Note: OpenAI Files API is primarily for Assistants/Fine-tuning.
        For chat completions, we use base64 encoding for images.
        
        Returns:
            File ID.
        """
        path = self._validate_file(file_path)
        
        with open(path, "rb") as f:
            uploaded = self.client.files.create(file=f, purpose="assistants")
        
        return uploaded.id
    
    def chat(
        self,
        prompt: str,
        files: Optional[List[Path]] = None,
        **kwargs
    ) -> Response:
        """
        Send chat request to OpenAI.
        
        Files are sent as base64 encoded data. API will return error if
        model doesn't support the content type.
        """
        messages = []
        
        if files:
            # Build multimodal content
            content = []
            
            for file_path in files:
                path = Path(file_path)
                mime_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
                
                # Send all files as base64 - let API decide if supported
                with open(path, "rb") as f:
                    b64_data = base64.b64encode(f.read()).decode("utf-8")
                
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{b64_data}"
                    }
                })
            
            # Add text prompt
            content.append({"type": "text", "text": prompt})
            messages.append({"role": "user", "content": content})
        
        else:
            # Pure text
            messages.append({"role": "user", "content": prompt})
        
        # Build request params - only include if specified
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
