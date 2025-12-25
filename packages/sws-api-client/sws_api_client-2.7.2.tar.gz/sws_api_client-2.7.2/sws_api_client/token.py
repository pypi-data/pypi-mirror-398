import datetime
import logging
import os
from pydantic import BaseModel
import requests

logger = logging.getLogger(__name__)
from sws_api_client.auth import AuthClientCredentials

class TokenModel(BaseModel):
    access_token: str
    expires_on: datetime.datetime

class Token:

    def __init__(self,authclient:AuthClientCredentials) -> None:
        self.authclient = authclient
        self.token = self.get_token()
    
    def get_token(self) -> TokenModel:
        if not hasattr(self, 'token') or self.token.expires_on is None or self.token.expires_on < datetime.datetime.now():
            url = f"{self.authclient.tokenEndpoint}"
            data = {
                "grant_type": "client_credentials",
                "client_id": self.authclient.clientId,
                "client_secret": self.authclient.clientSecret,
                "scope": self.authclient.scope,
            }
            response = requests.post(url, data=data)
            response.raise_for_status()
            result = response.json()
            self.token = TokenModel(
                access_token=result["access_token"],
                expires_on=datetime.datetime.now() + datetime.timedelta(seconds=result["expires_in"])
            )
            logger.debug(f"Token: {self.token}")
            return self.token
        else:
            return self.token