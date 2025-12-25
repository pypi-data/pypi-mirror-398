"""
Classrooms module for GitHub Classroom API.

Handles operations related to GitHub Classroom classrooms.
"""

from .base import ClassroomBase
from typing import List, Dict, Any


class Classrooms(ClassroomBase):
    """
    Class for managing GitHub Classroom classrooms.
    
    Provides methods to list, retrieve, and filter classrooms.
    """
    
    def list(self, page: int = 1, per_page: int = 30) -> List[Dict[str, Any]]:
        """
        List all classrooms for the authenticated user.
        
        Only returns classrooms where the user is an administrator.
        
        Args:
            page: Page number for pagination (default: 1)
            per_page: Results per page, max 100 (default: 30)
            
        Returns:
            List of classroom dictionaries containing:
                - id: Classroom ID
                - name: Classroom name
                - archived: Whether classroom is archived
                - url: Classroom URL
                
        Example:
            >>> classrooms = classroom.classrooms.list()
            >>> for c in classrooms:
            ...     print(f"{c['name']}: {c['id']}")
        """
        self.logger.info(f"Listing classrooms (page={page}, per_page={per_page})")
        
        params = {
            'page': page,
            'per_page': min(per_page, 100)  # Max 100 per page
        }
        
        response = self.call_api('/classrooms', params=params)
        
        # API returns a list directly
        classrooms = response if isinstance(response, list) else [response]
        
        self.logger.info(f"Retrieved {len(classrooms)} classrooms")
        return classrooms
    
    def get(self, classroom_id: int) -> Dict[str, Any]:
        """
        Get a specific classroom by ID.
        
        Args:
            classroom_id: The unique identifier of the classroom
            
        Returns:
            Classroom dictionary containing:
                - id: Classroom ID
                - name: Classroom name
                - archived: Whether classroom is archived
                - organization: Organization details (id, login, name, avatar_url)
                - url: Classroom URL
                
        Raises:
            ClassroomResourceNotFoundError: If classroom not found
            
        Example:
            >>> classroom_details = classroom.classrooms.get(12345)
            >>> print(classroom_details['organization']['login'])
        """
        self.logger.info(f"Getting classroom {classroom_id}")
        
        response = self.call_api(f'/classrooms/{classroom_id}')
        
        self.logger.debug(f"Retrieved classroom: {response.get('name')}")
        return response
    
    def get_all(self, per_page: int = 100) -> List[Dict[str, Any]]:
        """
        Get all classrooms with automatic pagination.
        
        Args:
            per_page: Results per page, max 100 (default: 100)
            
        Returns:
            List of all classrooms
            
        Example:
            >>> all_classrooms = classroom.classrooms.get_all()
            >>> print(f"Total: {len(all_classrooms)}")
        """
        self.logger.info("Getting all classrooms with pagination")
        
        all_classrooms = []
        page = 1
        
        while True:
            classrooms = self.list(page=page, per_page=per_page)
            
            if not classrooms:
                break
                
            all_classrooms.extend(classrooms)
            
            # If less than per_page, we've reached the end
            if len(classrooms) < per_page:
                break
                
            page += 1
        
        self.logger.info(f"Retrieved total of {len(all_classrooms)} classrooms")
        return all_classrooms
    
    def filter_by_name(self, name_pattern: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """
        Filter classrooms by name pattern.
        
        Args:
            name_pattern: Pattern to match in classroom name
            case_sensitive: Whether to perform case-sensitive matching (default: False)
            
        Returns:
            List of matching classrooms
            
        Example:
            >>> # Get all classrooms containing "iir5g"
            >>> iir_classrooms = classroom.classrooms.filter_by_name("iir5g")
            >>> for c in iir_classrooms:
            ...     print(c['name'])
        """
        self.logger.info(f"Filtering classrooms by name: '{name_pattern}'")
        
        all_classrooms = self.get_all()
        
        if case_sensitive:
            filtered = [
                c for c in all_classrooms
                if name_pattern in c.get('name', '')
            ]
        else:
            pattern_lower = name_pattern.lower()
            filtered = [
                c for c in all_classrooms
                if pattern_lower in c.get('name', '').lower()
            ]
        
        self.logger.info(f"Found {len(filtered)} classrooms matching '{name_pattern}'")
        return filtered
    
    def filter_active(self) -> List[Dict[str, Any]]:
        """
        Get only non-archived (active) classrooms.
        
        Returns:
            List of active classrooms
            
        Example:
            >>> active = classroom.classrooms.filter_active()
        """
        self.logger.info("Filtering active classrooms")
        
        all_classrooms = self.get_all()
        active = [c for c in all_classrooms if not c.get('archived', False)]
        
        self.logger.info(f"Found {len(active)} active classrooms")
        return active
