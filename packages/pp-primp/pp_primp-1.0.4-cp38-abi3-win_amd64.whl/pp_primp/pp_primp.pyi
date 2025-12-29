from __future__ import annotations

import sys
from typing import Any, Iterator, Literal, TypedDict

if sys.version_info <= (3, 11):
    from typing_extensions import Unpack
else:
    from typing import Unpack

HttpMethod = Literal["GET", "HEAD", "OPTIONS", "DELETE", "POST", "PUT", "PATCH"]
IMPERSONATE = Literal[
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
        "safari_18.3.1", "safari_18.5", "safari_26", "safari_26.1","safari_26.2",
        "safari_ios_16.5", "safari_ios_17.2", "safari_ios_17.4.1", "safari_ios_18.1.1",
        "safari_ios_26", "safari_ipad_18", "safari_ipad_26","safari_ipad_26.2","safari_ios_26.2",
        "okhttp_3.9", "okhttp_3.11", "okhttp_3.13", "okhttp_3.14", "okhttp_4.9",
        "okhttp_4.10", "okhttp_4.12", "okhttp_5",
        "edge_101", "edge_122", "edge_127", "edge_131", "edge_134", "edge_142",
        "opera_116", "opera_117", "opera_118", "opera_119",
        "firefox_109", "firefox_117", "firefox_128", "firefox_133", "firefox_135",
        "firefox_136", "firefox_139", "firefox_142", "firefox_143", "firefox_144",
        "firefox_145", "firefox_private_135", "firefox_private_136", "firefox_android_135",
        "random",
    ]  # fmt: skip
IMPERSONATE_RANDOM = Literal["chrome", "firefox", "safari", "edge", "opera", "okhttp", "random", "all"]
IMPERSONATE_OS = Literal["android", "ios", "linux", "macos", "windows", "random"]

class RequestParams(TypedDict, total=False):
    auth: tuple[str, str | None] | None
    auth_bearer: str | None
    params: dict[str, str] | None
    headers: dict[str, str] | None
    cookies: dict[str, str] | None
    timeout: float | None
    read_timeout: float | None
    content: bytes | None
    data: dict[str, Any] | None
    json: Any | None
    files: dict[str, str] | None
    proxy: str | None
    impersonate: IMPERSONATE | None
    impersonate_random: IMPERSONATE_RANDOM | None
    impersonate_os: IMPERSONATE_OS | None
    verify: bool | None
    ca_cert_file: str | None
    follow_redirects: bool | None
    max_redirects: int | None
    https_only: bool | None
    http2_only: bool | None

class ClientRequestParams(RequestParams):
    pass

class Response:
    @property
    def content(self) -> bytes: ...
    @property
    def cookies(self) -> dict[str, str]: ...
    @property
    def headers(self) -> dict[str, str]: ...
    @property
    def status_code(self) -> int: ...
    @property
    def url(self) -> str: ...
    @property
    def encoding(self) -> str: ...
    @property
    def text(self) -> str: ...
    def json(self) -> Any: ...
    def stream(self) -> Iterator[bytes]: ...
    @property
    def text_markdown(self) -> str: ...
    @property
    def text_plain(self) -> str: ...
    @property
    def text_rich(self) -> str: ...

