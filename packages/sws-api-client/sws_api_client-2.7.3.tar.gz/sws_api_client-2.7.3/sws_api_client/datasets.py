import logging
import warnings
from time import sleep
import os
import zipfile
import tempfile
import csv
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Union, Any, Literal
from sws_api_client.codelist import Codelists
from sws_api_client.flaglist import Flaglists
from sws_api_client.generic_models import Code, Multilanguage
from sws_api_client.sws_api_client import SwsApiClient
from sws_api_client.s3 import S3
from sws_api_client.data_retrieval import DataRetrieval, GetDataResult
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed


warnings.filterwarnings(
    "ignore",
    message='Field name "schema" in "DatasetBinding" shadows an attribute in parent "BaseModel"',
)

logger = logging.getLogger(__name__)

class Lifecycle(BaseModel):
    state: str
    type: str
    previousState: Optional[str] = None
    created: int
    lastModified: Optional[int] = None
    lastModifiedBy: Optional[str] = None

class Domain(BaseModel):
    id: str
    label: Multilanguage
    description: Dict

class Binding(BaseModel):
    joinColumn: Optional[str] = None

class Dimension(BaseModel):
    id: str
    label: Multilanguage
    description: Dict
    sdmxName: Optional[str] = None
    codelist: str
    roots: List[str]
    binding: Optional[Binding] = None
    checkValidityPeriod: bool
    formulas: List
    type: str

class Dimensions(BaseModel):
    dimensions: List[Dimension]

class PivotingGrouped(BaseModel):
    id: str
    ascending: bool

class Pivoting(BaseModel):
    grouped: List[PivotingGrouped]
    row: PivotingGrouped
    cols: PivotingGrouped

