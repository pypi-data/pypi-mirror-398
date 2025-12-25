import logging
from time import time
from typing import Callable, Dict, Any, Optional, TypedDict

import pandas as pd
import requests

from sws_api_client.db import DB
from sws_api_client.sws_api_client import SwsApiClient
from sws_api_client.tasks import TaskManager, PluginPayload

logger = logging.getLogger(__name__)


class GetDataMetadata(TypedDict):
    retrieval_method: Optional[str]
    task_id: Optional[str]
    url: Optional[str]
    execution_time_seconds: Optional[float]
    error: Optional[str]


class GetDataResult(TypedDict):
    data: Optional[pd.DataFrame]
    metadata: GetDataMetadata
    success: bool


class DataRetrieval:
    """Generic utility for data retrieval with fallback strategy.

    Mirrors the R client pattern used by datasets/sessions/datatables:
    1. Get SQL query from API
    2. Check cache if requested
    3. Try database execution
    4. Fallback to S3 download
    5. Fallback to plugin task
    6. Return query only as last resort
    """

    def __init__(self, sws_client: SwsApiClient):
        self.sws_client = sws_client

    def get_data_generic(
        self,
        sql_query_fn: Callable[..., Dict[str, Any]],
        entity_id: str,
        entity_type: str,
        plugin_name: str,
        plugin_params: Dict[str, Any],
        s3_export: bool = False,
        cache_time: int = 0,
    ) -> GetDataResult:
        start_time = time()
        logger.debug("Starting generic data retrieval for %s %s", entity_type, entity_id)

        metadata_info: GetDataMetadata = {
            "retrieval_method": None,
            "task_id": None,
            "url": None,
            "execution_time_seconds": None,
            "error": None,
        }

        data_processed = False

        # Step 1: Get the SQL query
        sql_resp = sql_query_fn()

        if not sql_resp or not sql_resp.get("query"):
            logger.error("Failed to get SQL query for %s %s", entity_type, entity_id)
            metadata_info["error"] = "Failed to get SQL query"
            metadata_info["execution_time_seconds"] = time() - start_time
            return {"data": None, "metadata": metadata_info, "success": False}

        # Step 2: Check cache if requested and available
        if cache_time > 0 and sql_resp.get("presignedUrl"):
            logger.debug("Cache requested (cache_time=%ss) - checking S3 file...", cache_time)

            url = sql_resp["presignedUrl"]
            age = None

            # Try to get age from sql_resp first
            if sql_resp.get("lastModified"):
                try:
                    from datetime import datetime, timezone
                    # Handle ISO format '2025-12-23T07:37:25.000Z'
                    last_modified_str = sql_resp["lastModified"].replace('Z', '+00:00')
                    file_time = datetime.fromisoformat(last_modified_str)
                    
                    if file_time.tzinfo is None:
                        file_time = file_time.replace(tzinfo=timezone.utc)

                    now = datetime.now(timezone.utc)
                    age = (now - file_time).total_seconds()
                    logger.debug("Calculated age from sql_resp['lastModified']: %s seconds", age)
                except Exception as e:
                    logger.warning("Failed to parse lastModified from sql_resp: %s", str(e))

            try:
                # If age not determined from sql_resp, try HEAD request
                if age is None:
                    try:
                        resp = requests.head(url)
                        if resp.status_code == 200:
                            last_modified = resp.headers.get("last-modified")
                            if last_modified:
                                from datetime import datetime, timezone
                                from email.utils import parsedate_to_datetime

                                try:
                                    file_time = parsedate_to_datetime(last_modified)
                                except Exception:
                                    file_time = None

                                if file_time is not None:
                                    if file_time.tzinfo is None:
                                        file_time = file_time.replace(tzinfo=timezone.utc)

                                    now = datetime.now(timezone.utc)
                                    age = (now - file_time).total_seconds()
                    except Exception as e:
                        logger.warning("HEAD request failed: %s", str(e))

                if age is not None and age <= cache_time:
                    logger.debug(
                        "Cached file is fresh (age: %s minutes) - using cache",
                        round(age / 60, 1),
                    )

                    resp = requests.get(url)
                    if resp.status_code == 200:
                        try:
                            from io import StringIO

                            df = pd.read_csv(StringIO(resp.text), dtype=str)
                            for col in ['Value', 'value']:
                                if col in df.columns:
                                    df[col] = pd.to_numeric(df[col], errors='coerce')

                            logger.info(
                                "Successfully retrieved %s data from cache (%s rows)",
                                entity_type,
                                len(df),
                            )
                            metadata_info["retrieval_method"] = "cache"
                            metadata_info["url"] = url
                            metadata_info["execution_time_seconds"] = time() - start_time

                            return {
                                "data": df,
                                "metadata": metadata_info,
                                "success": True,
                                # Legacy fields
                                "presignedUrl": url,
                                "source": "cache",
                            }
                        except Exception as e:
                            logger.warning(
                                "Failed to parse cached CSV from S3: %s. Will proceed to execute query/plugin",
                                str(e),
                            )
                    else:
                        logger.warning(
                            "Failed to download cached S3 file (status %s). Will proceed to execute query/plugin",
                            resp.status_code,
                        )
                else:
                    if age is not None:
                        logger.debug(
                            "Cached file is too old (%s minutes) for cache_time=%ss - will generate fresh data",
                            round(age / 60, 1),
                            cache_time,
                        )
                    else:
                        logger.debug("Could not determine cache age - will generate fresh data")

            except Exception as e:
                logger.warning("Error checking cache: %s", str(e))
        elif cache_time == 0:
            logger.debug("Cache disabled (cache_time=0) - will generate fresh data")

        # Step 3: If cache not requested or not available, proceed
        logger.debug("Cache not available or not requested - proceeding with execution")

        # Step 4: Try DB execution if available
        logger.debug("Checking database availability for %s %s", entity_type, entity_id)

        db_available = False
        db = None
        try:
            db = DB(self.sws_client)
            try:
                db.get_credentials(write=False)
                db_available = True
            except Exception as e:
                logger.debug("DB credentials not available: %s", str(e))
                db_available = False
        except Exception as e:
            logger.debug("Database initialization failed: %s", str(e))
            db_available = False
            db = None

        if db_available and sql_resp.get("query"):
            if not s3_export:
                logger.debug("Attempting to execute query locally for %s %s", entity_type, entity_id)
                try:
                    result = db.execute_query(sql_resp["query"])
                    if result is not None:
                        df = pd.DataFrame(result, dtype=str)
                        for col in ['Value', 'value']:
                            if col in df.columns:
                                df[col] = pd.to_numeric(df[col], errors='coerce')

                        logger.debug(
                            "Query executed successfully. Retrieved %s rows with %s columns",
                            len(df),
                            len(df.columns),
                        )

                        metadata_info["retrieval_method"] = "database"
                        metadata_info["execution_time_seconds"] = time() - start_time

                        return {
                            "data": df,
                            "metadata": metadata_info,
                            "success": True,
                            # Legacy field
                            "source": "db",
                        }
                    logger.warning("Local DB execution returned None for %s %s", entity_type, entity_id)
                except Exception as e:
                    logger.warning(
                        "Local DB execution failed for %s %s: %s",
                        entity_type,
                        entity_id,
                        str(e),
                    )
            else:
                logger.debug("Executing DB query for S3 export for %s %s", entity_type, entity_id)
                try:
                    db.execute_query(sql_resp["query"])
                    data_processed = True
                    logger.debug("S3 export query executed successfully for %s %s", entity_type, entity_id)
                except Exception as e:
                    logger.warning(
                        "S3 export query execution failed: %s - proceeding to plugin task",
                        str(e),
                    )

        # If data was processed via DB (S3 export), we need to refresh the SQL query to get the new presigned URL
        if data_processed:
            logger.debug("Data processed via DB export - refreshing SQL query to get presigned URL")
            sql_resp = sql_query_fn()

        # Step 5: Fallback to S3 download if available
        if data_processed and sql_resp.get("presignedUrl"):
            logger.debug("Attempting to download %s data from S3...", entity_type)
            url = sql_resp["presignedUrl"]
            try:
                resp = requests.get(url)
                if resp.status_code == 200:
                    try:
                        from io import StringIO

                        df = pd.read_csv(StringIO(resp.text), dtype=str)
                        for col in ['Value', 'value']:
                            if col in df.columns:
                                df[col] = pd.to_numeric(df[col], errors='coerce')

                        metadata_info["retrieval_method"] = "s3_direct"
                        metadata_info["url"] = url
                        metadata_info["execution_time_seconds"] = time() - start_time
                        logger.info(
                            "Successfully retrieved %s data from S3 (%s rows)",
                            entity_type,
                            len(df),
                        )
                        return {"data": df, "metadata": metadata_info, "success": True}
                    except Exception as e:
                        logger.warning("Failed to parse CSV from S3: %s", str(e))
            except Exception as e:
                logger.warning("Failed to download from S3: %s", str(e))

        # Step 6: If data not processed, execute plugin
        if not data_processed:
            logger.debug("Falling back to plugin task execution for %s %s", entity_type, entity_id)
            tasks = TaskManager(self.sws_client)

            try:
                payload = PluginPayload(parameters=plugin_params)
                plugin_resp = tasks.create_plugin_task(
                    pluginName=plugin_name,
                    payload=payload,
                    slow=False,
                    description=f"Get Data for {entity_type} {entity_id}",
                    parentTaskId=self.sws_client.current_task_id,
                )

                task_id = getattr(plugin_resp, "task_id", None) or getattr(plugin_resp, "taskId", None)

                if not plugin_resp or not task_id:
                    logger.error("Failed to create plugin task for %s %s", entity_type, entity_id)
                    metadata_info["error"] = "Failed to create plugin task"
                    metadata_info["execution_time_seconds"] = time() - start_time
                    return {"data": None, "metadata": metadata_info, "success": False}
                metadata_info["task_id"] = task_id

                task_response = tasks.wait_completion(task_id)

                if not task_response:
                    logger.error("Plugin task did not complete successfully for %s %s", entity_type, entity_id)
                    metadata_info["error"] = "Plugin task did not complete successfully"
                    metadata_info["execution_time_seconds"] = time() - start_time
                    return {"data": None, "metadata": metadata_info, "success": False}

                if task_response.info.outcome == "SUCCESS":
                    # Try to get the S3 URL, forcing s3_export=True since the task should have exported it
                    try:
                        final_sql = sql_query_fn(force_s3=True)
                    except TypeError:
                        # Fallback for functions that don't accept force_s3
                        final_sql = sql_query_fn()
                    
                    logger.debug(f"Final SQL response after task: {final_sql}")
                    
                    if final_sql and final_sql.get("presignedUrl"):
                        final_url = final_sql["presignedUrl"]
                        resp = requests.get(final_url)

                        if resp.status_code == 200:
                            try:
                                from io import StringIO

                                df = pd.read_csv(StringIO(resp.text), dtype=str)
                                for col in ['Value', 'value']:
                                    if col in df.columns:
                                        df[col] = pd.to_numeric(df[col], errors='coerce')

                                logger.info(
                                    "Plugin task completed successfully for %s %s - retrieved %s rows",
                                    entity_type,
                                    entity_id,
                                    len(df),
                                )
                                metadata_info["retrieval_method"] = "plugin_task"
                                metadata_info["url"] = final_url
                                metadata_info["execution_time_seconds"] = time() - start_time

                                return {
                                    "data": df,
                                    "metadata": metadata_info,
                                    "success": True,
                                    # Legacy fields
                                    "presignedUrl": final_url,
                                    "source": "s3_direct",
                                }
                            except Exception as e:
                                logger.warning("Failed to parse CSV after plugin execution: %s", str(e))

                    # Fallback: Check for task artifact
                    output = task_response.info.output
                    output_type = None
                    if hasattr(output, 'type'):
                        output_type = output.type
                    elif isinstance(output, dict):
                        output_type = output.get('type')

                    if output_type == 'file':
                        logger.debug("Checking task artifact for data...")
                        try:
                            artifact_url = tasks.get_task_artifact_url(task_id)
                            resp = requests.get(artifact_url)
                            if resp.status_code == 200:
                                from io import StringIO
                                df = pd.read_csv(StringIO(resp.text), dtype=str)
                                for col in ['Value', 'value']:
                                    if col in df.columns:
                                        df[col] = pd.to_numeric(df[col], errors='coerce')
                                
                                logger.info(
                                    "Retrieved data from task artifact (%s rows)",
                                    len(df),
                                )
                                metadata_info["retrieval_method"] = "plugin_task_artifact"
                                metadata_info["url"] = artifact_url
                                metadata_info["execution_time_seconds"] = time() - start_time
                                return {
                                    "data": df,
                                    "metadata": metadata_info,
                                    "success": True,
                                    "source": "task_artifact"
                                }
                        except Exception as e:
                            logger.warning("Failed to retrieve/parse task artifact: %s", str(e))

                    logger.error("Plugin task succeeded but no data could be retrieved for %s %s", entity_type, entity_id)
                    metadata_info["error"] = "Task succeeded but data retrieval failed"
                    metadata_info["execution_time_seconds"] = time() - start_time
                    return {"data": None, "metadata": metadata_info, "success": False}

                logger.error(
                    "Plugin task failed for %s %s: %s",
                    entity_type,
                    entity_id,
                    task_response.info.outcome,
                )
                metadata_info["error"] = f"Plugin task failed: {task_response.info.outcome}"
                metadata_info["execution_time_seconds"] = time() - start_time
                return {"data": None, "metadata": metadata_info, "success": False}

            except Exception as e:
                logger.error("Error during plugin execution: %s", str(e))
                metadata_info["error"] = f"Plugin execution error: {str(e)}"
                metadata_info["execution_time_seconds"] = time() - start_time
                return {"data": None, "metadata": metadata_info, "success": False}

        # Step 7: Return SQL query only if all else fails
        logger.debug("Returning SQL query only for %s %s", entity_type, entity_id)
        metadata_info["retrieval_method"] = "query_only"
        metadata_info["execution_time_seconds"] = time() - start_time
        return {"data": sql_resp, "metadata": metadata_info, "success": True}