class RClient:
    """HTTP client that can impersonate web browsers."""

    def __init__(
        self,
        auth: tuple[str, str | None] | None = None,
        auth_bearer: str | None = None,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        cookie_store: bool | None = True,
        referer: bool | None = True,
        proxy: str | None = None,
        impersonate: IMPERSONATE | None = None,
        impersonate_random: IMPERSONATE_RANDOM | None = None,
        impersonate_os: IMPERSONATE_OS | None = None,
        follow_redirects: bool | None = True,
        max_redirects: int | None = 20,
        verify: bool | None = True,
        ca_cert_file: str | None = None,
        https_only: bool | None = False,
        http2_only: bool | None = False,
    ): ...

    @property
    def headers(self) -> dict[str, str]:
        """Get current default headers (excluding cookies)."""
        ...

    @headers.setter
    def headers(self, headers: dict[str, str]) -> None:
        """Set default headers. This will rebuild the client with new headers."""
        ...

    def headers_update(self, headers: dict[str, str]) -> None:
        """Update existing headers. This will rebuild the client."""
        ...

    def get_cookies(self, url: str) -> dict[str, str]:
        """Get cookies for a specific URL."""
        ...

    def set_cookies(self, url: str, cookies: dict[str, str]) -> None:
        """Set cookies for a specific URL."""
        ...

    @property
    def proxy(self) -> str | None:
        """Get current proxy setting."""
        ...

    @proxy.setter
    def proxy(self, proxy: str) -> None:
        """Set proxy. This will rebuild the client with new proxy settings."""
        ...

    @property
    def impersonate(self) -> str | None:
        """Get current browser impersonation setting."""
        ...

    @impersonate.setter
    def impersonate(self, impersonate: IMPERSONATE) -> None:
        """Set browser impersonation. This will rebuild the client."""
        ...

    @property
    def impersonate_os(self) -> str | None:
        """Get current OS impersonation setting."""
        ...

    @impersonate_os.setter
    def impersonate_os(self, impersonate: IMPERSONATE_OS) -> None:
        """Set OS impersonation. This will rebuild the client."""
        ...

    def request(
        self,
        method: HttpMethod,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        content: bytes | None = None,
        data: dict[str, Any] | None = None,
        json: Any | None = None,
        files: dict[str, str] | None = None,
        auth: tuple[str, str | None] | None = None,
        auth_bearer: str | None = None,
        timeout: float | None = None,
        read_timeout: float | None = None,
        proxy: str | None = None,
        impersonate: IMPERSONATE | None = None,
        impersonate_random: IMPERSONATE_RANDOM | None = None,
        impersonate_os: IMPERSONATE_OS | None = None,
        verify: bool | None = None,
        ca_cert_file: str | None = None,
        follow_redirects: bool | None = None,
        max_redirects: int | None = None,
        https_only: bool | None = None,
        http2_only: bool | None = None,
    ) -> Response:
        """Send an HTTP request."""
        ...

    def get(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        auth: tuple[str, str | None] | None = None,
        auth_bearer: str | None = None,
        timeout: float | None = None,
        read_timeout: float | None = None,
        proxy: str | None = None,
        impersonate: IMPERSONATE | None = None,
        impersonate_random: IMPERSONATE_RANDOM | None = None,
        impersonate_os: IMPERSONATE_OS | None = None,
        verify: bool | None = None,
        ca_cert_file: str | None = None,
        follow_redirects: bool | None = None,
        max_redirects: int | None = None,
        https_only: bool | None = None,
        http2_only: bool | None = None,
    ) -> Response:
        """Send a GET request."""
        ...

    def head(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        auth: tuple[str, str | None] | None = None,
        auth_bearer: str | None = None,
        timeout: float | None = None,
        read_timeout: float | None = None,
        proxy: str | None = None,
        impersonate: IMPERSONATE | None = None,
        impersonate_random: IMPERSONATE_RANDOM | None = None,
        impersonate_os: IMPERSONATE_OS | None = None,
        verify: bool | None = None,
        ca_cert_file: str | None = None,
        follow_redirects: bool | None = None,
        max_redirects: int | None = None,
        https_only: bool | None = None,
        http2_only: bool | None = None,
    ) -> Response:
        """Send a HEAD request."""
        ...

    def options(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        auth: tuple[str, str | None] | None = None,
        auth_bearer: str | None = None,
        timeout: float | None = None,
        read_timeout: float | None = None,
        proxy: str | None = None,
        impersonate: IMPERSONATE | None = None,
        impersonate_random: IMPERSONATE_RANDOM | None = None,
        impersonate_os: IMPERSONATE_OS | None = None,
        verify: bool | None = None,
        ca_cert_file: str | None = None,
        follow_redirects: bool | None = None,
        max_redirects: int | None = None,
        https_only: bool | None = None,
        http2_only: bool | None = None,
    ) -> Response:
        """Send an OPTIONS request."""
        ...

    def delete(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        content: bytes | None = None,
        data: dict[str, Any] | None = None,
        json: Any | None = None,
        files: dict[str, str] | None = None,
        auth: tuple[str, str | None] | None = None,
        auth_bearer: str | None = None,
        timeout: float | None = None,
        read_timeout: float | None = None,
        proxy: str | None = None,
        impersonate: IMPERSONATE | None = None,
        impersonate_random: IMPERSONATE_RANDOM | None = None,
        impersonate_os: IMPERSONATE_OS | None = None,
        verify: bool | None = None,
        ca_cert_file: str | None = None,
        follow_redirects: bool | None = None,
        max_redirects: int | None = None,
        https_only: bool | None = None,
        http2_only: bool | None = None,
    ) -> Response:
        """Send a DELETE request."""
        ...

    def post(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        content: bytes | None = None,
        data: dict[str, Any] | None = None,
        json: Any | None = None,
        files: dict[str, str] | None = None,
        auth: tuple[str, str | None] | None = None,
        auth_bearer: str | None = None,
        timeout: float | None = None,
        read_timeout: float | None = None,
        proxy: str | None = None,
        impersonate: IMPERSONATE | None = None,
        impersonate_random: IMPERSONATE_RANDOM | None = None,
        impersonate_os: IMPERSONATE_OS | None = None,
        verify: bool | None = None,
        ca_cert_file: str | None = None,
        follow_redirects: bool | None = None,
        max_redirects: int | None = None,
        https_only: bool | None = None,
        http2_only: bool | None = None,
    ) -> Response:
        """Send a POST request."""
        ...

    def put(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        content: bytes | None = None,
        data: dict[str, Any] | None = None,
        json: Any | None = None,
        files: dict[str, str] | None = None,
        auth: tuple[str, str | None] | None = None,
        auth_bearer: str | None = None,
        timeout: float | None = None,
        read_timeout: float | None = None,
        proxy: str | None = None,
        impersonate: IMPERSONATE | None = None,
        impersonate_random: IMPERSONATE_RANDOM | None = None,
        impersonate_os: IMPERSONATE_OS | None = None,
        verify: bool | None = None,
        ca_cert_file: str | None = None,
        follow_redirects: bool | None = None,
        max_redirects: int | None = None,
        https_only: bool | None = None,
        http2_only: bool | None = None,
    ) -> Response:
        """Send a PUT request."""
        ...

    def patch(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        content: bytes | None = None,
        data: dict[str, Any] | None = None,
        json: Any | None = None,
        files: dict[str, str] | None = None,
        auth: tuple[str, str | None] | None = None,
        auth_bearer: str | None = None,
        timeout: float | None = None,
        read_timeout: float | None = None,
        proxy: str | None = None,
        impersonate: IMPERSONATE | None = None,
        impersonate_random: IMPERSONATE_RANDOM | None = None,
        impersonate_os: IMPERSONATE_OS | None = None,
        verify: bool | None = None,
        ca_cert_file: str | None = None,
        follow_redirects: bool | None = None,
        max_redirects: int | None = None,
        https_only: bool | None = None,
        http2_only: bool | None = None,
    ) -> Response:
        """Send a PATCH request."""
        ...

