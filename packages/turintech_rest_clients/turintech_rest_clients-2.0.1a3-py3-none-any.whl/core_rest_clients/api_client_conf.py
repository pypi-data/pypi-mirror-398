# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
from typing import Dict, Optional

from pydantic import Field, field_validator

# Internal libraries
from core_common_configuration.base_conf_env import BaseConfEnv
from core_utils_base import url_utils
from core_utils_file.data_utils import join_values

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                           specifies all modules that shall be loaded and imported into the                           #
#                                current namespace when we use 'from package import *'                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = ["ApiClientConf", "api_client_conf_factory"]


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                 Configuration class                                                  #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


class ApiClientConf(BaseConfEnv):
    """
    This is a configuration class for the API client, primarily used for Rocket Client.
    """

    host: str = Field(
        default="127.0.0.1",
        description="The IP address or hostname of the API server to connect to.",
    )
    protocol: str = Field(default="http", description="Set the HTTP protocol implementation (HTTP, HTTPs)")
    port: Optional[int] = Field(default=5000, description="The port number to connect to on the API server.")
    postfix: Optional[str] = Field(default="", description="The postfix to be added to the URL.")
    headers: Optional[Dict[str, str]] = Field(default=None, description="The headers to be sent.")

    # --------------------------------------------------------------------------------------------------

    @field_validator("protocol")
    def protocol_validation(cls, value: str) -> str:  # pylint: disable=no-self-argument
        """
        Validate the protocol value.
        """
        _value = value.lower() if value else None
        return _value if _value in ["http", "https"] else "http"

    _validate_no_leading_slash = field_validator("host")(url_utils.no_leading_slash)
    _validate_no_trailing_slash = field_validator("host")(url_utils.no_trailing_slash)
    _validate_no_http = field_validator(
        "host",
    )(url_utils.no_http)

    @property
    def server_url(self):
        """
        Base URL:
            <api_protocol>://<api_host>:<api_port><postfix>
        For rocket client use
        """
        if self.host:
            return join_values(
                values=[
                    f"{self.protocol}://" if self.protocol else None,
                    self.host,
                    f":{self.port}" if self.port else None,
                    f"{self.postfix}" if self.postfix else None,
                ]
            )
        return ""


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                Configuration Factory                                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


def api_client_conf_factory(
    _env_file: Optional[str] = None, prefix: Optional[str] = None, defaults: Optional[Dict] = None, **kwargs
) -> ApiClientConf:
    """This is a factory generating a BasicServerConf class specific to a service, loading every value from a generic
    .env file storing variables in uppercase with a service prefix.

    For rocket client use

    """
    return ApiClientConf.with_defaults(env_file=_env_file, env_prefix=prefix, defaults=defaults, **kwargs)
