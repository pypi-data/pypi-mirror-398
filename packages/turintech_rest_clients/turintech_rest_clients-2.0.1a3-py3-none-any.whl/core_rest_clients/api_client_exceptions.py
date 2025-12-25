# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
import functools
from typing import Callable, Optional, Type

from requests.exceptions import ConnectionError as RequestsConnectionError  # type: ignore
from requests.exceptions import HTTPError, Timeout

# Core Source imports
from core_common_data_types.type_definitions import GenericT
from core_exceptions.core import BaseGenericException, ExceptionType
from core_exceptions.decorators import inner_wrapper
from core_logging import logger

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                           specifies all modules that shall be loaded and imported into the                           #
#                                current namespace when we use 'from package import *'                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = [
    "client_catch_exception",
    "ClientException",
    "BadRequestException",
    "RequestTimeoutException",
    "ServiceUnavailable",
    "NoResponseException",
    "UnauthorizedException",
    "ClientNotFoundException",
]


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                             Exception handler decorator                                              #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


def client_catch_exception(
    run_func: Optional[Callable[..., GenericT]] = None, *, default: Type[BaseGenericException] = BaseGenericException
) -> Callable[..., GenericT]:
    """
    This function implements a decorator to catch and handle the exceptions that are thrown in the methods of the API
    client services.
    """
    if run_func is None:
        return functools.partial(client_catch_exception, default=default)  # type: ignore

    @functools.wraps(run_func)
    def wrapper(*args, **kwargs) -> GenericT:
        def func(*_args, **_kwargs) -> GenericT:
            try:
                return run_func(*_args, **_kwargs)
            except (RequestsConnectionError, Timeout) as error:
                raise RequestTimeoutException(message=str(error))
            except HTTPError as error:
                raise ServiceUnavailable(message=str(error))

        return inner_wrapper(logger_=logger, logger_depth=2, default=default, run_func=func, args=args, kwargs=kwargs)

    return wrapper


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                  Request Exceptions                                                  #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


class ClientException(BaseGenericException):
    """
    Error raised after invoking the service of a client.
    """

    message = "Unexpected response error"

    def __init__(
        self,
        message: Optional[str] = None,
        client_name: Optional[str] = None,
        error: Optional[str] = None,
        error_code: Optional[int] = None,
    ):
        super().__init__(
            message=message,
            details=" - ".join([str(msg) for msg in [client_name, error_code, error] if msg]),
        )


class BadRequestException(ClientException):
    """
    Error raised when a "400 Bad Request" error response is received from the client.
    """

    type = ExceptionType.INVALID_PARAMS
    message = "Bad request"


class RequestTimeoutException(ClientException):
    """
    A client has initiated a request but for some reason, it has not been transmitted in full.
    """

    type = ExceptionType.TIMEOUT
    message = "Request Timeout"


class ServiceUnavailable(ClientException):
    """
    Error raised when the client is not available.
    """

    type = ExceptionType.UNAVAILABLE
    message = "Client unavailable"


class NoResponseException(ServiceUnavailable):
    """
    Error raised when there is no response from the client.
    """

    message = "Response not received from the client"


class UnauthorizedException(ClientException):
    """
    Error raised when a 401 error is received.
    """

    type = ExceptionType.UNAUTHORIZED
    message = "Client unauthorized error"


class ClientNotFoundException(ClientException):
    """
    Error raised when the service cannot find the requested resource.
    """

    type = ExceptionType.NOT_FOUND
    message = "Client resource not found"
