import os
import requests
from typing import Optional, Union, List, Dict, Any
import warnings
from .schemas.credentials import CredentialsConfig
from brynq_sdk_functions import Functions


class Credentials:
    """
    Handles all credential-related operations for BrynQ SDK.
    """
    def __init__(self, brynq_instance):
        """
        Initialize Credentials manager.
        
        Args:
            brynq_instance: The parent BrynQ instance
        """
        self._brynq = brynq_instance

    def get_system_credential(self, system: str, label: Union[str, list], test_environment: bool = False) -> dict:
        """
        DEPRECATED: Use brynq.interfaces.credentials.get() instead
        """
        warnings.warn("This function is deprecated and will be removed in a future version.", DeprecationWarning, stacklevel=2)
        response = self._brynq.brynq_session.get(
            url=f'{self._brynq.url}apps/{system}',
            timeout=self._brynq.timeout
        )
        response.raise_for_status()
        credentials = response.json()
        # rename parameter for readability
        if isinstance(label, str):
            labels = [label]
        else:
            labels = label
        # filter credentials based on label. All labels specified in label parameter should be present in the credential object
        credentials = [credential for credential in credentials if all(label in credential['labels'] for label in labels)]
        if system == 'profit':
            credentials = [credential for credential in credentials if credential['isTestEnvironment'] is test_environment]

        if len(credentials) == 0:
            raise ValueError(f'No credentials found for {system}')
        if len(credentials) != 1:
            raise ValueError(f'Multiple credentials found for {system} with the specified labels')

        return credentials[0]

    def get(self, system: str, system_type: Optional[str] = None, test_environment: bool = False) -> Union[dict, List[dict]]:
        """
        This method retrieves authentication credentials from BrynQ for a specific interface and system.
        
        :param interface_id: ID of the interface to get credentials for
        :param system: The app name to search for in credentials (e.g., 'bob', 'profit')
        :param system_type: Optional parameter to specify 'source' or 'target'. If not provided,
                            searches in both lists
        :param test_environment: boolean indicating if the test environment is used (only for 'profit' system)
        :return: Credential dictionary or list of credential dictionaries for the specified system
        """
        
        # Fetch the config using a separate method
        config = self._fetch_config()

        matching_credentials = []

        # If system_type is provided, only search in that list
        if system_type:
            if system_type not in ['source', 'target']:
                raise ValueError("system_type must be either 'source' or 'target'")
            credentials_list = config.get(f'{system_type}s', [])
            for cred in credentials_list:
                if cred.get('app') == system:
                    # Check test environment for 'profit'
                    if system == 'profit':
                        is_test = cred.get('data', {}).get('isTestEnvironment', False)
                        if is_test == test_environment:
                            matching_credentials.append({'credential': cred, 'type': system_type})
                    else:
                        matching_credentials.append({'credential': cred, 'type': system_type})

        # If no system_type provided, search both lists
        else:
            source_credentials = []
            target_credentials = []

            # Check sources
            for source in config.get('sources', []):
                if source.get('app') == system:
                    if system == 'profit':
                        is_test = source.get('data', {}).get('isTestEnvironment', False)
                        if is_test == test_environment:
                            source_credentials.append({'credential': source, 'type': 'source'})
                    else:
                        source_credentials.append({'credential': source, 'type': 'source'})

            # Check targets
            for target in config.get('targets', []):
                if target.get('app') == system:
                    if system == 'profit':
                        is_test = target.get('data', {}).get('isTestEnvironment', False)
                        if is_test == test_environment:
                            target_credentials.append({'credential': target, 'type': 'target'})
                    else:
                        target_credentials.append({'credential': target, 'type': 'target'})

            # Combine matching credentials based on type
            if source_credentials and target_credentials:
                raise ValueError(
                    f'Multiple credentials found for system {system} in both source and target. '
                    f'Please specify system_type as "source" or "target"'
                )
            matching_credentials = source_credentials or target_credentials

        # Handle results
        if len(matching_credentials) == 0:
            if system == 'profit':
                raise ValueError(f'No credentials found for system {system} with test_environment={test_environment}')
            else:
                raise ValueError(f'No credentials found for system {system}')

        if len(matching_credentials) == 1:
            return matching_credentials[0]['credential']

        if len(matching_credentials) > 1:
            warning_msg = f'Multiple credentials found for system {system}'
            if system_type:
                warning_msg += f' in {system_type}'
            warnings.warn(warning_msg)
            return [cred['credential'] for cred in matching_credentials]

    def _fetch_config(self) -> Dict[str, Any]:
        """
        Fetch configuration from BrynQ for a given interface ID.

        Args:
            interface_id (str): The ID of the interface to fetch configuration for.

        Returns:
            Dict[str, Any]: Validated credentials configuration.

        Raises:
            ValueError: If the response data is invalid.
            requests.exceptions.RequestException: If the API request fails.
        """
        response = self._brynq.brynq_session.get(
            url=f'{self._brynq.url}interfaces/{self._brynq.data_interface_id}/config/auth',
            timeout=self._brynq.timeout
        )
        response.raise_for_status()
        
        try:
            config_data = response.json()
            valid_data, _ = Functions.validate_pydantic_data(config_data, CredentialsConfig, debug=False)
            return valid_data[0]
        except ValueError as e:
            raise ValueError(f"Invalid credentials configuration received from API: {str(e)}")