class DatasetBinding(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    observationTable: Optional[str] = None
    coordinateTable: Optional[str] = None
    sessionObservationTable: Optional[str] = None
    metadataTable: Optional[str] = None
    metadataElementTable:  Optional[str] = None
    sessionMetadataTable: Optional[str] = None
    sessionMetadataElementTable: Optional[str] = None
    validationTable: Optional[str] = None
    sessionValidationTable: Optional[str] = None
    tagObservationTable: Optional[str] = None
    tags: Optional[List] = None
    schema: Optional[str] = None

class Dataset(BaseModel):
    id: str
    label: Multilanguage
    description: Dict
    sdmxName: Optional[str] = None
    lifecycle: Lifecycle
    domain: Domain
    dimensions: Dimensions
    flags: Dict
    rules: Dict
    pivoting: Pivoting
    pluginbar: Dict
    showEmptyRows: bool
    showRealCalc: bool
    useApproveCycle: bool
    binding: Optional[DatasetBinding] = None

class Fingerprint(BaseModel):
    empty: bool
    sessions: int
    queries: int
    tags: int
    computationTags: int
    modules: int
class DataModel(BaseModel):
    dataset: Dataset
    fingerprint: Optional[Fingerprint] = None

class MappedCode(BaseModel):
    code: Code
    include: bool

class ValueFilter(BaseModel):
    equal: Optional[Union[int, float]] = None
    less: Optional[Union[int, float]] = None
    higher: Optional[Union[int, float]] = None
    lessOrEqual: Optional[Union[int, float]] = None
    higherOrEqual: Optional[Union[int, float]] = None
    null: Optional[bool] = None
    notNull: Optional[bool] = None

class MetadataFilter(BaseModel):
    startsWith: Optional[str] = None
    endsWith: Optional[str] = None
    contains: Optional[str] = None
    equal: Optional[str] = None

FlagsFilter = Dict[str, str]
DimensionsProps = Dict[str, List[str]]

class Datasets:

    def __init__(self, sws_client: SwsApiClient) -> None:
        self.sws_client = sws_client
        self.codelists = Codelists(sws_client)
        self.flaglists = Flaglists(sws_client)
        self.s3_client = S3(sws_client)
        self.data_retrieval = DataRetrieval(sws_client)
        self.cache = {}

    def get_all(self) -> List[dict]:
        """Retrieve all datasets.

        Returns:
            List[Dataset]: List of all datasets
        """
        url = "/admin/dataset"
        response = self.sws_client.discoverable.get('is_api', url)
        return response

    def get_metadata_combinations(self) -> List[Dict]:
        """Retrieve valid metadata combinations.

        Returns:
            List[Dict]: List of valid metadata combinations
        """
        url = "/dataset/metadata/combinations"
        return self.sws_client.discoverable.get('session_api', url)

    def scan(self, dataset_id: str, body: dict) -> dict:
        """Scan a dataset using the session_api endpoint.

        Args:
            dataset_id (str): The dataset identifier.
            body (dict): The scan request body.

        Returns:
            dict: The scan response.
        """
        url = f"/dataset/{dataset_id}/scan"
        response = self.sws_client.discoverable.put('session_api', url, data=body, options={"json_body": True})
        return response

    def get_dataset_export_details(self, dataset_id: str) -> dict:

        url = f"/dataset/{dataset_id}/info"
        params = {"extended": "true"}

        response = self.sws_client.discoverable.get('session_api', url, params=params)

        return response
    
    def get_dataset_info(self, dataset_id: str, use_cache: Optional[bool] = None) -> DataModel:
        
        if use_cache is None:
            use_cache = self.sws_client.object_cache

        if use_cache and dataset_id in self.cache:
            return self.cache[dataset_id]

        url = f"/admin/dataset/{dataset_id}"

        response = self.sws_client.discoverable.get('is_api', url)
        result = DataModel(**response)
        
        if use_cache:
            self.cache[dataset_id] = result
            
        return result

    def create_dataset(self, dataset: Dataset) -> DataModel:

        url = "/admin/dataset"

        response = self.sws_client.discoverable.post('is_api', url, data=dataset.model_dump())

        return response
    
    def clone_dataset(self, dataset_id: str, new_id: str) -> DataModel:

        dataset = self.get_dataset_info(dataset_id)
        dataset.dataset.id = new_id
        new_dataset = self.create_dataset(dataset.dataset)
        return new_dataset
    
    def get_job_status(self, jobId: str) -> dict:

        url = f"/job/status/{jobId}"

        response = self.sws_client.discoverable.get('is_api', url)
        return response

    def import_data(
        self,
        dataset_id: str,
        file_path,
        sessionId = None,
        zip=False,
        data: bool = True,
        metadata: bool = False,
        separator: str = ",",
        quote: str = "\"",
        isS3: bool = False
    ) -> dict:
        """Import data into a dataset, optionally including metadata and custom CSV settings."""

        if isS3:
            return self.import_data_from_s3(
                dataset_id,
                file_path,
                sessionId,
                data=data,
                metadata=metadata,
                separator=separator,
                quote=quote
            )

        return self.import_data_chunk(
            dataset_id,
            file_path,
            sessionId,
            data=data,
            metadata=metadata,
            separator=separator,
            quote=quote
        )

    def import_data_from_s3(
        self,
        dataset_id: str,
        file_path: str,
        sessionId: Optional[int] = None,
        data: Optional[bool] = True,
        metadata: Optional[bool] = False,
        separator: Optional[str] = ",",
        quote: Optional[str] = "\""
    ) -> dict:

        is_zip = zipfile.is_zipfile(file_path)
        mediaType = 'application/zip' if is_zip else 'text/csv'

        s3_key = self.s3_client.upload_file_to_s3(file_path)

        url = "/observations/import-v2"

        dataset_info = self.get_dataset_info(dataset_id)

        scope: List[str] = ["DATA"]

        if data and metadata:
            scope = ["DATA", "METADATA"]

        execution = "ASYNC"
        if sessionId is not None:
            execution = "SYNC"


        dataPayload = {
            "domain": dataset_info.dataset.domain.id,
            "dataset": dataset_id,
            "sessionId": -1 if sessionId is None else sessionId,
            "format": "CSV",
            "scope": scope,
            "execution": execution,
            "fieldSeparator": separator,
            "quoteOptions": quote,
            "filedownload": execution,
            "lineSeparator": "\n",
            "headers": "CODE",
            "structure": "NORMALIZED",
            "s3Key": s3_key,
            "mediaType": mediaType
        }

        response = self.sws_client.discoverable.post('is_api', url, data=dataPayload)
        logger.debug(f"Import data from s3 response: {response}")

        job_id = response['result']
        return self.get_job_result(job_id, sleepTime=5)

    def save_data(
        self,
        dataset_id: str,
        data: pd.DataFrame,
        metadata: Optional[pd.DataFrame] = None,
        session_id: Optional[int] = None,
        use_cache: Optional[bool] = None,
        force_s3: bool = False
    ) -> dict:
        """Save data to a dataset.

        Args:
            dataset_id (str): The ID of the dataset.
            data (pd.DataFrame): The data to save.
                The DataFrame must contain:
                - All dimension columns defined in the dataset (e.g., 'geographicAreaM49', 'measuredItemCPC', 'timePointYears').
                - A 'Value' column containing the numerical values.
                - Flag columns (e.g., 'Status', 'Method') corresponding to the dataset's flag definitions.
            metadata (Optional[pd.DataFrame]): The metadata to save.
                The DataFrame must contain:
                - All dimension columns (matching the data rows they describe).
                - 'Metadata Type': The code of the metadata type (e.g., 'COMPUTATION_INFO').
                - 'Metadata Element Type': The code of the metadata element type (e.g., 'SUMMARY').
                - 'Value': The metadata content/value.
                - 'Language': (Optional) The language code (e.g., 'en') if applicable.
            session_id (Optional[int]): The session ID. Defaults to None.
            use_cache (Optional[bool]): Whether to use client-side cache for validation. Defaults to None (uses global config).

        Returns:
            dict: The result of the import operation.
        """
        # 1. Get Dataset Info
        info = self.get_dataset_info(dataset_id, use_cache=use_cache)
        dimensions = [d.id for d in info.dataset.dimensions.dimensions]
        
        # 2. Validate and Sort Data
        data = data.copy()

        # Ensure all dimension columns are present
        missing_dims = [d for d in dimensions if d not in data.columns]
        if missing_dims:
            raise ValueError(f"Data is missing dimension columns: {missing_dims}")

        # Clean dimension columns (ensure string type and remove .0 suffix)
        for dim_id in dimensions:
            if dim_id in data.columns:
                data[dim_id] = data[dim_id].astype(str).apply(lambda x: x[:-2] if x.endswith('.0') else x)

        # Validate dimensions (codelists)
        try:
            dimension_codes_map = self.get_dataset_dimension_codes(dataset_id, use_cache=use_cache)
            for dim_id, codes in dimension_codes_map.items():
                if dim_id in data.columns:
                    valid_codes = set(str(c.id) for c in codes)
                    unique_values = data[dim_id].unique()
                    # Convert to string for comparison as codes are strings
                    invalid_codes = [v for v in unique_values if str(v) not in valid_codes]
                    
                    if invalid_codes:
                        raise ValueError(f"Invalid codes found in dimension column '{dim_id}': {invalid_codes}. Valid codes are: {valid_codes}")
        except Exception as e:
            logger.warning(f"Could not validate dimension codes: {e}")

        # Validate flags
        flags_config = info.dataset.flags.get('flags', [])
        flag_ids = []
        for flag_def in flags_config:
            flag_id = flag_def['id']
            flag_ids.append(flag_id)
            flaglist_id = flag_def['flaglist']
            
            if flag_id not in data.columns:
                raise ValueError(f"Data is missing flag column: {flag_id}")
            
            # Get valid codes for this flaglist
            try:
                flaglist_obj = self.flaglists.get_flaglist(flaglist_id, use_cache=use_cache)
                valid_codes = set(f.value for f in flaglist_obj.values)
                
                # Check if all values in the flag column are valid codes (ignoring NaN/None if allowed)
                # Assuming empty flags are allowed (represented as empty string or NaN)
                unique_values = data[flag_id].dropna().unique()
                # Strip whitespace from values for validation
                invalid_codes = [v for v in unique_values if str(v).strip() != '' and str(v).strip() not in valid_codes]
                
                if invalid_codes:
                    raise ValueError(f"Invalid codes found in flag column '{flag_id}': {invalid_codes}. Valid codes are: {valid_codes}")
            except Exception as e:
                logger.warning(f"Could not validate codes for flaglist {flaglist_id}: {e}")

        # Filter columns to keep only dimensions, flags and Value
        value_col = 'Value' if 'Value' in data.columns else 'value'
        if value_col not in data.columns:
             raise ValueError("Data is missing 'Value' column")
        
        # Rename value column to 'Value' if needed
        if value_col != 'Value':
            data = data.rename(columns={value_col: 'Value'})
            value_col = 'Value'

        # Ensure correct column order: Dimensions, Value, Flags
        cols_to_keep = dimensions + [value_col] + flag_ids
        data = data[cols_to_keep]

        # Check for duplicates based on dimensions
        duplicates = data[data.duplicated(subset=dimensions, keep=False)]
        if not duplicates.empty:
            # Sort to group duplicates together for the error message
            duplicates = duplicates.sort_values(by=dimensions)
            
            # Create a readable error message with a sample
            sample_str = duplicates.head(10).to_string()
            
            msg = (
                f"Duplicate entries found for the same dimension keys. "
                f"The dataset cannot contain multiple rows for the same combination of dimensions.\n"
                f"Total duplicate rows: {len(duplicates)}\n"
                f"Sample of duplicates:\n{sample_str}"
            )
            logger.error(msg)
            raise ValueError(msg)

        # Sort data by dimensions
        data = data.sort_values(by=dimensions)
        
        # 3. Validate and Sort Metadata
        if metadata is not None:
            # Ensure all dimension columns are present in metadata
            missing_meta_dims = [d for d in dimensions if d not in metadata.columns]
            if missing_meta_dims:
                raise ValueError(f"Metadata is missing dimension columns: {missing_meta_dims}")

            # Get valid combinations
            valid_combinations = self.get_metadata_combinations()
            valid_comb_set = set((c['metadata_type'], c['metadata_element_type']) for c in valid_combinations)
            
            # Check combinations
            required_meta_cols = ['Metadata Type', 'Metadata Element Type']
            missing_req_cols = [c for c in required_meta_cols if c not in metadata.columns]
            if missing_req_cols:
                raise ValueError(f"Metadata is missing required columns: {missing_req_cols}")

            # Add Metadata Id column required by SWS
            metadata['Metadata Id'] = 1

            for index, row in metadata.iterrows():
                if (row['Metadata Type'], row['Metadata Element Type']) not in valid_comb_set:
                    raise ValueError(f"Invalid metadata combination at row {index}: {row['Metadata Type']}, {row['Metadata Element Type']}")
            
            # Check for duplicates in metadata
            meta_keys = dimensions + ['Metadata Type', 'Metadata Element Type', 'Value']
            meta_duplicates = metadata[metadata.duplicated(subset=meta_keys, keep=False)]
            if not meta_duplicates.empty:
                # Sort to group duplicates together
                meta_duplicates = meta_duplicates.sort_values(by=meta_keys)
                
                # Create a readable error message with a sample
                sample_str = meta_duplicates.head(10).to_string()
                
                msg = (
                    f"Duplicate entries found in metadata for the same key combinations.\n"
                    f"Each metadata entry must be unique for a given set of Dimensions + Metadata Type + Metadata Element Type + Value.\n"
                    f"Total duplicate rows: {len(meta_duplicates)}\n"
                    f"Sample of duplicates:\n{sample_str}"
                )
                logger.error(msg)
                raise ValueError(msg)

            # Sort metadata
            metadata = metadata.sort_values(by=dimensions + ['Metadata Type', 'Metadata Element Type'])

            # Ensure correct column order for metadata: Dimensions, Metadata Type, Metadata Id, Metadata Element Type, Language, Value
            # Based on error analysis, 'Metadata Id' (Long) seems to be expected at the 2nd metadata column position.
            meta_cols_order = dimensions + ['Metadata Type', 'Metadata Id', 'Metadata Element Type', 'Language', 'Value']
            # Check if all columns exist
            missing_cols = [c for c in meta_cols_order if c not in metadata.columns]
            if missing_cols:
                 # If Language is missing (optional in input), add it as empty or default?
                 # The docstring says Language is optional. If missing, maybe we should add it as empty string?
                 if 'Language' in missing_cols:
                     metadata['Language'] = ''
                     missing_cols.remove('Language')
                 
                 if missing_cols:
                    raise ValueError(f"Metadata dataframe is missing columns for final output: {missing_cols}")
            
            metadata = metadata[meta_cols_order]

        # 4. Create CSVs and Zip
        with tempfile.TemporaryDirectory() as tmpdirname:
            data_path = os.path.join(tmpdirname, 'data.csv')
            data.to_csv(data_path, index=False, quoting=csv.QUOTE_ALL)
            
            file_to_upload = data_path
            
            if metadata is not None:
                metadata_path = os.path.join(tmpdirname, 'metadata.csv')
                metadata.to_csv(metadata_path, index=False, quoting=csv.QUOTE_ALL)
                
                zip_path = os.path.join(tmpdirname, 'archive.zip')
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    zipf.write(data_path, 'data.csv')
                    zipf.write(metadata_path, 'metadata.csv')
                
                file_to_upload = zip_path
            
            logger.info(f"Uploading file from: {file_to_upload}")

            # 5. Upload
            # Check file size. If > 5MB, use S3 upload.
            file_size = os.path.getsize(file_to_upload)
            if force_s3 or file_size > 5 * 1024 * 1024:  # 5MB
                return self.import_data_from_s3(
                    dataset_id=dataset_id,
                    file_path=file_to_upload,
                    sessionId=session_id,
                    data=True,
                    metadata=(metadata is not None)
                )
            else:
                return self.import_data_chunk(
                    dataset_id=dataset_id,
                    file_path=file_to_upload,
                    sessionId=session_id,
                    data=True,
                    metadata=(metadata is not None)
                )
        

    def get_dataset_dimension_codes(self, dataset_id: str, use_cache: Optional[bool] = None) -> Dict[str, List[Code]]:
        dataset_info = self.get_dataset_info(dataset_id, use_cache=use_cache)
        dimensions = dataset_info.dataset.dimensions.dimensions

        # Fetch codelist codes for each dimension and use the dimension name for the CSV header
        dimensions_map:Dict[str, Dict[str, Dict[str, MappedCode]]] = {}
        for dimension in dimensions:
            logger.debug(f"Fetching codelist for dimension: {dimension}")
            codelist = self.codelists.get_codelist(dimension.codelist, use_cache=use_cache)
            # filter out codes that have more than 0 children
            
            dimensions_map[dimension.id] = {}
            for code in codelist.codes:
                dimensions_map[dimension.id][code.id] = {"code":code, "include":False}
        
        
        def include_children(code:Code, dimension_id:str):
            if dimensions_map[dimension_id][code.id]["include"] is False:
                dimensions_map[dimension_id][code.id]["include"] = True
            if len(code.children) > 0:
                for child in code.children:
                    if dimensions_map[dimension_id][child]["include"] is False:
                        dimensions_map[dimension_id][child]["include"] = True
                        include_children(dimensions_map[dimension_id][child]["code"], dimension_id)

        dimensions_codes = {}
        for dimension in dimensions:
            dimensions_codes[dimension.id] = []
            if len(dimension.roots) > 0:
                for root in dimension.roots:
                    # Check if root exists in the dimension's codelist
                    if root in dimensions_map[dimension.id]:
                        include_children(dimensions_map[dimension.id][root]["code"], dimension.id)
                    else:
                        logger.warning(f"Root code '{root}' not found in dimension '{dimension.id}' codelist")
                for code in dimensions_map[dimension.id]:
                    if dimensions_map[dimension.id][code]["include"]:
                        dimensions_codes[dimension.id].append(dimensions_map[dimension.id][code]["code"])
            else:
                for code in dimensions_map[dimension.id]:
                    dimensions_codes[dimension.id].append(dimensions_map[dimension.id][code]["code"])
        return dimensions_codes

    def convert_codes_to_ids(self, codes: Dict[str, List[str]]) -> Dict[str, List[int]]:
        """Convert codes to ids.

        Args:
            codes (Dict[str, List[str]]): A dictionary of codes to convert.
                Example: {"geographicAreaM49": ["12", "24"], "measuredElement": ["5510"]}

        Returns:
            Dict[str, List[int]]: A dictionary of converted ids.
        """
        payload = {"codelists": codes}
        logger.debug(f"Payload: \n{payload}")

        response = self.sws_client.discoverable.post(
            "session_api",
            "codelist/convert_codes_to_ids",
            data=payload
        )
        
        if response is not None:
            return response
        else:
            logger.error(f"Error in converting codes to ids: {response}")
            return None

    def get_sql_queries(self, dataset_id: str, include_history: bool, include_metadata: bool,
                       dimension: Optional[DimensionsProps] = None, value: Optional[ValueFilter] = None,
                       flag: Optional[FlagsFilter] = None, metadata: Optional[MetadataFilter] = None,
                       s3_export: Optional[bool] = None, show_username: Optional[bool] = None,
                       sort_by_id: Optional[bool] = None, tags: Optional[List[int]] = None,
                       limit: Optional[int] = None, metadata_as_array: Optional[bool] = None) -> Dict:
        """Generate SQL queries for dataset.

        Generates SQL queries based on various filter parameters for a specific dataset.

        Args:
            dataset_id (str): The ID of the dataset.
            include_history (bool): Whether to include history in the results.
            include_metadata (bool): Whether to include metadata in the results.
            dimension (Optional[DimensionsProps]): Dimension filters. A dictionary where keys are dimension IDs and values are lists of codes to filter by.
                Example: {"geographicAreaM49": ["12", "24"], "measuredElement": ["5510"]}
            value (Optional[ValueFilter]): Value filtering criteria.
                Example: ValueFilter(higher=100, less=1000)
            flag (Optional[FlagsFilter]): Flags filtering. A dictionary where keys are flag IDs and values are flag values.
                Example: {"flagObservationStatus": "E"}
            metadata (Optional[MetadataFilter]): Metadata filtering criteria.
                Example: MetadataFilter(contains="official")
            s3_export (Optional[bool]): If True, indicates that the result is intended for S3 export.
            show_username (Optional[bool]): If True, includes the username in the results.
            sort_by_id (Optional[bool]): If True, sorts the results by ID.
            tags (Optional[List[int]]): List of tag IDs to filter by.
            limit (Optional[int]): Maximum number of results to return.
            metadata_as_array (Optional[bool]): If True, returns metadata as an array.

        Returns:
            Dict: Dictionary containing the query and optionally S3 information including 
                  originalQuery, bucketName, s3Key, queryHash, region.

        Raises:
            Exception: If failed to generate SQL queries.
        """
        url = f"/dataset/{dataset_id}/sql_queries"
        
        # Build the request body
        body = {
            "includeHistory": include_history,
            "includeMetadata": include_metadata
        }
        
        # Add optional parameters if provided
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
        if tags is not None:
            body["tags"] = tags
        if limit is not None:
            body["limit"] = limit
        if metadata_as_array is not None:
            body["metadataAsArray"] = metadata_as_array
        
        logger.debug(f"Final request body: {body}")
        logger.debug(f"Generating SQL queries for dataset {dataset_id}")
        
        try:
            result = self.sws_client.discoverable.post("session_api", url, data=body)
            logger.info(f"SQL queries generated successfully for dataset {dataset_id}")
            
            # Return the result as-is since the API already provides the correct format
            return result
        except Exception as e:
            logger.error(f"Failed to generate SQL queries for dataset {dataset_id}: {str(e)}")
            raise Exception(f"Failed to generate SQL queries: {str(e)}")

    def import_data_chunk(
        self,
        dataset_id: str,
        file_path: str,
        sessionId: Optional[int] = None,
        data: Optional[bool] = True,
        metadata: Optional[bool] = False,
        separator: Optional[str] = ",",
        quote: Optional[str] = "\""
    ) -> dict:
        """Helper function to import a single data chunk, zipping files over 10MB automatically."""

        is_zip = zipfile.is_zipfile(file_path)
        zip_file_path = None
        if not is_zip:
            # Check file size and zip if greater than 10MB
            if os.path.getsize(file_path) > 10 * 1024 * 1024:  # 10MB in bytes
                zip_file_path = f"{file_path}.zip"
                with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(file_path, arcname=os.path.basename(file_path))
                file_path = zip_file_path  # Use zipped file for upload
                is_zip = True
            else:
                is_zip = False

        url = "/observations/import"
        dataset_info = self.get_dataset_info(dataset_id)

        scope: Union[str, List[str]] = "DATA"
        if data and metadata:
            scope = ["DATA", "METADATA"]
        elif metadata:
            scope = "METADATA"

        execution = "ASYNC"
        if sessionId is not None:
            execution = "SYNC"

        dataPayload = {
            "domain": dataset_info.dataset.domain.id,
            "dataset": dataset_id,
            "sessionId": -1 if sessionId is None else f"{sessionId}",
            "format": "CSV",
            "scope": scope,
            "execution": execution,
            "fieldSeparator": separator,
            "quoteOptions": quote,
            "filedownload": "ASYNC",
            "lineSeparator": "\n",
            "headers": "CODE",
            "structure": "NORMALIZED",
        }

        file_name = os.path.basename(file_path)
        files = {"file": (file_name, open(file_path, 'rb'), "application/zip" if is_zip else "text/csv")}
        response = self.sws_client.discoverable.multipartpost('is_api', url, data=dataPayload, files=files)
        logger.debug(f"Import data response for chunk: {response}")

        # Clean up the zip file if it was created
        if zip_file_path:
            os.remove(zip_file_path)

        job_id = response['result']
        return self.get_job_result(job_id)

    def get_job_result(self, job_id: str, sleepTime: int = 5) -> dict:
        """Check job status until it's completed."""
        while True:
            logger.debug(f"Checking job status for job ID {job_id}")
            job_status = self.get_job_status(job_id)
            if job_status['result']:
                return job_status

            if not job_status['success']:
                return job_status

            sleep(sleepTime)

    def chunk_csv_file(self, file_path: str, chunk_size: int) -> List[str]:
        """Splits the CSV file into smaller chunks while preserving leading zeros for all columns except 'value'."""
        temp_files = []
        
        # Load the data in chunks and process each chunk
        for i, chunk in enumerate(pd.read_csv(file_path, chunksize=chunk_size, dtype=str)):
            # Convert 'value' column to numeric, allowing other columns to stay as strings to preserve leading zeros
            if 'value' in chunk.columns:
                chunk['value'] = pd.to_numeric(chunk['value'], errors='coerce')
            
            chunk_file = f"{file_path}_chunk_{i}.csv"
            chunk.to_csv(chunk_file, index=False, quoting=1)  # quoting=1 ensures quotes around strings to preserve zeros
            temp_files.append(chunk_file)
        
        return temp_files

    def import_data_concurrent(
        self,
        dataset_id: str,
        file_path: str,
        sessionId: Optional[int] = None,
        data: bool = True,
        metadata: bool = False,
        separator: str = ",",
        quote: str = "\"",
        chunk_size: int = 10000,
        max_workers: int = 5
    ) -> None:
        """Splits the CSV and imports chunks concurrently with limited workers, showing progress in the logs."""
        
        # Step 1: Split the file into chunks
        chunk_files = self.chunk_csv_file(file_path, chunk_size)
        total_chunks = len(chunk_files)  # Total number of chunks for progress tracking
        completed_chunks = 0  # Initialize counter for completed chunks
        
        logger.info(f"Importing chunks: started")
        # Step 2: Use ThreadPoolExecutor to manage parallel imports
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_chunk = {
                executor.submit(
                    self.import_data_chunk,
                    dataset_id,
                    chunk_file,
                    sessionId,
                    data,
                    metadata,
                    separator,
                    quote
                ): chunk_file for chunk_file in chunk_files
            }
            results = []

            # Step 3: Collect and manage job statuses
            for future in as_completed(future_to_chunk):
                chunk_file = future_to_chunk[future]
                try:
                    chunk_result = future.result()
                    result = {"result": chunk_result, "chunk_file": chunk_file}
                    results.append(result)
                    logger.debug(f"Chunk {chunk_file} ended successfully")
                except Exception as exc:
                    logger.error(f"Chunk {chunk_file} generated an exception: {exc}")
                finally:
                    # Update and log progress
                    completed_chunks += 1
                    logger.info(f"Importing chunks: {completed_chunks}/{total_chunks} cmopleted")
        
        # Step 4: Wait for all jobs to complete and clean up temporary files
        for result in results:
            success = result.get('result')
            if not success:
                logger.error(f"Chunk {result.get('chunk_file')} failed to import.")
            else:
                logger.debug(f"Chunk {result.get('chunk_file')} completed successfully.")
                os.remove(result.get('chunk_file'))

        logger.info("Importing chunks: completed")

    def get_data(
        self,
        dataset_id: str,
        include_history: bool = False,
        include_metadata: bool = False,
        dimension: Optional[DimensionsProps] = None,
        value: Optional[ValueFilter] = None,
        flag: Optional[FlagsFilter] = None,
        metadata: Optional[MetadataFilter] = None,
        s3_export: bool = False,
        show_username: bool = False,
        sort_by_id: bool = False,
        tags: Optional[List[int]] = None,
        limit: Optional[int] = None,
        metadata_as_array: bool = False,
        cache_time: int = 0,
        plugin_name: str = "get_data",
    ) -> GetDataResult:
        """Retrieve dataset data using the shared DataRetrieval fallback strategy.

        Args:
            dataset_id (str): The ID of the dataset.
            include_history (bool): Whether to include history in the results. Defaults to False.
            include_metadata (bool): Whether to include metadata in the results. Defaults to False.
            dimension (Optional[DimensionsProps]): Dimension filters. A dictionary where keys are dimension IDs and values are lists of codes to filter by.
                Example: {"geographicAreaM49": ["12", "24"], "measuredElement": ["5510"]}
            value (Optional[ValueFilter]): Value filtering criteria.
                Example: ValueFilter(higher=100, less=1000)
            flag (Optional[FlagsFilter]): Flags filtering. A dictionary where keys are flag IDs and values are flag values.
                Example: {"flagObservationStatus": "E"}
            metadata (Optional[MetadataFilter]): Metadata filtering criteria.
                Example: MetadataFilter(contains="official")
            s3_export (bool): If True, indicates that the result is intended for S3 export. Defaults to False.
            show_username (bool): If True, includes the username in the results. Defaults to False.
            sort_by_id (bool): If True, sorts the results by ID. Defaults to False.
            tags (Optional[List[int]]): List of tag IDs to filter by.
            limit (Optional[int]): Maximum number of results to return.
            metadata_as_array (bool): If True, returns metadata as an array. Defaults to False.
            cache_time (int): Cache time in seconds. Defaults to 0.
            plugin_name (str): Name of the plugin invoking this method. Defaults to "get_data".

        Returns:
            GetDataResult: The dataset data.
        """

        def sql_query_fn(force_s3: bool = False) -> Dict:
            return self.get_sql_queries(
                dataset_id=dataset_id,
                include_history=include_history,
                include_metadata=include_metadata,
                dimension=dimension,
                value=value,
                flag=flag,
                metadata=metadata,
                s3_export=s3_export or force_s3,
                show_username=show_username,
                sort_by_id=sort_by_id,
                tags=tags,
                limit=limit,
                metadata_as_array=metadata_as_array,
            )

        plugin_params: Dict[str, Any] = {
            "dataset_id": dataset_id,
            "includeHistory": include_history,
            "includeMetadata": include_metadata,
        }
        if dimension is not None:
            plugin_params["dimension"] = dimension
        if value is not None:
            plugin_params["value"] = value.model_dump(exclude_none=True) if isinstance(value, BaseModel) else value
        if flag is not None:
            plugin_params["flag"] = flag
        if metadata is not None:
            plugin_params["metadata"] = metadata.model_dump(exclude_none=True) if isinstance(metadata, BaseModel) else metadata
        if tags is not None:
            plugin_params["tags"] = tags
        if limit is not None:
            plugin_params["limit"] = limit

        return self.data_retrieval.get_data_generic(
            sql_query_fn=sql_query_fn,
            entity_id=dataset_id,
            entity_type="dataset",
            plugin_name=plugin_name,
            plugin_params=plugin_params,
            s3_export=s3_export,
            cache_time=cache_time,
        )



