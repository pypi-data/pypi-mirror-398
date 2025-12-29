#![allow(clippy::too_many_arguments)]
use std::sync::{Arc, LazyLock, Mutex};
use std::time::Duration;

use anyhow::Result;
use foldhash::fast::RandomState;
use indexmap::IndexMap;
use pyo3::prelude::*;
use pythonize::depythonize;
use rquest::{
    header::{HeaderValue, COOKIE},
    multipart,
    redirect::Policy,
    Body, EmulationProviderFactory, Method,
};
use rquest_util::{Emulation, EmulationOS, EmulationOption};
use serde_json::Value;
use tokio::{
    fs::File,
    runtime::{self, Runtime},
};
use tokio_util::codec::{BytesCodec, FramedRead};
use tracing;

mod response;
use response::Response;

mod traits;
use traits::HeadersTraits;

mod utils;
use utils::load_ca_certs;

mod random_impersonate;
use random_impersonate::random_impersonate;

type IndexMapSSR = IndexMap<String, String, RandomState>;

// Tokio global one-thread runtime
static RUNTIME: LazyLock<Runtime> = LazyLock::new(|| {
    runtime::Builder::new_current_thread()
        .enable_all()
        .build()
        .unwrap()
});

#[pyclass(subclass)]
/// HTTP client that can impersonate web browsers.
pub struct RClient {
    client: Arc<Mutex<rquest::Client>>,
    #[pyo3(get, set)]
    auth: Option<(String, Option<String>)>,
    #[pyo3(get, set)]
    auth_bearer: Option<String>,
    #[pyo3(get, set)]
    params: Option<IndexMapSSR>,
    #[pyo3(get, set)]
    proxy: Option<String>,
    #[pyo3(get, set)]
    timeout: Option<f64>,
    #[pyo3(get)]
    impersonate: Option<String>,
    #[pyo3(get)]
    impersonate_os: Option<String>,
    // Store configuration for runtime rebuilding
    headers: Option<IndexMapSSR>,
    cookie_store: Option<bool>,
    referer: Option<bool>,
    follow_redirects: Option<bool>,
    max_redirects: Option<usize>,
    verify: Option<bool>,
    ca_cert_file: Option<String>,
    https_only: Option<bool>,
    http2_only: Option<bool>,
}

