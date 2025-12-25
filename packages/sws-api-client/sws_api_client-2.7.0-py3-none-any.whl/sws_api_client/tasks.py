"""TaskManager Module allow to interact with SWS TaskManager API.

This module provides functionality for managing tasks, including creation,
monitoring, and artifact retrieval through the SWS API client.
"""

import logging

import requests
from sws_api_client.sws_api_client import SwsApiClient
from dataclasses import (dataclass, asdict)
from typing import List, Dict, Optional, Literal, Any
import json
import time
logger = logging.getLogger(__name__)


@dataclass
class TaskDataset:
    """Dataset information for task execution.
    
    Attributes:
        dataset (str): The identifier of the dataset
        session (Optional[str]): The identifier of the dataset
        selection (Optional[Dict[str,List[str]]]): A dictionary containing the codes selection per each dimension
    """
    dataset: str
    session: Optional[str] = None
    selection: Optional[Dict[str,List[str]]] = None

@dataclass
class PluinPayloadContainer:
    """Container configuration for plugin execution.
    
    Attributes:
        image (str): Container image name
        tag (str): Container image tag
    """
    image: str
    tag: str

@dataclass
class PluginPayloadEndpoint:
    """Endpoint configuration for plugin execution.
    
    Attributes:
        port (int): Port number for the endpoint
        protocol (str): Protocol used by the endpoint
    """
    port: int
    protocol: str


@dataclass
class PluginPayloadGit:
    """Git repository configuration for plugin execution.
    
    Attributes:
        repository (str): URL of the git repository
        target (str): Target branch or commit
        root (str): Root directory in the repository
    """
    repository: str
    target: str
    root: str

@dataclass
class PluginPayload:
    """Payload configuration for plugin execution.
    
    Attributes:
        datasets (List[TaskDataset]): List of datasets to process
        parameters (Dict): Plugin-specific parameters
        cpu (Optional[int]): CPU allocation for the task
        memory (Optional[int]): Memory allocation for the task
    """
    datasets: Optional[List[TaskDataset]] = None
    parameters: Optional[Dict] = None
    cpu: Optional[int] = None
    memory: Optional[int] = None
    language: Optional[str] = None
    version: Optional[str] = None
    git: Optional[PluginPayloadGit] = None
    container: Optional[PluinPayloadContainer] = None
    indexFilePath: Optional[str] = None
    dependenciesFilePath: Optional[str] = None
    endpoint: Optional[PluginPayloadEndpoint] = None
    slow: Optional[bool] = None

    def to_dict(self) -> Dict:
        """Convert the payload to a dictionary format, excluding None values.

        Returns:
            Dict: Dictionary representation of the payload with None values removed
        """
        result = asdict(self)
        return {k: v for k, v in result.items() if v is not None}

@dataclass
class TaskExecutionOutput:
    """Task execution output information.
    """
    type: Literal['error','file','text','json']
    content: Any

# Define Status and DetailStatus as Literal types
Status = Literal['ACTIVE', 'ARCHIVED']
DetailStatus = Literal['CREATED', 'EXECUTION_PREPARED', 'EXECUTION_PROCESSING', 'EXECUTION_PROCESSED', 'STOP_REQUESTED', 'RETRIED', 'ENDED', 'ARCHIVED']
Outcome = Literal['SUCCESS', 'FAILURE']
@dataclass
class TaskInfo:
    """Information about a task's current state and configuration.
    
    Attributes:
        detail_status (DetailStatus): Current detailed status of the task
        ended_on (Optional[str]): Timestamp when task ended
        description (str): Task description
        updated_on (str): Last update timestamp
        created_on (str): Creation timestamp
        service_user (str): Service user executing the task
        tags (Dict[str, str]): Task tags
        output (Dict): Task output data
        input (Dict): Task input configuration
        task_type (str): Type of task
        context (str): Execution context
        progress (int): Task progress percentage
        user (str): User who created the task
        outcome (Outcome): Task execution outcome
        group (Optional[str]): Task group identifier
        status (Status): Current status
        parent_task_id (Optional[str]): Parent task identifier
    """
    detail_status: DetailStatus
    ended_on: Optional[str]
    description: str
    updated_on: str
    created_on: str
    service_user: str
    tags: Dict[str, str]
    output: Dict
    input: Dict
    task_type: str
    context: str
    progress: int
    user: str
    outcome: Optional[Outcome]
    output: Optional[TaskExecutionOutput]
    group: Optional[str]
    status: Status
    parent_task_id: Optional[str]

@dataclass
class TaskResponse:
    """Response containing task information.
    
    Attributes:
        task_id (str): Unique identifier of the task
        info (TaskInfo): Detailed task information
    """
    task_id: str
    info: TaskInfo

@dataclass
class TaskCreateResponse:
    """Response from task creation request.
    
    Attributes:
        task_id (str): Identifier of the created task
    """
    task_id: str