class Client(RClient):
    """HTTP client that can impersonate web browsers."""

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
        impersonate_random: IMPERSONATE_RANDOM | None = None,
        impersonate_os: IMPERSONATE_OS | None = None,
        follow_redirects: bool | None = True,
        max_redirects: int | None = 20,
        verify: bool | None = True,
        ca_cert_file: str | None = None,
        https_only: bool | None = False,
        http2_only: bool | None = False,
    ): ...

    def __enter__(self) -> Client: ...
    def __exit__(self, *args) -> None: ...

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
        impersonate_random: IMPERSONATE_RANDOM | None = None,
        impersonate_os: IMPERSONATE_OS | None = None,
        follow_redirects: bool | None = True,
        max_redirects: int | None = 20,
        verify: bool | None = True,
        ca_cert_file: str | None = None,
        https_only: bool | None = False,
        http2_only: bool | None = False,
    ): ...

    async def __aenter__(self) -> AsyncClient: ...
    async def __aexit__(self, *args) -> None: ...

    async def request(
        self,
        method: HttpMethod,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        content: bytes | None = None,
        data: dict[str, Any] | None = None,
        json: Any | None = None,
        files: dict[str, str] | None = None,
        auth: tuple[str, str | None] | None = None,
        auth_bearer: str | None = None,
        timeout: float | None = None,
        read_timeout: float | None = None,
        proxy: str | None = None,
        impersonate: IMPERSONATE | None = None,
        impersonate_random: IMPERSONATE_RANDOM | None = None,
        impersonate_os: IMPERSONATE_OS | None = None,
        verify: bool | None = None,
        ca_cert_file: str | None = None,
        follow_redirects: bool | None = None,
        max_redirects: int | None = None,
        https_only: bool | None = None,
        http2_only: bool | None = None,
    ) -> Response:
        """Asynchronously send an HTTP request."""
        ...

    async def get(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        auth: tuple[str, str | None] | None = None,
        auth_bearer: str | None = None,
        timeout: float | None = None,
        read_timeout: float | None = None,
        proxy: str | None = None,
        impersonate: IMPERSONATE | None = None,
        impersonate_random: IMPERSONATE_RANDOM | None = None,
        impersonate_os: IMPERSONATE_OS | None = None,
        verify: bool | None = None,
        ca_cert_file: str | None = None,
        follow_redirects: bool | None = None,
        max_redirects: int | None = None,
        https_only: bool | None = None,
        http2_only: bool | None = None,
    ) -> Response:
        """Asynchronously send a GET request."""
        ...

    async def head(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        auth: tuple[str, str | None] | None = None,
        auth_bearer: str | None = None,
        timeout: float | None = None,
        read_timeout: float | None = None,
        proxy: str | None = None,
        impersonate: IMPERSONATE | None = None,
        impersonate_random: IMPERSONATE_RANDOM | None = None,
        impersonate_os: IMPERSONATE_OS | None = None,
        verify: bool | None = None,
        ca_cert_file: str | None = None,
        follow_redirects: bool | None = None,
        max_redirects: int | None = None,
        https_only: bool | None = None,
        http2_only: bool | None = None,
    ) -> Response:
        """Asynchronously send a HEAD request."""
        ...

    async def options(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        auth: tuple[str, str | None] | None = None,
        auth_bearer: str | None = None,
        timeout: float | None = None,
        read_timeout: float | None = None,
        proxy: str | None = None,
        impersonate: IMPERSONATE | None = None,
        impersonate_random: IMPERSONATE_RANDOM | None = None,
        impersonate_os: IMPERSONATE_OS | None = None,
        verify: bool | None = None,
        ca_cert_file: str | None = None,
        follow_redirects: bool | None = None,
        max_redirects: int | None = None,
        https_only: bool | None = None,
        http2_only: bool | None = None,
    ) -> Response:
        """Asynchronously send an OPTIONS request."""
        ...

    async def delete(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        content: bytes | None = None,
        data: dict[str, Any] | None = None,
        json: Any | None = None,
        files: dict[str, str] | None = None,
        auth: tuple[str, str | None] | None = None,
        auth_bearer: str | None = None,
        timeout: float | None = None,
        read_timeout: float | None = None,
        proxy: str | None = None,
        impersonate: IMPERSONATE | None = None,
        impersonate_random: IMPERSONATE_RANDOM | None = None,
        impersonate_os: IMPERSONATE_OS | None = None,
        verify: bool | None = None,
        ca_cert_file: str | None = None,
        follow_redirects: bool | None = None,
        max_redirects: int | None = None,
        https_only: bool | None = None,
        http2_only: bool | None = None,
    ) -> Response:
        """Asynchronously send a DELETE request."""
        ...

    async def post(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        content: bytes | None = None,
        data: dict[str, Any] | None = None,
        json: Any | None = None,
        files: dict[str, str] | None = None,
        auth: tuple[str, str | None] | None = None,
        auth_bearer: str | None = None,
        timeout: float | None = None,
        read_timeout: float | None = None,
        proxy: str | None = None,
        impersonate: IMPERSONATE | None = None,
        impersonate_random: IMPERSONATE_RANDOM | None = None,
        impersonate_os: IMPERSONATE_OS | None = None,
        verify: bool | None = None,
        ca_cert_file: str | None = None,
        follow_redirects: bool | None = None,
        max_redirects: int | None = None,
        https_only: bool | None = None,
        http2_only: bool | None = None,
    ) -> Response:
        """Asynchronously send a POST request."""
        ...

    async def put(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        content: bytes | None = None,
        data: dict[str, Any] | None = None,
        json: Any | None = None,
        files: dict[str, str] | None = None,
        auth: tuple[str, str | None] | None = None,
        auth_bearer: str | None = None,
        timeout: float | None = None,
        read_timeout: float | None = None,
        proxy: str | None = None,
        impersonate: IMPERSONATE | None = None,
        impersonate_random: IMPERSONATE_RANDOM | None = None,
        impersonate_os: IMPERSONATE_OS | None = None,
        verify: bool | None = None,
        ca_cert_file: str | None = None,
        follow_redirects: bool | None = None,
        max_redirects: int | None = None,
        https_only: bool | None = None,
        http2_only: bool | None = None,
    ) -> Response:
        """Asynchronously send a PUT request."""
        ...

    async def patch(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        content: bytes | None = None,
        data: dict[str, Any] | None = None,
        json: Any | None = None,
        files: dict[str, str] | None = None,
        auth: tuple[str, str | None] | None = None,
        auth_bearer: str | None = None,
        timeout: float | None = None,
        read_timeout: float | None = None,
        proxy: str | None = None,
        impersonate: IMPERSONATE | None = None,
        impersonate_random: IMPERSONATE_RANDOM | None = None,
        impersonate_os: IMPERSONATE_OS | None = None,
        verify: bool | None = None,
        ca_cert_file: str | None = None,
        follow_redirects: bool | None = None,
        max_redirects: int | None = None,
        https_only: bool | None = None,
        http2_only: bool | None = None,
    ) -> Response:
        """Asynchronously send a PATCH request."""
        ...

