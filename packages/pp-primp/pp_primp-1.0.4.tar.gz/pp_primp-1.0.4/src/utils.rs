use std::sync::LazyLock;

use rquest::tls::{CertStore, CertStoreBuilder};
use tracing;

/// Loads custom CA certificates from env var PRIMP_CA_BUNDLE
/// Returns None if no custom cert path is specified (will use rquest default webpki-roots)
pub fn load_ca_certs() -> Option<&'static CertStore> {
    static CERT_STORE: LazyLock<Option<CertStore>> = LazyLock::new(|| {
        // Only load custom certs if explicitly specified
        if let Ok(ca_cert_path) = std::env::var("PRIMP_CA_BUNDLE").or(std::env::var("CA_CERT_FILE"))
        {
            tracing::info!("Loading custom CA certificates from: {}", ca_cert_path);
            match load_custom_certs(&ca_cert_path) {
                Ok(store) => {
                    tracing::info!("Successfully loaded custom CA certificates");
                    Some(store)
                }
                Err(err) => {
                    tracing::error!("Failed to load custom CA certs: {:?}", err);
                    None
                }
            }
        } else {
            // No custom certs specified, let rquest use its default webpki-roots
            tracing::debug!("Using default webpki-roots for certificate verification");
            None
        }
    });

    CERT_STORE.as_ref()
}

fn load_custom_certs(ca_cert_path: &str) -> Result<CertStore, anyhow::Error> {
    let cert_file = std::fs::read(ca_cert_path)?;
    let cert_store = CertStoreBuilder::default()
        .add_pem_certs(&[&cert_file[..]])
        .build()?;
    Ok(cert_store)
}

#[cfg(test)]
mod load_ca_certs_tests {
    use super::*;
    use std::env;
    use std::fs;
    use std::path::Path;

    #[test]
    fn test_load_ca_certs_with_env_var() {
        // Create a temporary file with a CA certificate
        let ca_cert_path = Path::new("test_ca_cert.pem");
        let ca_cert = "-----BEGIN CERTIFICATE-----
MIIDdTCCAl2gAwIBAgIVAMIIujU9wQIBADANBgkqhkiG9w0BAQUFADBGMQswCQYD
VQQGEwJVUzETMBEGA1UECAwKQ2FsaWZvcm5pYTEWMBQGA1UEBwwNTW91bnRhaW4g
Q29sbGVjdGlvbjEgMB4GA1UECgwXUG9zdGdyZXMgQ29uc3VsdGF0aW9uczEhMB8G
A1UECwwYUG9zdGdyZXMgQ29uc3VsdGF0aW9uczEhMB8GA1UEAwwYUG9zdGdyZXMg
Q29uc3VsdGF0aW9uczEiMCAGCSqGSIb3DQEJARYTcGVyc29uYWwtZW1haWwuY29t
MIIDdTCCAl2gAwIBAgIVAMIIujU9wQIBADANBgkqhkiG9w0BAQUFADBGMQswCQYD
VQQGEwJVUzETMBEGA1UECAwKQ2FsaWZvcm5pYTEWMBQGA1UEBwwNTW91bnRhaW4g
Q29sbGVjdGlvbjEgMB4GA1UECgwXUG9zdGdyZXMgQ29uc3VsdGF0aW9uczEhMB8G
A1UECwwYUG9zdGdyZXMgQ29uc3VsdGF0aW9uczEhMB8GA1UEAwwYUG9zdGdyZXMg
Q29uc3VsdGF0aW9uczEiMCAGCSqGSIb3DQEJARYTcGVyc29uYWwtZW1haWwuY29t
-----END CERTIFICATE-----";
        fs::write(ca_cert_path, ca_cert).unwrap();

        // Set the environment variable
        env::set_var("PRIMP_CA_BUNDLE", ca_cert_path);

        // Call the function
        let result = load_ca_certs();

        // Check the result
        assert!(result.is_some());

        // Clean up
        fs::remove_file(ca_cert_path).unwrap();
    }

    #[test]
    fn test_load_ca_certs_without_env_var() {
        // Call the function
        let result = load_ca_certs();

        // Check the result
        assert!(result.is_some());
    }
}
