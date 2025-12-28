import requests
from typing import Dict, Any, List, Optional


class SourceSystems:
    """
    Handles all source system related operations for BrynQ SDK.
    """
    def __init__(self, brynq_instance):
        """
        Initialize SourceSystems manager.
        
        Args:
            brynq_instance: The parent BrynQ instance
        """
        self._brynq = brynq_instance

    def get(self) -> List[Dict[str, Any]]:
        """
        Get all source systems.
        
        Returns:
            List[Dict[str, Any]]: List of all source systems
            
        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
        response = self._brynq.brynq_session.get(
            url=f'{self._brynq.url}source-systems',
            timeout=self._brynq.timeout
        )
        response.raise_for_status()
        return response.json()

    def create(self, name: str, entities: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Create new source systems.
        
        Args:
            name: Name of the source system
            entities: Optional list of entities to assign. Each entity should have 'name' and 'code' keys
            
        Returns:
            Dict[str, Any]: Created source system details
            
        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
        data = {
            'name': name,
            'entities': entities or []
        }
        response = self._brynq.brynq_session.post(
            url=f'{self._brynq.url}source-systems',
            json=data,
            timeout=self._brynq.timeout
        )
        response.raise_for_status()
        return response.json()

    def delete(self, system_id: int) -> None:
        """
        Delete a source system.
        
        Args:
            system_id: ID of the source system to delete
            
        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
        response = self._brynq.brynq_session.delete(
            url=f'{self._brynq.url}source-systems/{system_id}',
            timeout=self._brynq.timeout
        )
        response.raise_for_status()

    def update(self, system_id: int, name: str, entities: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Update a source system by overwriting its name and entities.
        
        Args:
            system_id: ID of the source system to update
            name: New name for the source system
            entities: Optional list of entities to replace existing ones. Each entity should have 'name' and 'code' keys
            
        Returns:
            Dict[str, Any]: Updated source system details
            
        Raises:
            requests.exceptions.RequestException: If the API request fails
            requests.exceptions.HTTPError: If source system is not found (404)
        """
        data = {
            'name': name,
            'entities': entities or []
        }
        response = self._brynq.brynq_session.put(
            url=f'{self._brynq.url}source-systems/{system_id}',
            json=data,
            timeout=self._brynq.timeout
        )
        response.raise_for_status()
        return response.json()

    def get_entities(self, system_id: int) -> requests.Response:
        """
        Get all entities from a source system in BrynQ
        
        Args:
            system_id: The ID of the source system
            
        Returns:
            List[Dict[str, Any]]: List of entities from the source system
            
        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
        response = self._brynq.brynq_session.get(
            url=f'{self._brynq.url}source-systems/{system_id}/entities',
            timeout=self._brynq.timeout
        )
        response.raise_for_status()
        return response.json()

    def create_entities(self, system_id: int, entities: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Create new entities for a source system.
        
        Args:
            system_id: ID of the source system
            entities: List of entities to create. Each entity should have 'name' and 'code' keys
            
        Returns:
            Dict[str, Any]: Result of the creation operation
            
        Raises:
            requests.exceptions.RequestException: If the API request fails
            requests.exceptions.HTTPError: If source system is not found (404)
        """
        data = {'entities': entities}
        response = self._brynq.brynq_session.post(
            url=f'{self._brynq.url}source-systems/{system_id}/entities',
            json=data,
            timeout=self._brynq.timeout
        )
        response.raise_for_status()
        return response.json()

    def update_entity(self, entity_id: int, name: str, code: str) -> Dict[str, Any]:
        """
        Update a specific source system entity.
        
        Args:
            entity_id: ID of the entity to update
            name: New name for the entity
            code: New code for the entity
            
        Returns:
            Dict[str, Any]: Updated entity details
            
        Raises:
            requests.exceptions.RequestException: If the API request fails
            requests.exceptions.HTTPError: If entity is not found (404)
        """
        data = {
            'name': name,
            'code': code
        }
        response = self._brynq.brynq_session.put(
            url=f'{self._brynq.url}source-systems/entities/{entity_id}',
            json=data,
            timeout=self._brynq.timeout
        )
        response.raise_for_status()
        return response.json()
