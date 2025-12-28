from typing import List, Dict, Any, Optional
import requests
from requests import Response
from .schemas.customers import CustomerSchema, CustomerContractDetailsSchema
from brynq_sdk_functions import Functions

class Customers:
    """Class for interacting with BrynQ customer endpoints"""

    def __init__(self, brynq):
        """Initialize Customers class
        
        Args:
            brynq: Parent BrynQ instance for authentication and configuration
        """
        self.brynq = brynq

    def get(self) -> List[Dict[str, Any]]:
        """Get all customers this token has access to.
        
        Returns:
            List[Dict[str, Any]]: List of customer objects with validated data
            
        Raises:
            requests.exceptions.RequestException: If the API request fails
            ValueError: If the response data doesn't match the expected schema
        """
        response = self.brynq.brynq_session.get(
            url=f"{self.brynq.url}customers",
            timeout=self.brynq.timeout
        )
        response.raise_for_status()
        
        try:
            customers_data = response.json()
            valid_data, _ = Functions.validate_pydantic_data(customers_data, CustomerSchema, debug=False)
            return valid_data
        except ValueError as e:
            raise ValueError(f"Invalid customer data received from API: {str(e)}")

    def get_all_contract_details(self) -> List[Dict[str, Any]]:
        """Get all customers contract details.
        
        Returns:
            List[Dict[str, Any]]: List of customer contract details with validated data
            
        Raises:
            requests.exceptions.RequestException: If the API request fails
            ValueError: If the response data doesn't match the expected schema
        """
        response = self.brynq.brynq_session.get(
            f"{self.brynq.url}customers/contract-details",
            timeout=self.brynq.timeout
        )
        response.raise_for_status()
        
        try:
            contract_details = response.json()
            valid_data, _ = Functions.validate_pydantic_data(contract_details, CustomerContractDetailsSchema, debug=False)
            return valid_data
        except ValueError as e:
            raise ValueError(f"Invalid contract details received from API: {str(e)}")

    def get_contract_details_by_id(self, customer_id: int) -> Dict[str, Any]:
        """Get contract details for a specific customer.
        
        Args:
            customer_id (int): The ID of the customer to get contract details for.

        Returns:
            Dict[str, Any]: Contract details for the specified customer.

        Raises:
            ValueError: If the response data is invalid.
            requests.exceptions.RequestException: If the API request fails.
        """
        response = self.brynq.brynq_session.get(
            f"{self.brynq.url}customers/{customer_id}/contract-details",
            timeout=self.brynq.timeout
        )
        response.raise_for_status()

        try:
            contract_details = response.json()
            valid_data, _ = Functions.validate_pydantic_data(contract_details, CustomerContractDetailsSchema, debug=False)
            return valid_data[0]
        except ValueError as e:
            raise ValueError(f"Invalid contract details received from API: {str(e)}")
