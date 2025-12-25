"""flaglists Module for SWS API.

This module provides functionality for managing flaglists and retrieving
flaglist information through the SWS API client.
"""

import logging
from time import sleep
import os
from pydantic import BaseModel, Extra
from typing import List, Optional, Dict
from sws_api_client.generic_models import Flag, Multilanguage
from sws_api_client.sws_api_client import SwsApiClient

logger = logging.getLogger(__name__)

class flaglistModel(BaseModel, extra="allow"):
    """Model representing a flaglist's metadata.

    Attributes:
        id (str): Unique identifier of the flaglist
        label (Multilanguage): Multilanguage labels for the flaglist
        type (str): Type of the flaglist
    """
    id: str
    label: Multilanguage

class flaglist(BaseModel, extra="allow"):
    """Model representing a complete flaglist with its codes.

    Attributes:
        model (flaglistModel): Metadata of the flaglist
        codes (List[Code]): List of codes belonging to this flaglist
    """
    model: flaglistModel
    values: List[Flag]

class Flaglists:
    """Class for managing flaglist operations through the SWS API.

    This class provides methods for retrieving flaglist information
    and managing flaglist data.

    Args:
        sws_client (SwsApiClient): An instance of the SWS API client
    """

    def __init__(self, sws_client: SwsApiClient) -> None:
        """Initialize the flaglists manager with SWS client."""
        self.sws_client = sws_client
        self.cache = {}

    def get_flaglist(self, flaglist_id: str, nocache: bool = False, use_cache: Optional[bool] = None) -> flaglist:
        """Retrieve a flaglist by its ID.

        Args:
            flaglist_id (str): The identifier of the flaglist
            nocache (bool, optional): Whether to bypass server cache. Defaults to False.
            use_cache (bool, optional): Whether to use client-side cache. Defaults to None (uses global config).

        Returns:
            flaglist: The requested flaglist with its codes

        Raises:
            HTTPError: If the flaglist cannot be retrieved
        """
        if use_cache is None:
            use_cache = self.sws_client.object_cache

        if use_cache and not nocache and flaglist_id in self.cache:
            return self.cache[flaglist_id]

        url = f"/admin/reference/flaglist/{flaglist_id}?nocache={'true' if nocache else 'false'}"

        response = self.sws_client.discoverable.get('is_api', url)
        result = flaglist(**response)
        
        if use_cache:
            self.cache[flaglist_id] = result
            
        return result