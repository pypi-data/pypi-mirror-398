"""WOWSQL Storage SDK - S3 Storage management with automatic quota validation."""

import requests
from typing import Optional, Dict, Any, List, BinaryIO
from datetime import datetime, timedelta
import os


class StorageQuota:
    """Storage quota information."""
    
    def __init__(self, data: dict):
        self.quota_gb = data.get('storage_quota_gb', 0)
        self.used_gb = data.get('storage_used_gb', 0)
        self.expansion_gb = data.get('storage_expansion_gb', 0)
        self.available_gb = data.get('storage_available_gb', 0)
        self.usage_percentage = data.get('usage_percentage', 0)
        self.can_expand = data.get('can_expand_storage', False)
        self.is_enterprise = data.get('is_enterprise', False)
        self.plan_name = data.get('plan_name', 'Free')
    
    def __repr__(self):
        return (f"StorageQuota(used={self.used_gb:.2f}GB, "
                f"available={self.available_gb:.2f}GB, "
                f"total={self.quota_gb + self.expansion_gb:.2f}GB, "
                f"usage={self.usage_percentage:.1f}%)")


class StorageFile:
    """Storage file information."""
    
    def __init__(self, data: dict):
        self.key = data.get('key', '')
        self.size = data.get('size', 0)
        self.last_modified = data.get('last_modified')
        self.etag = data.get('etag', '')
        self.storage_class = data.get('storage_class', 'STANDARD')
        self.url = data.get('file_url')
        self.public_url = data.get('public_url')
    
    @property
    def size_mb(self) -> float:
        """File size in megabytes."""
        return self.size / (1024 * 1024)
    
    @property
    def size_gb(self) -> float:
        """File size in gigabytes."""
        return self.size / (1024 * 1024 * 1024)
    
    def __repr__(self):
        return f"StorageFile(key={self.key}, size={self.size_mb:.2f}MB)"


