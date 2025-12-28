from typing import Dict, List, Any, Optional
import requests
from .schemas.roles import  RoleSchema, CreateRoleRequest, RoleUser, DashboardRight, QlikDashboardRight
from brynq_sdk_functions import Functions

class Roles:
    """
    Handles all role-related operations for BrynQ SDK.
    """
    def __init__(self, brynq_instance):
        """
        Initialize Roles manager.
        
        Args:
            brynq_instance: The parent BrynQ instance
        """
        self._brynq = brynq_instance

    def get(self) -> List[Dict[str, Any]]:
        """
        Get all roles from BrynQ
        
        :return: A list of validated role dictionaries
        :raises: 
            requests.HTTPError: If the API request fails
            ValueError: If the role data is invalid
        """
        response = self._brynq.brynq_session.get(
            url=f'{self._brynq.url}roles',
            timeout=self._brynq.timeout
        )
        response.raise_for_status()
        
        # Get the raw data
        roles_data = response.json()
        
        # Validate each role
        try:
            valid_data, _ = Functions.validate_pydantic_data(roles_data, schema=RoleSchema)
            return valid_data  # Return first item since it's a list
        except ValueError as e:
            raise ValueError(f"Invalid role data received from API: {str(e)}")

    def get_by_id(self, role_id: int) -> Dict[str, Any]:
        """Get a specific role by ID.

        Args:
            role_id (int): ID of the role to retrieve.

        Returns:
            Dict[str, Any]: Role data including id, name, permissions, dashboards, and qlik_dashboards.

        Raises:
            ValueError: If the response data is invalid.
            requests.exceptions.RequestException: If the API request fails.
        """
        response = self._brynq.brynq_session.get(
            f"{self._brynq.url}roles/{role_id}",
            timeout=self._brynq.timeout
        )
        response.raise_for_status()

        try:
            role_data = response.json()
            valid_data, _ = Functions.validate_pydantic_data(role_data, schema=RoleSchema)
            return valid_data[0]
        except ValueError as e:
            raise ValueError(f"Invalid role data received from API: {str(e)}")

    def create(self, data: Dict[str, Any]) -> None:
        """Create a new role.
        
        Args:
            data: Dictionary containing role data:
                {
                    "name": str,  # Name of the role
                    "dashboards": List[Dict], # Optional list of dashboard rights
                    "qlikDashboards": List[Dict]  # Optional list of Qlik dashboard rights
                }
                
        Raises:
            ValueError: If the request data is invalid.
            requests.exceptions.RequestException: If the API request fails.
        """
        try:
            valid_data, _ = Functions.validate_pydantic_data(data, schema=CreateRoleRequest)
            if valid_data:
                response = self._brynq.brynq_session.post(
                    f"{self._brynq.url}roles",
                    json=valid_data[0],
                    timeout=self._brynq.timeout
                )
                response.raise_for_status()
                return response
            else:
                raise ValueError(f"Invalid role creation data")
        except ValueError as e:
            raise ValueError(f"Invalid role creation data: {str(e)}")

    def update(self, data: Dict[str, Any]) -> requests.Response:
        """Update an existing role.
        
        Args:
            data: Dictionary containing role data:
                {
                    "id": int,  # ID of the role to update
                    "name": str,  # New name for the role
                    "dashboards": List[Dict],  # Optional list of dashboard rights
                    "qlikDashboards": List[Dict]  # Optional list of Qlik dashboard rights
                }
                
        Raises:
            ValueError: If the request data is invalid.
            requests.exceptions.RequestException: If the API request fails.
        """
        try:
            valid_data, _ = Functions.validate_pydantic_data(data, schema=RoleSchema)
            if valid_data:
                response = self._brynq.brynq_session.put(
                    f"{self._brynq.url}roles/{data['id']}",
                    json=valid_data[0],
                    timeout=self._brynq.timeout
                )
                response.raise_for_status()
                return response
            else:
                raise ValueError(f"Invalid role update data")
        except ValueError as e:
            raise ValueError(f"Invalid role update data: {str(e)}")

    def delete(self, role_id: int, force: bool = False) -> None:
        """Delete a role by ID.
        
        Args:
            role_id (int): ID of the role to delete
            force (bool, optional): Whether to force delete even if role is in use. Defaults to False.
            
        Raises:
            ValueError: If role_id is not a positive integer.
            requests.exceptions.RequestException: If the API request fails.
        """
        # Basic validation
        if not isinstance(role_id, int) or role_id <= 0:
            raise ValueError("role_id must be a positive integer")

        params = {"force": "true" if force else "false"}
        response = self._brynq.brynq_session.delete(
            f"{self._brynq.url}roles/{role_id}",
            params=params,
            timeout=self._brynq.timeout
        )
        response.raise_for_status()
        return response

    def get_users(self, role_id: int) -> List[Dict[str, Any]]:
        """Get list of users assigned to a role.
        
        Args:
            role_id (int): ID of the role to get users for
            
        Returns:
            List[Dict[str, Any]]: List of users with their details (id, name, email, active status)
            
        Raises:
            ValueError: If role_id is not a positive integer or if the response data is invalid.
            requests.exceptions.RequestException: If the API request fails.
        """
        # Basic validation
        if not isinstance(role_id, int) or role_id <= 0:
            raise ValueError("role_id must be a positive integer")

        response = self._brynq.brynq_session.get(
            f"{self._brynq.url}roles/{role_id}/users",
            timeout=self._brynq.timeout
        )
        response.raise_for_status()
        
        try:
            users_data = response.json()
            valid_data, _ = Functions.validate_pydantic_data(users_data, schema=RoleUser)
            return valid_data
        except ValueError as e:
            raise ValueError(f"Invalid user data received from API: {str(e)}")

    def assign_dashboard_rights(self, role_id: int, dashboard_rights: List[Dict[str, Any]]) -> None:
        """Assign or update dashboard rights for a role.
        
        Args:
            role_id (int): ID of the role
            dashboard_rights: List of dashboard rights, each containing:
                - dashboardId (int): ID of the dashboard
                - editable (bool): Whether the dashboard is editable
                - entities (List[int]): List of entity IDs
                
        Raises:
            ValueError: If role_id is not a positive integer or if dashboard_rights data is invalid.
            requests.exceptions.RequestException: If the API request fails.
        """
        # Basic validation
        if not isinstance(role_id, int) or role_id <= 0:
            raise ValueError("role_id must be a positive integer")

        try:
            valid_data, _ = Functions.validate_pydantic_data(dashboard_rights, schema=DashboardRight)
            response = self._brynq.brynq_session.post(
                f"{self._brynq.url}roles/{role_id}/dashboards",
                json=valid_data[0],
                timeout=self._brynq.timeout
            )
            response.raise_for_status()
            return response
        except ValueError as e:
            raise ValueError(f"Invalid dashboard rights data: {str(e)}")

    def assign_qlik_dashboard_rights(self, role_id: int, qlik_dashboard_rights: List[Dict[str, Any]]) -> None:
        """Assign or update Qlik dashboard rights for a role.
        
        Args:
            role_id (int): ID of the role
            qlik_dashboard_rights: List of Qlik dashboard rights, each containing:
                - guid (str): Dashboard GUID
                - dataModelEditable (bool): Whether the data model is editable
                - editable (bool): Whether the dashboard is editable
                - entities (List[int]): List of entity IDs
                
        Raises:
            ValueError: If role_id is not a positive integer or if qlik_dashboard_rights data is invalid.
            requests.exceptions.RequestException: If the API request fails.
        """
        # Basic validation
        if not isinstance(role_id, int) or role_id <= 0:
            raise ValueError("role_id must be a positive integer")

        try:
            valid_data, _ = Functions.validate_pydantic_data(qlik_dashboard_rights, schema=QlikDashboardRight)
            response = self._brynq.brynq_session.post(
                f"{self._brynq.url}roles/{role_id}/dashboards/qlik",
                json=valid_data[0],
                timeout=self._brynq.timeout
            )
            response.raise_for_status()
            return response
        except ValueError as e:
            raise ValueError(f"Invalid Qlik dashboard rights data: {str(e)}")

    def assign_dashboard_qlik(self, role_id: int, qlik_dashboards: list) -> dict:
        """Assign or update role Qlik dashboard rights.

        Args:
            role_id (int): ID of the role
            qlik_dashboards (list): List of Qlik dashboard rights objects

        Returns:
            dict: Response from the API

        Raises:
            ValueError: If role_id is not a positive integer or if input data is invalid
            requests.exceptions.RequestException: If the API request fails
        """
        if not isinstance(role_id, int) or role_id <= 0:
            raise ValueError("role_id must be a positive integer")

        payload = {"qlikDashboards": qlik_dashboards}
        valid_data, _ = Functions.validate_pydantic_data(payload, schema=QlikDashboardRight)

        response = self._brynq.brynq_session.post(
            f"{self._brynq.url}roles/{role_id}/dashboards/qlik",
            json=valid_data[0],
            timeout=self._brynq.timeout
        )
        response.raise_for_status()
        return response.json()
