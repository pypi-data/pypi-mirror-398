"""
Code API Resource

Provides access to code generation and execution endpoints.
"""

from typing import Optional, Dict, Any, List
import os
from ..http_client import HTTPClient
from ..models import CodeOptions, APIResponse


class CodeResource:
    """Code API resource for code generation and execution."""

    def __init__(self, http_client: HTTPClient):
        """Initialize code resource."""
        self.client = http_client

    def create(
        self,
        prompt: str,
        options: Optional[CodeOptions] = None,
        async_mode: bool = True
    ) -> Any:
        """
        Generate code based on a prompt.

        Args:
            prompt: Description of the code to generate.
            options: Options for code generation.
            async_mode: Whether to process asynchronously.

        Returns:
            Code generation response.

        Example:
            >>> response = code.create(
            ...     prompt="Create a Python REST API server",
            ...     options=CodeOptions(language="python", framework="fastapi")
            ... )
            >>> print(response.data.code)
        """
        endpoint = "/api/v1/code/sync" if not async_mode else "/code"

        payload = {"prompt": prompt}
        if options:
            payload["options"] = options.model_dump(exclude_none=True) if hasattr(options, "model_dump") else options

        response = self.client.post(endpoint, data=payload)
        return response

    def create_sync(
        self,
        prompt: str,
        options: Optional[CodeOptions] = None
    ) -> Any:
        """Generate code synchronously."""
        return self.create(prompt, options, async_mode=False)

    def execute(
        self,
        python_code: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Execute Python code.

        Args:
            python_code: The Python code to execute.
            options: Execution options (timeout, etc.).

        Returns:
            Code execution results.

        Example:
            >>> response = code.execute("print('Hello, World!')")
            >>> print(response.data.output)
        """
        payload = {"python_code": python_code}
        if options:
            payload["options"] = options

        response = self.client.post("/api/v1/code/execute", data=payload)
        return response

    def save_code(
        self,
        python_code: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Save code as a zip file.

        Args:
            python_code: The Python code to save.
            options: Save options (filename, etc.).

        Returns:
            Save response with download information.

        Example:
            >>> response = code.save_code(
            ...     "print('Hello')",
            ...     options={"filename": "my_script.py"}
            ... )
            >>> filename = response.data.filename
        """
        payload = {"python_code": python_code}
        if options:
            payload["options"] = options

        response = self.client.post("/api/v1/code/saveCode", data=payload)
        return response

    def download(self, filename: str, save_path: Optional[str] = None) -> str:
        """
        Download a code file.

        Args:
            filename: The filename to download.
            save_path: Local path to save the file. If not provided, uses current directory.

        Returns:
            Path to the downloaded file.
        """
        if not save_path:
            save_path = os.path.join(os.getcwd(), filename)

        return self.client.download(f"/code/download/{filename}", save_path)

    def get_status(self, job_id: str) -> Any:
        """
        Get the status of an async code generation job.

        Args:
            job_id: The job ID returned from async code creation.

        Returns:
            Job status information.
        """
        response = self.client.get(f"/code/status/{job_id}")
        return response