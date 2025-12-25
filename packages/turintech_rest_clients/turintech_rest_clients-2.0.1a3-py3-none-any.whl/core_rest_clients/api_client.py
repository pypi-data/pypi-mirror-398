# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
from typing import IO, Any, Dict, List, Optional, Tuple, Union

import requests  # type: ignore
from requests import Response

from core_logging import get_logger
from core_logging.logger_utils import LoggerType
from core_rest_clients.api_client_conf import ApiClientConf
from core_rest_clients.api_client_exceptions import client_catch_exception
from core_rest_clients.api_client_utils import JsonRequest, check_response
from core_utils_base.formatting_utils import get_dict_formatter
from core_utils_base.url_utils import no_leading_slash, no_trailing_slash

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                           specifies all modules that shall be loaded and imported into the                           #
#                                current namespace when we use 'from package import *'                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = ["ApiClient"]


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                Service implementation                                                #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


class ApiClient:
    """
    Integration with an API client.
    """

    logger: LoggerType

    conf: ApiClientConf
    client_name: Optional[str] = None
    error_field: Optional[str] = None
    default_timeout: float
    accept_header: Dict[str, Any] = {"accept": "application/json"}

    def __init__(
        self,
        client_conf: ApiClientConf,
        client_name: Optional[str] = None,
        error_field: Optional[str] = None,
        default_timeout: float = 120,
    ):
        """
        Args:
            client_conf (ApiClientConf): API client configuration
            client_name (Optional[str]): API client name
            error_field (Optional[str]): Response field where the message error is stored
        """
        self.conf = client_conf
        self.logger = get_logger()
        self.client_name = client_name
        self.error_field = error_field
        self.default_timeout = default_timeout

    # --------------------------------------------------------------------------------------------------

    def get_api_url(self, endpoint: str) -> str:
        """
        Compose the URL of the service to be invoked.
        """
        return no_trailing_slash(f"{self.conf.server_url}/{no_leading_slash(endpoint)}")

    # --------------------------------------------------------------------------------------------------

    @client_catch_exception
    def check_client_status(self) -> bool:
        """
        Validation of connection with the client.
        """
        response: Response = requests.get(url=self.conf.server_url, timeout=self.default_timeout)
        response.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xxx
        return True

    # -------------------------------------------------------------------------------------------
    # --- Operation
    # -------------------------------------------------------------------------------------------

    def _logger_request(self, operation: str, request: Dict[str, Any]):
        self.logger.debug(
            "Request"
            + get_dict_formatter(
                data={"operation": operation, **{key: value for key, value in request.items() if value}},
            ),
        )

    def update_headers(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Update the headers to be sent if necessary.
        """
        return {**(self.conf.headers if self.conf.headers else {}), **(headers if headers else {})}

    def prepare_request_params(
        self,
        url: str,
        params: Optional[Dict] = None,
        data: Optional[Union[Dict, List[Tuple], bytes, IO]] = None,
        files: Optional[Union[Dict, bytes]] = None,
        json: Optional[JsonRequest] = None,
        headers: Optional[Dict] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Compose the request to be sent.
        """
        return {
            "url": url,
            "params": params,
            "data": data,
            "files": files,
            "json": json,
            "headers": self.update_headers(headers=headers),
            "timeout": timeout if timeout else self.default_timeout,
        }

    @client_catch_exception
    def post(
        self,
        endpoint: str,
        headers: Optional[Dict] = None,
        params: Optional[Dict] = None,
        data: Optional[Union[Dict, List[Tuple], bytes, IO]] = None,
        files: Optional[Union[Dict, bytes]] = None,
        json: Optional[JsonRequest] = None,
    ) -> Tuple[int, Any]:
        """Send data and return response data from POST endpoint.

        Args:
            endpoint (str): Endpoint for the new :class:`Request` object.
            headers: (Optional) Dictionary of HTTP Headers to send with the :class:`Request`.
            params (Optional): Dictionary or bytes to be sent in the query string for the :class:`Request`.
            data (Optional): Dictionary, list of tuples, bytes, or file-like object to send in the body of the
                :class:`Request`.
            files (Optional): Dictionary or bytes to be sent in the query string for the :class:`Request`.
            json: json to send in the body of the :class:`Request`.

        Returns:
            (status_code, body) (Tuple[bool, int, Any]): Tuple with the values:
                - status_code: The status code response.
                - body: The content of the response

        """
        request = self.prepare_request_params(
            url=self.get_api_url(endpoint=endpoint), params=params, data=data, files=files, json=json, headers=headers
        )
        self._logger_request(operation="POST", request=request)
        response: Response = requests.post(**request)
        return check_response(response=response, client_name=self.client_name, error_field=self.error_field)

    @client_catch_exception
    def put(
        self,
        endpoint: str,
        headers: Optional[Dict] = None,
        params: Optional[Dict] = None,
        data: Optional[Union[Dict, List[Tuple], bytes, IO]] = None,
        json: Optional[JsonRequest] = None,
    ) -> Tuple[int, Any]:
        """Sends a PUT request.

        Args:
            endpoint (str): Endpoint for the new :class:`Request` object.
            headers: (Optional) Dictionary of HTTP Headers to send with the :class:`Request`.
            params (Optional): Dictionary or bytes to be sent in the query string for the :class:`Request`.
            data (Optional): Dictionary, list of tuples, bytes, or file-like object to send in the body of the
                :class:`Request`.
            json: json to send in the body of the :class:`Request`.

        Returns:
            (status_code, body) (Tuple[bool, int, Any]): Tuple with the values:
                - status_code: The status code response.
                - body: The content of the response

        """
        request = self.prepare_request_params(
            url=self.get_api_url(endpoint=endpoint), params=params, data=data, json=json, headers=headers
        )
        self._logger_request(operation="PUT", request=request)
        response: Response = requests.put(**request)
        return check_response(response=response, client_name=self.client_name, error_field=self.error_field)

    @client_catch_exception
    def get(
        self,
        endpoint: str,
        headers: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Tuple[int, Any]:
        """Sends a GET request.

        Args:
            endpoint (str): Endpoint for the new :class:`Request` object.
            headers: (Optional) Dictionary of HTTP Headers to send with the :class:`Request`.
            params (Optional): Dictionary or bytes to be sent in the query string for the :class:`Request`.

        Returns:
            (status_code, body) (Tuple[bool, int, Any]): Tuple with the values:
                - status_code: The status code response.
                - body: The content of the response

        """
        request = self.prepare_request_params(url=self.get_api_url(endpoint=endpoint), params=params, headers=headers)
        self._logger_request(operation="GET", request=request)
        response: Response = requests.get(**request)
        return check_response(response=response, client_name=self.client_name, error_field=self.error_field)

    @client_catch_exception
    def delete(
        self,
        endpoint: str,
        headers: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Tuple[int, Any]:
        """Sends a DELETE request.

        Args:
            endpoint (str): Endpoint for the new :class:`Request` object.
            headers: (Optional) Dictionary of HTTP Headers to send with the :class:`Request`.
            params (Optional): Dictionary or bytes to be sent in the query string for the :class:`Request`.

        Returns:
            (status_code, body) (Tuple[bool, int, Any]): Tuple with the values:
                - status_code: The status code response.
                - body: The content of the response

        """
        request = self.prepare_request_params(url=self.get_api_url(endpoint=endpoint), params=params, headers=headers)
        self._logger_request(operation="DELETE", request=request)
        response: Response = requests.delete(**request)
        return check_response(response=response, client_name=self.client_name, error_field=self.error_field)

    @client_catch_exception
    def patch(
        self,
        endpoint: str,
        headers: Optional[Dict] = None,
        params: Optional[Dict] = None,
        data: Optional[Union[Dict, List[Tuple], bytes, IO]] = None,
        json: Optional[JsonRequest] = None,
    ) -> Tuple[int, Any]:
        """Sends a PATCH request.

        Args:
            endpoint (str): Endpoint for the new :class:`Request` object.
            headers: (Optional) Dictionary of HTTP Headers to send with the :class:`Request`.
            params (Optional): Dictionary or bytes to be sent in the query string for the :class:`Request`.
            data (Optional): Dictionary, list of tuples, bytes, or file-like object to send in the body of the
                :class:`Request`.
            json: json to send in the body of the :class:`Request`.

        Returns:
            (status_code, body) (Tuple[int, Any]): Tuple with the values:
                - status_code: The status code response.
                - body: The content of the response

        """
        request = self.prepare_request_params(
            url=self.get_api_url(endpoint=endpoint), params=params, data=data, json=json, headers=headers
        )
        self._logger_request(operation="PATCH", request=request)
        response: Response = requests.patch(**request)
        return check_response(response=response, client_name=self.client_name, error_field=self.error_field)
