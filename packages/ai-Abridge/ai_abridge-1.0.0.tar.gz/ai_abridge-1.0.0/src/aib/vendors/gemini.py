"""Gemini (Google) adapter using google-genai SDK."""

import mimetypes
import time
from pathlib import Path
from typing import List, Optional
import logging

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

from .base import VendorAdapter
from ..models import Response, Usage


class GeminiAdapter(VendorAdapter):
    """
    Google Gemini adapter using official google-genai SDK.
    
    Supports:
    - Native multimodal via Files API
    - PDF, images, video, audio
    - Custom base_url for proxies
    """
    
    # Default model
    DEFAULT_MODEL = "gemini-2.0-flash"
    
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
            base_url=base_url,
            timeout=timeout,
            **kwargs
        )
        
        # Initialize client
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["http_options"] = {"api_endpoint": self.base_url}
        if self.timeout:
            client_kwargs.setdefault("http_options", {})["timeout"] = self.timeout
        
        self.client = genai.Client(**client_kwargs)
    
    def upload_file(self, file_path: Path) -> str:
        """
        Upload file to Gemini Files API.
        
        Returns:
            File URI for use in chat requests.
        """
        path = self._validate_file(file_path)
        mime_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        
        with open(path, "rb") as f:
            uploaded = self.client.files.upload(
                file=f,
                config=types.UploadFileConfig(
                    display_name=path.name,
                    mime_type=mime_type
                )
            )
        
        # Wait for file to be processed (with timeout)
        max_wait = 60  # 1 minute - balance between patience and UX
        start_time = time.time()
        while uploaded.state.name == "PROCESSING":
            if time.time() - start_time > max_wait:
                raise RuntimeError(
                    f"File processing timeout after {max_wait}s. "
                    f"Large files may take longer to process."
                )
            time.sleep(1)
            uploaded = self.client.files.get(name=uploaded.name)
        
        if uploaded.state.name != "ACTIVE":
            raise RuntimeError(f"File upload failed: {uploaded.state.name}")
        
        return uploaded.uri
    
    def chat(
        self,
        prompt: str,
        files: Optional[List[Path]] = None,
        **kwargs
    ) -> Response:
        """
        Send chat request to Gemini.
        
        Supports multimodal input via Files API.
        """
        contents = []
        
        # Upload and add files
        if files:
            for file_path in files:
                file_uri = self.upload_file(Path(file_path))
                mime_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
                contents.append(
                    types.Part.from_uri(file_uri=file_uri, mime_type=mime_type)
                )
        
        # Add text prompt
        contents.append(prompt)
        
        # Build config - only include params if specified
        config_args = {}
        if "temperature" in kwargs:
            config_args["temperature"] = kwargs.pop("temperature")
        if "max_tokens" in kwargs:
            config_args["max_output_tokens"] = kwargs.pop("max_tokens")
        config_args.update(kwargs)
        
        # Send request
        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(**config_args)
        )
        
        # Handle safety filtering and blocked responses
        content = ""
        try:
            if response.candidates:
                candidate = response.candidates[0]
                # Check for safety filtering
                if hasattr(candidate, 'finish_reason'):
                    if candidate.finish_reason == types.FinishReason.SAFETY:
                        content = "[内容因安全原因被过滤]"
                        logger.warning(f"Gemini response blocked by safety filter: {candidate.safety_ratings}")
                    elif candidate.finish_reason == types.FinishReason.RECITATION:
                        content = "[内容因重复原因被过滤]"
                        logger.warning("Gemini response blocked due to recitation")
                    else:
                        content = response.text or ""
                else:
                    content = response.text or ""
            else:
                logger.warning("Gemini returned no candidates")
        except (ValueError, AttributeError) as e:
            logger.error(f"Error extracting Gemini response text: {e}")
            content = "[无法获取响应内容]"
        
        return Response(
            content=content,
            usage=Usage.from_gemini(response.usage_metadata),
            raw=response
        )
