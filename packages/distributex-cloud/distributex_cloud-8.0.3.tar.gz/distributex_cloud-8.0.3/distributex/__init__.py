# distributex/__init__.py
import requests
import time
from typing import Dict, Any, List

class DistributeXClient:
    """Python client for DistributeX distributed computing platform"""

    def __init__(self, api_key: str, base_url: str = "https://api.distributex.cloud"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def submit(
        self,
        type: str,
        script: str,
        requirements: List[str] = None,
        timeout: int = 300,
        bid_price: int = 10,
        gpu: bool = False,
        memory: str = "2GB"
    ) -> Dict[str, Any]:
        payload = {
            "type": type,
            "payload": {
                "script": script,
                "requirements": requirements or [],
                "timeout": timeout,
                "gpu": gpu,
                "memory": memory
            },
            "price": bid_price
        }

        response = requests.post(
            f"{self.base_url}/api/jobs",
            json=payload,
            headers=self.headers,
            timeout=30
        )

        response.raise_for_status()
        return response.json()

    def get_job(self, job_id: int) -> Dict[str, Any]:
        response = requests.get(
            f"{self.base_url}/api/jobs/{job_id}",
            headers=self.headers,
            timeout=15
        )
        response.raise_for_status()
        return response.json()

    def wait_for_job(self, job_id: int, timeout: int = 600, poll_interval: int = 5) -> Dict[str, Any]:
        start_time = time.time()
        while time.time() - start_time < timeout:
            job = self.get_job(job_id)
            if job["status"] in ["completed", "failed"]:
                return job
            time.sleep(poll_interval)
        raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")

    def cancel_job(self, job_id: int) -> bool:
        response = requests.delete(
            f"{self.base_url}/api/jobs/{job_id}",
            headers=self.headers,
            timeout=15
        )
        return response.status_code == 200

    def get_balance(self) -> int:
        response = requests.get(
            f"{self.base_url}/api/auth/me",
            headers=self.headers,
            timeout=15
        )
        response.raise_for_status()
        return response.json().get("credits", 0)

# Example usage guard can be added separately when testing.
