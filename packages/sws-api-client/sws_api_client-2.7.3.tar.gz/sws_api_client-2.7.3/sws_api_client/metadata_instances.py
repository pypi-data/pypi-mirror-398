"""Metadata Instances Module for SWS API.

This module provides functionality for managing metadata instances,
including retrieving metadata information through the SWS API client.
"""

import logging
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sws_api_client.sws_api_client import SwsApiClient

logger = logging.getLogger(__name__)

class Target(BaseModel):
    """Model representing a metadata target.

    Attributes:
        id (str): Target identifier
        type (str): Target type (dataset, plugin, domain, etc.)
    """
    id: str
    type: str

class MetadataInstance(BaseModel):
    """Model representing a metadata instance.

    Attributes:
        id (int): Metadata instance identifier
        version (str): Version of the metadata
        model (str): Model type (scanProps, dissemination_metadata, file, flower, etc.)
        target (Target): Target information
        content (Optional[Any]): Content of the metadata instance
        createdOn (int): Creation timestamp
        lastModifiedOn (int): Last modification timestamp
        createdBy (str): User who created the instance
        lastModifiedBy (str): User who last modified the instance
    """
    id: int
    version: str
    model: str
    target: Target
    content: Optional[Any] = None
    createdOn: int
    lastModifiedOn: int
    createdBy: str
    lastModifiedBy: str

class MetadataInstances:
    """Class for managing metadata instances operations through the SWS API.

    This class provides methods for retrieving metadata instances information.

    Args:
        sws_client (SwsApiClient): An instance of the SWS API client
    """

    def __init__(self, sws_client: SwsApiClient) -> None:
        """Initialize the MetadataInstances manager with SWS client."""
        self.sws_client = sws_client

    def get_all(self) -> List[MetadataInstance]:
        """Retrieve all metadata instances.

        Returns:
            List[MetadataInstance]: List of all metadata instances
        """
        url = "/metadata/instance/all"
        response = self.sws_client.discoverable.get('is_api', url)
        return [MetadataInstance(**instance) for instance in response]

    def get(self, instance_id: int) -> Optional[MetadataInstance]:
        """Retrieve a specific metadata instance by ID.

        Args:
            instance_id (int): The metadata instance identifier

        Returns:
            Optional[MetadataInstance]: The metadata instance if found, None otherwise
        """
        url = f"/metadata/instance/all/{instance_id}"
        response = self.sws_client.discoverable.get('is_api', url)
        if response:
            return MetadataInstance(**response)
        return None

    def create(self, version: str, model: str, target: Target, content: Optional[Any] = None) -> MetadataInstance:
        """Create a new metadata instance.

        Args:
            version (str): Version of the metadata
            model (str): Model type (scanProps, dissemination_metadata, file, flower, etc.)
            target (Target): Target information
            content (Optional[Any]): Content of the metadata instance

        Returns:
            MetadataInstance: The created metadata instance
        """
        url = "/metadata/instance/all"
        data = {
            "version": version,
            "model": model,
            "target": target.model_dump(),
            "content": content
        }
        response = self.sws_client.discoverable.post('is_api', url, data=data)
        return MetadataInstance(**response)

    def update(self, metadata_instance: MetadataInstance) -> MetadataInstance:
        """Update an existing metadata instance.

        Args:
            metadata_instance (MetadataInstance): The complete metadata instance to update

        Returns:
            MetadataInstance: The updated metadata instance
        """
        url = f"/metadata/instance/all/{metadata_instance.id}"
        data = metadata_instance.model_dump()
        options = {'json_body': True}
        
        response = self.sws_client.discoverable.put('is_api', url, data=data, options=options)
        return MetadataInstance(**response)

    def delete(self, instance_id: int) -> bool:
        """Delete a metadata instance by ID.

        Args:
            instance_id (int): The metadata instance identifier

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        url = f"/metadata/instance/all/{instance_id}"
        response = self.sws_client.discoverable.delete('is_api', url)
        
        # Check if the response indicates success
        if isinstance(response, dict):
            return response.get('success', False)
        
        # If response is not a dict, assume success if no exception was raised
        return True