class StorageError(Exception):
    """Storage-specific error."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class StorageLimitExceededError(StorageError):
    """Error raised when storage limit would be exceeded."""
    pass


class WowSQLStorage:
    """
    WOWSQL Storage Client - Manage S3 storage with automatic quota validation.
    
    Features:
    - Automatic storage limit validation before upload
    - Real-time quota checking
    - File upload/download/delete operations
    - Presigned URL generation
    - Storage provisioning and management
    
    Example:
        >>> storage = WowSQLStorage(
        ...     project_slug="myproject",
        ...     api_key="your_api_key",
        ...     base_url="https://api.wowsql.com"
        ... )
        >>> 
        >>> # Check quota before upload
        >>> quota = storage.get_quota()
        >>> print(f"Available: {quota.available_gb:.2f} GB")
        >>> 
        >>> # Upload file (auto-validates limits)
        >>> with open('document.pdf', 'rb') as f:
        ...     result = storage.upload_file(f, 'documents/document.pdf')
        >>> 
        >>> # List files
        >>> files = storage.list_files(prefix='documents/')
    """
    
    def __init__(
        self,
        project_slug: str,
        api_key: str,
        base_url: str = "https://api.wowsql.com",
        timeout: int = 60,
        verify_ssl: bool = True,
        auto_check_quota: bool = True
    ):
        """
        Initialize WOWSQL Storage client.
        
        Args:
            project_slug: Project slug (e.g., 'myproject')
            api_key: API key for authentication
            base_url: API base URL (default: https://api.wowsql.com)
            timeout: Request timeout in seconds (default: 60 for file uploads)
            verify_ssl: Verify SSL certificates (default: True)
            auto_check_quota: Automatically check quota before uploads (default: True)
        """
        self.project_slug = project_slug
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.auto_check_quota = auto_check_quota
        
        # Setup session
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
        })
        self.session.verify = verify_ssl
        
        # Suppress SSL warnings if disabled
        if not verify_ssl:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Cache quota (refreshed on each operation)
        self._quota_cache: Optional[StorageQuota] = None
    
    def _request(
        self,
        method: str,
        path: str,
        params: Optional[dict] = None,
        json: Optional[dict] = None,
        files: Optional[dict] = None,
        data: Optional[dict] = None
    ) -> dict:
        """Make HTTP request to Storage API."""
        url = f"{self.base_url}{path}"
        
        # Remove Content-Type header for file uploads
        headers = {}
        if files:
            headers = {"Content-Type": None}
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json,
                files=files,
                data=data,
                headers=headers if files else {},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.HTTPError as e:
            error_data = {}
            try:
                error_data = e.response.json() if e.response.content else {}
            except:
                pass
            
            error_msg = error_data.get("detail", str(e))
            
            # Check if it's a storage limit error
            if e.response.status_code == 413:
                raise StorageLimitExceededError(
                    error_msg,
                    status_code=e.response.status_code,
                    response=error_data
                )
            
            raise StorageError(
                error_msg,
                status_code=e.response.status_code,
                response=error_data
            )
        except requests.exceptions.RequestException as e:
            raise StorageError(str(e))
    
    def get_quota(self, force_refresh: bool = False) -> StorageQuota:
        """
        Get storage quota and usage information.
        
        Args:
            force_refresh: Force refresh quota from server (default: False)
        
        Returns:
            StorageQuota object with quota details
        
        Raises:
            StorageError: If quota fetch fails
        """
        if self._quota_cache and not force_refresh:
            return self._quota_cache
        
        response = self._request(
            "GET",
            f"/api/v1/storage/s3/projects/{self.project_slug}/quota"
        )
        
        self._quota_cache = StorageQuota(response)
        return self._quota_cache
    
    def check_upload_allowed(self, file_size_bytes: int) -> tuple[bool, str]:
        """
        Check if file upload is allowed based on storage quota.
        
        Args:
            file_size_bytes: Size of file to upload in bytes
        
        Returns:
            Tuple of (allowed: bool, message: str)
        """
        quota = self.get_quota(force_refresh=True)
        file_size_gb = file_size_bytes / (1024 ** 3)
        
        if file_size_gb > quota.available_gb:
            return False, (
                f"Storage limit exceeded! "
                f"File size: {file_size_gb:.4f} GB, "
                f"Available: {quota.available_gb:.4f} GB. "
                f"Upgrade your plan to get more storage."
            )
        
        return True, f"Upload allowed. {quota.available_gb:.4f} GB available."
    
    def upload_file(
        self,
        file_data: BinaryIO,
        file_key: str,
        folder: Optional[str] = None,
        content_type: Optional[str] = None,
        check_quota: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to S3 storage with automatic quota validation.
        
        Args:
            file_data: File-like object (opened in binary mode)
            file_key: File name or path in bucket
            folder: Optional folder path (e.g., 'avatars', 'documents/reports')
            content_type: Optional content type (e.g., 'image/png')
            check_quota: Override auto_check_quota setting for this upload
        
        Returns:
            Dict with upload result:
            {
                'success': True,
                'file_key': 'documents/file.pdf',
                'file_size': 1024000,
                'bucket_name': 'WOWSQL-project-123',
                'message': 'File uploaded successfully'
            }
        
        Raises:
            StorageLimitExceededError: If storage quota would be exceeded
            StorageError: If upload fails
        
        Example:
            >>> with open('photo.jpg', 'rb') as f:
            ...     result = storage.upload_file(f, 'photo.jpg', folder='images')
            >>> print(result['file_key'])
        """
        # Read file data
        file_content = file_data.read()
        file_size = len(file_content)
        
        # Check quota if enabled
        should_check = check_quota if check_quota is not None else self.auto_check_quota
        if should_check:
            allowed, message = self.check_upload_allowed(file_size)
            if not allowed:
                raise StorageLimitExceededError(message, status_code=413)
        
        # Prepare upload
        params = {}
        if folder:
            params['folder'] = folder
        
        files = {
            'file': (file_key, file_content, content_type or 'application/octet-stream')
        }
        
        # Upload
        response = self._request(
            "POST",
            f"/api/v1/storage/s3/projects/{self.project_slug}/upload",
            params=params,
            files=files
        )
        
        # Refresh quota cache after upload
        self._quota_cache = None
        
        return response
    
    def upload_from_path(
        self,
        file_path: str,
        file_key: Optional[str] = None,
        folder: Optional[str] = None,
        content_type: Optional[str] = None,
        check_quota: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Upload a file from local filesystem path.
        
        Args:
            file_path: Path to local file
            file_key: Optional file name in bucket (defaults to filename)
            folder: Optional folder path
            content_type: Optional content type
            check_quota: Override auto_check_quota setting
        
        Returns:
            Dict with upload result
        
        Raises:
            FileNotFoundError: If file doesn't exist
            StorageLimitExceededError: If storage quota would be exceeded
            StorageError: If upload fails
        
        Example:
            >>> result = storage.upload_from_path(
            ...     'documents/report.pdf',
            ...     folder='reports'
            ... )
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not file_key:
            file_key = os.path.basename(file_path)
        
        with open(file_path, 'rb') as f:
            return self.upload_file(f, file_key, folder, content_type, check_quota)
    
    def list_files(
        self,
        prefix: Optional[str] = None,
        max_keys: int = 1000
    ) -> List[StorageFile]:
        """
        List files in S3 bucket.
        
        Args:
            prefix: Filter by prefix/folder (e.g., 'avatars/')
            max_keys: Maximum files to return (default: 1000)
        
        Returns:
            List of StorageFile objects
        
        Example:
            >>> files = storage.list_files(prefix='documents/')
            >>> for file in files:
            ...     print(f"{file.key}: {file.size_mb:.2f} MB")
        """
        params = {'max_keys': max_keys}
        if prefix:
            params['prefix'] = prefix
        
        response = self._request(
            "GET",
            f"/api/v1/storage/s3/projects/{self.project_slug}/files",
            params=params
        )
        
        return [StorageFile(file_data) for file_data in response.get('files', [])]
    
    def delete_file(self, file_key: str) -> Dict[str, Any]:
        """
        Delete a file from S3 bucket.
        
        Args:
            file_key: Path to file in bucket
        
        Returns:
            Dict with deletion result
        
        Example:
            >>> result = storage.delete_file('documents/old-file.pdf')
            >>> print(result['message'])
        """
        response = self._request(
            "DELETE",
            f"/api/v1/storage/s3/projects/{self.project_slug}/files/{file_key}"
        )
        
        # Refresh quota cache after delete
        self._quota_cache = None
        
        return response
    
    def get_file_url(
        self,
        file_key: str,
        expires_in: int = 3600
    ) -> Dict[str, Any]:
        """
        Get presigned URL for file access.
        
        Args:
            file_key: Path to file in bucket
            expires_in: URL validity in seconds (default: 3600 = 1 hour)
        
        Returns:
            Dict with file URL and metadata:
            {
                'file_key': 'documents/file.pdf',
                'file_url': 'https://...',  # Presigned URL
                'public_url': 'https://...',  # Public URL structure
                'expires_at': '2024-01-01T12:00:00',
                'bucket_name': 'WOWSQL-project-123',
                'region': 'us-east-1',
                'size': 1024000
            }
        
        Example:
            >>> url_data = storage.get_file_url('photo.jpg', expires_in=7200)
            >>> print(url_data['file_url'])
        """
        params = {'expires_in': expires_in}
        
        response = self._request(
            "GET",
            f"/api/v1/storage/s3/projects/{self.project_slug}/files/{file_key}/url",
            params=params
        )
        
        return response
    
    def get_presigned_url(
        self,
        file_key: str,
        expires_in: int = 3600,
        operation: str = 'get_object'
    ) -> str:
        """
        Generate presigned URL for file operations.
        
        Args:
            file_key: Path to file in bucket
            expires_in: URL validity in seconds (default: 3600)
            operation: 'get_object' (download) or 'put_object' (upload)
        
        Returns:
            Presigned URL string
        
        Example:
            >>> download_url = storage.get_presigned_url('file.pdf')
            >>> upload_url = storage.get_presigned_url(
            ...     'new-file.pdf',
            ...     operation='put_object'
            ... )
        """
        response = self._request(
            "POST",
            f"/api/v1/storage/s3/projects/{self.project_slug}/presigned-url",
            json={
                'file_key': file_key,
                'expires_in': expires_in,
                'operation': operation
            }
        )
        
        return response['url']
    
    def get_storage_info(self) -> Dict[str, Any]:
        """
        Get S3 storage information for the project.
        
        Returns:
            Dict with storage info:
            {
                's3_storage_id': 123,
                'bucket_name': 'WOWSQL-project-123',
                'region': 'us-east-1',
                'status': 'active',
                'total_objects': 42,
                'total_size_bytes': 1024000000,
                'total_size_gb': 0.95,
                'provisioned_at': '2024-01-01T00:00:00',
                'created_at': '2024-01-01T00:00:00'
            }
        """
        return self._request(
            "GET",
            f"/api/v1/storage/s3/projects/{self.project_slug}/info"
        )
    
    def provision_storage(self, region: str = 'us-east-1') -> Dict[str, Any]:
        """
        Provision S3 storage for the project.
        
        **IMPORTANT**: Save the credentials returned! They're only shown once.
        
        Args:
            region: AWS region (default: 'us-east-1')
        
        Returns:
            Dict with provisioning result including credentials
        
        Example:
            >>> result = storage.provision_storage(region='us-west-2')
            >>> print(f"Bucket: {result['bucket_name']}")
            >>> print(f"Access Key: {result['credentials']['access_key_id']}")
        """
        return self._request(
            "POST",
            f"/api/v1/storage/s3/projects/{self.project_slug}/provision",
            json={'region': region}
        )
    
    def get_available_regions(self) -> List[Dict[str, Any]]:
        """
        Get list of available S3 regions with pricing.
        
        Returns:
            List of region dictionaries with pricing info
        
        Example:
            >>> regions = storage.get_available_regions()
            >>> for region in regions:
            ...     print(f"{region['name']}: ${region['storage_price_gb']}/GB/month")
        """
        return self._request("GET", "/api/v1/storage/s3/regions")
    
    def close(self):
        """Close the HTTP session."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def __repr__(self):
        return f"WowSQLStorage(project={self.project_slug})"

