import requests
from typing import Dict, List, Any, Literal, Union, Optional
from .schemas.organization_chart import (
    OrganizationChartNode,
    OrganizationLayerCreate,
    OrganizationLayerGet,
    OrganizationLayerUpdate,
    OrganizationNode,
    OrganizationNodeCreate, OrganizationNodeUpdate
)
from brynq_sdk_functions import Functions


class OrganizationChart:
    """
    Handles all organization chart related operations for BrynQ SDK.
    """
    def __init__(self, brynq_instance):
        """
        Initialize OrganizationChart manager.
        
        Args:
            brynq_instance: The parent BrynQ instance
        """
        self._brynq = brynq_instance

    def get(self, layout: Literal["nested", "flat"] = "nested") -> List[Dict[str, Any]]:
        """Get all organization charts.

        Args:
            layout (str): Layout format, either "nested" or "flat"

        Returns:
            Dict[str, Any]: Organization charts data including:
                - id (int): Node ID
                - name (str): Node name
                - dropIndex (int): Drop index for ordering
                - parent_id (int, optional): Parent node ID, null for root nodes
                - source_system_entities (List[str]): List of source system entities

        Raises:
            requests.exceptions.RequestException: If the API request fails
            ValueError: If layout is not "nested" or "flat" or if the response data is invalid
        """
        if layout not in ["nested", "flat"]:
            raise ValueError('layout must be either "nested" or "flat"')

        response = self._brynq.brynq_session.get(
            f"{self._brynq.url}organization-chart",
            params={"layout": layout},
            timeout=self._brynq.timeout
        )
        response.raise_for_status()
        
        try:
            chart_data = response.json()
            valid_data, _ = Functions.validate_pydantic_data(chart_data, schema=OrganizationChartNode)
            return valid_data
        except ValueError as e:
            raise ValueError(f"Invalid organization chart data: {str(e)}")

    def get_layers(self) -> List[Dict[str, Any]]:
        """Get all organization layers.
        
        Returns:
            Dict[str, Any]: Organization chart layers data including:
                - id (int): Layer ID
                - name (str): Layer name
                - level (int): Layer level in hierarchy
            
        Raises:
            requests.exceptions.RequestException: If the API request fails
            ValueError: If the response data is invalid
        """
        response = self._brynq.brynq_session.get(
            f"{self._brynq.url}organization-chart/layers",
            timeout=self._brynq.timeout
        )
        response.raise_for_status()
        
        try:
            layers_data = response.json()
            valid_data, _ = Functions.validate_pydantic_data(layers_data, schema=OrganizationLayerGet)
            return valid_data
        except ValueError as e:
            raise ValueError(f"Invalid organization layer data: {str(e)}")

    def create_layer(self, data:Dict[str,Any]) -> Dict[str, Any]:
        """Create a new organization layer.
        
        Args:
            data (Dict[str,Any]): Data to create a new layer for
                {
                    name (str): Layer name
                    level (int): Layer level in hierarchy
                }
        Returns:
            Dict[str, Any]: Response from the API
            
        Raises:
            requests.exceptions.RequestException: If the API request fails
            ValueError: If the input data is invalid
        """
        valid_data, _ = Functions.validate_pydantic_data(data, schema=OrganizationLayerCreate)
        
        response = self._brynq.brynq_session.post(
            f"{self._brynq.url}organization-chart/layers",
            json=valid_data[0],
            timeout=self._brynq.timeout
        )
        response.raise_for_status()
        return response

    def update_layer(self, data:dict[str, Any]) -> Dict[str, Any]:
        """Update an existing organization layer.
        
        Args:
            data(dict[]): Organization layer data
                {
                    layer_id (int): ID of the layer to update
                    name (str): New layer name
                    level (int): New layer level in hierarchy
                }
        Returns:
            Dict[str, Any]: Response from the API
            
        Raises:
            requests.exceptions.RequestException: If the API request fails
            ValueError: If the input data is invalid
        """
        valid_data, _ = Functions.validate_pydantic_data(data, schema=OrganizationLayerUpdate)
        
        response = self._brynq.brynq_session.put(
            f"{self._brynq.url}organization-chart/layers/{data['id']}",
            json=valid_data[0],
            timeout=self._brynq.timeout
        )
        response.raise_for_status()
        return response

    def delete_layer(self, layer_id: int) -> None:
        """Delete a layer and its underlying layers.
        
        Args:
            layer_id (int): ID of the layer to delete
            
        Raises:
            requests.exceptions.RequestException: If the API request fails
            ValueError: If layer_id is not an integer
        """
        if not isinstance(layer_id, int):
            raise ValueError("layer_id must be an integer")
        
        response = self._brynq.brynq_session.delete(
            f"{self._brynq.url}organization-chart/layers/{layer_id}",
            timeout=self._brynq.timeout
        )
        response.raise_for_status()
        return response

    def get_nodes(self) -> List[Dict[str, Any]]:
        """Get all organization chart nodes.
        
        Returns:
            Dict[str, Any]: Organization chart nodes data including:
                - id (int): Node ID
                - name (str): Node name
                - parentId (int, optional): Parent node ID
            
        Raises:
            requests.exceptions.RequestException: If the API request fails
            ValueError: If the response data is invalid
        """
        response = self._brynq.brynq_session.get(
            url=f'{self._brynq.url}organization-chart/nodes',
            timeout=self._brynq.timeout
        )
        response.raise_for_status()
        valid_data, _ = Functions.validate_pydantic_data(response.json(), schema=OrganizationNode)
        return valid_data

    def create_nodes(self, data:dict) -> Dict[str, Any]:
        """Create an organization chart node.
        
        Args:
            data (dict): Node data
                {
                    name (str): Name of the node
                    position (int, optional): Position among siblings
                    parent_id (int, optional): ID of the parent node
                }
        Returns:
            Dict[str, Any]: Response from the API
            
        Raises:
            requests.exceptions.RequestException: If the API request fails
            ValueError: If the input data is invalid
        """

        valid_data, _ = Functions.validate_pydantic_data(data, schema=OrganizationNodeCreate)
        
        response = self._brynq.brynq_session.post(
            f"{self._brynq.url}organization-chart/nodes",
            json=valid_data[0],
            timeout=self._brynq.timeout
        )
        response.raise_for_status()
        return response

    def update_node(self, data: dict) -> dict:
        """Update an organization chart node.

        Args:
            data (dict): Dictionary containing fields to update (e.g. name, position, parentId)

        Returns:
            dict: Updated node details returned from API

        Raises:
            ValueError: If node_id is not a positive integer
            requests.exceptions.RequestException: If the API request fails
        """
        valid_data, _ = Functions.validate_pydantic_data(data, schema=OrganizationNodeUpdate)

        response = self._brynq.brynq_session.put(
            f"{self._brynq.url}organization-chart/nodes/{data['id']}",
            json=valid_data[0],
            timeout=self._brynq.timeout
        )
        response.raise_for_status()
        return response

    def delete_node(self, node_id: int) -> None:
        """Delete a node and its underlying nodes.

        Args:
            node_id (int): ID of the layer to delete

        Raises:
            requests.exceptions.RequestException: If the API request fails
            ValueError: If layer_id is not an integer
        """
        if not isinstance(node_id, int):
            raise ValueError("node_id must be an integer")

        response = self._brynq.brynq_session.delete(
            f"{self._brynq.url}organization-chart/nodes/{node_id}",
            timeout=self._brynq.timeout
        )
        response.raise_for_status()
        return response
