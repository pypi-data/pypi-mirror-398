"""
RAG API Resource

Provides access to RAG (Retrieval-Augmented Generation) endpoints.
"""

from typing import Optional, Dict, Any, List
from ..http_client import HTTPClient
from ..models import RAGOptions, APIResponse


class RAGResource:
    """RAG API resource for document search and management."""

    def __init__(self, http_client: HTTPClient):
        """Initialize RAG resource."""
        self.client = http_client

    def search(
        self,
        query: str,
        rag_search_scope: str = "personal",
        actual_user_id: Optional[str] = None,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        async_mode: bool = True
    ) -> Any:
        """
        Search documents using RAG.

        Args:
            query: Search query.
            rag_search_scope: Search scope - "personal", "shared", or "all".
            actual_user_id: Actual user ID for 'all' scope searches.
            user_id: User ID (legacy, for search scope filtering).
            username: Username (legacy support).
            async_mode: Whether to process asynchronously (queue) or sync.

        Returns:
            RAG search results.

        Example:
            >>> response = rag.search_sync(
            ...     query="What is machine learning?",
            ...     rag_search_scope="personal"
            ... )
        """
        endpoint = "/api/v1/rag/search/sync" if not async_mode else "/api/v1/rag/search"

        payload = {
            "query": query,
            "ragSearchScope": rag_search_scope
        }
        if actual_user_id:
            payload["actual_user_id"] = actual_user_id
        if user_id:
            payload["user_id"] = user_id
        if username:
            payload["username"] = username

        response = self.client.post(endpoint, data=payload)
        return response

    def search_sync(
        self,
        query: str,
        rag_search_scope: str = "personal",
        actual_user_id: Optional[str] = None,
        user_id: Optional[str] = None,
        username: Optional[str] = None
    ) -> Any:
        """Search documents synchronously."""
        return self.search(query, rag_search_scope, actual_user_id, user_id, username, async_mode=False)

    def add(
        self,
        documents: List[str],
        user_id: Optional[str] = None
    ) -> Any:
        """
        Add documents to RAG.

        Args:
            documents: List of document paths or URLs.
            user_id: User ID for personal RAG.

        Returns:
            Document addition response.

        Example:
            >>> response = rag.add(
            ...     documents=["/path/to/doc.pdf", "https://example.com/doc"],
            ...     user_id="user123"
            ... )
            >>> print(response.data.added_count)
        """
        payload = {"documents": documents}
        if user_id:
            payload["user_id"] = user_id

        response = self.client.post("/api/v1/rag/add", data=payload)
        return response

    def init(
        self,
        user_id: Optional[str] = None,
        document_name: Optional[str] = None
    ) -> Any:
        """
        Initialize RAG for a user.

        Args:
            user_id: User ID to initialize RAG for.
            document_name: Name of the document collection.

        Returns:
            Initialization response.
        """
        payload = {}
        if user_id:
            payload["user_id"] = user_id
        if document_name:
            payload["document_name"] = document_name

        response = self.client.post("/api/v1/rag/init", data=payload)
        return response

    def delete(
        self,
        user_id: Optional[str] = None,
        file_paths: Optional[List[str]] = None
    ) -> Any:
        """
        Delete documents from RAG.

        Args:
            user_id: User ID whose documents to delete.
            file_paths: Specific file paths to delete.

        Returns:
            Deletion response.
        """
        payload = {}
        if user_id:
            payload["user_id"] = user_id
        if file_paths:
            payload["file_paths"] = file_paths

        response = self.client.post("/api/v1/rag/delete", data=payload)
        return response

    def list(self) -> Any:
        """
        List all RAG documents.

        Returns:
            List of documents.
        """
        response = self.client.get("/api/v1/rag/list")
        return response

    def get_init_status(self) -> Any:
        """
        Get RAG initialization status.

        Returns:
            Initialization status information.
        """
        response = self.client.get("/api/v1/rag/init-status")
        return response

    def create_dataset(
        self,
        method: str = "rag-default",
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> Any:
        """
        Create a RAG dataset.

        Args:
            method: Dataset creation method.
            provider: AI provider to use.
            model: Model to use for dataset creation.

        Returns:
            Dataset creation response.
        """
        payload = {"method": method}
        if provider:
            payload["provider"] = provider
        if model:
            payload["model"] = model

        response = self.client.post("/api/v1/rag/datasets", data=payload)
        return response

    def get_total_time(self) -> Any:
        """
        Get total RAG processing time.

        Returns:
            Processing time statistics.
        """
        response = self.client.get("/api/v1/rag/total-time")
        return response

    def get_thumbnail(
        self,
        user_id: str,
        filename: str,
        page: int = 1
    ) -> Any:
        """
        Get a thumbnail for a document page.

        Args:
            user_id: User ID.
            filename: Document filename.
            page: Page number.

        Returns:
            Thumbnail information.
        """
        params = {
            "user_id": user_id,
            "filename": filename,
            "page": page
        }
        response = self.client.get("/api/v1/rag/thumbnail", params=params)
        return response

    def upload(
        self,
        file_path: str,
        file_type: str = "document",
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        overwrite: bool = False,
        project_name: Optional[str] = None,
        rag_mode: Optional[str] = None,
        rag_pdf_backend: Optional[str] = None,
        rag_process_text_only: Optional[bool] = None,
        rag_generate_image_embeddings: Optional[bool] = None,
        rag_enable_graphrag: Optional[bool] = None,
        use_enhanced_embedding: Optional[bool] = None
    ) -> Any:
        """
        Upload a file to RAG.

        Args:
            file_path: Path to the file to upload.
            file_type: Type of file ("image" or "document").
            user_id: User ID for personal RAG.
            username: Username for personal RAG.
            overwrite: Whether to overwrite existing files.
            project_name: Project name for organization.
            rag_mode: RAG mode setting.
            rag_pdf_backend: PDF backend setting.
            rag_process_text_only: Process text only setting.
            rag_generate_image_embeddings: Generate image embeddings setting.
            rag_enable_graphrag: Enable GraphRAG setting.
            use_enhanced_embedding: Use enhanced embedding setting.

        Returns:
            Upload response with file information.

        Example:
            >>> response = client.rag.upload(
            ...     file_path="/path/to/document.pdf",
            ...     file_type="document",
            ...     user_id="user123"
            ... )
            >>> print(response["imageUrl"])
        """
        import os

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Prepare form data
        files = {"file": (os.path.basename(file_path), open(file_path, "rb"))}

        data = {}
        if file_type:
            data["type"] = file_type
        if user_id:
            data["user_id"] = user_id
        if username:
            data["username"] = username
        if overwrite:
            data["overwrite"] = "true"
        if project_name:
            data["project_name"] = project_name
        if rag_mode:
            data["rag_mode"] = rag_mode
        if rag_pdf_backend:
            data["rag_pdf_backend"] = rag_pdf_backend
        if rag_process_text_only is not None:
            data["rag_process_text_only"] = rag_process_text_only
        if rag_generate_image_embeddings is not None:
            data["rag_generate_image_embeddings"] = rag_generate_image_embeddings
        if rag_enable_graphrag is not None:
            data["rag_enable_graphrag"] = rag_enable_graphrag
        if use_enhanced_embedding is not None:
            data["use_enhanced_embedding"] = use_enhanced_embedding

        try:
            response = self.client.post("/api/v1/rag/upload", data=data, files=files)
            return response
        finally:
            # Close the file
            if "file" in files:
                files["file"][1].close()