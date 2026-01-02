use pyo3::prelude::*;

mod utils;

use utils::{freeze, FrozenDict, LRUCache};

/// TinyDB Rust implementation
///
/// TinyDB is a tiny, document oriented database optimized for your happiness :)
///
/// This is a Rust-based reimplementation of TinyDB that provides high performance
/// and memory safety while maintaining compatibility with the original TinyDB API.
#[pymodule]
fn _tinydb_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<LRUCache>()?;
    m.add_class::<FrozenDict>()?;
    m.add_function(wrap_pyfunction!(freeze, m)?)?;
    Ok(())
}