def request(
    method: HttpMethod,
    url: str,
    *,
    impersonate: IMPERSONATE | None = None,
    impersonate_random: IMPERSONATE_RANDOM | None = None,
    impersonate_os: IMPERSONATE_OS | None = None,
    verify: bool | None = True,
    ca_cert_file: str | None = None,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    cookies: dict[str, str] | None = None,
    content: bytes | None = None,
    data: dict[str, Any] | None = None,
    json: Any | None = None,
    files: dict[str, str] | None = None,
    auth: tuple[str, str | None] | None = None,
    auth_bearer: str | None = None,
    timeout: float | None = None,
    read_timeout: float | None = None,
    proxy: str | None = None,
    follow_redirects: bool | None = None,
    max_redirects: int | None = None,
    https_only: bool | None = None,
    http2_only: bool | None = None,
) -> Response:
    """Send an HTTP request using a temporary client."""
    ...

def get(
    url: str,
    *,
    impersonate: IMPERSONATE | None = None,
    impersonate_random: IMPERSONATE_RANDOM | None = None,
    impersonate_os: IMPERSONATE_OS | None = None,
    verify: bool | None = True,
    ca_cert_file: str | None = None,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    cookies: dict[str, str] | None = None,
    auth: tuple[str, str | None] | None = None,
    auth_bearer: str | None = None,
    timeout: float | None = None,
    read_timeout: float | None = None,
    proxy: str | None = None,
    follow_redirects: bool | None = None,
    max_redirects: int | None = None,
    https_only: bool | None = None,
    http2_only: bool | None = None,
) -> Response:
    """Send a GET request using a temporary client."""
    ...

