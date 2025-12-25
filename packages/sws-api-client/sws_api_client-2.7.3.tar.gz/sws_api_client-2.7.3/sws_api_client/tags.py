"""Module for managing Tags and DisseminatedTags in the SWS API.

This module provides functionality for managing tags, dissemination steps,
and related operations through the SWS API client.
"""

import logging
from typing import List, Dict, Optional, TypedDict, Union
from enum import Enum
from sws_api_client.sws_api_client import SwsApiClient

logger = logging.getLogger(__name__)

# Enum definitions
class TableLayer(str, Enum):
    """Enumeration of available table layers in the system.
    
    Attributes:
        GOLD: Production-ready data layer
        SILVER: Intermediate processed data layer
        BRONZE: Raw data layer
        STAGING: Temporary staging area
        CACHE: Cached data layer
    """
    GOLD = 'gold'
    SILVER = 'silver'
    BRONZE = 'bronze'
    STAGING = 'staging'
    CACHE = 'cache'

class TableType(str, Enum):
    """Enumeration of supported table types.
    
    Attributes:
        SDMX_CSV: SDMX-formatted CSV files
        CSV: Standard CSV files
        ICEBERG: Apache Iceberg table format
    """
    SDMX_CSV = 'SDMX-csv'
    CSV = 'csv'
    ICEBERG = 'iceberg'

class DisseminationTarget(str, Enum):
    """Enumeration of dissemination target platforms.
    
    Attributes:
        SDW: Statistical Data Warehouse target
        FAOSTAT: FAO Statistics Division target
    """
    SDW = 'sdw'
    FAOSTAT = 'faostat'

class Platform(str, Enum):
    """Enumeration of supported dissemination platforms.

    Attributes:
        STAT: .Stat
        MDM: Istat MDM
    """
    STAT = '.stat'
    MDM = 'mdm'

class DisseminationStepStatus(str, Enum):
    """Enumeration of possible dissemination step statuses.

    Attributes:
        SUCCESS: Step completed successfully
        FAILURE: Step failed
    """
    SUCCESS = 'success'
    FAILURE = 'failure'

class DisseminationAction(str, Enum):
    """Enumeration of possible dissemination actions.

    Attributes:
        INSERT: Insert new data
        APPEND: Append data
        REPLACE: Replace data
        DELETE: Delete data
    """
    INSERT = 'I'
    APPEND = 'A'
    REPLACE = 'R'
    DELETE = 'D'

# Type definitions
class LifecycleHistory(TypedDict):
    """Type definition for a lifecycle history entry."""
    modifiedOn: str
    modifiedBy: str
    description: str

class Lifecycle(TypedDict):
    """Type definition for a lifecycle object."""
    createdOn: str
    createdBy: str
    history: List[LifecycleHistory]

class Column(TypedDict):
    """Type definition for a table column."""
    name: str
    type: str
    description: str

class Structure(TypedDict):
    """Type definition for a table structure."""
    columns: List[Column]

class BaseDisseminatedTagTable(TypedDict):
    """Type definition for a base disseminated tag table."""
    id: str
    name: str
    description: str
    layer: TableLayer
    private: bool
    debug: bool = False
    type: TableType
    database: Optional[str]
    table: Optional[str]
    path: Optional[str]
    structure: Structure
    pinned_columns: List[str] = []

class DisseminatedTagTable(BaseDisseminatedTagTable):
    """Type definition for a disseminated tag table."""
    lifecycle: Lifecycle

class BaseDisseminatedTag(TypedDict):
    """Type definition for a base disseminated tag."""
    domain: str
    dataset: str
    name: str
    disseminatedTagid: str
    description: Optional[str]

class DisseminationStepInfo(TypedDict, total=False):
    """Type definition for dissemination step information."""
    endpoint: Optional[str]
    structure: Optional[str]
    structure_id: Optional[str]
    action: Optional[DisseminationAction]
    dataspace: Optional[str]

class BaseDisseminationStep(TypedDict):
    """Type definition for a base dissemination step."""
    target: DisseminationTarget
    platform: Optional[Platform]
    startedOn: str
    endedOn: str
    status: DisseminationStepStatus
    table: str
    info: Optional[DisseminationStepInfo]

class DisseminationStep(BaseDisseminationStep):
    """Type definition for a dissemination step."""
    user: str

class DisseminatedTagInfo(TypedDict):
    """Type definition for disseminated tag information."""
    disseminationSteps: List[DisseminationStep]
    tables: List[DisseminatedTagTable]

class DisseminatedTag(BaseDisseminatedTag):
    """Type definition for a disseminated tag."""
    createdOn: str
    disseminationSteps: List[DisseminationStep]
    tables: List[DisseminatedTagTable]

class PaginatedResponseLight(TypedDict):
    """Type definition for a paginated response with light disseminated tags."""
    items: List[BaseDisseminatedTag]
    next: Optional[str]

class PaginatedResponse(TypedDict):
    """Type definition for a paginated response with full disseminated tags."""
    items: List[DisseminatedTag]
    next: Optional[str]

