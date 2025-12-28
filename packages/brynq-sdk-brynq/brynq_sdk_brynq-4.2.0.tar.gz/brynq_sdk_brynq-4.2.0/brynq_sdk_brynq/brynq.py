import os
import requests
import pandas as pd
import warnings
from typing import Union, Literal, Optional, List, Dict, Any
from .users import Users
from .organization_chart import OrganizationChart
from .source_systems import SourceSystems
from .customers import Customers
from .interfaces import Interfaces
from .roles import Roles
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class BrynQ:
    def __init__(self, subdomain: str = None, api_token: str = None, staging: str = 'prod'):
        self.subdomain = os.getenv("BRYNQ_SUBDOMAIN", subdomain)
        self.api_token = os.getenv("BRYNQ_API_TOKEN", api_token)
        self.environment = os.getenv("BRYNQ_ENVIRONMENT", staging)
        self.timeout = 3600
        self.data_interface_id = os.getenv("DATA_INTERFACE_ID")
        if self.data_interface_id is None:
            raise ValueError("BRYNQ_DATA_INTERFACE_ID environment variable is not set, you should use this class via the TaskScheduler or set the variable in your code with:"
                             "os.environ['DATA_INTERFACE_ID'] = str(self.data_interface_id). This is better than setting it in your .env where you will have to change it when switching between interfaces.")

        if any([self.subdomain is None, self.api_token is None]):
            raise ValueError("Set the subdomain, api_token either in your .env file or provide the subdomain and api_token parameters")

        possible_environments = {
            'staging' : 'https://app.brynq-staging.com/api/v2/',
            'prod': 'https://app.brynq.com/api/v2/',
            'next': 'https://app.brynq-next.com/api/v2/'
        }
        if self.environment not in possible_environments.keys():
            raise ValueError(f"Environment should be in {','.join(possible_environments)}")

        self.url = possible_environments[self.environment]

        # Initialize session with retry strategy. This is called brynq_session and not session as to not conflict with other SDKs that use self.session
        self.brynq_session = requests.Session()
        retry_strategy = Retry(
            total=3,  # number of retries
            backoff_factor=0.5,  # wait 0.5s * (2 ** (retry - 1)) between retries
            status_forcelist=[500, 502, 503, 504]  # HTTP status codes to retry on
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.brynq_session.mount("http://", adapter)
        self.brynq_session.mount("https://", adapter)
        self.brynq_session.headers.update(self._get_headers())

        # Initialize components
        self.users = Users(self)
        self.organization_chart = OrganizationChart(self)
        self.source_systems = SourceSystems(self)
        self.customers = Customers(self)
        self.interfaces = Interfaces(self)
        self.roles = Roles(self)

    def _get_headers(self):
        return {
            'Authorization': f'Bearer {self.api_token}',
            'Domain': self.subdomain
        }

    def get_mapping(self, mapping: str, return_format: Literal['input_as_key', 'columns_names_as_keys', 'nested_input_output'] = 'input_as_key') -> dict:
        """
        DEPRECATED: Use brynq.mappings.get_mapping() instead
        """
        warnings.warn(
            "This method is deprecated. Use brynq.interfaces.mappings.get() instead",
            DeprecationWarning,
            stacklevel=2
        )
        """
        Get the mapping json from the mappings
        :param data_interface_id: The id of the task in BrynQ. this does not have to be the task id of the current task
        :param mapping: The name of the mapping
        :param return_format: Determines how the mapping should be returned. Options are 'input_as_key' (Default, the input column is the key, the output columns are the values), 'columns_names_as_keys', 'nested_input_output'
        :return: The json of the mapping
        """
        # Find the mapping for the given sheet name
        mappings = self.interfaces.mappings._get_mappings()
        mapping_data = next((item for item in mappings if item['name'] == mapping), None)
        if not mapping_data:
            raise ValueError(f"Mapping named '{mapping}' not found")

        # If the user want to get the column names back as keys, transform the data accordingly and return
        if return_format == 'columns_names_as_keys':
            final_mapping = []
            for row in mapping_data['values']:
                combined_dict = {}
                combined_dict.update(row['input'])
                combined_dict.update(row['output'])
                final_mapping.append(combined_dict)
        elif return_format == 'nested_input_output':
            final_mapping = mapping_data
        else:
            final_mapping = {}
            for value in mapping_data['values']:
                input_values = []
                output_values = []
                for _, val in value['input'].items():
                    input_values.append(val)
                for _, val in value['output'].items():
                    output_values.append(val)
                # Detect if there are multiple input or output columns and concatenate them
                if len(value['input'].items()) > 1 or len(value['output'].items()) > 1:
                    concatenated_input = ','.join(input_values)
                    concatenated_output = ','.join(output_values)
                    final_mapping[concatenated_input] = concatenated_output
                else:  # Default to assuming there's only one key-value pair if not concatenating
                    if output_values:
                        final_mapping[input_values[0]] = output_values[0]

        return final_mapping

    def get_mapping_as_dataframe(self, mapping: str, prefix: bool = False) -> pd.DataFrame:
        """
        DEPRECATED: Use brynq.mappings.get_mapping_as_dataframe() instead
        """
        warnings.warn(
            "This method is deprecated. Use brynq.interfaces.mappings.get(as_df = True) instead",
            DeprecationWarning,
            stacklevel=2
        )
        """
        Get the mapping dataframe from the mappings
        :param mapping: The name of the mapping
        :param prefix: A boolean to indicate if the keys should be prefixed with 'input.' and 'output.'
        :return: The dataframe of the mapping
        """
        # Find the mapping for the given sheet name
        mappings = self.interfaces.mappings._get_mappings()
        mapping_data = next((item for item in mappings if item['name'] == mapping), None)
        if not mapping_data:
            raise ValueError(f"Mapping named '{mapping}' not found")

        # Extract the values which contain the input-output mappings
        values = mapping_data['values']

        # Create a list to hold all row data
        rows = []
        for value in values:
            # Check if prefix is needed and adjust keys accordingly
            if prefix:
                input_data = {f'input.{key}': val for key, val in value['input'].items()}
                output_data = {f'output.{key}': val for key, val in value['output'].items()}
            else:
                input_data = value['input']
                output_data = value['output']

            # Combine 'input' and 'output' dictionaries
            row_data = {**input_data, **output_data}
            rows.append(row_data)

        # Create DataFrame from rows
        df = pd.DataFrame(rows)

        return df

    def get_system_credential(self, system: str, label: Union[str, list], test_environment: bool = False) -> dict:
        """
        DEPRECATED: Use brynq.credentials.get() instead
        """
        warnings.warn(
            "This method is deprecated. Use brynq.credentials.get() instead",
            DeprecationWarning,
            stacklevel=2
        )
        return self.interfaces.credentials.get_system_credential(system, label, test_environment)

    def get_interface_credential(self, system: str, system_type: Optional[str] = None,
                                 test_environment: bool = False) -> Union[dict, List[dict]]:
        """
        DEPRECATED: Use brynq.credentials.get_interface_credential() instead
        """
        warnings.warn(
            "This method is deprecated. Use brynq.credentials.get() instead",
            DeprecationWarning,
            stacklevel=2
        )
        return self.interfaces.credentials.get(self.data_interface_id, system, system_type, test_environment)

    def get_user_data(self):
        """
        DEPRECATED: Use brynq.users.get_user_data() instead
        """
        warnings.warn(
            "This method is deprecated. Use brynq.users.get_user_data() instead",
            DeprecationWarning,
            stacklevel=2
        )
        return self.users.get()

    def get_user_authorization_qlik_app(self, dashboard_id):
        """
        DEPRECATED: Use brynq.users.get_user_authorization_qlik_app() instead
        """
        warnings.warn(
            "This method is deprecated. Use brynq.users.get_user_authorization_qlik_app() instead",
            DeprecationWarning,
            stacklevel=2
        )
        return self.users.get_user_authorization_qlik_app(dashboard_id)

    def get_role_data(self):
        """
        DEPRECATED: Use brynq.users.get_role_data() instead
        """
        warnings.warn(
            "This method is deprecated. Use brynq.users.get_role_data() instead",
            DeprecationWarning,
            stacklevel=2
        )
        return self.roles.get()

    def create_user(self, user_data: dict) -> requests.Response:
        """
        DEPRECATED: Use brynq.users.create_user() instead
        """
        warnings.warn(
            "This method is deprecated. Use brynq.users.create_user() instead",
            DeprecationWarning,
            stacklevel=2
        )
        return self.users.invite(user_data)

    def update_user(self, user_id: str, user_data: dict) -> requests.Response:
        """
        DEPRECATED: Use brynq.users.update_user() instead
        """
        warnings.warn(
            "This method is deprecated. Use brynq.users.update_user() instead",
            DeprecationWarning,
            stacklevel=2
        )
        return self.users.update(user_id, user_data)

    def delete_user(self, user_id: str) -> requests.Response:
        """
        DEPRECATED: Use brynq.users.delete_user() instead
        """
        warnings.warn(
            "This method is deprecated. Use brynq.users.delete_user() instead",
            DeprecationWarning,
            stacklevel=2
        )
        return self.users.delete(user_id)

    def overwrite_user_roles(self, roles: dict) -> requests.Response:
        """
        DEPRECATED: Use brynq.users.overwrite_user_roles() instead
        """
        warnings.warn(
            "This method is deprecated. Use brynq.users.overwrite_user_roles() instead",
            DeprecationWarning,
            stacklevel=2
        )
        return self.roles.update(roles)

    def get_source_system_entities(self, system: int) -> requests.Response:
        """
        DEPRECATED: Use brynq.source_systems.get_entities() instead
        """
        warnings.warn(
            "This method is deprecated. Use brynq.source_systems.get_entities() instead",
            DeprecationWarning,
            stacklevel=2
        )
        return self.source_systems.get_entities(system)

    def get_layers(self) -> List[Dict[str, Any]]:
        """
        DEPRECATED: Use brynq.organization_chart.get_layers() instead
        """
        warnings.warn(
            "This method is deprecated. Use brynq.organization_chart.get_layers() instead",
            DeprecationWarning,
            stacklevel=2
        )
        return self.organization_chart.get_layers()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Close the session and cleanup resources"""
        if hasattr(self, 'session'):
            self.brynq_session.close()