def head(
    url: str,
    *,
    impersonate: IMPERSONATE | None = None,
    impersonate_random: IMPERSONATE_RANDOM | None = None,
    impersonate_os: IMPERSONATE_OS | None = None,
    verify: bool | None = True,
    ca_cert_file: str | None = None,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    cookies: dict[str, str] | None = None,
    auth: tuple[str, str | None] | None = None,
    auth_bearer: str | None = None,
    timeout: float | None = None,
    read_timeout: float | None = None,
    proxy: str | None = None,
    follow_redirects: bool | None = None,
    max_redirects: int | None = None,
    https_only: bool | None = None,
    http2_only: bool | None = None,
) -> Response:
    """Send a HEAD request using a temporary client."""
    ...

def options(
    url: str,
    *,
    impersonate: IMPERSONATE | None = None,
    impersonate_random: IMPERSONATE_RANDOM | None = None,
    impersonate_os: IMPERSONATE_OS | None = None,
    verify: bool | None = True,
    ca_cert_file: str | None = None,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    cookies: dict[str, str] | None = None,
    auth: tuple[str, str | None] | None = None,
    auth_bearer: str | None = None,
    timeout: float | None = None,
    read_timeout: float | None = None,
    proxy: str | None = None,
    follow_redirects: bool | None = None,
    max_redirects: int | None = None,
    https_only: bool | None = None,
    http2_only: bool | None = None,
) -> Response:
    """Send an OPTIONS request using a temporary client."""
    ...

