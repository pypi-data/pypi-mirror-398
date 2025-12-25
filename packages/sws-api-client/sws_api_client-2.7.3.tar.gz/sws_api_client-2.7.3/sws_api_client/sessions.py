import datetime
from typing import Optional, Dict
import pandas as pd

from pydantic import BaseModel
from sws_api_client.datasets import Datasets, ValueFilter, MetadataFilter, FlagsFilter, DimensionsProps
from sws_api_client.sws_api_client import SwsApiClient
from sws_api_client.data_retrieval import DataRetrieval, GetDataResult

import logging

logger = logging.getLogger(__name__)

class SessionListItemModel(BaseModel):

    """Model representing a session list item.
    Attributes:
        description (str): Description of the session
        id (int): Unique identifier of the session
        creationDate (int): Creation date of the session in milliseconds since epoch
        updateDate (int): Update date of the session in milliseconds since epoch
        dataSetCode (str): Code of the dataset associated with the session
        dataSetName (str): Name of the dataset associated with the session
        domainCode (str): Code of the domain associated with the session
        domainName (str): Name of the domain associated with the session
        userName (str): Name of the user who created or updated the session
        userEmail (Optional[str]): Email of the user who created or updated the session
        dirty (bool): Indicates if the session is dirty
        willConflict (bool): Indicates if there will be a conflict with this session
    """
    description: str
    id: int
    creationDate: int
    updateDate: int
    dataSetCode: str
    dataSetName: str
    domainCode: str
    domainName: str
    userName: str
    userEmail: Optional[str]
    dirty: bool
    willConflict: bool

class SessionExtendedItemModel(BaseModel):

    """Model representing an extended session item.
    Attributes:
        session (SessionListItemModel): Basic session information
        dimensions (List[dict]): List of dimensions associated with the session
        flags (List[dict]): List of flags associated with the session
        pivoting (dict): Pivoting information for the session
    """
    session: dict
    dimensions: list[dict]
    flags: list[dict]
    pivoting: dict

    

