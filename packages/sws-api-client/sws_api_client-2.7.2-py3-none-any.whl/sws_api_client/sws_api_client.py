"""SWS API Client Module.

This module provides the main client interface for interacting with the SWS API,
handling authentication, token management, and API discovery.
"""

import argparse
import json
import os
import boto3
from typing import Optional
from sws_api_client.auth import AuthClientCredentials
from sws_api_client.discover import Discover
from sws_api_client.token import Token
import logging

logger = logging.getLogger(__name__)

DEFAULT_CREDENTIALS_SECRET_NAME = "SWS_USER_CREDENTIALS_SECRET_NAME"

class SwsApiClient:
    """Main client class for interacting with the SWS API.

    This class handles authentication, API discovery, and provides various
    initialization methods for different deployment scenarios.

    Attributes:
        sws_endpoint (str): The base URL of the SWS API
        sws_token (str): Authentication token for API access
        authclient (AuthClientCredentials): Authentication credentials
        current_task_id (Optional[str]): ID of the current task
        current_execution_id (Optional[str]): ID of the current execution
        token (Token): Token management instance
        is_debug (bool): Debug mode status
        discoverable (Discover): API discovery interface
    """

    def __init__(self,
                 sws_endpoint: str,
                 sws_token: str,
                 authclient: AuthClientCredentials,
                 current_task_id: Optional[str],
                 current_execution_id: Optional[str],
                 object_cache: bool = False
        ) -> None:
        """Initialize the SWS API client.

        Args:
            sws_endpoint: Base URL of the SWS API
            sws_token: Authentication token
            authclient: Authentication credentials
            current_task_id: Optional current task identifier
            current_execution_id: Optional current execution identifier
            object_cache: Whether to enable client-side object caching (e.g. for codelists, dataset info)
        """
        
        logger.info("Initializing SwsApiClient")

        self.sws_endpoint = sws_endpoint
        self.sws_token = sws_token
        self.authclient = authclient
        self.current_task_id = current_task_id
        self.current_execution_id = current_execution_id
        self.object_cache = object_cache
        self.token = Token(authclient)
        self.is_debug = self.check_debug()
        self.discoverable = Discover(sws_endpoint=sws_endpoint, sws_token=sws_token, token=self.token)
        logger.debug(f"SwsApiClient initialized with endpoint {sws_endpoint} and token {sws_token}")

    @classmethod
    def __get_authclient_credentials_from_secret(cls, env_name="SWS_USER_CREDENTIALS_SECRET_NAME") -> AuthClientCredentials:
        """Retrieve authentication credentials from AWS Secrets Manager.

        Args:
            env_name: Environment variable name containing the secret name

        Returns:
            AuthClientCredentials: Authentication credentials object

        Raises:
            ValueError: If secret name environment variable is not set
        """
        logger.debug(f"Fetching auth client credentials from secret: {env_name}")
        secret_name = os.getenv(env_name)
        if not secret_name:
            raise ValueError(f"Secret name not found in environment variable: {env_name}")
        cls.session = getattr(cls, 'session', boto3.Session())
        cls.secret_manager = getattr(cls, 'secret_manager', cls.session.client('secretsmanager'))
        response = cls.secret_manager.get_secret_value(SecretId=secret_name)
        secretContent = json.loads(response['SecretString'])
        logger.debug(f"Secret fetched successfully: {secretContent}")
        return AuthClientCredentials(
            clientId=secretContent["ID"],
            clientSecret=secretContent["SECRET"],
            scope=secretContent["SCOPE"],
            tokenEndpoint=secretContent["TOKEN_ENDPOINT"]
        )

    @classmethod
    def from_env(cls, sws_endpoint_env="SWS_ENDPOINT", authclient_secret_name=DEFAULT_CREDENTIALS_SECRET_NAME):
        """Create client instance from environment variables.

        Args:
            sws_endpoint_env: Environment variable name for SWS endpoint
            authclient_secret_name: Secret name for authentication credentials

        Returns:
            SwsApiClient: Configured client instance

        Raises:
            ValueError: If required environment variables are missing
        """
        
        logger.debug(f"Creating SwsApiClient from environment variables: {sws_endpoint_env}, {authclient_secret_name}")
        if(os.getenv("SWS_AUTH_CLIENTID") and os.getenv("SWS_AUTH_CLIENTSECRET") and os.getenv("SWS_AUTH_SCOPE") and os.getenv("SWS_AUTH_TOKENENDPOINT")):
            authclient = AuthClientCredentials(
                clientId=os.getenv("SWS_AUTH_CLIENTID"),
                clientSecret=os.getenv("SWS_AUTH_CLIENTSECRET"),
                scope=os.getenv("SWS_AUTH_SCOPE"),
                tokenEndpoint=os.getenv("SWS_AUTH_TOKENENDPOINT")
            )
        else:
            if not os.getenv(authclient_secret_name):
                raise ValueError(f"You need ({authclient_secret_name}) or (SWS_AUTH_CLIENTID, SWS_AUTH_CLIENTSECRET, SWS_AUTH_SCOPE, SWS_AUTH_TOKENENDPOINT) environment variables to be set")
            authclient:AuthClientCredentials = cls.__get_authclient_credentials_from_secret( env_name=authclient_secret_name)
        
        sws_token = os.getenv("SWS_TOKEN")
        if not sws_token:
            raise ValueError("SWS_TOKEN environment variable must be set")
        
        sws_endpoint = os.getenv(sws_endpoint_env)
        if not sws_endpoint:
            raise ValueError(f"{sws_endpoint_env} environment variable must be set")
        

        return cls(
            sws_token=os.getenv("SWS_TOKEN"),
            sws_endpoint=os.getenv(sws_endpoint_env),
            current_task_id=os.getenv("TASK_ID"),
            current_execution_id=os.getenv("EXECUTION_ID"),
            authclient=authclient
        )

    @classmethod
    def from_conf(cls, conf_file="conf_sws_api_client.json"):
        """Create client instance from configuration file.

        Args:
            conf_file: Path to JSON configuration file

        Returns:
            SwsApiClient: Configured client instance

        Raises:
            FileNotFoundError: If configuration file doesn't exist
            json.JSONDecodeError: If configuration file is invalid JSON
        """
        logger.debug(f"Creating SwsApiClient from config file: {conf_file}")
        with open(conf_file) as f:
            kwargs = json.load(f)
            logger.debug(f"Config loaded: {kwargs}")
            return cls(
                sws_endpoint=kwargs["sws_endpoint"],
                sws_token=kwargs["sws_token"],
                current_task_id=kwargs.get("current_task_id"),
                current_execution_id=kwargs.get("current_execution_id"),
                authclient=AuthClientCredentials(**kwargs["authclient"])
            )

    @classmethod
    def from_args(cls):
        """Create client instance from command line arguments.

        Returns:
            SwsApiClient: Configured client instance

        Raises:
            SystemExit: If required arguments are missing
        """
        logger.debug("Creating SwsApiClient from command line arguments")
        parser = argparse.ArgumentParser(description="Instantiate SwsApiClient from args")
        parser.add_argument("--sws_endpoint", type=str, required=True, help="The sws endpoint")
        parser.add_argument("--sws_token", type=str, required=True, help="The SWS access token")
        parser.add_argument("--authclient_id", type=str, required=True, help="The authclient ID")
        parser.add_argument("--authclient_secret", type=str, required=True, help="The authclient secret")
        parser.add_argument("--authclient_scope", type=str, required=True, help="The authclient scope")
        parser.add_argument("--authclient_endpoint", type=str, required=True, help="The authclient endpoint URI")
        parser.add_argument("--current_task_id", type=str, required=False, help="The current task ID")
        parser.add_argument("--current_execution_id", type=str, required=False, help="The current execution ID")
        args, _ = parser.parse_known_args()
        props = vars(args)
        logger.debug(f"Arguments parsed: {props}")
        return cls(
            sws_endpoint=props.get("sws_endpoint"),
            current_task_id=props.get("current_task_id"),
            current_execution_id=props.get("current_execution_id"),
            authclient={
                "client_id": props.get("authclient_id"),
                "client_secret": props.get("authclient_secret"),
                "scope": props.get("authclient_scope"),
                "endpoint": props.get("authclient_endpoint")
            }
        )
    
    @classmethod
    def check_debug(cls) -> bool:
        """Check if debug mode is enabled.

        Debug mode is enabled if DEBUG_MODE environment variable
        is either "TRUE" or not set.

        Returns:
            bool: True if debug mode is enabled, False otherwise
        """
        debug = os.getenv("DEBUG_MODE") == "TRUE" or os.getenv("DEBUG_MODE") is None
        logger.debug(f"Debug mode is {'on' if debug else 'off'}")
        return debug
    
    @classmethod
    def auto(cls):
        """Automatically create client instance based on environment.

        Uses from_conf() in debug mode, from_env() otherwise.

        Returns:
            SwsApiClient: Configured client instance
        """
        debug = cls.check_debug()
        logger.debug(f"Auto-detecting client creation method, debug mode: {debug}")
        if debug:
            return cls.from_conf()
        else:
            return cls.from_env()
