from __future__ import annotations

import asyncio
import sys
from functools import partial
from typing import TYPE_CHECKING, TypedDict

if sys.version_info <= (3, 11):
    from typing_extensions import Unpack
else:
    from typing import Unpack


from .pp_primp import RClient

if TYPE_CHECKING:
    from .pp_primp import IMPERSONATE, IMPERSONATE_OS, HttpMethod, RequestParams, Response
else:

    class _Unpack:
        @staticmethod
        def __getitem__(*args, **kwargs):
            pass

    Unpack = _Unpack()
    RequestParams = TypedDict


class Client(RClient):
    """Initializes an HTTP client that can impersonate web browsers."""

    def __init__(
        self,
        auth: tuple[str, str | None] | None = None,
        auth_bearer: str | None = None,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookie_store: bool | None = True,
        referer: bool | None = True,
        proxy: str | None = None,
        timeout: float | None = 30,
        impersonate: IMPERSONATE | None = None,
        impersonate_random: str | None = None,
        impersonate_os: IMPERSONATE_OS | None = None,
        follow_redirects: bool | None = True,
        max_redirects: int | None = 20,
        verify: bool | None = True,
        ca_cert_file: str | None = None,
        https_only: bool | None = False,
        http2_only: bool | None = False,
    ):
        """
        Args:
            auth: a tuple containing the username and an optional password for basic authentication. Default is None.
            auth_bearer: a string representing the bearer token for bearer token authentication. Default is None.
            params: a map of query parameters to append to the URL. Default is None.
            headers: an optional map of HTTP headers to send with requests. Ignored if `impersonate` is set.
            cookie_store: enable a persistent cookie store. Received cookies will be preserved and included
                 in additional requests. Default is True.
            referer: automatic setting of the `Referer` header. Default is True.
            proxy: proxy URL for HTTP requests, example: "socks5://127.0.0.1:9150". Default is None.
            timeout: timeout for HTTP requests in seconds. Default is 30.
            impersonate: impersonate browser. Supported browsers:
                "chrome_100", "chrome_101", "chrome_104", "chrome_105", "chrome_106",
                "chrome_107", "chrome_108", "chrome_109", "chrome_110", "chrome_114", "chrome_116",
                "chrome_117", "chrome_118", "chrome_119", "chrome_120", "chrome_123",
                "chrome_124", "chrome_126", "chrome_127", "chrome_128", "chrome_129",
                "chrome_130", "chrome_131", "chrome_132", "chrome_133", "chrome_134", "chrome_135",
                "chrome_136", "chrome_137", "chrome_138", "chrome_139", "chrome_140", "chrome_141",
                "chrome_142", "chrome_143",
                "safari_15.3", "safari_15.5", "safari_15.6.1", "safari_16",
                "safari_16.5", "safari_17.0", "safari_17.2.1", "safari_17.4.1",
                "safari_17.5", "safari_17.6", "safari_18", "safari_18.2", "safari_18.3",
                "safari_18.3.1", "safari_18.5", "safari_26", "safari_26.1",
                "safari_ios_16.5", "safari_ios_17.2", "safari_ios_17.4.1", "safari_ios_18.1.1",
                "safari_ios_26", "safari_ipad_18", "safari_ipad_26",
                "okhttp_3.9", "okhttp_3.11", "okhttp_3.13", "okhttp_3.14", "okhttp_4.9",
                "okhttp_4.10", "okhttp_4.12", "okhttp_5",
                "edge_101", "edge_122", "edge_127", "edge_131", "edge_134", "edge_142",
                "opera_116", "opera_117", "opera_118", "opera_119",
                "firefox_109", "firefox_117", "firefox_128", "firefox_133", "firefox_135",
                "firefox_136", "firefox_139", "firefox_142", "firefox_143", "firefox_144",
                "firefox_145", "firefox_private_135", "firefox_private_136", "firefox_android_135".
                Default is None.
            impersonate_random: randomly select a version from the specified browser type.
                Supported: "chrome", "firefox", "safari", "edge", "opera", "okhttp", "random"/"all".
                Example: "chrome" will randomly select from chrome_100, chrome_101, etc.
                Default is None.
            impersonate_os: impersonate OS. Supported OS:
                "android", "ios", "linux", "macos", "windows". Default is None.
            follow_redirects: a boolean to enable or disable following redirects. Default is True.
            max_redirects: the maximum number of redirects if `follow_redirects` is True. Default is 20.
            verify: an optional boolean indicating whether to verify SSL certificates. Default is True.
            ca_cert_file: path to CA certificate store. Default is None.
            https_only: restrict the Client to be used with HTTPS only requests. Default is False.
            http2_only: if true - use only HTTP/2, if false - use only HTTP/1. Default is False.
        """
        super().__init__()

    def __enter__(self) -> Client:
        return self

    def __exit__(self, *args):
        del self

    def request(self, method: HttpMethod, url: str, **kwargs: Unpack[RequestParams]) -> Response:
        """
        Sends an HTTP request.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS)
            url: URL to request
            params: Query parameters to append to the URL
            headers: HTTP headers to send with the request
            cookies: Cookies to send with requests as the Cookie header
            content: Raw bytes to send in the request body
            data: Form data to send in the request body
            json: JSON serializable object to send in the request body
            files: Map of file fields to file paths for multipart/form-data
            auth: Tuple of (username, password) for basic authentication
            auth_bearer: Bearer token for authentication
            timeout: Request timeout in seconds

        Returns:
            Response object containing the server's response
        """
        return super().request(method=method, url=url, **kwargs)

    def get(self, url: str, **kwargs: Unpack[RequestParams]) -> Response:
        """
        Sends a GET request.

        Args:
            url: URL to request
            **kwargs: Additional request parameters (params, headers, cookies, auth, auth_bearer, timeout)

        Returns:
            Response object
        """
        return self.request(method="GET", url=url, **kwargs)

    def head(self, url: str, **kwargs: Unpack[RequestParams]) -> Response:
        """
        Sends a HEAD request.

        Args:
            url: URL to request
            **kwargs: Additional request parameters (params, headers, cookies, auth, auth_bearer, timeout)

        Returns:
            Response object
        """
        return self.request(method="HEAD", url=url, **kwargs)

    def options(self, url: str, **kwargs: Unpack[RequestParams]) -> Response:
        """
        Sends an OPTIONS request.

        Args:
            url: URL to request
            **kwargs: Additional request parameters (params, headers, cookies, auth, auth_bearer, timeout)

        Returns:
            Response object
        """
        return self.request(method="OPTIONS", url=url, **kwargs)

    def delete(self, url: str, **kwargs: Unpack[RequestParams]) -> Response:
        """
        Sends a DELETE request.

        Args:
            url: URL to request
            **kwargs: Additional request parameters (params, headers, cookies, content, data, json, files, auth, auth_bearer, timeout)

        Returns:
            Response object
        """
        return self.request(method="DELETE", url=url, **kwargs)

    def post(self, url: str, **kwargs: Unpack[RequestParams]) -> Response:
        """
        Sends a POST request.

        Args:
            url: URL to request
            **kwargs: Additional request parameters (params, headers, cookies, content, data, json, files, auth, auth_bearer, timeout)

        Returns:
            Response object
        """
        return self.request(method="POST", url=url, **kwargs)

    def put(self, url: str, **kwargs: Unpack[RequestParams]) -> Response:
        """
        Sends a PUT request.

        Args:
            url: URL to request
            **kwargs: Additional request parameters (params, headers, cookies, content, data, json, files, auth, auth_bearer, timeout)

        Returns:
            Response object
        """
        return self.request(method="PUT", url=url, **kwargs)

    def patch(self, url: str, **kwargs: Unpack[RequestParams]) -> Response:
        """
        Sends a PATCH request.

        Args:
            url: URL to request
            **kwargs: Additional request parameters (params, headers, cookies, content, data, json, files, auth, auth_bearer, timeout)

        Returns:
            Response object
        """
        return self.request(method="PATCH", url=url, **kwargs)


