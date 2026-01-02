
import os
from typing import Optional

from ..tarsus_client_generated.client import AuthenticatedClient, Client

class TarsusClient:
    """
    Tarsus Python Client
    
    Provides convenient access to the Tarsus API resources.
    """
    
    def __init__(self, api_key: str, base_url: str = "https://api.tarsus.tech/api/v1", project_id: Optional[str] = None):
        """
        Initialize the Tarsus Client.
        
        Args:
            api_key: Your Tarsus API Key (or Service Key).
            base_url: The base URL for the API (defaults to production).
            project_id: Optional Tenant/Project ID.
        """
        self.api_key = api_key
        self.base_url = base_url
        self.project_id = project_id
        
        headers = {}
        if self.project_id:
            headers["X-Tenant-ID"] = self.project_id
            
        self._client = AuthenticatedClient(
            base_url=self.base_url,
            token=self.api_key,
            headers=headers,
            timeout=60.0
        )
        
    @property
    def client(self) -> AuthenticatedClient:
        """Access the underlying generated AuthenticatedClient"""
        return self._client
    
    # We can add resource property wrappers here for better UX if needed, 
    # but the generated client uses top-level functions or method groups typically.
    # The openapi-python-client structure is usually:
    # client.api.tag.operation(client=client.client, ...)
    # 
    # To make it truly nice, we would wrap these.
    # For now, let's expose the client so users can use the generated API functions directly 
    # or improve this wrapper later.


def init(api_key: Optional[str] = None, base_url: Optional[str] = None, project_id: Optional[str] = None) -> TarsusClient:
    """
    Initialize a global Tarsus client instance.
    
    Automatically reads MY_SERVICE_API_KEY from environment if api_key is not provided.
    
    Args:
        api_key: API Key (defaults to env var MY_SERVICE_API_KEY)
        base_url: Optional base URL override
        project_id: Optional project/tenant ID
        
    Returns:
        TarsusClient instance
    """
    key = api_key or os.getenv("MY_SERVICE_API_KEY") or os.getenv("TARSUS_API_KEY")
    if not key:
        raise ValueError("API Key is required. Set MY_SERVICE_API_KEY environment variable or pass api_key parameter.")
        
    url = base_url or os.getenv("TARSUS_BASE_URL") or "https://api.tarsus.tech/api/v1"
    
    return TarsusClient(api_key=key, base_url=url, project_id=project_id)
