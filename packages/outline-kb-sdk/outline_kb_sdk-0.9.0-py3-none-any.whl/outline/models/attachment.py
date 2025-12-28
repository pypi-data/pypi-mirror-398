"""Attachment model for Outline API."""

import mimetypes
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

from .base import BaseModel

if TYPE_CHECKING:
    from ..client import OutlineClient


@dataclass
class AttachmentReference:
    """
    Lightweight reference to an attachment found in document markdown.
    
    This represents an attachment discovered by parsing the document text,
    containing metadata extracted from the markdown syntax.
    
    Attributes:
        id: Attachment UUID
        name: Filename extracted from markdown (if available)
        size: File size in bytes extracted from markdown (if available)
        is_image: Whether this is an image attachment
    """
    
    id: str
    name: Optional[str] = None
    size: Optional[int] = None
    is_image: bool = False
    
    @property
    def download_url(self) -> str:
        """Get the API path for downloading this attachment."""
        return f"/api/attachments.redirect?id={self.id}"
    
    def __repr__(self) -> str:
        """String representation."""
        type_str = "Image" if self.is_image else "File"
        name_str = f", name={self.name!r}" if self.name else ""
        size_str = f", size={self.size}" if self.size else ""
        return f"AttachmentReference({type_str}, id={self.id!r}{name_str}{size_str})"