class Tags:
    """Class for managing tag-related operations through the SWS API.

    This class provides methods for creating, retrieving, and managing tags
    and their dissemination processes.

    Args:
        sws_client (SwsApiClient): An instance of the SWS API client
        endpoint (str, optional): The API endpoint to use. Defaults to 'tag_api'
    """

    def __init__(self, sws_client: SwsApiClient, endpoint: str = 'tag_api') -> None:
        self.sws_client = sws_client
        self.endpoint = endpoint

    def get_tags(self, domain: Optional[str]=None, dataset: Optional[str]=None, **params) -> List[Dict]:
        """Retrieve tags based on optional domain and dataset filters.

        Args:
            domain (str, optional): Domain to filter tags
            dataset (str, optional): Dataset to filter tags
            **params: Additional query parameters

        Returns:
            List[Dict]: List of matching tags
        """
        url = f"/tags"
        _params = {**params}
        if domain:
            _params["domain"] = domain
        if dataset:
            _params["dataset"] = dataset

        response = self.sws_client.discoverable.get(self.endpoint, url, params=_params)
        return response
    
    def get_tag(self, tag_id: str) -> Dict:
        """Retrieve a specific tag by its ID.

        Args:
            tag_id (str): The unique identifier of the tag

        Returns:
            Dict: Tag information
        """
        url = f"/tags/{tag_id}"
        response = self.sws_client.discoverable.get(self.endpoint, url)
        return response

    def get_read_access_url(self, path: str, expiration: int) -> Dict:
        """Generate a temporary read access URL for a resource.

        Args:
            path (str): Path to the resource
            expiration (int): URL expiration time in seconds

        Returns:
            Dict: Dictionary containing the access URL
        """
        url = "/tags/dissemination/getReadAccessUrl"
        body = {"path": path, "expiration": expiration}
        response = self.sws_client.discoverable.post(self.endpoint, url, data=body)
        return response

    def get_all_disseminated_tags(self, limit: int, next_token: Optional[str] = None) -> PaginatedResponseLight:
        """Retrieve all disseminated tags with pagination.

        Args:
            limit (int): Maximum number of items to return
            next_token (str, optional): Token for next page of results

        Returns:
            PaginatedResponseLight: Paginated list of disseminated tags
        """
        url = "/tags/dissemination/all"
        params = {"limit": limit, "next": next_token}
        response = self.sws_client.discoverable.get(self.endpoint, url, params=params)
        return response

    def get_disseminated_tags_by_dataset(self, dataset: str, limit: int, next_token: Optional[str] = None) -> PaginatedResponse:
        """Retrieve disseminated tags for a specific dataset.

        Args:
            dataset (str): Dataset identifier
            limit (int): Maximum number of items to return
            next_token (str, optional): Token for next page of results

        Returns:
            PaginatedResponse: Paginated list of disseminated tags for the dataset
        """
        url = f"/tags/dissemination/dataset/{dataset}"
        params = {"limit": limit, "next": next_token}
        response = self.sws_client.discoverable.get(self.endpoint, url, params=params)
        return response

    def get_disseminated_tag(self, dataset: str, tag_id: str) -> Optional[DisseminatedTag]:
        """Retrieve a specific disseminated tag from a dataset.

        Args:
            dataset (str): Dataset identifier
            tag_id (str): Tag identifier

        Returns:
            Optional[DisseminatedTag]: The disseminated tag if found, None otherwise
        """
        url = f"/tags/dissemination/dataset/{dataset}/{tag_id}"
        response = self.sws_client.discoverable.get(self.endpoint, url)
        if not response:
            return None
        return response
    
    def create_disseminated_tag(self, dataset: str, name: str, tag_id: str, description: Optional[str] = None) -> DisseminatedTag:
        """Create a new disseminated tag.

        Args:
            dataset (str): Dataset identifier
            name (str): Tag name
            tag_id (str): Tag identifier
            description (str, optional): Tag description

        Returns:
            DisseminatedTag: The created disseminated tag
        """
        url = "/tags/dissemination"
        body = {
            "dataset": dataset,
            "name": name,
            "id": tag_id,
            "description": description
        }
        response = self.sws_client.discoverable.post(self.endpoint, url, data=body)
        return response

    def add_dissemination_table(self, dataset: str, tag_id: str, table: BaseDisseminatedTagTable) -> DisseminatedTag:
        """Add a table to a disseminated tag.

        Args:
            dataset (str): Dataset identifier
            tag_id (str): Tag identifier
            table (BaseDisseminatedTagTable): Table configuration

        Returns:
            DisseminatedTag: Updated disseminated tag
        """
        url = f"/tags/dissemination/dataset/{dataset}/{tag_id}/table"
        body = {"table": table}
        
        response = self.sws_client.discoverable.post(self.endpoint, url, data=body)
        return response

    def update_dissemination_table(self, dataset: str, tag_id: str, table: DisseminatedTagTable) -> DisseminatedTag:
        """Update an existing dissemination table.

        Args:
            dataset (str): Dataset identifier
            tag_id (str): Tag identifier
            table (DisseminatedTagTable): Updated table configuration

        Returns:
            DisseminatedTag: Updated disseminated tag
        """
        url = f"/tags/dissemination/dataset/{dataset}/{tag_id}/table"
        body = {"table": table}
        print(body)
        print(url)
        response = self.sws_client.discoverable.put(self.endpoint, url, data=body)
        return response

    def add_dissemination_step(self, dataset: str, tag_id: str, step: BaseDisseminationStep) -> DisseminatedTag:
        """Add a dissemination step to a tag.

        Args:
            dataset (str): Dataset identifier
            tag_id (str): Tag identifier
            step (BaseDisseminationStep): Step configuration

        Returns:
            DisseminatedTag: Updated disseminated tag
        """
        url = f"/tags/dissemination/dataset/{dataset}/{tag_id}/step"
        body = {"step": step}
        response = self.sws_client.discoverable.post(self.endpoint, url, data=body)
        return response
