from pydantic import BaseModel

class AuthClientCredentials(BaseModel):
    clientId: str
    clientSecret: str
    scope: str
    tokenEndpoint: str