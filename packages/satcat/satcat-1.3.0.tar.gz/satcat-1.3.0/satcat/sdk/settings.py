import json
import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Literal
from urllib.parse import urljoin, urlparse, urlunparse

try:
    from pydantic.v1 import AnyUrl, BaseModel, BaseSettings, Extra, Field, validator
except ImportError:
    from pydantic import AnyUrl, BaseModel, BaseSettings, Extra, Field, validator


class OutputFormat(str, Enum):
    JSON = "json"
    RICH = "rich"


CONFIG_PATH = None


def json_config_settings_source(settings: BaseSettings) -> Dict[str, Any]:
    """
    A simple settings source that loads variables from a JSON file
    at the project's root.

    Here we happen to choose to use the `env_file_encoding` from Config
    when reading `config.json`
    """
    try:
        if CONFIG_PATH is not None:
            env_path = CONFIG_PATH
        else:
            env_path = os.getenv("SATCAT_CONFIG_PATH", "config.json")
        encoding = settings.__config__.env_file_encoding
        loaded_json = json.loads(Path(env_path).read_text(encoding))
        lowered_json = {key.lower(): val for key, val in loaded_json.items()}
        return lowered_json
    except FileNotFoundError:
        return {}


class CLISettings(BaseModel):
    is_cli: bool = False
    output_format: OutputFormat = OutputFormat.RICH
    show_progress: bool = True


class Settings(BaseSettings):
    auth_method: Literal['password', 'client_credentials'] = "client_credentials"
    auth_username: Optional[str] = None
    auth_password: Optional[str] = None
    auth_client_id: Optional[str] = None
    auth_client_secret: Optional[str] = None
    auth_url: AnyUrl = "https://api.satcat.com/oauth/token/"
    satcat_base_url: AnyUrl = "https://satcat.com/"
    satcat_rest_api_url_override: Optional[AnyUrl] = None
    satcat_web_api_url_override: Optional[AnyUrl] = None
    default_timeout: int = 1200
    cli: CLISettings = Field(default_factory=CLISettings)

    @validator("satcat_base_url")
    def satcat_base_url_must_end_with_slash(cls, v: str):
        if not v.endswith("/"):
            v = v + "/"
        return v

    class Config:
        env_file_encoding = "utf-8"
        extra = Extra.allow
        env_prefix = "satcat_"

        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            return (
                init_settings,
                json_config_settings_source,
                env_settings,
                file_secret_settings,
            )

    @property
    def satcat_rest_api_url(self) -> str:
        if self.satcat_rest_api_url_override is not None:
            return self.satcat_rest_api_url_override
        else:
            parsed = urlparse(self.satcat_base_url)
            netloc_parts = parsed.netloc.split('.')
            netloc_parts.insert(0, "api")
            new_netloc = '.'.join(netloc_parts)
            new_url = urlunparse(parsed._replace(netloc=new_netloc))
            return new_url

    @property
    def satcat_web_api_url(self) -> str:
        if self.satcat_web_api_url_override is not None:
            return self.satcat_web_api_url_override
        else:
            return urljoin(self.satcat_base_url, "/api")

settings = Settings()


def load_settings_file(config_path: Path):
    if not os.path.exists(config_path):
        raise FileNotFoundError(config_path)
    global CONFIG_PATH
    CONFIG_PATH = config_path

    new_settings = Settings()
    for field, value in new_settings.__dict__.items():
        setattr(settings, field, value)