class AsyncClient(Client):
    """Asynchronous HTTP client that can impersonate web browsers."""

    def __init__(
        self,
        auth: tuple[str, str | None] | None = None,
        auth_bearer: str | None = None,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookie_store: bool | None = True,
        referer: bool | None = True,
        proxy: str | None = None,
        timeout: float | None = 30,
        impersonate: IMPERSONATE | None = None,
        impersonate_random: str | None = None,
        impersonate_os: IMPERSONATE_OS | None = None,
        follow_redirects: bool | None = True,
        max_redirects: int | None = 20,
        verify: bool | None = True,
        ca_cert_file: str | None = None,
        https_only: bool | None = False,
        http2_only: bool | None = False,
    ):
        """
        Initializes an asynchronous HTTP client that can impersonate web browsers.

        Args:
            auth: a tuple containing the username and an optional password for basic authentication. Default is None.
            auth_bearer: a string representing the bearer token for bearer token authentication. Default is None.
            params: a map of query parameters to append to the URL. Default is None.
            headers: an optional map of HTTP headers to send with requests. Ignored if `impersonate` is set.
            cookie_store: enable a persistent cookie store. Received cookies will be preserved and included
                 in additional requests. Default is True.
            referer: automatic setting of the `Referer` header. Default is True.
            proxy: proxy URL for HTTP requests, example: "socks5://127.0.0.1:9150". Default is None.
            timeout: timeout for HTTP requests in seconds. Default is 30.
            impersonate: impersonate browser. See IMPERSONATE type for supported browsers. Default is None.
            impersonate_random: randomly select a version from the specified browser type.
                Supported: "chrome", "firefox", "safari", "edge", "opera", "okhttp", "random"/"all".
            impersonate_os: impersonate OS. Supported: "android", "ios", "linux", "macos", "windows". Default is None.
            follow_redirects: a boolean to enable or disable following redirects. Default is True.
            max_redirects: the maximum number of redirects if `follow_redirects` is True. Default is 20.
            verify: an optional boolean indicating whether to verify SSL certificates. Default is True.
            ca_cert_file: path to CA certificate store. Default is None.
            https_only: restrict the Client to be used with HTTPS only requests. Default is False.
            http2_only: if true - use only HTTP/2, if false - use only HTTP/1. Default is False.
        """
        super().__init__(
            auth=auth,
            auth_bearer=auth_bearer,
            params=params,
            headers=headers,
            cookie_store=cookie_store,
            referer=referer,
            proxy=proxy,
            timeout=timeout,
            impersonate=impersonate,
            impersonate_random=impersonate_random,
            impersonate_os=impersonate_os,
            follow_redirects=follow_redirects,
            max_redirects=max_redirects,
            verify=verify,
            ca_cert_file=ca_cert_file,
            https_only=https_only,
            http2_only=http2_only,
        )

    async def __aenter__(self) -> AsyncClient:
        return self

    async def __aexit__(self, *args):
        del self

    async def _run_sync_asyncio(self, fn, *args, **kwargs):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(fn, *args, **kwargs))

    async def request(self, method: HttpMethod, url: str, **kwargs: Unpack[RequestParams]):  # type: ignore
        """
        Asynchronously sends an HTTP request.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS)
            url: URL to request
            params: Query parameters to append to the URL
            headers: HTTP headers to send with the request
            cookies: Cookies to send with requests as the Cookie header
            content: Raw bytes to send in the request body
            data: Form data to send in the request body
            json: JSON serializable object to send in the request body
            files: Map of file fields to file paths for multipart/form-data
            auth: Tuple of (username, password) for basic authentication
            auth_bearer: Bearer token for authentication
            timeout: Request timeout in seconds

        Returns:
            Response object containing the server's response

        Example:
            >>> async with AsyncClient() as client:
            ...     response = await client.request("GET", "https://httpbin.org/get")
            ...     print(response.status_code)
        """
        return await self._run_sync_asyncio(super().request, method=method, url=url, **kwargs)

    async def get(self, url: str, **kwargs: Unpack[RequestParams]):  # type: ignore
        """
        Asynchronously sends a GET request.

        Args:
            url: URL to request
            params: Query parameters to append to the URL
            headers: HTTP headers to send with the request
            cookies: Cookies to send with requests as the Cookie header
            auth: Tuple of (username, password) for basic authentication
            auth_bearer: Bearer token for authentication
            timeout: Request timeout in seconds

        Returns:
            Response object

        Example:
            >>> async with AsyncClient() as client:
            ...     response = await client.get("https://httpbin.org/get")
            ...     print(response.json())
        """
        return await self.request(method="GET", url=url, **kwargs)

    async def head(self, url: str, **kwargs: Unpack[RequestParams]):  # type: ignore
        """
        Asynchronously sends a HEAD request.

        Args:
            url: URL to request
            params: Query parameters to append to the URL
            headers: HTTP headers to send with the request
            cookies: Cookies to send with requests as the Cookie header
            auth: Tuple of (username, password) for basic authentication
            auth_bearer: Bearer token for authentication
            timeout: Request timeout in seconds

        Returns:
            Response object

        Example:
            >>> async with AsyncClient() as client:
            ...     response = await client.head("https://httpbin.org/get")
            ...     print(response.headers)
        """
        return await self.request(method="HEAD", url=url, **kwargs)

    async def options(self, url: str, **kwargs: Unpack[RequestParams]):  # type: ignore
        """
        Asynchronously sends an OPTIONS request.

        Args:
            url: URL to request
            params: Query parameters to append to the URL
            headers: HTTP headers to send with the request
            cookies: Cookies to send with requests as the Cookie header
            auth: Tuple of (username, password) for basic authentication
            auth_bearer: Bearer token for authentication
            timeout: Request timeout in seconds

        Returns:
            Response object

        Example:
            >>> async with AsyncClient() as client:
            ...     response = await client.options("https://httpbin.org/get")
            ...     print(response.headers)
        """
        return await self.request(method="OPTIONS", url=url, **kwargs)

    async def delete(self, url: str, **kwargs: Unpack[RequestParams]):  # type: ignore
        """
        Asynchronously sends a DELETE request.

        Args:
            url: URL to request
            params: Query parameters to append to the URL
            headers: HTTP headers to send with the request
            cookies: Cookies to send with requests as the Cookie header
            content: Raw bytes to send in the request body
            data: Form data to send in the request body
            json: JSON serializable object to send in the request body
            files: Map of file fields to file paths for multipart/form-data
            auth: Tuple of (username, password) for basic authentication
            auth_bearer: Bearer token for authentication
            timeout: Request timeout in seconds

        Returns:
            Response object

        Example:
            >>> async with AsyncClient() as client:
            ...     response = await client.delete("https://httpbin.org/delete")
            ...     print(response.status_code)
        """
        return await self.request(method="DELETE", url=url, **kwargs)

    async def post(self, url: str, **kwargs: Unpack[RequestParams]):  # type: ignore
        """
        Asynchronously sends a POST request.

        Args:
            url: URL to request
            params: Query parameters to append to the URL
            headers: HTTP headers to send with the request
            cookies: Cookies to send with requests as the Cookie header
            content: Raw bytes to send in the request body
            data: Form data to send in the request body
            json: JSON serializable object to send in the request body
            files: Map of file fields to file paths for multipart/form-data
            auth: Tuple of (username, password) for basic authentication
            auth_bearer: Bearer token for authentication
            timeout: Request timeout in seconds

        Returns:
            Response object

        Example:
            >>> async with AsyncClient() as client:
            ...     response = await client.post(
            ...         "https://httpbin.org/post",
            ...         json={"key": "value"}
            ...     )
            ...     print(response.json())
        """
        return await self.request(method="POST", url=url, **kwargs)

    async def put(self, url: str, **kwargs: Unpack[RequestParams]):  # type: ignore
        """
        Asynchronously sends a PUT request.

        Args:
            url: URL to request
            params: Query parameters to append to the URL
            headers: HTTP headers to send with the request
            cookies: Cookies to send with requests as the Cookie header
            content: Raw bytes to send in the request body
            data: Form data to send in the request body
            json: JSON serializable object to send in the request body
            files: Map of file fields to file paths for multipart/form-data
            auth: Tuple of (username, password) for basic authentication
            auth_bearer: Bearer token for authentication
            timeout: Request timeout in seconds

        Returns:
            Response object

        Example:
            >>> async with AsyncClient() as client:
            ...     response = await client.put(
            ...         "https://httpbin.org/put",
            ...         json={"key": "value"}
            ...     )
            ...     print(response.status_code)
        """
        return await self.request(method="PUT", url=url, **kwargs)

    async def patch(self, url: str, **kwargs: Unpack[RequestParams]):  # type: ignore
        """
        Asynchronously sends a PATCH request.

        Args:
            url: URL to request
            params: Query parameters to append to the URL
            headers: HTTP headers to send with the request
            cookies: Cookies to send with requests as the Cookie header
            content: Raw bytes to send in the request body
            data: Form data to send in the request body
            json: JSON serializable object to send in the request body
            files: Map of file fields to file paths for multipart/form-data
            auth: Tuple of (username, password) for basic authentication
            auth_bearer: Bearer token for authentication
            timeout: Request timeout in seconds

        Returns:
            Response object

        Example:
            >>> async with AsyncClient() as client:
            ...     response = await client.patch(
            ...         "https://httpbin.org/patch",
            ...         json={"key": "value"}
            ...     )
            ...     print(response.status_code)
        """
        return await self.request(method="PATCH", url=url, **kwargs)