class Attachment(BaseModel):
    """
    Represents a file attachment in Outline.

    Attachments represent files uploaded to cloud storage with metadata
    such as file type, size, and location.
    """

    @classmethod
    def create(
        cls,
        client: "OutlineClient",
        name: str,
        content_type: str,
        size: int,
        document_id: Optional[str] = None,
    ) -> "Attachment":
        """
        Create a new attachment record.

        This creates the database record and returns the inputs needed to
        generate a signed URL and upload the file from the client to cloud storage.

        Args:
            client: OutlineClient instance
            name: File name (e.g., 'image.png')
            content_type: MIME type (e.g., 'image/png')
            size: File size in bytes
            document_id: Optional associated document ID

        Returns:
            Created Attachment instance with upload information
        """
        data = {
            "name": name,
            "contentType": content_type,
            "size": size,
        }

        if document_id is not None:
            data["documentId"] = document_id

        response = client.request("attachments.create", data)
        # The response contains both attachment and upload info
        attachment_data = response["data"]["attachment"]
        # Store upload info as well for reference
        attachment_data["_uploadUrl"] = response["data"].get("uploadUrl")
        attachment_data["_uploadForm"] = response["data"].get("form")
        attachment_data["_maxUploadSize"] = response["data"].get("maxUploadSize")

        return cls(client, attachment_data)

    @classmethod
    def delete_by_id(cls, client: "OutlineClient", id: str) -> None:
        """
        Delete an attachment by ID.

        Note: This is a class method as you may want to delete without fetching first.

        Args:
            client: OutlineClient instance
            id: Attachment ID (UUID)
        """
        client.request("attachments.delete", {"id": id})

    # Properties
    @property
    def name(self) -> str:
        """File name."""
        return self._data["name"]

    @property
    def content_type(self) -> str:
        """MIME type (e.g., 'image/png')."""
        return self._data["contentType"]

    @property
    def size(self) -> int:
        """File size in bytes."""
        return self._data["size"]

    @property
    def url(self) -> Optional[str]:
        """URL to access the attachment."""
        return self._data.get("url")

    @property
    def document_id(self) -> Optional[str]:
        """ID of associated document (if any)."""
        return self._data.get("documentId")

    @property
    def upload_url(self) -> Optional[str]:
        """Signed upload URL (only present after creation)."""
        return self._data.get("_uploadUrl")

    @property
    def upload_form(self) -> Optional[dict]:
        """Form data for upload (only present after creation)."""
        return self._data.get("_uploadForm")

    @property
    def max_upload_size(self) -> Optional[int]:
        """Maximum allowed upload size (only present after creation)."""
        return self._data.get("_maxUploadSize")

    # Methods
    def get_redirect_url(self) -> str:
        """
        Get a temporary signed URL to access this attachment.

        If the attachment is private, this generates a temporary signed URL
        with embedded credentials on demand.

        Returns:
            URL to access the attachment file
        """
        response = self._client.request("attachments.redirect", {"id": self.id})
        
        # Handle 302 redirect response (plain text)
        if response.get('status_code') == 302:
            redirect_text = response.get('redirect_text', '')
            if 'Redirecting to' in redirect_text:
                # Extract URL from text like "Redirecting to URL"
                parts = redirect_text.split('Redirecting to ')
                if len(parts) > 1:
                    return parts[1].strip().rstrip('.')
        
        # Handle standard JSON response
        if 'data' in response:
            return response['data']
        
        return response.get("url", self.url or "")

    def delete(self) -> None:
        """
        Delete this attachment.

        Warning: This is permanent and won't delete references in documents.
        """
        self._client.request("attachments.delete", {"id": self.id})

    def upload(self, file_path: Union[str, Path]) -> bool:
        """
        Upload a file to cloud storage using the upload URL.
        
        This method handles the actual file upload after creating an
        attachment record with Attachment.create().
        
        Args:
            file_path: Path to the file to upload
            
        Returns:
            True if upload succeeded
            
        Raises:
            ValueError: If upload_url is not available (call create() first)
            FileNotFoundError: If file_path doesn't exist
            requests.HTTPError: If upload fails
            
        Example:
            >>> attachment = Attachment.create(
            ...     client,
            ...     name="report.pdf",
            ...     content_type="application/pdf",
            ...     size=os.path.getsize("report.pdf"),
            ...     document_id=doc.id
            ... )
            >>> attachment.upload("report.pdf")
            True
        """
        import requests
        
        if not self.upload_url:
            raise ValueError(
                "No upload URL available. This attachment may have already been uploaded, "
                "or was not created with Attachment.create()."
            )
        
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Handle relative URLs by prepending the base URL
        upload_url = self.upload_url
        is_outline_endpoint = upload_url.startswith('/')
        if is_outline_endpoint:
            upload_url = self._client.api_url + upload_url
        
        # Prepare headers (authorization needed for Outline endpoints)
        headers = {}
        if is_outline_endpoint:
            headers['Authorization'] = f'Bearer {self._client.api_key}'
        
        # Prepare multipart upload
        with open(file_path, 'rb') as file:
            files = {
                'file': (self.name, file, self.content_type)
            }
            
            # Include any form data provided by the API
            data = self.upload_form if self.upload_form else {}
            
            # Perform upload with generous timeout for large files
            response = requests.post(
                upload_url,
                files=files,
                data=data,
                headers=headers,
                timeout=300  # 5 minutes
            )
            
            response.raise_for_status()
            return True

    def upload_from_bytes(
        self,
        file_bytes: bytes,
        filename: Optional[str] = None
    ) -> bool:
        """
        Upload file content from bytes/memory buffer.
        
        Useful when you have file content in memory rather than on disk.
        
        Args:
            file_bytes: File content as bytes
            filename: Optional filename to use (defaults to attachment name)
            
        Returns:
            True if upload succeeded
            
        Raises:
            ValueError: If upload_url is not available
            requests.HTTPError: If upload fails
            
        Example:
            >>> import io
            >>> content = b"Hello, World!"
            >>> attachment = Attachment.create(
            ...     client,
            ...     name="hello.txt",
            ...     content_type="text/plain",
            ...     size=len(content),
            ...     document_id=doc.id
            ... )
            >>> attachment.upload_from_bytes(content)
            True
        """
        import requests
        
        if not self.upload_url:
            raise ValueError(
                "No upload URL available. This attachment may have already been uploaded, "
                "or was not created with Attachment.create()."
            )
        
        # Handle relative URLs by prepending the base URL
        upload_url = self.upload_url
        is_outline_endpoint = upload_url.startswith('/')
        if is_outline_endpoint:
            upload_url = self._client.api_url + upload_url
        
        # Prepare headers (authorization needed for Outline endpoints)
        headers = {}
        if is_outline_endpoint:
            headers['Authorization'] = f'Bearer {self._client.api_key}'
        
        filename = filename or self.name
        file_obj = BytesIO(file_bytes)
        
        # Prepare multipart upload
        files = {
            'file': (filename, file_obj, self.content_type)
        }
        
        data = self.upload_form if self.upload_form else {}
        
        response = requests.post(
            upload_url,
            files=files,
            data=data,
            headers=headers,
            timeout=300
        )
        
        response.raise_for_status()
        return True

    @classmethod
    def create_and_upload(
        cls,
        client: "OutlineClient",
        file_path: Union[str, Path],
        name: Optional[str] = None,
        content_type: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> "Attachment":
        """
        Create an attachment and upload the file in one step.
        
        Convenience method that combines create() and upload().
        
        Args:
            client: OutlineClient instance
            file_path: Path to the file to upload
            name: Filename (defaults to file's basename)
            content_type: MIME type (auto-detected if not provided)
            document_id: Optional document to attach to
            
        Returns:
            Created and uploaded Attachment instance
            
        Raises:
            FileNotFoundError: If file doesn't exist
            requests.HTTPError: If creation or upload fails
            
        Example:
            >>> # Simple upload with auto-detection
            >>> attachment = Attachment.create_and_upload(
            ...     client,
            ...     "report.pdf",
            ...     document_id=doc.id
            ... )
            >>> print(f"Uploaded: {attachment.id}")
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Auto-detect name and content type if not provided
        if name is None:
            name = file_path.name
        
        if content_type is None:
            content_type, _ = mimetypes.guess_type(str(file_path))
            if content_type is None:
                content_type = "application/octet-stream"
        
        # Get file size
        size = file_path.stat().st_size
        
        # Create attachment record
        attachment = cls.create(
            client,
            name=name,
            content_type=content_type,
            size=size,
            document_id=document_id
        )
        
        # Upload the file
        attachment.upload(file_path)
        
        return attachment

    def download(self, output_path: Optional[Union[str, Path]] = None) -> bytes:
        """
        Download the attachment file content.
        
        Gets a temporary signed URL from the API and downloads the file.
        Optionally saves to disk.
        
        Args:
            output_path: Optional path to save the downloaded file
            
        Returns:
            File content as bytes
            
        Raises:
            requests.HTTPError: If download fails
            
        Example:
            >>> # Download to memory
            >>> content = attachment.download()
            >>>
            >>> # Download and save to file
            >>> attachment.download("output.pdf")
        """
        import requests
        
        # Get the redirect URL (temporary signed URL)
        redirect_url = self.get_redirect_url()
        
        # Download the file
        # Note: redirect_url should already be the final download URL
        # but we use allow_redirects=True to be safe
        response = requests.get(redirect_url, stream=True, allow_redirects=True)
        response.raise_for_status()
        
        content = response.content
        
        # Optionally save to file
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(content)
        
        return content

    def download_to_file(self, output_path: Union[str, Path]) -> None:
        """
        Download attachment and save directly to a file.
        
        Convenience wrapper around download() that only saves to disk.
        
        Args:
            output_path: Path where the file should be saved
            
        Raises:
            requests.HTTPError: If download fails
            OSError: If file cannot be written
            
        Example:
            >>> attachment.download_to_file("downloads/report.pdf")
        """
        self.download(output_path=output_path)

    def download_stream(self, chunk_size: int = 8192):
        """
        Download attachment as a streaming iterator.
        
        Useful for very large files to avoid loading entire content into memory.
        
        Args:
            chunk_size: Size of chunks to yield
            
        Yields:
            bytes: Chunks of file content
            
        Example:
            >>> with open("output.pdf", "wb") as f:
            ...     for chunk in attachment.download_stream():
            ...         f.write(chunk)
        """
        import requests
        
        redirect_url = self.get_redirect_url()
        
        response = requests.get(redirect_url, stream=True, allow_redirects=True)
        response.raise_for_status()
        
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:  # filter out keep-alive chunks
                yield chunk

    def refresh(self) -> None:
        """
        Attachments don't have a direct info endpoint.

        Raises:
            NotImplementedError: Attachments cannot be refreshed directly
        """
        raise NotImplementedError("Attachments cannot be refreshed directly via API")

    def __repr__(self) -> str:
        """String representation of Attachment."""
        return f"Attachment(id={self.id!r}, name={self.name!r}, size={self.size})"
