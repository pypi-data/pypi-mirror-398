import requests
from typing import List, Dict, Any
from .schemas.users import (
    User, UserUpdate, UserInvite,
    QlikDashboardRightsPayload, DashboardRightsPayload, QlikAppUserAuthorization, UserEntitiesPayload
)
from brynq_sdk_functions import Functions


class Users:
    """
    Handles all user-related operations for BrynQ SDK.
    """
    def __init__(self, brynq_instance):
        """
        Initialize Users manager.

        Args:
            brynq_instance: The parent BrynQ instance
        """
        self._brynq = brynq_instance

    def get(self) -> List[Dict[str, Any]]:
        """Get all users from BrynQ

        Returns:
            List[Dict[str, Any]]: List of users with their details:
                - id (int): User ID
                - name (str): First name
                - email (str): User email
                - roles (List[dict]): User roles
                - organization_chart_entities (List[dict]): Organization chart entities
                - qlik_dashboards (List[dict]): Qlik dashboards
                - dashboards (List[dict]): Standard dashboards

        Raises:
            requests.exceptions.RequestException: If the API request fails
            ValueError: If the response data is invalid
        """
        response = self._brynq.brynq_session.get(
            url=f'{self._brynq.url}users',
            timeout=self._brynq.timeout
        )
        response.raise_for_status()

        valid_data, _ = Functions.validate_pydantic_data(response.json(), schema=User)
        return valid_data

    def get_by_id(self, user_id: int) -> Dict[str, Any]:
        """
        Get a specific user by ID.

        Args:
            user_id: The ID of the user to retrieve

        Returns:
            Dict[str, Any]: User details

        Raises:
            requests.exceptions.RequestException: If the API request fails
            requests.exceptions.HTTPError: If user is not found (404)
        """
        response = self._brynq.brynq_session.get(
            url=f'{self._brynq.url}users/{user_id}',
            timeout=self._brynq.timeout
        )
        response.raise_for_status()
        valid_data, _ = Functions.validate_pydantic_data(response.json(), schema=User)
        return valid_data[0]

    def invite(self, user_data: dict) -> requests.Response:
        """Invite a new user to BrynQ

        Args:
            user_data: Dictionary containing user details. Example:
                {
                    "email": "user@example.com",
                    "products": {
                        "qlikSenseAnalyzer": true,
                        "qlikSenseProfessional": false
                    }
                }
                Note: products field is optional

        Raises:
            requests.exceptions.RequestException: If the API request fails
            ValueError: If the input data is invalid
        """
        valid_data, _ = Functions.validate_pydantic_data(user_data, schema=UserInvite)

        response = self._brynq.brynq_session.post(
            url=f'{self._brynq.url}users',
            json=valid_data[0],
            timeout=self._brynq.timeout
        )
        response.raise_for_status()
        return response

    def update(self, user_id: str, user_data: dict) -> requests.Response:
        """Update a user in BrynQ

        Args:
            user_id: The ID of the user to update
            user_data: Dictionary containing user details to update. Example:
                {
                    "name": "John Doe",
                    "username": "johndoe",
                    "email": "john@example.com",
                    "language": "en",
                    "roles": [1, 2, 3],
                    "products": {
                        "qlikSenseAnalyzer": true,
                        "qlikSenseProfessional": false
                    }
                }
                All fields are optional.

        Returns:
            Dict[str, Any]: Updated user data

        Raises:
            requests.exceptions.RequestException: If the API request fails
            ValueError: If the input data is invalid
            requests.exceptions.HTTPError: If user is not found (404)
        """
        if not isinstance(user_id, str):
            raise ValueError("user_id must be a string")

        valid_data, _ = Functions.validate_pydantic_data(user_data, schema=UserUpdate)

        response = self._brynq.brynq_session.put(
            url=f'{self._brynq.url}users/{user_id}',
            json=valid_data[0],
            timeout=self._brynq.timeout
        )
        response.raise_for_status()

        return response

    def delete(self, user_id: str) -> requests.Response:
        """
        Delete a user in BrynQ
        :param user_id: The id of the user in BrynQ
        """
        if not isinstance(user_id, int):
            raise ValueError("user_id must be an integer")
        response = self._brynq.brynq_session.delete(
            url=f'{self._brynq.url}users/{user_id}',
            timeout=self._brynq.timeout
        )
        response.raise_for_status()
        return response

    def assign_dashboard_rights(self, user_id: int, dashboard_rights: List[Dict[str, Any]]) -> None:
        """Assign or update dashboard rights to a user by ID

        Args:
            user_id: Numeric ID of the user
            dashboard_rights: List of dashboard rights. Example:
                [
                    {
                        "dashboardId": 123,
                        "editable": true,
                        "organigrams": [1, 2, 3]
                    }
                ]

        Raises:
            requests.exceptions.RequestException: If the API request fails
            ValueError: If user_id is not an integer or input data is invalid
            requests.exceptions.HTTPError: If user is not found (404)
        """
        if not isinstance(user_id, int):
            raise ValueError("user_id must be an integer")

        payload = {
            "dashboardRights": dashboard_rights
        }
        valid_data, _ = Functions.validate_pydantic_data(payload, schema=DashboardRightsPayload)

        response = self._brynq.brynq_session.post(
            url=f'{self._brynq.url}users/{user_id}/dashboards',
            json=valid_data[0],
            timeout=self._brynq.timeout
        )
        response.raise_for_status()
        return response

    def assign_roles(self, user_id: int, roles: List[int]) -> None:
        """Assign roles to a user by ID

        Args:
            user_id: Numeric ID of the user
            roles: List of role IDs to assign. Example:
                [1, 2, 3]

        Raises:
            requests.exceptions.RequestException: If the API request fails
            ValueError: If user_id is not an integer or input data is invalid
            requests.exceptions.HTTPError: If user is not found (404)
        """
        import warnings
        warnings.warn("This method is deprecated. Use update() instead.", DeprecationWarning)
        response = self.update(user_id, {"roles": roles})
        response.raise_for_status()
        return response

    def assign_organigram_entities(self, user_id: int, organigram_entities: list) -> dict:
        """Assign organigrams to a user by ID.

        Args:
            user_id (int): Numeric ID of the user
            organigram_entities (list): List of organigram entity objects

        Returns:
            dict: Response from the API

        Raises:
            ValueError: If user_id is not an integer or input data is invalid
            requests.exceptions.RequestException: If the API request fails
        """
        if not isinstance(user_id, int):
            raise ValueError("user_id must be an integer")
        payload = {"organigramEntities": organigram_entities}
        valid_data, _ = Functions.validate_pydantic_data(payload, schema=UserEntitiesPayload)
        response = self._brynq.brynq_session.post(
            url=f"{self._brynq.url}users/{user_id}/organigram-entities",
            json=valid_data[0],
            timeout=self._brynq.timeout
        )
        response.raise_for_status()
        return response.json()

    def assign_dashboard_qlik(self, user_id: int, qlik_dashboard_rights: list) -> dict:
        """Assign or update Qlik dashboard rights to a user by ID.

        Args:
            user_id (int): Numeric ID of the user
            qlik_dashboard_rights (list): List of Qlik dashboard rights objects

        Returns:
            dict: Response from the API

        Raises:
            ValueError: If user_id is not an integer or input data is invalid
            requests.exceptions.RequestException: If the API request fails
        """
        if not isinstance(user_id, int):
            raise ValueError("user_id must be an integer")
        payload = {"qlikDashboardRights": qlik_dashboard_rights}
        valid_data, _ = Functions.validate_pydantic_data(payload, schema=QlikDashboardRightsPayload)
        response = self._brynq.brynq_session.post(
            url=f"{self._brynq.url}users/{user_id}/dashboards/qlik",
            json=valid_data[0],
            timeout=self._brynq.timeout
        )
        response.raise_for_status()
        return response.json()

    def assign_qlik_dashboard_rights(self, user_id: int, dashboard_rights: List[Dict[str, Any]]) -> None:
        """Assign or update Qlik dashboard rights to a user by ID

        Args:
            user_id: Numeric ID of the user
            dashboard_rights: List of dashboard rights. Example:
                [
                    {
                        "guid": "dashboard-guid",
                        "dataModelEdit": true,
                        "editable": true,
                        "organigrams": [1, 2, 3]
                    }
                ]

        Raises:
            requests.exceptions.RequestException: If the API request fails
            ValueError: If user_id is not an integer or input data is invalid
            requests.exceptions.HTTPError: If user is not found (404)
        """
        if not isinstance(user_id, int):
            raise ValueError("user_id must be an integer")

        payload = {
            "dashboardRights": dashboard_rights
        }
        valid_data, _ = Functions.validate_pydantic_data(payload, schema=QlikDashboardRightsPayload)

        response = self._brynq.brynq_session.post(
            url=f'{self._brynq.url}users/{user_id}/dashboards/qlik',
            json=valid_data[0],
            timeout=self._brynq.timeout
        )
        response.raise_for_status()
        return response

    def get_user_authorization_qlik_app(self, guid: str) -> List[Dict[str, Any]]:
        """Get all users who have access to a Qlik dashboard with their entities

        Args:
            guid: GUID of the Qlik dashboard

        Returns:
            List[Dict[str, Any]]: List of users and their entities. Example:
                [
                    {
                        "username": null,
                        "userId": 420687,
                        "entityCodes": []
                    }
                ]

        Raises:
            requests.exceptions.RequestException: If the API request fails
            ValueError: If the input data is invalid
        """
        response = self._brynq.brynq_session.get(
            url=f'{self._brynq.url}/qlik/{guid}/users',
            timeout=self._brynq.timeout
        )
        response.raise_for_status()

        # Wrap response in authorizations field to match schema
        valid_data, _ = Functions.validate_pydantic_data(response.json(), schema=QlikAppUserAuthorization)
        return valid_data

    def assign_user_entities(self, user_id: int, entity_ids: List[int]) -> requests.Response:
        """Assign organization entities to a user

        Args:
            user_id: Numeric ID of the user
            entity_ids: List of entity IDs to assign. Example:
                [1, 2, 3]

        Raises:
            requests.exceptions.RequestException: If the API request fails
            ValueError: If user_id is not an integer or input data is invalid
            requests.exceptions.HTTPError: If user is not found (404)
        """
        if not isinstance(user_id, int):
            raise ValueError("user_id must be an integer")

        payload = {"entities": entity_ids}
        valid_data, _ = Functions.validate_pydantic_data(payload, schema=UserEntitiesPayload)

        response = self._brynq.brynq_session.post(
            url=f'{self._brynq.url}users/{user_id}/organigram-entities',
            json=valid_data[0],
            timeout=self._brynq.timeout
        )
        response.raise_for_status()
        return response

    def update_user_entities(self, user_id: int, entity_ids: List[int]) -> None:
        """Overwrite organization entities for a user

        Args:
            user_id: Numeric ID of the user
            entity_ids: List of entity IDs to set. Example:
                [1, 2, 3]

        Raises:
            requests.exceptions.RequestException: If the API request fails
            ValueError: If user_id is not an integer or input data is invalid
            requests.exceptions.HTTPError: If user is not found (404)
        """
        if not isinstance(user_id, int):
            raise ValueError("user_id must be an integer")

        payload = {"entities": entity_ids}
        valid_data, _ = Functions.validate_pydantic_data(payload, schema=UserEntitiesPayload)

        response = self._brynq.brynq_session.put(
            url=f'{self._brynq.url}users/{user_id}/organigram-entities',
            json=valid_data[0],
            timeout=self._brynq.timeout
        )
        response.raise_for_status()
        return response

    def delete_user_entities(self, user_id: int, entity_ids: List[int]) -> None:
        """Delete organization entities from a user

        Args:
            user_id: Numeric ID of the user
            entity_ids: List of entity IDs to delete. Example:
                [1, 2, 3]

        Raises:
            requests.exceptions.RequestException: If the API request fails
            ValueError: If user_id is not an integer or input data is invalid
            requests.exceptions.HTTPError: If user is not found (404)
        """
        if not isinstance(user_id, int):
            raise ValueError("user_id must be an integer")

        payload = {"entities": entity_ids}
        valid_data, _ = Functions.validate_pydantic_data(payload, schema=UserEntitiesPayload)

        response = self._brynq.brynq_session.delete(
            url=f'{self._brynq.url}users/{user_id}/organigram-entities',
            json=valid_data[0],
            timeout=self._brynq.timeout
        )
        response.raise_for_status()
        return response
