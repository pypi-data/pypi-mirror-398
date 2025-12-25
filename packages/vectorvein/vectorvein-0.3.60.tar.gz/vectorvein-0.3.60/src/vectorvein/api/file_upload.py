"""File Upload API functionality"""

from typing import BinaryIO

from .models import FileUploadResult


class FileUploadSyncMixin:
    """Synchronous file upload API methods"""

    def upload_file(self, file: BinaryIO | str, filename: str | None = None) -> FileUploadResult:
        """Upload file to OSS

        Args:
            file: File object or file path
            filename: File name (optional, will be inferred if not provided)

        Returns:
            FileUploadResult: Upload result containing OSS path and file info

        Raises:
            VectorVeinAPIError: Upload error
        """
        if isinstance(file, str):
            # File path provided
            import os

            if not filename:
                filename = os.path.basename(file)
            with open(file, "rb") as f:
                files = {"file": (filename, f, None)}
                response = self._request("POST", "file-upload/upload", files=files)
        else:
            # File object provided
            if not filename:
                filename = getattr(file, "name", "unknown")
            files = {"file": (filename, file, None)}
            response = self._request("POST", "file-upload/upload", files=files)

        return FileUploadResult(**response["data"])


class FileUploadAsyncMixin:
    """Asynchronous file upload API methods"""

    async def upload_file(self, file: BinaryIO | str, filename: str | None = None) -> FileUploadResult:
        """Async upload file to OSS

        Args:
            file: File object or file path
            filename: File name (optional, will be inferred if not provided)

        Returns:
            FileUploadResult: Upload result containing OSS path and file info

        Raises:
            VectorVeinAPIError: Upload error
        """
        if isinstance(file, str):
            # File path provided
            import os

            if not filename:
                filename = os.path.basename(file)
            with open(file, "rb") as f:
                files = {"file": (filename, f, None)}
                response = await self._request("POST", "file-upload/upload", files=files)
        else:
            # File object provided
            if not filename:
                filename = getattr(file, "name", "unknown")
            files = {"file": (filename, file, None)}
            response = await self._request("POST", "file-upload/upload", files=files)

        return FileUploadResult(**response["data"])