class Sessions:
    """Class for managing sessions operations through the SWS API.

    This class provides methods for creating, updating, and deleting sessions

    Args:
        sws_client (SwsApiClient): An instance of the SWS API client
    """

    def __init__(self, sws_client: SwsApiClient) -> None:
        """Initialize the Datasets manager with SWS client."""
        self.sws_client = sws_client
        self.datasets = Datasets(sws_client)
        self.data_retrieval = DataRetrieval(sws_client)
    
    def get_all_sessions(self) -> dict:
        """Get all sessions.

        Returns:
            dict: Dictionary containing all sessions
        """
        url = f"/session"

        response = self.sws_client.discoverable.get('is_api', url, )
        # map response to an array of SessionListItemModel
        return [SessionListItemModel(**item) for item in response]
    
    def get_session(self, session_id: int) -> dict:
        """Get a session by its ID.

        Args:
            session_id (int): The identifier of the session

        Returns:
            dict: The requested session
        """
        url = f"/session/{session_id}"

        response = self.sws_client.discoverable.get('session_api', url)
        return SessionExtendedItemModel(**response)
    
    def create_session(self, dataset_id:str, dimensions:dict = None, name:str = None) -> SessionExtendedItemModel: 
        """Create a new session.

        Args:
            dataset (str): The identifier of the dataset
            dimensions (dict): The dimensions of the session. If None, an empty selection for all dimensions is created.
        """
        # convert dimenisons codes to internal ids
        dataset = self.datasets.get_dataset_info(dataset_id)

        if dimensions is None:
            ids = {d.id: [] for d in dataset.dataset.dimensions.dimensions}
        else:
            # Check if all dimensions are present
            required_dims = [d.id for d in dataset.dataset.dimensions.dimensions]
            missing_dims = [d for d in required_dims if d not in dimensions]
            if missing_dims:
                raise ValueError(f"Missing dimensions: {', '.join(missing_dims)}")
            ids = self.datasets.convert_codes_to_ids(codes=dimensions)
        # {"domainCode":"agriculture","dataSetCode":"aproduction","dimension2ids":{"geographicAreaM49":[144],"measuredElement":[216],"measuredItemCPC":[3],"timePointYears":[112]},"sessionDescription":"AGR 2025-04-14 09:38:11"}

        # create a session name as a first three letters of the dataset capitalized id plus the current date
        # and time in the format YYYY-MM-DD HH:MM:SS
        new_session_name = f"{dataset_id[:3].upper()} {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        url = f"/session"
        data = {
            "domainCode": dataset.dataset.domain.id,
            "dataSetCode": dataset.dataset.id,
            "dimension2ids": ids,
            "sessionDescription": name if name is not None else new_session_name
        }
        response = self.sws_client.discoverable.post('is_api', url, data=data)
        new_id = response.get('result').get('id')
        return new_id

    def create_with_data(
        self,
        dataset_id: str,
        data: pd.DataFrame,
        metadata: Optional[pd.DataFrame] = None,
        name: Optional[str] = None,
        force_s3: bool = False
    ) -> int:
        """Create a new session and import data into it.

        Args:
            dataset_id (str): The identifier of the dataset
            data (pd.DataFrame): The data to save
            metadata (Optional[pd.DataFrame]): The metadata to save
            name (Optional[str]): The name of the session
            force_s3 (bool): Whether to force S3 upload

        Returns:
            int: The ID of the created session
        """
        session_id = self.create_session(dataset_id, dimensions=None, name=name)
        
        self.datasets.save_data(
            dataset_id=dataset_id,
            data=data,
            metadata=metadata,
            session_id=session_id,
            force_s3=force_s3
        )
        
        return session_id
            
    def delete_sessions(self, ids:list[str]) -> None:
        """Delete one or more sessions.

        Args:
            ids (list[str]): The identifiers of the sessions
        """
        url = f"/session"
        data = {
            "ids": ids
        }
        result = self.sws_client.discoverable.delete('is_api', url, data=data)
        if result.get('success'):
            return True
        else:
            # log the error
            logger.error(f"Error deleting sessions: {result.get('error')}")
            return False

    def get_sql_queries(self, session_id: int, include_metadata: bool,
                       dimension: Optional[DimensionsProps] = None, value: Optional[ValueFilter] = None,
                       flag: Optional[FlagsFilter] = None, metadata: Optional[MetadataFilter] = None,
                       s3_export: Optional[bool] = None, show_username: Optional[bool] = None,
                       sort_by_id: Optional[bool] = None,
                       limit: Optional[int] = None, metadata_as_array: Optional[bool] = None) -> Dict:
        """Generate SQL queries for session.

        Generates SQL queries based on various filter parameters for a specific session.

        Args:
            session_id (int): The ID of the session
            include_metadata (bool): Whether to include metadata
            dimension (Optional[DimensionsProps]): Dimension filters with structure {dimensionId: filter_criteria}
            value (Optional[ValueFilter]): Value filtering with equal, less, higher, lessOrEqual, higherOrEqual
            flag (Optional[FlagsFilter]): Flags filtering with key-value pairs
            metadata (Optional[MetadataFilter]): Metadata filtering with startsWith, endsWith, contains, equal
            s3_export (Optional[bool]): S3 export flag
            show_username (Optional[bool]): Show username flag
            sort_by_id (Optional[bool]): Sort by ID flag
            limit (Optional[int]): Numeric limit for results
            metadata_as_array (Optional[bool]): Metadata as array flag

        Returns:
            Dict: Dictionary containing the query and optionally S3 information including 
                  originalQuery, bucketName, s3Key, queryHash, region

        Raises:
            Exception: If failed to generate SQL queries
        """
        url = f"/session/{session_id}/sql_queries"
        
        # Build the request body
        body = {
            
        }
        
        # Add optional parameters if provided
        if include_metadata is not None:
            body["includeMetadata"] = include_metadata
        if dimension is not None:
            body["dimension"] = dimension
            logger.debug(f"Added dimension filter to body: {dimension}")
        if value is not None:
            body["value"] = value.model_dump(exclude_none=True) if isinstance(value, BaseModel) else value
        if flag is not None:
            body["flag"] = flag
        if metadata is not None:
            body["metadata"] = metadata.model_dump(exclude_none=True) if isinstance(metadata, BaseModel) else metadata
        if s3_export is not None:
            body["s3Export"] = s3_export
        if show_username is not None:
            body["showUsername"] = show_username
        if sort_by_id is not None:
            body["sortById"] = sort_by_id
        if limit is not None:
            body["limit"] = limit
        if metadata_as_array is not None:
            body["metadataAsArray"] = metadata_as_array
        
        logger.debug(f"Final request body: {body}")
        logger.debug(f"Generating SQL queries for session {session_id}")
        
        try:
            result = self.sws_client.discoverable.post("session_api", url, data=body)
            logger.info(f"SQL queries generated successfully for session {session_id}")
            
            # Return the result as-is since the API already provides the correct format
            return result
        except Exception as e:
            logger.error(f"Failed to generate SQL queries for session {session_id}: {str(e)}")
            raise Exception(f"Failed to generate SQL queries: {str(e)}")

    def get_data(
        self,
        session_id: int,
        dataset_id: str,
        include_metadata: bool = False,
        dimension: Optional[DimensionsProps] = None,
        value: Optional[ValueFilter] = None,
        flag: Optional[FlagsFilter] = None,
        metadata: Optional[MetadataFilter] = None,
        s3_export: bool = False,
        show_username: bool = False,
        sort_by_id: bool = False,
        limit: Optional[int] = None,
        metadata_as_array: bool = False,
        cache_time: int = 0,
    ) -> GetDataResult:
        """Retrieve session data using the shared DataRetrieval fallback strategy.
        
        Args:
            session_id (int): The ID of the session.
            dataset_id (str): The ID of the dataset.
            include_metadata (bool): Whether to include metadata in the results. Defaults to False.
            dimension (Optional[DimensionsProps]): Dimension filters.
            value (Optional[ValueFilter]): Value filtering criteria.
            flag (Optional[FlagsFilter]): Flags filtering.
            metadata (Optional[MetadataFilter]): Metadata filtering criteria.
            s3_export (bool): If True, indicates that the result is intended for S3 export. Defaults to False.
            show_username (bool): If True, includes the username in the results. Defaults to False.
            sort_by_id (bool): If True, sorts the results by ID. Defaults to False.
            limit (Optional[int]): Maximum number of results to return.
            metadata_as_array (bool): If True, returns metadata as an array. Defaults to False.
            cache_time (int): Cache time in seconds. Defaults to 0.

        Returns:
            GetDataResult: The session data.
        """
        
        def sql_query_fn(force_s3: bool = False) -> Dict:
            return self.get_sql_queries(
                session_id=session_id,
                include_metadata=include_metadata,
                dimension=dimension,
                value=value,
                flag=flag,
                metadata=metadata,
                s3_export=s3_export or force_s3,
                show_username=show_username,
                sort_by_id=sort_by_id,
                limit=limit,
                metadata_as_array=metadata_as_array,
            )

        plugin_params = {
            "dataset_id": dataset_id,
            "session_id": str(session_id),
            "includeMetadata": include_metadata,
            "printPresignedUrl": True,
            "s3Export": True
        }
        
        if dimension is not None:
            plugin_params["dimension"] = dimension
        if value is not None:
            plugin_params["value"] = value.model_dump(exclude_none=True) if isinstance(value, BaseModel) else value
        if flag is not None:
            plugin_params["flag"] = flag
        if metadata is not None:
            plugin_params["metadata"] = metadata.model_dump(exclude_none=True) if isinstance(metadata, BaseModel) else metadata
        if limit is not None:
            plugin_params["limit"] = limit
        if show_username is not None:
            plugin_params["showUsername"] = show_username
        if sort_by_id is not None:
            plugin_params["sortById"] = sort_by_id
        if metadata_as_array is not None:
            plugin_params["metadataAsArray"] = metadata_as_array

        return self.data_retrieval.get_data_generic(
            sql_query_fn=sql_query_fn,
            entity_id=str(session_id),
            entity_type="session",
            plugin_name="get_session_data",
            plugin_params=plugin_params,
            s3_export=s3_export,
            cache_time=cache_time,
        )

    

        

