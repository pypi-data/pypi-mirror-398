# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
import inspect
from http import HTTPStatus
from json import JSONDecodeError
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from requests import Response  # type: ignore
from typing_extensions import TypeAlias

# Core Source imports
from core_logging import get_logger
from core_logging.logger_utils import LoggerType
from core_rest_clients.api_client_exceptions import (
    BadRequestException,
    ClientException,
    ClientNotFoundException,
    NoResponseException,
    UnauthorizedException,
)
from core_utils_base.formatting_utils import get_dict_formatter

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                           specifies all modules that shall be loaded and imported into the                           #
#                                current namespace when we use 'from package import *'                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = ["JsonRequest", "STATUS_ERROR_MAPPING", "check_response"]

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                      Data types                                                      #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

JsonRequest: TypeAlias = Union[Dict[str, Any], List[Any], int, str, float, bool]  # Serialized

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                  Exception Mapping                                                   #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

STATUS_ERROR_MAPPING: Dict[int, Type[ClientException]] = {
    HTTPStatus.BAD_REQUEST.value: BadRequestException,
    HTTPStatus.UNAUTHORIZED.value: UnauthorizedException,
    HTTPStatus.NOT_FOUND.value: ClientNotFoundException,
}


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                 API Client utilities                                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


def check_response(
    response: Response,
    operation: Optional[str] = None,
    client_name: Optional[str] = None,
    error_field: Optional[str] = None,
    default_exception: Optional[Type[ClientException]] = None,
    exclude_body: bool = False,
) -> Tuple[int, Any]:
    """Check that the answer is as expected.

    Args:
        response: Service invocation response
        operation: Request operation
        client_name: Provider name of the response
        error_field: Response field where the message error is stored
        default_exception: Default exception type to raise
        exclude_body: Flag to enable/disable response body logging

    Returns:
        (status_code, body) (Tuple[bool, int, Any]): Tuple with the values:
            - status_code: The status code response
            - body: The content of the response

    """
    logger: LoggerType = get_logger()

    if response is None:
        raise NoResponseException(client_name=client_name)

    status_code = response.status_code
    try:
        body_json = response.json()
    except JSONDecodeError:
        body_json = None

    body = body_json if body_json is not None else response.text
    logger.debug(
        "Response"
        + get_dict_formatter(
            data={
                key: value
                for key, value in {
                    "operation": (operation or inspect.stack()[1][3]).upper(),
                    "url": response.url,
                    "response": response,
                    "response.status_code": status_code,
                    "response.reason": response.reason,  # Textual reason of responded HTTP Status
                    "response.content": response.content,  # Return the raw bytes of the data payload,
                    "response.text": response.text,  # Return a string representation of the data payload
                    "response.json": body_json,  # This method is convenient when the API returns JSON
                    "body": body,
                    "body type": type(body),
                }.items()
                if value
                and not (exclude_body and key in ["response.content", "response.text", "response.json", "body"])
            },
        ),
    )

    if status_code > 299:
        message = body.get(error_field, body) if isinstance(body, dict) else response.reason
        error: Type[ClientException] = STATUS_ERROR_MAPPING.get(status_code, default_exception or ClientException)
        logger.error(f"{error}: client_name={client_name}, error_code={status_code}, error={message}")
        raise error(client_name=client_name, error_code=status_code, error=message)

    return status_code, body