def delete(
    url: str,
    *,
    impersonate: IMPERSONATE | None = None,
    impersonate_random: IMPERSONATE_RANDOM | None = None,
    impersonate_os: IMPERSONATE_OS | None = None,
    verify: bool | None = True,
    ca_cert_file: str | None = None,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    cookies: dict[str, str] | None = None,
    content: bytes | None = None,
    data: dict[str, Any] | None = None,
    json: Any | None = None,
    files: dict[str, str] | None = None,
    auth: tuple[str, str | None] | None = None,
    auth_bearer: str | None = None,
    timeout: float | None = None,
    read_timeout: float | None = None,
    proxy: str | None = None,
    follow_redirects: bool | None = None,
    max_redirects: int | None = None,
    https_only: bool | None = None,
    http2_only: bool | None = None,
) -> Response:
    """Send a DELETE request using a temporary client."""
    ...

def post(
    url: str,
    *,
    impersonate: IMPERSONATE | None = None,
    impersonate_random: IMPERSONATE_RANDOM | None = None,
    impersonate_os: IMPERSONATE_OS | None = None,
    verify: bool | None = True,
    ca_cert_file: str | None = None,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    cookies: dict[str, str] | None = None,
    content: bytes | None = None,
    data: dict[str, Any] | None = None,
    json: Any | None = None,
    files: dict[str, str] | None = None,
    auth: tuple[str, str | None] | None = None,
    auth_bearer: str | None = None,
    timeout: float | None = None,
    read_timeout: float | None = None,
    proxy: str | None = None,
    follow_redirects: bool | None = None,
    max_redirects: int | None = None,
    https_only: bool | None = None,
    http2_only: bool | None = None,
) -> Response:
    """Send a POST request using a temporary client."""
    ...

def put(
    url: str,
    *,
    impersonate: IMPERSONATE | None = None,
    impersonate_random: IMPERSONATE_RANDOM | None = None,
    impersonate_os: IMPERSONATE_OS | None = None,
    verify: bool | None = True,
    ca_cert_file: str | None = None,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    cookies: dict[str, str] | None = None,
    content: bytes | None = None,
    data: dict[str, Any] | None = None,
    json: Any | None = None,
    files: dict[str, str] | None = None,
    auth: tuple[str, str | None] | None = None,
    auth_bearer: str | None = None,
    timeout: float | None = None,
    read_timeout: float | None = None,
    proxy: str | None = None,
    follow_redirects: bool | None = None,
    max_redirects: int | None = None,
    https_only: bool | None = None,
    http2_only: bool | None = None,
) -> Response:
    """Send a PUT request using a temporary client."""
    ...

def patch(
    url: str,
    *,
    impersonate: IMPERSONATE | None = None,
    impersonate_random: IMPERSONATE_RANDOM | None = None,
    impersonate_os: IMPERSONATE_OS | None = None,
    verify: bool | None = True,
    ca_cert_file: str | None = None,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    cookies: dict[str, str] | None = None,
    content: bytes | None = None,
    data: dict[str, Any] | None = None,
    json: Any | None = None,
    files: dict[str, str] | None = None,
    auth: tuple[str, str | None] | None = None,
    auth_bearer: str | None = None,
    timeout: float | None = None,
    read_timeout: float | None = None,
    proxy: str | None = None,
    follow_redirects: bool | None = None,
    max_redirects: int | None = None,
    https_only: bool | None = None,
    http2_only: bool | None = None,
) -> Response:
    """Send a PATCH request using a temporary client."""
    ...
