from pydantic import BaseModel


class Credentials(BaseModel):
    api_key: str
    api_secret_key: str
