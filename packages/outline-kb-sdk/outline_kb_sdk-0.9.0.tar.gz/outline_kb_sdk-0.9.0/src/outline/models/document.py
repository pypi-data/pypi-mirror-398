"""Document model for Outline API."""

import re
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from pathlib import Path

from .base import BaseModel

if TYPE_CHECKING:
    from ..client import OutlineClient
    from .attachment import Attachment, AttachmentReference
    from .comment import Comment


class Document(BaseModel):
    """
    Represents an Outline document.

    Documents are the core content unit in Outline, representing individual
    pages of information stored in Markdown format.
    """

    @classmethod
    def create(
        cls,
        client: "OutlineClient",
        title: str,
        collection_id: str,
        text: Optional[str] = None,
        publish: bool = False,
        parent_document_id: Optional[str] = None,
        template: bool = False,
        template_id: Optional[str] = None,
    ) -> "Document":
        """
        Create a new document.

        Args:
            client: OutlineClient instance
            title: Document title
            collection_id: Collection ID (UUID)
            text: Document content in Markdown
            publish: Whether to publish immediately (default: False creates draft)
            parent_document_id: Optional parent document ID for nesting
            template: Whether this document is a template
            template_id: Optional template ID to use

        Returns:
            Created Document instance
        """
        data: Dict[str, Any] = {
            "title": title,
            "collectionId": collection_id,
            "publish": publish,
            "template": template,
        }

        if text is not None:
            data["text"] = text
        if parent_document_id is not None:
            data["parentDocumentId"] = parent_document_id
        if template_id is not None:
            data["templateId"] = template_id

        response = client.request("documents.create", data)
        return cls(client, response["data"])

    @classmethod
    def get(cls, client: "OutlineClient", id: str, share_id: Optional[str] = None) -> "Document":
        """
        Retrieve a document by ID.

        Args:
            client: OutlineClient instance
            id: Document ID (UUID or urlId)
            share_id: Optional share ID for accessing via share link

        Returns:
            Document instance
        """
        data: Dict[str, Any] = {"id": id}

        if share_id is not None:
            data["shareId"] = share_id

        response = client.request("documents.info", data)
        return cls(client, response["data"])

    @classmethod
    def list(
        cls,
        client: "OutlineClient",
        collection_id: Optional[str] = None,
        user_id: Optional[str] = None,
        parent_document_id: Optional[str] = None,
        backlink_document_id: Optional[str] = None,
        template: Optional[bool] = None,
        limit: int = 25,
        offset: int = 0,
        sort: str = "updatedAt",
        direction: str = "DESC",
    ) -> List["Document"]:
        """
        List documents with optional filters.

        Args:
            client: OutlineClient instance
            collection_id: Filter by collection
            user_id: Filter by user
            parent_document_id: Filter by parent document
            backlink_document_id: Filter by backlinks
            template: Filter by template status
            limit: Maximum results (default: 25)
            offset: Pagination offset (default: 0)
            sort: Sort field (default: 'updatedAt')
            direction: Sort direction ('ASC' or 'DESC')

        Returns:
            List of Document instances
        """
        data: Dict[str, Any] = {
            "limit": limit,
            "offset": offset,
            "sort": sort,
            "direction": direction,
        }

        if collection_id is not None:
            data["collectionId"] = collection_id
        if user_id is not None:
            data["userId"] = user_id
        if parent_document_id is not None:
            data["parentDocumentId"] = parent_document_id
        if backlink_document_id is not None:
            data["backlinkDocumentId"] = backlink_document_id
        if template is not None:
            data["template"] = template

        response = client.request("documents.list", data)
        return [cls(client, item) for item in response["data"]]

    # Properties
    @property
    def title(self) -> str:
        """Document title."""
        return self._data["title"]

    @property
    def text(self) -> str:
        """Document content (Markdown)."""
        return self._data.get("text", "")

    @property
    def collection_id(self) -> str:
        """ID of the collection this document belongs to."""
        return self._data["collectionId"]

    @property
    def parent_document_id(self) -> Optional[str]:
        """ID of parent document (if nested)."""
        return self._data.get("parentDocumentId")

    @property
    def url_id(self) -> str:
        """Short unique identifier (alternative to UUID)."""
        return self._data.get("urlId", "")

    @property
    def emoji(self) -> Optional[str]:
        """Emoji associated with the document."""
        return self._data.get("emoji")

    @property
    def full_width(self) -> bool:
        """Whether document should display in full-width view."""
        return self._data.get("fullWidth", False)

    @property
    def template(self) -> bool:
        """Whether this document is a template."""
        return self._data.get("template", False)

    @property
    def template_id(self) -> Optional[str]:
        """ID of template this was created from."""
        return self._data.get("templateId")

    @property
    def revision(self) -> int:
        """Auto-incrementing revision number."""
        return self._data.get("revision", 0)

    @property
    def pinned(self) -> bool:
        """Whether document is pinned in collection."""
        return self._data.get("pinned", False)

    @property
    def published_at(self) -> Optional[datetime]:
        """When document was published."""
        published = self._data.get("publishedAt")
        return self._parse_datetime(published) if published else None

    @property
    def archived_at(self) -> Optional[datetime]:
        """When document was archived."""
        archived = self._data.get("archivedAt")
        return self._parse_datetime(archived) if archived else None

    # Methods
    def update(
        self,
        title: Optional[str] = None,
        text: Optional[str] = None,
        append: bool = False,
        publish: Optional[bool] = None,
        done: bool = False,
    ) -> None:
        """
        Update document properties.

        Args:
            title: New title
            text: New content
            append: If True, append text instead of replacing
            publish: Whether to publish (if draft)
            done: Whether editing session is finished
        """
        data: Dict[str, Any] = {"id": self.id}

        if title is not None:
            data["title"] = title
        if text is not None:
            data["text"] = text
            if append:
                data["append"] = True
        if publish is not None:
            data["publish"] = publish
        if done:
            data["done"] = True

        response = self._client.request("documents.update", data)
        self._data = response["data"]

    def delete(self, permanent: bool = False) -> None:
        """
        Delete or trash this document.

        Args:
            permanent: If True, permanently delete. If False, move to trash.
        """
        data = {
            "id": self.id,
            "permanent": permanent,
        }
        self._client.request("documents.delete", data)

    def move(
        self, collection_id: Optional[str] = None, parent_document_id: Optional[str] = None
    ) -> None:
        """
        Move document to a new location or collection.

        Args:
            collection_id: Target collection ID
            parent_document_id: Target parent document ID (None for root)
        """
        data: Dict[str, Any] = {"id": self.id}

        if collection_id is not None:
            data["collectionId"] = collection_id
        if parent_document_id is not None:
            data["parentDocumentId"] = parent_document_id

        response = self._client.request("documents.move", data)
        # Update with returned data
        if "data" in response and "documents" in response["data"]:
            # Find this document in the response
            for doc_data in response["data"]["documents"]:
                if doc_data["id"] == self.id:
                    self._data = doc_data
                    break

    def archive(self) -> None:
        """Archive this document."""
        response = self._client.request("documents.archive", {"id": self.id})
        self._data = response["data"]

    def restore(self, revision_id: Optional[str] = None) -> None:
        """
        Restore document from archive or trash.

        Args:
            revision_id: Optional revision ID to restore to
        """
        data: Dict[str, Any] = {"id": self.id}

        if revision_id is not None:
            data["revisionId"] = revision_id

        response = self._client.request("documents.restore", data)
        self._data = response["data"]

    def publish(self) -> None:
        """Publish this draft document."""
        self.update(publish=True)

    def unpublish(self) -> None:
        """Unpublish document back to draft."""
        response = self._client.request("documents.unpublish", {"id": self.id})
        self._data = response["data"]

    def export(self) -> str:
        """
        Export document as Markdown.

        Returns:
            Document content in Markdown format
        """
        response = self._client.request("documents.export", {"id": self.id})
        return response["data"]

    def add_comment(self, text: str, parent_comment_id: Optional[str] = None) -> "Comment":
        """
        Add a comment to this document.

        Args:
            text: Comment text (Markdown)
            parent_comment_id: Optional parent comment ID for replies

        Returns:
            Created Comment instance
        """
        from .comment import Comment

        return Comment.create(
            self._client,
            document_id=self.id,
            text=text,
            parent_comment_id=parent_comment_id,
        )

    def list_comments(self, limit: int = 25, offset: int = 0) -> List["Comment"]:
        """
        List all comments on this document.

        Args:
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of Comment instances
        """
        from .comment import Comment

        return Comment.list(
            self._client,
            document_id=self.id,
            limit=limit,
            offset=offset,
        )

    def list_attachments(self) -> List["AttachmentReference"]:
        """
        Parse document markdown to find all attachment references.
        
        Scans the document text for Outline attachment URLs and extracts
        attachment IDs along with any available metadata.
        
        Returns:
            List of AttachmentReference objects found in the document
            
        Example:
            >>> doc = Document.get(client, "doc-id")
            >>> attachments = doc.list_attachments()
            >>> for ref in attachments:
            ...     print(f"{ref.name}: {ref.id}")
        """
        from .attachment import AttachmentReference
        
        attachments = []
        text = self.text
        
        if not text:
            return attachments
        
        # Pattern to match attachment redirect URLs
        # Matches: /api/attachments.redirect?id=UUID
        url_pattern = r'/api/attachments\.redirect\?id=([a-f0-9-]{36})'
        
        # Find all attachment URLs
        for match in re.finditer(url_pattern, text):
            attachment_id = match.group(1)
            
            # Get surrounding context to extract metadata
            match_pos = match.start()
            line_start = text.rfind('\n', 0, match_pos) + 1
            line_end = text.find('\n', match.end())
            if line_end == -1:
                line_end = len(text)
            line = text[line_start:line_end]
            
            # Determine if this is an image (markdown image syntax)
            is_image = line.lstrip().startswith('![')
            
            # Extract metadata
            name = None
            size = None
            
            if is_image:
                # Image format: ![alt text](url)
                # Try to extract alt text as name
                img_pattern = r'!\[([^\]]*)\]\(' + re.escape(match.group(0))
                img_match = re.search(img_pattern, line)
                if img_match and img_match.group(1):
                    name = img_match.group(1)
            else:
                # File format: [filename size](url)
                # Example: [document.pdf 123456](/api/attachments.redirect?id=...)
                file_pattern = r'\[([^\]]+?)\s+(\d+)\]\(' + re.escape(match.group(0))
                file_match = re.search(file_pattern, line)
                if file_match:
                    name = file_match.group(1).strip()
                    try:
                        size = int(file_match.group(2))
                    except ValueError:
                        pass
            
            # Only add if we haven't seen this ID yet (deduplication)
            if not any(a.id == attachment_id for a in attachments):
                attachments.append(AttachmentReference(
                    id=attachment_id,
                    name=name,
                    size=size,
                    is_image=is_image
                ))
        
        return attachments

    def get_attachment(self, attachment_id: str) -> "Attachment":
        """
        Get an Attachment instance for a specific attachment ID.
        
        Creates a minimal Attachment object that can be used to download
        the file or get its redirect URL. The attachment must exist in
        this document's markdown text.
        
        Args:
            attachment_id: UUID of the attachment
            
        Returns:
            Attachment instance ready for download operations
            
        Raises:
            ValueError: If attachment_id not found in this document
            
        Example:
            >>> doc = Document.get(client, "doc-id")
            >>> attachment = doc.get_attachment("attachment-uuid")
            >>> content = attachment.download()
        """
        from .attachment import Attachment
        
        # Verify the attachment exists in this document
        refs = self.list_attachments()
        ref = next((r for r in refs if r.id == attachment_id), None)
        
        if not ref:
            raise ValueError(
                f"Attachment {attachment_id} not found in document {self.id}. "
                f"Use list_attachments() to see available attachments."
            )
        
        # Create minimal Attachment object with known data
        # Note: Some fields may be approximate/unknown since we're reconstructing
        # from markdown rather than API response
        attachment_data = {
            "id": attachment_id,
            "documentId": self.id,
            "name": ref.name or "unknown",
            "size": ref.size or 0,
            "contentType": "image/*" if ref.is_image else "application/octet-stream",
            # Timestamps will be None - we don't have this info from markdown
            "createdAt": None,
            "updatedAt": None,
        }
        
        return Attachment(self._client, attachment_data)

    def download_attachment(self, attachment_id: str, output_path: Optional[Union[str, Path]] = None) -> bytes:
        """
        Convenience method to download an attachment directly from a document.
        
        This combines get_attachment() and download() into a single call.
        
        Args:
            attachment_id: UUID of the attachment to download
            output_path: Optional path to save the file
            
        Returns:
            Downloaded file content as bytes
            
        Raises:
            ValueError: If attachment not found in document
            
        Example:
            >>> doc = Document.get(client, "doc-id")
            >>> # Download to memory
            >>> content = doc.download_attachment("attachment-uuid")
            >>> # Download to file
            >>> doc.download_attachment("attachment-uuid", "output.pdf")
        """
        attachment = self.get_attachment(attachment_id)
        return attachment.download(output_path=output_path)

    def add_subdocument(
        self,
        title: str,
        text: Optional[str] = None,
        publish: bool = False,
        template: bool = False,
        template_id: Optional[str] = None,
        **kwargs
    ) -> "Document":
        """
        Create a subdocument (child document) under this document.
        
        Convenience method that creates a document with this document
        as its parent.
        
        Args:
            title: Document title
            text: Document content in Markdown
            publish: Whether to publish immediately (default: False creates draft)
            template: Whether this document is a template
            template_id: Optional template ID to use
            **kwargs: Additional arguments passed to Document.create()
            
        Returns:
            Created Document instance
            
        Example:
            >>> parent = Document.get(client, "parent-id")
            >>> child = parent.add_subdocument(
            ...     title="Chapter 1",
            ...     text="# Chapter 1\\n\\nContent here...",
            ...     publish=True
            ... )
            >>> print(f"Created: {child.title}")
        """
        return Document.create(
            self._client,
            title=title,
            collection_id=self.collection_id,
            text=text,
            publish=publish,
            parent_document_id=self.id,
            template=template,
            template_id=template_id,
            **kwargs
        )

    def list_subdocuments(
        self,
        limit: int = 25,
        offset: int = 0,
        sort: str = "updatedAt",
        direction: str = "DESC",
        **kwargs
    ) -> List["Document"]:
        """
        List all direct child documents (subdocuments).
        
        Returns only immediate children, not nested descendants.
        
        Args:
            limit: Maximum results (default: 25)
            offset: Pagination offset (default: 0)
            sort: Sort field (default: 'updatedAt')
            direction: Sort direction ('ASC' or 'DESC')
            **kwargs: Additional filter arguments
            
        Returns:
            List of child Document instances
            
        Example:
            >>> parent = Document.get(client, "parent-id")
            >>> children = parent.list_subdocuments()
            >>> for child in children:
            ...     print(f"- {child.title}")
        """
        return Document.list(
            self._client,
            parent_document_id=self.id,
            limit=limit,
            offset=offset,
            sort=sort,
            direction=direction,
            **kwargs
        )

    def has_subdocuments(self) -> bool:
        """
        Check if this document has any subdocuments.
        
        This is a convenience method that checks if list_subdocuments()
        returns any results.
        
        Returns:
            True if document has subdocuments, False otherwise
            
        Example:
            >>> if doc.has_subdocuments():
            ...     print(f"{doc.title} has child documents")
        """
        children = self.list_subdocuments(limit=1)
        return len(children) > 0

    def refresh(self) -> None:
        """Reload document data from the API."""
        response = self._client.request("documents.info", {"id": self.id})
        self._data = response["data"]

    def __repr__(self) -> str:
        """String representation of Document."""
        return f"Document(id={self.id!r}, title={self.title!r})"
