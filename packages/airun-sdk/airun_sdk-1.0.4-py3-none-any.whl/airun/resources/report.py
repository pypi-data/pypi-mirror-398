"""
Report API Resource

Provides access to report generation and management endpoints.
"""

from typing import Optional, Dict, Any, List
from ..http_client import HTTPClient
from ..models import APIResponse


class ReportResource:
    """Report API resource for report generation and management."""

    def __init__(self, http_client: HTTPClient):
        """Initialize report resource."""
        self.client = http_client

    def create(
        self,
        prompt: str,
        filepath: Optional[str] = None,
        format: Optional[str] = None,
        template: Optional[str] = None,
        type: Optional[str] = None,
        title: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        documents: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        email: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> Any:
        """
        Generate a report.

        Args:
            prompt: Report prompt or task description.
            filepath: Path to file containing prompt content (alternative to prompt).
            format: Output format (pdf, docx, etc.).
            template: Template to use for report generation.
            type: Report type.
            title: Report title.
            data: Additional data for report generation.
            documents: List of document sources.
            session_id: Session ID for context.
            user_id: User ID.
            username: Username.
            email: User email.
            provider: AI provider to use.
            model: Model to use.

        Returns:
            Report generation response with job_id.

        Example:
            >>> response = client.report.create(
            ...     prompt="Generate a market analysis report",
            ...     format="pdf",
            ...     template="simple"
            ... )
            >>> job_id = response["data"].get("job_id")
        """
        payload = {}
        if prompt:
            payload["prompt"] = prompt
        if filepath:
            payload["filepath"] = filepath
        if format:
            payload["format"] = format
        if template:
            payload["template"] = template
        if type:
            payload["type"] = type
        if title:
            payload["title"] = title
        if data:
            payload["data"] = data
        if documents:
            payload["documents"] = documents
        if session_id:
            payload["sessionId"] = session_id
        if user_id:
            payload["userId"] = user_id
        if username:
            payload["username"] = username
        if email:
            payload["email"] = email
        if provider:
            payload["provider"] = provider
        if model:
            payload["model"] = model

        response = self.client.post("/api/v1/report", data=payload)
        return response

    def get_reports(self, user_id: Optional[str] = None) -> Any:
        """
        Get user's report list.

        Args:
            user_id: User ID to filter reports.

        Returns:
            List of reports.
        """
        params = {}
        if user_id:
            params["userId"] = user_id

        response = self.client.get("/reports", params=params)
        return response

    def get_report(self, report_id: str, user_id: Optional[str] = None) -> Any:
        """
        Get a specific report.

        Args:
            report_id: Report ID.
            user_id: User ID.

        Returns:
            Report details.
        """
        params = {}
        if user_id:
            params["userId"] = user_id

        response = self.client.get(f"/reports/{report_id}", params=params)
        return response

    def download_report(
        self,
        report_id: str,
        save_path: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> str:
        """
        Download a report file.

        Args:
            report_id: Report ID.
            save_path: Local path to save the file.
            user_id: User ID.

        Returns:
            Path to the saved file.
        """
        import os

        if not save_path:
            save_path = os.path.join(os.getcwd(), f"report_{report_id}.pdf")

        params = {}
        if user_id:
            params["userId"] = user_id

        return self.client.download(f"/reports/{report_id}/download", save_path, params=params)

    def delete_report(self, report_id: str, user_id: Optional[str] = None) -> Any:
        """
        Delete a report.

        Args:
            report_id: Report ID.
            user_id: User ID.

        Returns:
            Deletion response.
        """
        params = {}
        if user_id:
            params["userId"] = user_id

        response = self.client.delete(f"/reports/{report_id}", params=params)
        return response

    def get_templates(self) -> Any:
        """
        Get report templates.

        Returns:
            List of available templates.
        """
        response = self.client.get("/report/templates")
        return response

    def get_simple_templates(self) -> Any:
        """
        Get simple template list (faster loading).

        Returns:
            List of templates with basic info.
        """
        response = self.client.get("/report/templates-simple")
        return response

    def get_template(self, template_name: str) -> Any:
        """
        Get template details.

        Args:
            template_name: Template name.

        Returns:
            Template details.
        """
        response = self.client.get(f"/report/templates/{template_name}")
        return response

    def get_status(self, job_id: str) -> Any:
        """
        Get report generation job status.

        Args:
            job_id: Job ID from report creation.

        Returns:
            Job status information.
        """
        response = self.client.get(f"/report/status/{job_id}")
        return response

    def get_active_jobs(self, user_id: Optional[str] = None, username: Optional[str] = None) -> Any:
        """
        Get active report generation jobs.

        Args:
            user_id: User ID.
            username: Username.

        Returns:
            List of active jobs.
        """
        params = {}
        if user_id:
            params["userId"] = user_id
        if username:
            params["username"] = username

        response = self.client.get("/report/active-jobs", params=params)
        return response

    def health(self) -> Any:
        """
        Check report service health.

        Returns:
            Health status information.
        """
        response = self.client.get("/health", base_url="http://localhost:5620")
        return response
