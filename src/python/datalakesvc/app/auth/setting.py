from functools import lru_cache
import os

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Setting(BaseSettings):
    auth0_domain : str
    auth0_api_audience : str
    auth0_issuer : str
    auth0_algorithms : str
    auth0_client_id : str
    auth0_client_secret : str
    auth0_grant_type : str
    

    model_config = ConfigDict(
        prefix="AUTH_",
        env_file=".env.dev" if os.getenv("ENV") == "dev" else ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    


@lru_cache()
def get_settings():
    return Setting()
