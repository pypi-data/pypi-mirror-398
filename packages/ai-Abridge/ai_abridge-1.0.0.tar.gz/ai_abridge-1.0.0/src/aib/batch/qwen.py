"""Qwen batch processing using OpenAI-compatible Batch API."""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from openai import OpenAI

from .base import BaseBatchManager, BatchJob, BatchStatus


class QwenBatchManager(BaseBatchManager):
    """
    Qwen batch processing manager.
    
    Uses Dashscope's OpenAI-compatible Batch API for 50% cost savings.
    """
    
    DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None
    ):
        super().__init__(api_key, base_url or self.DEFAULT_BASE_URL, timeout)
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout
        )
    
    def submit(
        self,
        requests: List[Dict[str, Any]],
        model: str,
        **kwargs
    ) -> BatchJob:
        """
        Submit batch job to Qwen.
        
        Args:
            requests: List of dicts with 'prompt' and optional 'files' keys.
            model: Model name (e.g., 'qwen-plus').
        
        Returns:
            BatchJob with Qwen job ID.
        """
        # Build JSONL file
        batch_requests = []
        for i, req in enumerate(requests):
            prompt = req.get("prompt", "")
            files = req.get("files", [])
            
            messages = []
            
            # Handle files (upload via File API)
            for file_path in files:
                path = Path(file_path)
                if path.exists():
                    with open(path, "rb") as f:
                        uploaded = self.client.files.create(file=f, purpose="file-extract")
                    messages.append({
                        "role": "system",
                        "content": f"fileid://{uploaded.id}"
                    })
            
            messages.append({"role": "user", "content": prompt})
            
            batch_requests.append({
                "custom_id": f"req_{i}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": model,
                    "messages": messages
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
            with open(jsonl_path, "rb") as f:
                batch_file = self.client.files.create(file=f, purpose="batch")
            
            # Create batch job
            job = self.client.batches.create(
                input_file_id=batch_file.id,
                endpoint="/v1/chat/completions",
                completion_window="24h"
            )
            
            return BatchJob(
                id=job.id,
                vendor="qwen",
                model=model,
                status=self._map_status(job.status),
                total_requests=len(requests)
            )
        
        finally:
            try:
                os.unlink(jsonl_path)
            except Exception:
                pass
    
    def get_status(self, job_id: str) -> BatchJob:
        """Get status of Qwen batch job."""
        job = self.client.batches.retrieve(job_id)
        
        return BatchJob(
            id=job.id,
            vendor="qwen",
            model="",
            status=self._map_status(job.status),
            completed_requests=job.request_counts.completed if job.request_counts else 0,
            total_requests=job.request_counts.total if job.request_counts else 0,
            output_file_id=job.output_file_id,
            error=str(job.errors) if job.errors else None
        )
    
    def get_results(self, job_id: str) -> Dict[str, str]:
        """Get results of completed Qwen batch job."""
        job = self.client.batches.retrieve(job_id)
        
        if not job.output_file_id:
            raise RuntimeError("Job has no output file")
        
        content = self.client.files.content(job.output_file_id).text
        
        results = {}
        for line in content.splitlines():
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
                custom_id = obj.get("custom_id", "unknown")
                # Return raw content, no processing
                response_content = obj["response"]["body"]["choices"][0]["message"]["content"]
                results[custom_id] = response_content
            except (KeyError, json.JSONDecodeError) as e:
                import warnings
                warnings.warn(f"Failed to parse batch result: {e}")
        
        return results
    
    def cancel(self, job_id: str) -> bool:
        """Cancel Qwen batch job."""
        try:
            self.client.batches.cancel(job_id)
            return True
        except Exception:
            return False
    
    def _map_status(self, status: str) -> BatchStatus:
        """Map Qwen status to BatchStatus."""
        mapping = {
            "validating": BatchStatus.VALIDATING,
            "in_progress": BatchStatus.RUNNING,
            "completed": BatchStatus.COMPLETED,
            "failed": BatchStatus.FAILED,
            "cancelled": BatchStatus.CANCELLED,
            "expired": BatchStatus.EXPIRED,
        }
        return mapping.get(status, BatchStatus.PENDING)
