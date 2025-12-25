"""API Discovery Module for SWS API.

This module provides functionality for discovering and interacting with
various SWS API endpoints through dynamic endpoint discovery.
"""

import logging
import os
from typing import Union

import requests

from sws_api_client.token import Token

logger = logging.getLogger(__name__)

class Discover:
    """Class for handling API endpoint discovery and requests.

    This class provides methods for discovering available API endpoints
    and making HTTP requests to them with appropriate authentication.

    Args:
        sws_endpoint (str): Base URL of the SWS API
        sws_token (str): SWS authentication token
        token (Token): Token management instance
    """

    def __init__(self,sws_endpoint:str,sws_token:str, token:Token) -> None:
        """Initialize the Discover instance with endpoint and authentication."""
        self.sws_endpoint = sws_endpoint
        self.sws_token = sws_token
        self.token = token
        self.discover = self.__get_discover()
        logger.debug(f"Discover initialized with endpoint {sws_endpoint} and token {sws_token}")

    def __get_discover(self) -> dict:
        """Retrieve the API discovery information.

        Returns:
            dict: Dictionary containing available endpoints and their configurations

        Raises:
            requests.exceptions.RequestException: If discovery request fails
        """
        token = self.token.get_token()
        discover_endpoint = f"{self.sws_endpoint}/discover"
        headers = {"Authorization": token.access_token, 'sws-token': self.sws_token}
        
        return requests.get(url=discover_endpoint, headers=headers).json()
    
    def call(self, method: str, endpoint: str, path: str, params: dict = None, headers: dict = None, 
             data: dict = None, files=None, options: dict = None, **kwargs) -> dict:
        """Make an HTTP request to a discovered API endpoint.

        Args:
            method (str): HTTP method (GET, POST, PUT, DELETE)
            endpoint (str): API endpoint identifier
            path (str): Request path
            params (dict, optional): Query parameters
            headers (dict, optional): Additional headers
            data (dict, optional): Request payload
            files (optional): Files to upload
            options (dict, optional): Additional request options
            **kwargs: Additional request arguments

        Returns:
            dict: Response data or empty dict if request fails

        Raises:
            ValueError: If endpoint is invalid or not found
            requests.exceptions.RequestException: If request fails
        """
        if not endpoint:
            raise ValueError("An endpoint must be provided.")

        if endpoint not in self.discover or 'path' not in self.discover[endpoint]:
            raise ValueError(f"endpoint '{endpoint}' not found")
        
        x_api_key = self.discover[endpoint].get("key", "")
        full_path = f"{self.discover[endpoint]['path']}{path}"
        token = self.token.get_token()
        full_headers = {"Authorization": token.access_token, "sws-token": self.sws_token}
        if x_api_key:
            full_headers["x-api-key"] = x_api_key

        if headers:
            full_headers.update(headers)

        request_func = getattr(requests, method.lower())
        if(options and options.get('json_body') and options.get('json_body') == True):
            response = request_func(full_path, params=params, headers=full_headers, json=data, files=files, **kwargs)
        else:
            response = request_func(full_path, params=params, headers=full_headers, data=self.dictToTupleList(data), files=files, **kwargs)

        try:
            response.raise_for_status()
            if(options and options.get('raw_response') and options.get('raw_response') == True):
                logger.debug(f"Returning raw response")
                return response
            return response.json()
        except requests.exceptions.HTTPError as errh:
            logger.error(f"HTTP Error: {errh}")
            logger.error(f"HTTP Status Code: {errh.response.status_code}")
            logger.error(f"Response Text: {errh.response.text}")
            logger.error(f"Request URL: {errh.request.url}")
            logger.error(f"Request Body: {response.request.body}")
            logger.error(f"Request Headers: {response.request.headers}")
        except requests.exceptions.RequestException as err:
            logger.error(f"Request Exception: {err}")

        return {}

    def get(self, endpoint, path: str, params: dict = None, headers: dict = None, 
            options:dict = None, **kwargs) -> Union[dict,requests.Response]:
        """Make a GET request to an endpoint.

        Args:
            endpoint: API endpoint identifier
            path: Request path
            params: Query parameters
            headers: Additional headers
            options: Request options
            **kwargs: Additional request arguments

        Returns:
            Union[dict, requests.Response]: Response data or raw response
        """
        return self.call("GET", endpoint, path, params=params, headers=headers, options=options, **kwargs)

    def multipartpost(self, endpoint, path: str, data: dict = None, params: dict = None, 
                     headers: dict = None, files = None,  options:dict = None, **kwargs) -> Union[dict,requests.Response]:
        """Make a multipart POST request for file uploads.

        Args:
            endpoint: API endpoint identifier
            path: Request path
            data: Form data
            params: Query parameters
            headers: Additional headers
            files: Files to upload
            options: Request options
            **kwargs: Additional request arguments

        Returns:
            Union[dict, requests.Response]: Response data or raw response
        """
        return self.call("POST", endpoint, path, params=params, headers=headers, data=data, files=files, options=options, **kwargs)
    
    def post(self, endpoint, path: str, data: dict = None, params: dict = None, 
             headers: dict = None, files = None,  options:dict = None, **kwargs) -> Union[dict,requests.Response]:
        """Make a POST request with JSON payload.

        Args:
            endpoint: API endpoint identifier
            path: Request path
            data: JSON payload
            params: Query parameters
            headers: Additional headers
            files: Files to upload
            options: Request options
            **kwargs: Additional request arguments

        Returns:
            Union[dict, requests.Response]: Response data or raw response
        """
        full_options = {'json_body': True}
        if options:
            full_options.update(options)
        return self.call("POST", endpoint, path, params=params, headers=headers, data=data, files=files, options=full_options, **kwargs)

    def put(self, endpoint, path: str, data: dict = None, params: dict = None, 
            headers: dict = None, options:dict = None, **kwargs) -> Union[dict,requests.Response]:
        """Make a PUT request to an endpoint.

        Args:
            endpoint: API endpoint identifier
            path: Request path
            data: Request payload
            params: Query parameters
            headers: Additional headers
            options: Request options
            **kwargs: Additional request arguments

        Returns:
            Union[dict, requests.Response]: Response data or raw response
        """
        return self.call("PUT", endpoint, path, params=params, headers=headers, data=data, options=options, **kwargs)

    def delete(self, endpoint, path: str, data:dict = None, params: dict = None, headers: dict = None, 
               options:dict = None, **kwargs) -> Union[dict,requests.Response]:
        """Make a DELETE request to an endpoint.

        Args:
            endpoint: API endpoint identifier
            path: Request path
            params: Query parameters
            headers: Additional headers
            options: Request options
            **kwargs: Additional request arguments

        Returns:
            Union[dict, requests.Response]: Response data or raw response
        """
        full_options = {'json_body': True}
        if options:
            full_options.update(options)
        return self.call("DELETE", endpoint, path, params=params, headers=headers, data=data, options=full_options, **kwargs)

    def dictToTupleList(self, _dict:dict) -> list[tuple[str, any]]:
        converted = []

        if _dict == None:
            return _dict

        for key, val in _dict.items():
            if isinstance(val, list):
                for _, innerVal in enumerate(val):
                    converted.append((key, innerVal))
            else:
                converted.append((key, val))

        return converted