def request(
    method: HttpMethod,
    url: str,
    impersonate: IMPERSONATE | None = None,
    impersonate_os: IMPERSONATE_OS | None = None,
    verify: bool | None = True,
    ca_cert_file: str | None = None,
    **kwargs: Unpack[RequestParams],
):
    """
    Args:
        method: the HTTP method to use (e.g., "GET", "POST").
        url: the URL to which the request will be made.
        impersonate: impersonate browser. Supported browsers:
            "chrome_100", "chrome_101", "chrome_104", "chrome_105", "chrome_106",
            "chrome_107", "chrome_108", "chrome_109", "chrome_110", "chrome_114", "chrome_116",
            "chrome_117", "chrome_118", "chrome_119", "chrome_120", "chrome_123",
            "chrome_124", "chrome_126", "chrome_127", "chrome_128", "chrome_129",
            "chrome_130", "chrome_131", "chrome_132", "chrome_133", "chrome_134", "chrome_135",
            "chrome_136", "chrome_137", "chrome_138", "chrome_139", "chrome_140", "chrome_141",
            "chrome_142", "chrome_143",
            "safari_15.3", "safari_15.5", "safari_15.6.1", "safari_16",
            "safari_16.5", "safari_17.0", "safari_17.2.1", "safari_17.4.1",
            "safari_17.5", "safari_17.6", "safari_18", "safari_18.2", "safari_18.3",
            "safari_18.3.1", "safari_18.5", "safari_26", "safari_26.1",
            "safari_ios_16.5", "safari_ios_17.2", "safari_ios_17.4.1", "safari_ios_18.1.1",
            "safari_ios_26", "safari_ipad_18", "safari_ipad_26",
            "okhttp_3.9", "okhttp_3.11", "okhttp_3.13", "okhttp_3.14", "okhttp_4.9",
            "okhttp_4.10", "okhttp_4.12", "okhttp_5",
            "edge_101", "edge_122", "edge_127", "edge_131", "edge_134", "edge_142",
            "opera_116", "opera_117", "opera_118", "opera_119",
            "firefox_109", "firefox_117", "firefox_128", "firefox_133", "firefox_135",
            "firefox_136", "firefox_139", "firefox_142", "firefox_143", "firefox_144",
            "firefox_145", "firefox_private_135", "firefox_private_136", "firefox_android_135".
            Default is None.
        impersonate_os: impersonate OS. Supported OS:
            "android", "ios", "linux", "macos", "windows". Default is None.
        verify: an optional boolean indicating whether to verify SSL certificates. Default is True.
        ca_cert_file: path to CA certificate store. Default is None.
        auth: a tuple containing the username and an optional password for basic authentication. Default is None.
        auth_bearer: a string representing the bearer token for bearer token authentication. Default is None.
        params: a map of query parameters to append to the URL. Default is None.
        headers: an optional map of HTTP headers to send with requests. If `impersonate` is set, this will be ignored.
        cookies: an optional map of cookies to send with requests as the `Cookie` header.
        timeout: the timeout for the request in seconds. Default is 30.
        content: the content to send in the request body as bytes. Default is None.
        data: the form data to send in the request body. Default is None.
        json: a JSON serializable object to send in the request body. Default is None.
        files: a map of file fields to file paths to be sent as multipart/form-data. Default is None.
    """
    with Client(
        impersonate=impersonate,
        impersonate_os=impersonate_os,
        verify=verify,
        ca_cert_file=ca_cert_file,
    ) as client:
        return client.request(method, url, **kwargs)


def get(url: str, **kwargs: Unpack[RequestParams]):
    return request(method="GET", url=url, **kwargs)


def head(url: str, **kwargs: Unpack[RequestParams]):
    return request(method="HEAD", url=url, **kwargs)


def options(url: str, **kwargs: Unpack[RequestParams]):
    return request(method="OPTIONS", url=url, **kwargs)


def delete(url: str, **kwargs: Unpack[RequestParams]):
    return request(method="DELETE", url=url, **kwargs)


def post(url: str, **kwargs: Unpack[RequestParams]):
    return request(method="POST", url=url, **kwargs)


def put(url: str, **kwargs: Unpack[RequestParams]):
    return request(method="PUT", url=url, **kwargs)


def patch(url: str, **kwargs: Unpack[RequestParams]):
    return request(method="PATCH", url=url, **kwargs)
