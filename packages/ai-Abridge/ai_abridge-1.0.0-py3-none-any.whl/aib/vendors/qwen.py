"""Qwen (Aliyun) adapter using Dashscope SDK."""

from pathlib import Path
from typing import List, Optional
import base64

import dashscope
from dashscope import Generation
from dashscope.aigc import MultiModalConversation

from .base import VendorAdapter
from ..models import Response, Usage


class QwenAdapter(VendorAdapter):
    """
    Aliyun Qwen adapter using official Dashscope SDK.
    
    Supports:
    - Native file processing via Files API
    - Multimodal (VL models) input
    - Custom base_url for proxies
    """
    
    # Default model
    DEFAULT_MODEL = "qwen-plus"
    
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
        
        # Set API key globally for dashscope
        dashscope.api_key = self.api_key
        
        # Set custom base URL if provided
        if self.base_url:
            dashscope.base_http_api_url = self.base_url
        
        # Set timeout if provided
        if self.timeout:
            dashscope.api_timeout = self.timeout
    
    def upload_file(self, file_path: Path) -> str:
        """
        Upload file to Qwen Files API.
        
        Returns:
            File ID for use in chat requests.
        """
        path = self._validate_file(file_path)
        
        # Use dashscope file upload - let SDK errors propagate
        response = dashscope.Files.upload(file_path=str(path), purpose="file-extract")
        
        # Extract file ID from response
        return response.output['uploaded_files'][0]['file_id']
    
    def chat(
        self,
        prompt: str,
        files: Optional[List[Path]] = None,
        **kwargs
    ) -> Response:
        """
        Send chat request to Qwen.
        
        For VL models (with 'vl' in name), uses MultiModalConversation API with base64 images.
        For text models, uses Generation API.
        """
        # Check if this is a multimodal (VL) model
        is_vl_model = 'vl' in self.model.lower()
        
        if files and is_vl_model:
            # Use MultiModalConversation for VL models with images
            content_list = []
            
            # Add images as base64
            for file_path in files:
                path = Path(file_path)
                with open(path, 'rb') as f:
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                content_list.append({"image": f"data:image;base64,{image_data}"})
            
            # Add text
            content_list.append({"text": prompt})
            
            # Build multimodal message
            messages = [{
                "role": "user",
                "content": content_list
            }]
            
            # Call multimodal API
            conv = MultiModalConversation()
            response = conv.call(
                model=self.model,
                messages=messages,
                **kwargs
            )
            
            # Extract content from multimodal response with safe access
            try:
                if (response.output and 
                    response.output.choices and 
                    len(response.output.choices) > 0):
                    message_content = response.output.choices[0].message.content
                    if isinstance(message_content, list) and len(message_content) > 0:
                        content = message_content[0].get('text', '')
                    else:
                        content = str(message_content) if message_content else ""
                else:
                    content = ""
            except (AttributeError, IndexError, KeyError, TypeError):
                content = ""
            
        else:
            # Use Generation API for text-only or non-VL models
            messages = []
            
            if files:
                # For non-VL models, try file ID approach
                for file_path in files:
                    file_id = self.upload_file(Path(file_path))
                    messages.append({
                        "role": "system",
                        "content": f"fileid://{file_id}"
                    })
                messages.append({"role": "user", "content": prompt})
            else:
                # Pure text
                messages.append({"role": "user", "content": prompt})
            
            # Build request - let SDK errors propagate
            response = Generation.call(
                model=self.model,
                messages=messages,
                temperature=kwargs.pop("temperature", None),
                max_tokens=kwargs.pop("max_tokens", None),
                result_format="message",
                **kwargs
            )
            
            # Extract content with validation
            if (response.output and 
                response.output.choices and 
                len(response.output.choices) > 0):
                content = response.output.choices[0].message.content or ""
            else:
                content = ""
        
        return Response(
            content=content,
            usage=Usage.from_dashscope(response.usage),
            raw=response
        )