#[pymethods]
impl RClient {
    /// Initializes an HTTP client that can impersonate web browsers.
    ///
    /// This function creates a new HTTP client instance that can impersonate various web browsers.
    /// It allows for customization of headers, proxy settings, timeout, impersonation type, SSL certificate verification,
    /// and HTTP version preferences.
    ///
    /// # Arguments
    ///
    /// * `auth` - A tuple containing the username and an optional password for basic authentication. Default is None.
    /// * `auth_bearer` - A string representing the bearer token for bearer token authentication. Default is None.
    /// * `params` - A map of query parameters to append to the URL. Default is None.
    /// * `headers` - An optional map of HTTP headers to send with requests. If `impersonate` is set, this will be ignored.
    /// * `cookie_store` - Enable a persistent cookie store. Received cookies will be preserved and included
    ///         in additional requests. Default is `true`.
    /// * `referer` - Enable or disable automatic setting of the `Referer` header. Default is `true`.
    /// * `proxy` - An optional proxy URL for HTTP requests.
    /// * `timeout` - An optional timeout for HTTP requests in seconds.
    /// * `impersonate` - An optional entity to impersonate. Supported browsers and versions include Chrome, Safari, OkHttp, and Edge.
    /// * `impersonate_random` - Randomly select a version for the specified browser type (e.g., "chrome", "firefox", "safari").
    /// * `impersonate_os` - An optional entity to impersonate OS. Supported OS: android, ios, linux, macos, windows.
    /// * `follow_redirects` - A boolean to enable or disable following redirects. Default is `true`.
    /// * `max_redirects` - The maximum number of redirects to follow. Default is 20. Applies if `follow_redirects` is `true`.
    /// * `verify` - An optional boolean indicating whether to verify SSL certificates. Default is `true`.
    /// * `ca_cert_file` - Path to CA certificate store. Default is None.
    /// * `https_only` - Restrict the Client to be used with HTTPS only requests. Default is `false`.
    /// * `http2_only` - If true - use only HTTP/2, if false - use only HTTP/1. Default is `false`.
    ///
    /// # Example
    ///
    /// ```
    /// from primp import Client
    ///
    /// client = Client(
    ///     auth=("name", "password"),
    ///     params={"p1k": "p1v", "p2k": "p2v"},
    ///     headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"},
    ///     cookie_store=False,
    ///     referer=False,
    ///     proxy="http://127.0.0.1:8080",
    ///     timeout=10,
    ///     impersonate="chrome_123",
    ///     impersonate_os="windows",
    ///     follow_redirects=True,
    ///     max_redirects=1,
    ///     verify=True,
    ///     ca_cert_file="/cert/cacert.pem",
    ///     https_only=True,
    ///     http2_only=True,
    /// )
    /// ```
    #[new]
    #[pyo3(signature = (auth=None, auth_bearer=None, params=None, headers=None, cookie_store=true,
        referer=true, proxy=None, timeout=None, impersonate=None, impersonate_random=None, impersonate_os=None, follow_redirects=true,
        max_redirects=20, verify=true, ca_cert_file=None, https_only=false, http2_only=false))]
    fn new(
        auth: Option<(String, Option<String>)>,
        auth_bearer: Option<String>,
        params: Option<IndexMapSSR>,
        headers: Option<IndexMapSSR>,
        cookie_store: Option<bool>,
        referer: Option<bool>,
        proxy: Option<String>,
        timeout: Option<f64>,
        impersonate: Option<String>,
        impersonate_random: Option<String>,
        impersonate_os: Option<String>,
        follow_redirects: Option<bool>,
        max_redirects: Option<usize>,
        verify: Option<bool>,
        ca_cert_file: Option<String>,
        https_only: Option<bool>,
        http2_only: Option<bool>,
    ) -> Result<Self> {
        // Client builder
        let mut client_builder = rquest::Client::builder();

        // Emulation (browser impersonation)
        // Handle impersonate_random first
        let impersonate = if let Some(random_type) = impersonate_random {
            Some(random_impersonate(&random_type)?)
        } else {
            impersonate
        };

        if let Some(impersonate) = &impersonate {
            let emulation = impersonate.parse::<Emulation>()
                .map_err(|e| anyhow::anyhow!(e))?;
            let emulation_os = if let Some(impersonate_os) = &impersonate_os {
                impersonate_os.parse::<EmulationOS>()
                    .map_err(|e| anyhow::anyhow!(e))?
            } else {
                EmulationOS::default()
            };
            let emulation_provider = EmulationOption::builder()
                .emulation(emulation)
                .emulation_os(emulation_os)
                .build()
                .emulation();
            client_builder = client_builder.emulation(emulation_provider);
        }

        // Headers
        if let Some(ref headers) = headers {
            let headers_headermap = headers.to_headermap();
            client_builder = client_builder.default_headers(headers_headermap);
        };

        // Cookie_store
        if cookie_store.unwrap_or(true) {
            client_builder = client_builder.cookie_store(true);
        }

        // Referer
        if referer.unwrap_or(true) {
            client_builder = client_builder.referer(true);
        }

        // Proxy
        let proxy = proxy.or_else(|| std::env::var("PRIMP_PROXY").ok());
        if let Some(proxy) = &proxy {
            client_builder = client_builder.proxy(rquest::Proxy::all(proxy)?);
        }

        // Timeout
        if let Some(seconds) = timeout {
            client_builder = client_builder.timeout(Duration::from_secs_f64(seconds));
        }

        // Redirects
        if follow_redirects.unwrap_or(true) {
            client_builder = client_builder.redirect(Policy::limited(max_redirects.unwrap_or(20)));
        } else {
            client_builder = client_builder.redirect(Policy::none());
        }

        // Ca_cert_file. Set env var before calling load_ca_certs
        if let Some(ca_bundle_path) = &ca_cert_file {
            std::env::set_var("PRIMP_CA_BUNDLE", ca_bundle_path);
        }

        // Verify
        if !verify.unwrap_or(true) {
            // Disable certificate verification
            client_builder = client_builder.cert_verification(false);
        } else if let Some(cert_store) = load_ca_certs() {
            // Only set custom cert store if user provided one
            // Otherwise rquest will use its default webpki-roots
            client_builder = client_builder.cert_store(cert_store.clone());
        }
        // If verify=true and no custom cert_store, rquest uses default webpki-roots

        // Https_only
        if let Some(true) = https_only {
            client_builder = client_builder.https_only(true);
        }

        // Http2_only
        if let Some(true) = http2_only {
            client_builder = client_builder.http2_only();
        }

        let client = Arc::new(Mutex::new(client_builder.build()?));

        Ok(RClient {
            client,
            auth,
            auth_bearer,
            params,
            proxy,
            timeout,
            impersonate,
            impersonate_os,
            headers,
            cookie_store,
            referer,
            follow_redirects,
            max_redirects,
            verify,
            ca_cert_file,
            https_only,
            http2_only,
        })
    }

    /// Internal method to rebuild the client with current configuration
    fn rebuild_client(&mut self) -> Result<()> {
        // Client builder
        let mut client_builder = rquest::Client::builder();

        // Emulation (browser impersonation)
        if let Some(impersonate) = &self.impersonate {
            let emulation = impersonate.parse::<Emulation>()
                .map_err(|e| anyhow::anyhow!(e))?;
            let emulation_os = if let Some(impersonate_os) = &self.impersonate_os {
                impersonate_os.parse::<EmulationOS>()
                    .map_err(|e| anyhow::anyhow!(e))?
            } else {
                EmulationOS::default()
            };
            let emulation_provider = EmulationOption::builder()
                .emulation(emulation)
                .emulation_os(emulation_os)
                .build()
                .emulation();
            client_builder = client_builder.emulation(emulation_provider);
        }

        // Headers
        if let Some(headers) = &self.headers {
            let headers_headermap = headers.to_headermap();
            client_builder = client_builder.default_headers(headers_headermap);
        };

        // Cookie_store
        if self.cookie_store.unwrap_or(true) {
            client_builder = client_builder.cookie_store(true);
        }

        // Referer
        if self.referer.unwrap_or(true) {
            client_builder = client_builder.referer(true);
        }

        // Proxy
        if let Some(ref proxy) = self.proxy {
            client_builder = client_builder.proxy(rquest::Proxy::all(proxy)?);
        } else if let Ok(proxy) = std::env::var("PRIMP_PROXY") {
            client_builder = client_builder.proxy(rquest::Proxy::all(&proxy)?);
        }

        // Timeout
        if let Some(seconds) = self.timeout {
            client_builder = client_builder.timeout(Duration::from_secs_f64(seconds));
        }

        // Redirects
        if self.follow_redirects.unwrap_or(true) {
            client_builder = client_builder.redirect(Policy::limited(self.max_redirects.unwrap_or(20)));
        } else {
            client_builder = client_builder.redirect(Policy::none());
        }

        // Ca_cert_file. Set env var before calling load_ca_certs
        if let Some(ca_bundle_path) = &self.ca_cert_file {
            std::env::set_var("PRIMP_CA_BUNDLE", ca_bundle_path);
        }

        // Verify
        if !self.verify.unwrap_or(true) {
            // Disable certificate verification
            client_builder = client_builder.cert_verification(false);
        } else if let Some(cert_store) = load_ca_certs() {
            // Only set custom cert store if user provided one
            // Otherwise rquest will use its default webpki-roots
            client_builder = client_builder.cert_store(cert_store.clone());
        }
        // If verify=true and no custom cert_store, rquest uses default webpki-roots

        // Https_only
        if let Some(true) = self.https_only {
            client_builder = client_builder.https_only(true);
        }

        // Http2_only
        if let Some(true) = self.http2_only {
            client_builder = client_builder.http2_only();
        }

        let new_client = client_builder.build()?;
        *self.client.lock().unwrap() = new_client;

        Ok(())
    }

    #[getter]
    pub fn get_headers(&self) -> Result<IndexMapSSR> {
        let client = self.client.lock().unwrap();
        let mut headers = client.headers().clone();
        headers.remove(COOKIE);
        Ok(headers.to_indexmap())
    }

    #[setter]
    pub fn set_headers(&mut self, new_headers: Option<IndexMapSSR>) -> Result<()> {
        self.headers = new_headers;
        self.rebuild_client()
    }

    pub fn headers_update(&mut self, new_headers: Option<IndexMapSSR>) -> Result<()> {
        if let Some(new_headers) = new_headers {
            if let Some(existing_headers) = &mut self.headers {
                existing_headers.extend(new_headers);
            } else {
                self.headers = Some(new_headers);
            }
        }
        self.rebuild_client()
    }

    #[getter]
    pub fn get_proxy(&self) -> Result<Option<String>> {
        Ok(self.proxy.to_owned())
    }

    #[setter]
    pub fn set_proxy(&mut self, proxy: String) -> Result<()> {
        self.proxy = Some(proxy);
        self.rebuild_client()
    }

    #[setter]
    pub fn set_impersonate(&mut self, impersonate: String) -> Result<()> {
        self.impersonate = Some(impersonate);
        self.rebuild_client()
    }

    #[setter]
    pub fn set_impersonate_os(&mut self, impersonate_os: String) -> Result<()> {
        self.impersonate_os = Some(impersonate_os);
        self.rebuild_client()
    }

    #[pyo3(signature = (url))]
    fn get_cookies(&self, url: &str) -> Result<IndexMapSSR> {
        let url = rquest::Url::parse(url).expect("Error parsing URL: {:url}");
        let client = self.client.lock().unwrap();
        let cookie = client.get_cookies(&url).expect("No cookies found");
        let cookie_str = cookie.to_str()?;
        let mut cookie_map = IndexMap::with_capacity_and_hasher(10, RandomState::default());
        for cookie in cookie_str.split(';') {
            let mut parts = cookie.splitn(2, '=');
            if let (Some(key), Some(value)) = (parts.next(), parts.next()) {
                cookie_map.insert(key.trim().to_string(), value.trim().to_string());
            }
        }
        Ok(cookie_map)
    }

    #[pyo3(signature = (url, cookies))]
    fn set_cookies(&self, url: &str, cookies: Option<IndexMapSSR>) -> Result<()> {
        let url = rquest::Url::parse(url).expect("Error parsing URL: {:url}");
        if let Some(cookies) = cookies {
            let header_values: Vec<HeaderValue> = cookies
                .iter()
                .filter_map(|(key, value)| {
                    HeaderValue::from_str(&format!("{}={}", key, value)).ok()
                })
                .collect();
            let client = self.client.lock().unwrap();
            client.set_cookies(&url, header_values);
        }
        Ok(())
    }

    /// Constructs an HTTP request with the given method, URL, and optionally sets a timeout, headers, and query parameters.
    /// Sends the request and returns a `Response` object containing the server's response.
    ///
    /// # Arguments
    ///
    /// * `method` - The HTTP method to use (e.g., "GET", "POST").
    /// * `url` - The URL to which the request will be made.
    /// * `params` - A map of query parameters to append to the URL. Default is None.
    /// * `headers` - A map of HTTP headers to send with the request. Default is None.
    /// * `cookies` - An optional map of cookies to send with requests as the `Cookie` header.
    /// * `content` - The content to send in the request body as bytes. Default is None.
    /// * `data` - The form data to send in the request body. Default is None.
    /// * `json` -  A JSON serializable object to send in the request body. Default is None.
    /// * `files` - A map of file fields to file paths to be sent as multipart/form-data. Default is None.
    /// * `auth` - A tuple containing the username and an optional password for basic authentication. Default is None.
    /// * `auth_bearer` - A string representing the bearer token for bearer token authentication. Default is None.
    /// * `timeout` - The timeout for the request in seconds. Default is 30.
    /// * `read_timeout` - The read timeout for the request in seconds. Default is None.
    /// * `proxy` - Proxy URL for this specific request. Default is None.
    /// * `impersonate` - Browser to impersonate for this specific request. Default is None.
    /// * `impersonate_random` - Randomly select a browser version (e.g., "chrome", "firefox"). Default is None.
    /// * `impersonate_os` - OS to impersonate for this specific request. Default is None.
    /// * `verify` - Whether to verify SSL certificates for this specific request. Default is None.
    /// * `ca_cert_file` - Path to CA certificate file for this specific request. Default is None.
    /// * `follow_redirects` - Whether to follow redirects for this specific request. Default is None.
    /// * `max_redirects` - Maximum number of redirects for this specific request. Default is None.
    /// * `https_only` - Restrict to HTTPS only for this specific request. Default is None.
    /// * `http2_only` - Use HTTP/2 only for this specific request. Default is None.
    ///
    /// # Returns
    ///
    /// * `Response` - A response object containing the server's response to the request.
    ///
    /// # Errors
    ///
    /// * `PyException` - If there is an error making the request.
    #[pyo3(signature = (method, url, params=None, headers=None, cookies=None, content=None,
        data=None, json=None, files=None, auth=None, auth_bearer=None, timeout=None,
        read_timeout=None, proxy=None, impersonate=None, impersonate_random=None, impersonate_os=None, verify=None,
        ca_cert_file=None, follow_redirects=None, max_redirects=None, https_only=None, http2_only=None))]
    fn request(
        &self,
        py: Python,
        method: &str,
        url: &str,
        params: Option<IndexMapSSR>,
        headers: Option<IndexMapSSR>,
        cookies: Option<IndexMapSSR>,
        content: Option<Vec<u8>>,
        data: Option<&Bound<'_, PyAny>>,
        json: Option<&Bound<'_, PyAny>>,
        files: Option<IndexMap<String, String>>,
        auth: Option<(String, Option<String>)>,
        auth_bearer: Option<String>,
        timeout: Option<f64>,
        read_timeout: Option<f64>,
        proxy: Option<String>,
        impersonate: Option<String>,
        impersonate_random: Option<String>,
        impersonate_os: Option<String>,
        verify: Option<bool>,
        ca_cert_file: Option<String>,
        follow_redirects: Option<bool>,
        max_redirects: Option<usize>,
        https_only: Option<bool>,
        http2_only: Option<bool>,
    ) -> Result<Response> {
        // Check if we need to create a temporary client with different settings
        let need_temp_client = impersonate.is_some()
            || impersonate_random.is_some()
            || impersonate_os.is_some()
            || verify.is_some()
            || ca_cert_file.is_some()
            || https_only.is_some()
            || http2_only.is_some();

        let client = if need_temp_client {
            // Create temporary client with request-specific settings
            let mut client_builder = rquest::Client::builder();

            // Handle impersonate_random first
            let impersonate = if let Some(random_type) = impersonate_random {
                Some(random_impersonate(&random_type)?)
            } else {
                impersonate
            };

            // Use request-specific impersonate or fall back to self
            let req_impersonate = impersonate.or_else(|| self.impersonate.clone());
            if let Some(imp) = &req_impersonate {
                let emulation = imp.parse::<Emulation>()
                    .map_err(|e| anyhow::anyhow!(e))?;
                let req_impersonate_os = impersonate_os.or_else(|| self.impersonate_os.clone());
                let emulation_os = if let Some(imp_os) = &req_impersonate_os {
                    imp_os.parse::<EmulationOS>()
                        .map_err(|e| anyhow::anyhow!(e))?
                } else {
                    EmulationOS::default()
                };
                let emulation_provider = EmulationOption::builder()
                    .emulation(emulation)
                    .emulation_os(emulation_os)
                    .build()
                    .emulation();
                client_builder = client_builder.emulation(emulation_provider);
            }

            // Apply other client-level settings from self
            if let Some(headers) = &self.headers {
                client_builder = client_builder.default_headers(headers.to_headermap());
            }

            if self.cookie_store.unwrap_or(true) {
                client_builder = client_builder.cookie_store(true);
            }

            if self.referer.unwrap_or(true) {
                client_builder = client_builder.referer(true);
            }

            // Use request-specific proxy or fall back to self
            let req_proxy = proxy.clone().or_else(|| self.proxy.clone())
                .or_else(|| std::env::var("PRIMP_PROXY").ok());
            if let Some(prx) = &req_proxy {
                client_builder = client_builder.proxy(rquest::Proxy::all(prx)?);
            }

            // Use request-specific timeout or fall back to self
            let req_timeout = timeout.or(self.timeout);
            if let Some(seconds) = req_timeout {
                client_builder = client_builder.timeout(Duration::from_secs_f64(seconds));
            }

            // Use request-specific verify or fall back to self
            let req_verify = verify.or(self.verify);
            if let Some(req_ca_cert_file) = &ca_cert_file {
                std::env::set_var("PRIMP_CA_BUNDLE", req_ca_cert_file);
            }
            if !req_verify.unwrap_or(true) {
                client_builder = client_builder.cert_verification(false);
            } else if let Some(cert_store) = load_ca_certs() {
                client_builder = client_builder.cert_store(cert_store.clone());
            }

            // Use request-specific https_only or fall back to self
            let req_https_only = https_only.or(self.https_only);
            if req_https_only.unwrap_or(false) {
                client_builder = client_builder.https_only(true);
            }

            // Use request-specific http2_only or fall back to self
            let req_http2_only = http2_only.or(self.http2_only);
            if req_http2_only.unwrap_or(false) {
                client_builder = client_builder.http2_only();
            }

            // Use request-specific redirect settings or fall back to self
            let req_follow_redirects = follow_redirects.or(self.follow_redirects);
            let req_max_redirects = max_redirects.or(self.max_redirects);
            if req_follow_redirects.unwrap_or(true) {
                client_builder = client_builder.redirect(Policy::limited(req_max_redirects.unwrap_or(20)));
            } else {
                client_builder = client_builder.redirect(Policy::none());
            }

            Arc::new(Mutex::new(client_builder.build()?))
        } else {
            Arc::clone(&self.client)
        };

        let method = Method::from_bytes(method.as_bytes())?;
        let is_post_put_patch = matches!(method, Method::POST | Method::PUT | Method::PATCH);
        let params = params.or_else(|| self.params.clone());

        // Handle data parameter - support bytes, dict/json types, and strings
        let mut data_bytes: Option<Vec<u8>> = None;
        let mut data_value: Option<Value> = None;
        if let Some(data_param) = data {
            // Check if data is bytes
            if let Ok(bytes) = data_param.extract::<Vec<u8>>() {
                data_bytes = Some(bytes);
            }
            // Check if data is a string (send as-is, don't parse)
            else if let Ok(string_data) = data_param.extract::<String>() {
                // Treat string as raw bytes, don't try to parse as JSON
                data_bytes = Some(string_data.into_bytes());
            }
            // Otherwise try to deserialize as JSON value (dict, list, etc.)
            else {
                data_value = Some(depythonize(data_param)?);
            }
        }

        let json_value: Option<Value> = json.map(depythonize).transpose()?;
        let auth = auth.or(self.auth.clone());
        let auth_bearer = auth_bearer.or(self.auth_bearer.clone());

        // Determine effective timeout and read_timeout
        let effective_timeout = if need_temp_client {
            timeout.or(self.timeout)
        } else {
            timeout
        };
        let effective_read_timeout = read_timeout;

        // Determine effective proxy (only for non-temp clients)
        let effective_proxy = if !need_temp_client {
            proxy.or_else(|| self.proxy.clone())
        } else {
            None
        };

        // Determine effective redirect settings (only for non-temp clients)
        let effective_follow_redirects = if !need_temp_client {
            follow_redirects
        } else {
            None
        };
        let effective_max_redirects = if !need_temp_client {
            max_redirects
        } else {
            None
        };

        // Cookies
        if let Some(cookies) = cookies {
            let url = rquest::Url::parse(url)?;
            let cookie_values: Vec<HeaderValue> = cookies
                .iter()
                .filter_map(|(key, value)| {
                    let cookie_string = format!("{}={}", key, value.to_string());
                    HeaderValue::from_str(&cookie_string).ok()
                })
                .collect();
            let client = client.lock().unwrap();
            client.set_cookies(&url, cookie_values);
        }

        let future = async {
            // Create request builder
            let mut request_builder = client.lock().unwrap().request(method, url);

            // Params
            if let Some(params) = params {
                request_builder = request_builder.query(&params);
            }

            // Check if user explicitly set Content-Type to application/json
            let headers_headermap = headers.as_ref().map(|h| h.to_headermap());
            let content_type_is_json = headers_headermap.as_ref()
                .and_then(|h| h.get("content-type"))
                .and_then(|v| v.to_str().ok())
                .map(|s| s.to_lowercase().contains("application/json"))
                .unwrap_or(false);

            // Headers
            if let Some(headers) = headers {
                request_builder = request_builder.headers(headers.to_headermap());
            }

            // Only if method POST || PUT || PATCH
            if is_post_put_patch {
                // Content (raw bytes from content parameter)
                if let Some(content) = content {
                    request_builder = request_builder.body(content);
                }
                // Data as bytes (raw bytes from data parameter)
                else if let Some(data_bytes) = data_bytes {
                    request_builder = request_builder.body(data_bytes);
                }
                // Smart handling of data and json parameters (dict/json types)
                // If user explicitly set Content-Type to application/json, both data and json use JSON encoding
                else if content_type_is_json {
                    // When Content-Type is application/json, prefer json parameter, fallback to data
                    if let Some(json_data) = json_value {
                        request_builder = request_builder.json(&json_data);
                    } else if let Some(form_data) = data_value {
                        // Even though it's data parameter, serialize as JSON when Content-Type is application/json
                        request_builder = request_builder.json(&form_data);
                    }
                } else {
                    // No explicit Content-Type: application/json header
                    // json parameter -> JSON encoding
                    // data parameter -> form encoding (or JSON if contains complex types)
                    if let Some(json_data) = json_value {
                        request_builder = request_builder.json(&json_data);
                    } else if let Some(form_data) = data_value {
                        // Check if data contains complex types (arrays/objects) that can't be form-encoded
                        let has_complex_type = form_data.as_object().map_or(false, |obj| {
                            obj.values().any(|v| v.is_array() || v.is_object())
                        });

                        if has_complex_type {
                            // Use JSON encoding for complex types
                            request_builder = request_builder.json(&form_data);
                        } else {
                            // Use form encoding for simple key-value pairs
                            request_builder = request_builder.form(&form_data);
                        }
                    }
                }

                // Files
                if let Some(files) = files {
                    let mut form = multipart::Form::new();
                    for (file_name, file_path) in files {
                        let file = File::open(file_path).await?;
                        let stream = FramedRead::new(file, BytesCodec::new());
                        let file_body = Body::wrap_stream(stream);
                        let part = multipart::Part::stream(file_body).file_name(file_name.clone());
                        form = form.part(file_name, part);
                    }
                    request_builder = request_builder.multipart(form);
                }
            }

            // Auth
            if let Some((username, password)) = auth {
                request_builder = request_builder.basic_auth(username, password);
            } else if let Some(token) = auth_bearer {
                request_builder = request_builder.bearer_auth(token);
            }

            // Timeout (request-level override)
            if let Some(seconds) = effective_timeout {
                request_builder = request_builder.timeout(Duration::from_secs_f64(seconds));
            }

            // Read timeout (request-level)
            if let Some(seconds) = effective_read_timeout {
                request_builder = request_builder.read_timeout(Duration::from_secs_f64(seconds));
            }

            // Proxy (request-level override for non-temp clients)
            if let Some(prx) = effective_proxy {
                request_builder = request_builder.proxy(rquest::Proxy::all(&prx)?);
            }

            // Redirect policy (request-level override for non-temp clients)
            if let Some(follow) = effective_follow_redirects {
                if follow {
                    let max = effective_max_redirects.unwrap_or(20);
                    request_builder = request_builder.redirect(Policy::limited(max));
                } else {
                    request_builder = request_builder.redirect(Policy::none());
                }
            }

            // Send the request and await the response
            let resp: rquest::Response = request_builder.send().await?;
            let url: String = resp.url().to_string();
            let status_code = resp.status().as_u16();

            tracing::info!("response: {} {}", url, status_code);
            Ok((resp, url, status_code))
        };

        // Execute an async future, releasing the Python GIL for concurrency.
        // Use Tokio global runtime to block on the future.
        let response: Result<(rquest::Response, String, u16)> =
            py.allow_threads(|| RUNTIME.block_on(future));
        let result = response?;
        let resp = http::Response::from(result.0);
        let url = result.1;
        let status_code = result.2;
        Ok(Response {
            resp,
            _content: None,
            _encoding: None,
            _headers: None,
            _cookies: None,
            url,
            status_code,
        })
    }
}

#[pymodule]
fn pp_primp(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    pyo3_log::init();

    m.add_class::<RClient>()?;
    Ok(())
}
