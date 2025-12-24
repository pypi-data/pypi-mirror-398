# distributex/__init__.py - PRODUCTION READY
"""
DistributeX Python SDK
Official Python client for the DistributeX distributed computing platform
"""

import requests
import time
import json
from typing import Dict, Any, List, Optional, Union

__version__ = "8.0.5"

class DistributeXError(Exception):
    """Base exception for DistributeX SDK errors"""
    pass

class AuthenticationError(DistributeXError):
    """Raised when authentication fails"""
    pass

class JobNotFoundError(DistributeXError):
    """Raised when a job cannot be found"""
    pass

class TimeoutError(DistributeXError):
    """Raised when a job times out"""
    pass

class DistributeXClient:
    """
    Python client for DistributeX distributed computing platform
    
    Example:
        >>> from distributex import DistributeXClient
        >>> client = DistributeXClient(api_key="dsx_...")
        >>> job = client.submit(script="print('Hello')")
        >>> result = client.wait_for_job(job["id"])
        >>> print(result["result"]["output"])
    """

    def __init__(
        self, 
        api_key: str, 
        base_url: str = "https://distributex-production-7fd2.up.railway.app",
        timeout: int = 30,
        verify_ssl: bool = True
    ):
        """
        Initialize DistributeX client
        
        Args:
            api_key: Your DistributeX API key (starts with dsx_)
            base_url: API base URL (default: production)
            timeout: Request timeout in seconds (default: 30)
            verify_ssl: Whether to verify SSL certificates (default: True)
        
        Raises:
            AuthenticationError: If API key is invalid
        """
        if not api_key:
            raise AuthenticationError("API key is required")
        
        if not api_key.startswith("dsx_"):
            raise AuthenticationError("Invalid API key format. Must start with 'dsx_'")
        
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "X-API-Key": api_key,
            "Content-Type": "application/json",
            "User-Agent": f"distributex-python/{__version__}"
        })
        
        # Verify connection
        self._verify_connection()
    
    def _verify_connection(self):
        """Verify API connection and authentication"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/health",
                timeout=10,
                verify=self.verify_ssl
            )
            if response.status_code != 200:
                raise AuthenticationError("Failed to connect to DistributeX API")
        except requests.exceptions.RequestException as e:
            raise DistributeXError(f"Connection failed: {str(e)}")
    
    def _request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request with error handling
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters
            timeout: Request timeout override
        
        Returns:
            Response JSON data
        
        Raises:
            AuthenticationError: If authentication fails
            JobNotFoundError: If job not found
            DistributeXError: For other API errors
        """
        url = f"{self.base_url}{endpoint}"
        timeout = timeout or self.timeout
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=timeout,
                verify=self.verify_ssl
            )
            
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key or unauthorized access")
            
            if response.status_code == 404:
                raise JobNotFoundError("Job not found")
            
            if response.status_code >= 400:
                error_msg = "API error"
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message", error_msg)
                except:
                    pass
                raise DistributeXError(f"{response.status_code}: {error_msg}")
            
            return response.json()
            
        except requests.exceptions.Timeout:
            raise DistributeXError("Request timed out")
        except requests.exceptions.RequestException as e:
            raise DistributeXError(f"Request failed: {str(e)}")

    def submit(
        self,
        script: str,
        type: str = "script",
        runtime: str = "python",
        requirements: Optional[List[str]] = None,
        timeout: int = 300,
        gpu: bool = False,
        memory: str = "2GB"
    ) -> Dict[str, Any]:
        """
        Submit a job to the distributed compute network
        
        Args:
            script: Code to execute (Python or JavaScript)
            type: Job type (default: "script")
            runtime: "python" or "node" (default: "python")
            requirements: List of pip packages to install
            timeout: Maximum execution time in seconds (default: 300)
            gpu: Whether GPU is required (default: False)
            memory: Memory limit, e.g., "2GB" (default: "2GB")
        
        Returns:
            Dict containing job details with 'id', 'status', 'type', etc.
        
        Example:
            >>> job = client.submit(
            ...     script="print('Hello World')",
            ...     runtime="python",
            ...     timeout=60
            ... )
            >>> print(job["id"])
        """
        if not script or not script.strip():
            raise ValueError("Script cannot be empty")
        
        if runtime not in ["python", "node"]:
            raise ValueError("Runtime must be 'python' or 'node'")
        
        payload = {
            "type": type,
            "payload": {
                "script": script,
                "requirements": requirements or [],
                "timeout": timeout,
                "gpu": gpu,
                "memory": memory,
                "runtime": runtime
            }
        }

        return self._request("POST", "/api/jobs", data=payload)

    def get_job(self, job_id: Union[int, str]) -> Dict[str, Any]:
        """
        Get job status and results
        
        Args:
            job_id: The job ID returned from submit()
        
        Returns:
            Dict containing job status, results, and metadata
        
        Example:
            >>> job = client.get_job(123)
            >>> print(job["status"])
        """
        return self._request("GET", f"/api/jobs/{job_id}")

    def wait_for_job(
        self, 
        job_id: Union[int, str], 
        timeout: int = 600, 
        poll_interval: int = 5,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Wait for job completion with polling
        
        Args:
            job_id: The job ID to wait for
            timeout: Maximum time to wait in seconds (default: 600)
            poll_interval: How often to check status in seconds (default: 5)
            verbose: Print status updates (default: False)
        
        Returns:
            Dict containing completed job with results
        
        Raises:
            TimeoutError: If job doesn't complete within timeout
        
        Example:
            >>> result = client.wait_for_job(123, verbose=True)
            >>> if result["status"] == "completed":
            ...     print(result["result"]["output"])
        """
        start_time = time.time()
        
        if verbose:
            print(f"⏳ Waiting for job {job_id}...")
        
        while time.time() - start_time < timeout:
            job = self.get_job(job_id)
            status = job.get("status", "")
            
            if verbose:
                elapsed = int(time.time() - start_time)
                print(f"⌛ Status: {status} (elapsed: {elapsed}s)")
            
            if status in ["completed", "failed"]:
                if verbose:
                    print(f"✓ Job {status}")
                return job
            
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")

    def cancel_job(self, job_id: Union[int, str]) -> bool:
        """
        Cancel a running job
        
        Args:
            job_id: The job ID to cancel
        
        Returns:
            True if successfully cancelled
        
        Example:
            >>> client.cancel_job(123)
        """
        try:
            self._request("DELETE", f"/api/jobs/{job_id}")
            return True
        except:
            return False

    def get_balance(self) -> Dict[str, Any]:
        """
        Get account information and balance
        
        Returns:
            Dict containing user account details
        
        Example:
            >>> info = client.get_balance()
            >>> print(info["email"], info["role"])
        """
        return self._request("GET", "/api/auth/user")
    
    def list_jobs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List recent jobs
        
        Args:
            limit: Maximum number of jobs to return (default: 100)
        
        Returns:
            List of job dictionaries
        
        Example:
            >>> jobs = client.list_jobs(limit=10)
            >>> for job in jobs:
            ...     print(job["id"], job["status"])
        """
        jobs = self._request("GET", "/api/jobs")
        return jobs[:limit] if isinstance(jobs, list) else []


# Convenience function for quick usage
def submit_job(
    api_key: str,
    script: str,
    runtime: str = "python",
    wait: bool = True,
    timeout: int = 300
) -> Dict[str, Any]:
    """
    Quick function to submit and optionally wait for a job
    
    Args:
        api_key: Your DistributeX API key
        script: Code to execute
        runtime: "python" or "node" (default: "python")
        wait: Whether to wait for completion (default: True)
        timeout: Max execution time in seconds (default: 300)
    
    Returns:
        Job result dict
    
    Example:
        >>> from distributex import submit_job
        >>> result = submit_job(
        ...     api_key="dsx_...",
        ...     script="print('Hello')"
        ... )
        >>> print(result["result"]["output"])
    """
    client = DistributeXClient(api_key)
    job = client.submit(script=script, runtime=runtime, timeout=timeout)
    
    if wait:
        return client.wait_for_job(job["id"])
    
    return job


# Example usage and tests
if __name__ == "__main__":
    print("DistributeX Python SDK - Example Usage")
    print("=" * 50)
    
    # Example 1: Basic usage
    print("\n1. Basic Example:")
    print("-" * 50)
    example_code = """
import os
api_key = os.getenv("DISTRIBUTEX_API_KEY", "dsx_your_key_here")

client = DistributeXClient(api_key=api_key)

job = client.submit(
    script="print('Hello from DistributeX!')",
    runtime="python"
)

print(f"Job ID: {job['id']}")
result = client.wait_for_job(job["id"], verbose=True)
print(f"Output: {result['result']['output']}")
"""
    print(example_code)
    
    # Example 2: Data processing
    print("\n2. Data Processing Example:")
    print("-" * 50)
    example_code2 = """
job = client.submit(
    script='''
import json
data = [1, 2, 3, 4, 5]
result = {"sum": sum(data), "count": len(data)}
print(json.dumps(result))
    ''',
    runtime="python",
    timeout=60
)

result = client.wait_for_job(job["id"])
output = result["result"]["output"]
print(json.loads(output))
"""
    print(example_code2)
    
    print("\n" + "=" * 50)
    print("Documentation: https://docs.distributex.cloud")
    print("PyPI: https://pypi.org/project/distributex-cloud/")
