use base64::Engine as _;
use base64::engine::general_purpose::STANDARD;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use std::collections::HashMap;
use std::sync::Mutex;

// Global asset store: optional HashMap from name -> bytes
static ASSET_STORE: Mutex<Option<HashMap<String, Vec<u8>>>> = Mutex::new(None);

fn init_store() {
    let mut s = ASSET_STORE.lock().unwrap();
    if s.is_none() {
        *s = Some(HashMap::new());
    }
}

fn store_put(name: String, bytes: Vec<u8>) {
    init_store();
    let mut s = ASSET_STORE.lock().unwrap();
    if let Some(ref mut map) = *s {
        map.insert(name, bytes);
    }
}

fn store_get(name: &str) -> Option<Vec<u8>> {
    let s = ASSET_STORE.lock().unwrap();
    if let Some(ref map) = *s {
        map.get(name).cloned()
    } else {
        None
    }
}

fn store_get_by_basename(basename: &str) -> Option<Vec<u8>> {
    let s = ASSET_STORE.lock().unwrap();
    if let Some(ref map) = *s {
        for (k, v) in map.iter() {
            if k.ends_with(basename) || k == basename {
                return Some(v.clone());
            }
        }
    }
    None
}

fn guess_mime_from_name(name: &str) -> &str {
    let name = name.to_lowercase();
    if name.ends_with(".png") {
        "image/png"
    } else if name.ends_with(".jpg") || name.ends_with(".jpeg") {
        "image/jpeg"
    } else if name.ends_with(".gif") {
        "image/gif"
    } else if name.ends_with(".svg") {
        "image/svg+xml"
    } else if name.ends_with(".webp") {
        "image/webp"
    } else if name.ends_with(".bmp") {
        "image/bmp"
    } else {
        "application/octet-stream"
    }
}

fn bytes_to_data_uri(name: &str, bytes: &[u8]) -> String {
    let mime = guess_mime_from_name(name);
    let b64 = STANDARD.encode(bytes);
    format!("data:{};base64,{}", mime, b64)
}

/// Python-facing AssetCatalog for registering raw assets from Python.
#[pyclass]
pub struct AssetCatalog;

#[pymethods]
impl AssetCatalog {
    #[new]
    fn new() -> Self {
        init_store();
        AssetCatalog {}
    }

    /// Add an asset by name and raw bytes.
    #[pyo3(text_signature = "($self, name, data)")]
    fn add<'py>(&self, _py: Python<'py>, name: String, data: &Bound<'py, PyAny>) -> PyResult<()> {
        let bytes: Vec<u8> = data
            .extract()
            .map_err(|_| PyValueError::new_err("data must be bytes"))?;

        store_put(name, bytes);
        Ok(())
    }

    /// Return an asset data URI if present, else None.
    #[pyo3(text_signature = "($self, name)")]
    fn get_data_uri(&self, name: String) -> Option<String> {
        if let Some(b) = store_get(&name) {
            Some(bytes_to_data_uri(&name, &b))
        } else if let Some(b) = store_get_by_basename(&name) {
            Some(bytes_to_data_uri(&name, &b))
        } else {
            None
        }
    }
}

// Helpers for other Rust code to consult the store
pub fn get_asset_data_uri(name: &str) -> Option<String> {
    if let Some(b) = store_get(name) {
        Some(bytes_to_data_uri(name, &b))
    } else if let Some(b) = store_get_by_basename(name) {
        Some(bytes_to_data_uri(name, &b))
    } else {
        None
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashMap;

    #[test]
    fn test_guess_mime_from_name() {
        assert_eq!(guess_mime_from_name("foo.png"), "image/png");
        assert_eq!(guess_mime_from_name("foo.JPG"), "image/jpeg");
        assert_eq!(guess_mime_from_name("foo.svg"), "image/svg+xml");
        assert_eq!(guess_mime_from_name("foo.webp"), "image/webp");
        assert_eq!(guess_mime_from_name("foo.unknown"), "application/octet-stream");
    }

    #[test]
    fn test_bytes_to_data_uri_content() {
        let b = b"abc";
        let s = bytes_to_data_uri("file.txt", b);
        assert!(s.starts_with("data:application/octet-stream;base64,"));
        // base64 for 'abc' is 'YWJj'
        assert!(s.ends_with("YWJj"));
    }

    #[test]
    fn test_store_and_get_asset_data_uri() {
        // reset the global store
        {
            let mut s = ASSET_STORE.lock().unwrap();
            *s = Some(HashMap::new());
        }

        let name = "images/logo.png".to_string();
        let bytes = vec![137u8, 80, 78, 71, 13, 10, 26, 10]; // PNG header bytes
        store_put(name.clone(), bytes.clone());

        // lookup by full name
        let uri = get_asset_data_uri("images/logo.png");
        assert!(uri.is_some());
        let uri = uri.unwrap();
        assert!(uri.starts_with("data:image/png;base64,"));

        // lookup by basename
        let uri2 = get_asset_data_uri("logo.png");
        assert!(uri2.is_some());
    }
}