class TaskManager:
    """TaskManager class.

    This class provides methods for creating, monitoring, and managing tasks
    through the SWS API client.

    Args:
        sws_client (SwsApiClient): Instance of the SWS API client
        endpoint (str, optional): API endpoint for task operations. Defaults to 'task_manager_api'
    """

    def __init__(self, sws_client: SwsApiClient, endpoint: str = 'task_manager_api') -> None:
        """Initialize TaskManager with SWS client and endpoint."""
        self.sws_client = sws_client
        self.endpoint = endpoint

    def update_current_task(self,
                            description:Optional[str]=None,
                            tags:Optional[Dict[str,str]]=None,
                            config:Optional[Dict[str,Any]]=None,
                            group:Optional[str]=None):
        """Update the current task with new information.
        Args:
            description (Optional[str]): New task description
            tags (Optional[Dict[str,str]]): New task tags
            config (Optional[Dict[str,Any]]): New task configuration
            group (Optional[str]): New task group
        
        Raises:
            ValueError: If current task ID is not set
        """
        if not self.sws_client.current_task_id:
            raise ValueError("A current task ID must be provided.")
        taskId = self.sws_client.current_task_id
        path = f'/task/{taskId}'
        data = {}
        if description is not None:
            data['description'] = description
        if tags is not None:
            data['tags'] = tags
        if config is not None:
            data['config'] = config
        if group is not None:
            data['group'] = group
        
        self.sws_client.discoverable.put(self.endpoint, path, json=data)

    def update_current(self,
                            progress:Optional[int]=None,
                            outcome:Optional[Outcome]=None,
                            output:Optional[TaskExecutionOutput]=None):
        """Update the status of the current task with additional information.

        Args:
            progress (Optional[int]): Current progress percentage
            outcome (Optional[Outcome]): Task execution outcome
            output (Optional[TaskExecutionOutput]): Task execution output

        Raises:
            ValueError: If current task ID or execution ID is not set
        """
        if not self.sws_client.current_task_id:
            raise ValueError("A current task ID must be provided.")
        if not self.sws_client.current_execution_id:
            raise ValueError("A current task ID must be provided.")
        taskId = self.sws_client.current_task_id
        executionId = self.sws_client.current_execution_id

        path = f'/task/{taskId}/execution/{executionId}'
        data = {}
        if progress is not None:
            data['progress'] = progress

        if outcome is not None:
            data['outcome'] = outcome
            
        if output is not None:
            data['output'] = output.__dict__

        self.sws_client.discoverable.put(self.endpoint, path, json=data)

    def get_upload_artifact_url(self, task_id: str) -> str:
        """Get URL for uploading task artifacts.

        Args:
            task_id: Task identifier

        Returns:
            str: Upload URL for the artifact
        """
        path = f'/task/{task_id}/get-upload-artifact-url'
        response = self.sws_client.discoverable.post(self.endpoint, path, options=dict(raw_response=True)).text
        return response
    
    def set_current_artifact(self, artifact_path: str):
        """Upload an artifact to the current task execution.

        Args:
            artifact_path: Path to the artifact file

        Raises:
            ValueError: If current task ID is not set
        """
        if not self.sws_client.current_task_id:
            raise ValueError("A current task ID must be provided.")
        task_id = self.sws_client.current_task_id

        upload_url = self.get_upload_artifact_url(task_id)
        with open(artifact_path, 'rb') as file:
            requests.put(upload_url, data=file)
        
        self.update_current(output=TaskExecutionOutput(type='file', content=artifact_path))

    def create_plugin_task(self,
            payload: PluginPayload,
            slow:Optional[bool] = None,
            pluginId:Optional[str] = None,
            pluginName:Optional[str] = None,
            description: Optional[str] = None,
            group: Optional[str] = None,
            parentTaskId: Optional[str] = None,
            user:Optional[str] = None,
            repeatable:bool = True,
            public:bool = False,
            retry:bool = False,
            emailNotification:bool = False
        ) -> TaskCreateResponse:
        """Create a new plugin execution task.

        Args:
            pluginId: Identifier of the plugin to execute (if not provided, pluginName must be given)
            pluginName: Name of the plugin to execute (if not provided, pluginId must be given)
            slow: Whether the plugin execution is slow
            payload: Plugin configuration payload
            description: Task description
            group: Optional task group
            parentTaskId: Optional parent task identifier
            user: Optional user identifier
            repeatable: Whether task can be repeated
            public: Whether task is public
            retry: Whether task can be retried
            emailNotification: Whether to send email notifications

        Returns:
            TaskCreateResponse: Response containing the created task ID
        """

        if not pluginId and not pluginName and payload is None and payload.get('git') is None:
            raise ValueError("Either pluginId or pluginName must be provided when no git conf is provided.")
        if pluginId and pluginName:
            raise ValueError("Only one of pluginId or pluginName should be provided.")

        path = 'task/create'

        input = {
            "payload": payload.to_dict()
        }

        if slow is not None:
            input['slow'] = slow
        if pluginId:
            input['pluginId'] = pluginId
        if pluginName:
            input['pluginName'] = pluginName

        data = {
            "user": user,
            "context": "IS",
            "type": "RUN_PLUGIN",
            "description": f"Run plugin {pluginId or pluginName}" if description is None else description,
            "input":input,
            "config": {
                "repeatable":repeatable,
                "public":public,
                "retry":retry,
                "emailNotification":emailNotification
            },
            "parentTaskId": parentTaskId
        }

        if group:
            data['group'] = group

        response = self.sws_client.discoverable.post(self.endpoint, path, data=data)
        if response:
            return self.get_task_create_response(response)
        else:
            return None

    def get_task_response(self, task: Dict) -> TaskResponse:
        """Convert raw task data to TaskResponse object.

        Args:
            task: Raw task data dictionary

        Returns:
            TaskResponse: Structured task response object
        """
        return TaskResponse(
            task_id=task['taskId'],
            info=TaskInfo(
                detail_status=task.get('info').get('detailStatus'),
                ended_on=task.get('info').get('endedOn'),
                description=task.get('info').get('description'),
                updated_on=task.get('info').get('updatedOn'),
                created_on=task.get('info').get('createdOn'),
                service_user=task.get('info').get('serviceUser'),
                tags=task.get('info').get('tags'),
                output=task.get('info').get('output'),
                input=json.loads(task.get('info').get('input', '{}')),  # Default to an empty dictionary if 'input' is missing
                task_type=task.get('info').get('taskType'),
                context=task.get('info').get('context'),
                progress=task.get('info').get('progress'),
                user=task.get('info').get('user'),
                outcome=task.get('info').get('outcome'),
                status=task.get('info').get('status'),
                group=task.get('info').get('group'),
                parent_task_id=task.get('info').get('parentTaskId')
            )
        )
    
    def get_task_create_response(self, task: Dict) -> TaskCreateResponse:
        """Convert raw task creation data to TaskCreateResponse object.

        Args:
            task: Raw task creation data dictionary

        Returns:
            TaskCreateResponse: Structured task creation response
        """
        return TaskCreateResponse(
            task_id=task['taskId']
        )


    def get_task(self, task_id: str) -> Optional[TaskResponse]:
        """Retrieve task information by ID.

        Args:
            task_id: Task identifier

        Returns:
            Optional[TaskResponse]: Task information if found, None otherwise
        """
        path = f'/task/{task_id}'
        response = self.sws_client.discoverable.get(self.endpoint, path)

        if response:
            return self.get_task_response(response)
        else:
            return None

    def get_tasks_by_ids(self, task_ids: List[str]) -> List[TaskResponse]:
        """Retrieve multiple tasks by their IDs.

        Args:
            task_ids: List of task identifiers

        Returns:
            List[TaskResponse]: List of found task responses
        """
        path = f'/task/by-ids'
        response = self.sws_client.discoverable.post(self.endpoint, path, data={"ids":task_ids})
        # the response is an object like this: {id, data?, error?}[]
        # we need to convert the task object to a TaskResponse object and return a list of TaskResponse objects
        if response:
            return [self.get_task_response(obj.get('data')) for obj in response if obj.get('data')]
    
    def wait_completion(self, task_id: str, poll_interval: int = 10) -> TaskResponse:
        """Wait for task completion and return final status.

        Args:
            task_id: Task identifier
            poll_interval: Seconds between status checks

        Returns:
            TaskResponse: Final task status

        Raises:
            ValueError: If task is not found after multiple attempts
        """
        not_created_counter = 0
        while True:
            task_response = self.get_task(task_id)

            if not task_response and not_created_counter > 5:
                raise ValueError(f"Task with ID {task_id} not found.")
            elif not task_response:
                not_created_counter += 1
            else:
                not_created_counter = 0
            
                task_status = task_response.info.detail_status
                logger.info(f"Task {task_id} status: {task_status}")
                if task_status == 'ENDED':
                    return task_response

                time.sleep(poll_interval)

    def wait_completion_by_ids(self, task_ids: List[str], poll_interval: int = 10) -> List[TaskResponse]:
        """Wait for multiple tasks to complete.

        Args:
            task_ids: List of task identifiers
            poll_interval: Seconds between status checks

        Returns:
            List[TaskResponse]: List of final task statuses
        """
        completed_tasks = []
        while True:
            tasks_response = self.get_tasks_by_ids(task_ids)
            completed_tasks = [task for task in tasks_response if task.info.detail_status == 'ENDED']
            if len(completed_tasks) == len(task_ids):
                return completed_tasks

            time.sleep(poll_interval)
    
    def get_task_artifact_url(self, task_id: str) -> str:
        """Get download URL for task artifacts.

        Args:
            task_id: Task identifier

        Returns:
            str: Download URL for task artifacts
        """
        path = f'/task/{task_id}/get-download-artifact-url'
        url = self.sws_client.discoverable.post(self.endpoint, path, options=dict(raw_response=True)).text
        return url