"""
Base module for GitHub Classroom API client.

Provides base class for API interactions and custom exceptions.
"""

import requests
from typing import Dict, Any, Optional
import logging


# Custom Exceptions
class ClassroomAPIError(Exception):
    """Base exception for GitHub Classroom API errors."""
    pass


class ClassroomAuthenticationError(ClassroomAPIError):
    """Exception raised for authentication errors."""
    pass


class ClassroomResourceNotFoundError(ClassroomAPIError):
    """Exception raised when a resource is not found."""
    pass


class ClassroomBase:
    """
    Base class for GitHub Classroom API interactions.
    
    Handles HTTP requests, session management, and error handling.
    """
    
    API_BASE_URL = "https://api.github.com"
    API_VERSION = "2022-11-28"
    
    def __init__(self, token: str, logger: Optional[logging.Logger] = None):
        """
        Initialize the Classroom base client.
        
        Args:
            token: GitHub personal access token
            logger: Optional logger instance
        """
        self.token = token
        self.logger = logger or logging.getLogger(__name__)
        self._session: Optional[requests.Session] = None
    
    @property
    def session(self) -> requests.Session:
        """
        Get or create a requests session (lazy loading).
        
        Returns:
            Configured requests Session instance
        """
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({
                'Authorization': f'Bearer {self.token}',
                'Accept': 'application/vnd.github+json',
                'X-GitHub-Api-Version': self.API_VERSION
            })
        return self._session
    
    def call_api(
        self,
        endpoint: str,
        method: str = 'GET',
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Make an API call to GitHub Classroom REST API.
        
        Args:
            endpoint: API endpoint (e.g., '/classrooms')
            method: HTTP method (GET, POST, PUT, DELETE)
            params: Query parameters
            data: Request body data
            
        Returns:
            API response as dict or list
            
        Raises:
            ClassroomAuthenticationError: For 401/403 errors
            ClassroomResourceNotFoundError: For 404 errors
            ClassroomAPIError: For other API errors
        """
        url = f"{self.API_BASE_URL}{endpoint}"
        
        self.logger.debug(f"API call: {method} {url}")
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data
            )
            
            # Handle HTTP errors
            if response.status_code == 401:
                raise ClassroomAuthenticationError(
                    "Authentication failed. Check your GitHub token."
                )
            elif response.status_code == 403:
                raise ClassroomAuthenticationError(
                    "Access forbidden. Ensure you have admin rights on the classroom."
                )
            elif response.status_code == 404:
                raise ClassroomResourceNotFoundError(
                    f"Resource not found: {endpoint}"
                )
            elif response.status_code >= 400:
                error_msg = f"API error {response.status_code}: {response.text}"
                raise ClassroomAPIError(error_msg)
            
            response.raise_for_status()
            
            # Return JSON response
            if response.content:
                return response.json()
            return None
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            self.logger.error(error_msg)
            raise ClassroomAPIError(error_msg) from e
    
    def close(self):
        """Close the session if it exists."""
        if self._session:
            self._session.close()
            self._session = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
