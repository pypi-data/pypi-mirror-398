"""Gemini batch processing using google-genai SDK."""

import json
import mimetypes
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from google import genai
from google.genai import types

from .base import BaseBatchManager, BatchJob, BatchStatus


class GeminiBatchManager(BaseBatchManager):
    """
    Gemini batch processing manager.
    
    Uses Google's Batch API for significant cost savings.
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None
    ):
        super().__init__(api_key, base_url, timeout)
        
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["http_options"] = {"api_endpoint": self.base_url}
        if self.timeout:
            client_kwargs.setdefault("http_options", {})["timeout"] = self.timeout
        
        self.client = genai.Client(**client_kwargs)
    
    def _upload_file(self, file_path: Path) -> str:
        """Upload file and return URI."""
        mime_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        
        with open(file_path, "rb") as f:
            uploaded = self.client.files.upload(
                file=f,
                config=types.UploadFileConfig(
                    display_name=file_path.name,
                    mime_type=mime_type
                )
            )
        
        # Wait for processing (with timeout)
        max_wait = 300  # 5 minutes
        start_time = time.time()
        while uploaded.state.name == "PROCESSING":
            if time.time() - start_time > max_wait:
                raise RuntimeError(f"File processing timeout after {max_wait}s")
            time.sleep(1)
            uploaded = self.client.files.get(name=uploaded.name)
        
        if uploaded.state.name != "ACTIVE":
            raise RuntimeError(f"File upload failed: {uploaded.state.name}")
        
        return uploaded.uri
    
    def submit(
        self,
        requests: List[Dict[str, Any]],
        model: str,
        **kwargs
    ) -> BatchJob:
        """
        Submit batch job to Gemini.
        
        Args:
            requests: List of dicts with 'prompt' and optional 'files' keys.
            model: Model name (e.g., 'gemini-1.5-flash').
        
        Returns:
            BatchJob with Gemini job name.
        """
        # Build JSONL
        batch_requests = []
        for i, req in enumerate(requests):
            prompt = req.get("prompt", "")
            files = req.get("files", [])
            
            parts = []
            
            # Upload files
            for file_path in files:
                path = Path(file_path)
                if path.exists():
                    uri = self._upload_file(path)
                    mime_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
                    parts.append({
                        "file_data": {
                            "file_uri": uri,
                            "mime_type": mime_type
                        }
                    })
            
            # Add text prompt
            parts.append({"text": prompt})
            
            batch_requests.append({
                "key": f"req_{i}",
                "request": {
                    "contents": [{"role": "user", "parts": parts}]
                }
            })
        
        # Write to temp file
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".jsonl",
            delete=False,
            encoding="utf-8"
        ) as f:
            for req in batch_requests:
                f.write(json.dumps(req, ensure_ascii=False) + "\n")
            jsonl_path = f.name
        
        try:
            # Upload batch file
            batch_file = self.client.files.upload(
                file=jsonl_path,
                config=types.UploadFileConfig(
                    display_name="batch_input.jsonl",
                    mime_type="application/jsonl"
                )
            )
            
            # Create batch job
            job = self.client.batches.create(
                model=model,
                src=batch_file.name,
                config=types.CreateBatchJobConfig(
                    display_name=f"batch_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                )
            )
            
            return BatchJob(
                id=job.name,
                vendor="gemini",
                model=model,
                status=self._map_status(job.state),
                total_requests=len(requests)
            )
        
        finally:
            try:
                os.unlink(jsonl_path)
            except Exception:
                pass
    
    def get_status(self, job_id: str) -> BatchJob:
        """Get status of Gemini batch job."""
        job = self.client.batches.get(name=job_id)
        
        return BatchJob(
            id=job.name,
            vendor="gemini",
            model=job.model if hasattr(job, 'model') else "",
            status=self._map_status(job.state),
            output_file_id=job.output_file if hasattr(job, 'output_file') else None
        )
    
    def get_results(self, job_id: str) -> Dict[str, str]:
        """Get results of completed Gemini batch job."""
        job = self.client.batches.get(name=job_id)
        
        if not hasattr(job, 'output_file') or not job.output_file:
            raise RuntimeError("Job has no output file")
        
        content = self.client.files.content(name=job.output_file).text
        
        results = {}
        for line in content.splitlines():
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
                key = obj.get("key", "unknown")
                # Return raw content, no processing
                response_content = obj["response"]["candidates"][0]["content"]["parts"][0]["text"]
                results[key] = response_content
            except (KeyError, json.JSONDecodeError) as e:
                import warnings
                warnings.warn(f"Failed to parse batch result: {e}")
        
        return results
    
    def cancel(self, job_id: str) -> bool:
        """Cancel Gemini batch job."""
        try:
            self.client.batches.cancel(name=job_id)
            return True
        except Exception:
            return False
    
    def _map_status(self, state) -> BatchStatus:
        """Map Gemini state to BatchStatus."""
        state_name = state if isinstance(state, str) else state.name
        mapping = {
            "JOB_STATE_PENDING": BatchStatus.PENDING,
            "JOB_STATE_RUNNING": BatchStatus.RUNNING,
            "JOB_STATE_SUCCEEDED": BatchStatus.COMPLETED,
            "JOB_STATE_FAILED": BatchStatus.FAILED,
            "JOB_STATE_CANCELLED": BatchStatus.CANCELLED,
            "PENDING": BatchStatus.PENDING,
            "RUNNING": BatchStatus.RUNNING,
            "SUCCEEDED": BatchStatus.COMPLETED,
            "COMPLETED": BatchStatus.COMPLETED,
            "FAILED": BatchStatus.FAILED,
            "CANCELLED": BatchStatus.CANCELLED,
        }
        return mapping.get(state_name, BatchStatus.PENDING)
