// Utility functions and data structures for TinyDB.
//
// This module contains utility functions and helper structures used throughout
// the TinyDB implementation, such as LRU cache and object freezing utilities.

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyFrozenSet, PyList, PySet, PyTuple};
use std::collections::HashMap;
use std::collections::VecDeque;

/// Wrapper for Python objects to use as HashMap keys
/// Uses Python's hash() function to get a hashable key
struct PyObjectKey {
    obj: Py<PyAny>,
    hash: i64,
}

impl PyObjectKey {
    fn new(py: Python<'_>, obj: Py<PyAny>) -> PyResult<Self> {
        let hash = obj.bind(py).hash()? as i64;
        Ok(PyObjectKey { obj, hash })
    }

    fn clone_ref(&self, py: Python<'_>) -> Self {
        PyObjectKey {
            obj: self.obj.clone_ref(py),
            hash: self.hash,
        }
    }
}

impl Clone for PyObjectKey {
    fn clone(&self) -> Self {
        Python::attach(|py| self.clone_ref(py))
    }
}

impl PartialEq for PyObjectKey {
    fn eq(&self, other: &Self) -> bool {
        Python::attach(|py| self.obj.bind(py).eq(other.obj.bind(py)).unwrap_or(false))
    }
}

impl Eq for PyObjectKey {}

impl std::hash::Hash for PyObjectKey {
    fn hash<H: std::hash::Hasher>(&self, state: &mut H) {
        self.hash.hash(state);
    }
}

/// LRU Cache implementation compatible with Python's TinyDB utils.LRUCache
///
/// A least-recently used (LRU) cache with a fixed cache size.
/// This class acts as a dictionary but has a limited size. If the number of
/// entries in the cache exceeds the cache size, the least-recently accessed
/// entry will be discarded.
#[pyclass(module = "_tinydb_core")]
pub struct LRUCache {
    cache: HashMap<PyObjectKey, Py<PyAny>>,
    order: VecDeque<PyObjectKey>,
    capacity: Option<usize>,
}

#[pymethods]
impl LRUCache {
    /// Create a new LRUCache with optional capacity.
    /// If capacity is None, the cache has unlimited size.
    #[new]
    #[pyo3(signature = (capacity = None))]
    fn new(_py: Python<'_>, capacity: Option<usize>) -> PyResult<Self> {
        Ok(LRUCache {
            cache: HashMap::new(),
            order: VecDeque::new(),
            capacity,
        })
    }

    /// Get the list of keys in LRU order (least recently used first)
    #[getter]
    fn lru(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        let keys: Vec<Py<PyAny>> = self.order.iter().map(|k| k.obj.clone_ref(py)).collect();
        Ok(PyList::new(py, keys)?.unbind().into())
    }

    /// Get the current length of the cache
    #[getter]
    fn length(&self) -> usize {
        self.cache.len()
    }

    /// Clear all entries from the cache
    fn clear(&mut self) {
        self.cache.clear();
        self.order.clear();
    }

    /// Get a value from the cache, returning default if key is not found.
    /// Accessing a key moves it to the most recently used position.
    #[pyo3(signature = (key, default = None))]
    fn get(
        &mut self,
        py: Python<'_>,
        key: Py<PyAny>,
        default: Option<Py<PyAny>>,
    ) -> PyResult<Py<PyAny>> {
        let key_wrapper = PyObjectKey::new(py, key.clone_ref(py))?;

        if let Some(value) = self.cache.get(&key_wrapper) {
            // Move to end (most recently used)
            if let Some(pos) = self.order.iter().position(|k| k == &key_wrapper) {
                self.order.remove(pos);
            }
            self.order.push_back(key_wrapper.clone_ref(py));
            Ok(value.clone_ref(py))
        } else {
            Ok(default.unwrap_or_else(|| py.None()))
        }
    }

    /// Set a key-value pair in the cache.
    /// If the cache is full, the least recently used item will be removed.
    fn set(&mut self, py: Python<'_>, key: Py<PyAny>, value: Py<PyAny>) -> PyResult<()> {
        let key_wrapper = PyObjectKey::new(py, key.clone_ref(py))?;

        if self.cache.contains_key(&key_wrapper) {
            // Update existing key and move to end
            self.cache.insert(key_wrapper.clone(), value);
            if let Some(pos) = self.order.iter().position(|k| k == &key_wrapper) {
                self.order.remove(pos);
            }
            self.order.push_back(key_wrapper);
        } else {
            // Add new key
            self.cache.insert(key_wrapper.clone(), value);
            self.order.push_back(key_wrapper);

            // Check if we need to remove old items
            if let Some(cap) = self.capacity {
                while self.cache.len() > cap {
                    if let Some(oldest_key) = self.order.pop_front() {
                        self.cache.remove(&oldest_key);
                    } else {
                        break;
                    }
                }
            }
        }
        Ok(())
    }

    /// Dictionary protocol: __getitem__
    fn __getitem__(&mut self, py: Python<'_>, key: Py<PyAny>) -> PyResult<Py<PyAny>> {
        let result = self.get(py, key.clone_ref(py), None)?;
        if result.is_none(py) {
            Err(PyErr::new::<pyo3::exceptions::PyKeyError, _>(
                "Key not found",
            ))
        } else {
            Ok(result)
        }
    }

    /// Dictionary protocol: __setitem__
    fn __setitem__(&mut self, py: Python<'_>, key: Py<PyAny>, value: Py<PyAny>) -> PyResult<()> {
        self.set(py, key, value)
    }

    /// Dictionary protocol: __delitem__
    fn __delitem__(&mut self, py: Python<'_>, key: Py<PyAny>) -> PyResult<()> {
        let key_wrapper = PyObjectKey::new(py, key)?;

        if self.cache.remove(&key_wrapper).is_some() {
            if let Some(pos) = self.order.iter().position(|k| k == &key_wrapper) {
                self.order.remove(pos);
            }
            Ok(())
        } else {
            Err(PyErr::new::<pyo3::exceptions::PyKeyError, _>(
                "Key not found",
            ))
        }
    }

    /// Dictionary protocol: __len__
    fn __len__(&self) -> usize {
        self.length()
    }

    /// Dictionary protocol: __contains__
    fn __contains__(&self, py: Python<'_>, key: Py<PyAny>) -> PyResult<bool> {
        let key_wrapper = PyObjectKey::new(py, key)?;
        Ok(self.cache.contains_key(&key_wrapper))
    }

    /// Dictionary protocol: __iter__
    fn __iter__(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        let keys: Vec<Py<PyAny>> = self.order.iter().map(|k| k.obj.clone_ref(py)).collect();
        let list = PyList::new(py, keys)?;
        // Return an iterator over the list using Python's iter() function
        let iter_func = py.import("builtins")?.getattr("iter")?;
        let iterator = iter_func.call1((list,))?;
        Ok(iterator.into())
    }
}

/// FrozenDict - An immutable dictionary that can be hashed
///
/// This is used to generate stable hashes for queries that contain dicts.
/// Usually, Python dicts are not hashable because they are mutable. This
/// class removes the mutability and implements the __hash__ method.
#[pyclass(module = "_tinydb_core")]
pub struct FrozenDict {
    dict: Py<PyDict>,
    hash_value: u64,
}

#[pymethods]
impl FrozenDict {
    #[new]
    fn new(py: Python<'_>, dict: Bound<'_, PyDict>) -> PyResult<Self> {
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};

        // Calculate hash from sorted items
        let mut hasher = DefaultHasher::new();

        // Sort items by key for stable hashing
        let mut items: Vec<(Py<PyAny>, Py<PyAny>)> =
            dict.iter().map(|(k, v)| (k.into(), v.into())).collect();

        // Sort by key hash for consistency
        items.sort_by(|a, b| {
            let hash_a = a.0.bind(py).hash().unwrap_or(0) as i64;
            let hash_b = b.0.bind(py).hash().unwrap_or(0) as i64;
            hash_a.cmp(&hash_b)
        });

        // Hash each key-value pair
        for (k, v) in items {
            let key_hash = k.bind(py).hash().unwrap_or(0) as i64;
            let val_hash = v.bind(py).hash().unwrap_or(0) as i64;
            key_hash.hash(&mut hasher);
            val_hash.hash(&mut hasher);
        }

        let hash_value = hasher.finish();

        Ok(FrozenDict {
            dict: dict.unbind(),
            hash_value,
        })
    }

    /// Implement __hash__ method
    fn __hash__(&self) -> u64 {
        self.hash_value
    }

    /// Get the underlying dict
    fn __getitem__(&self, py: Python<'_>, key: Py<PyAny>) -> PyResult<Py<PyAny>> {
        self.dict.bind(py).get_item(key).and_then(|opt| {
            opt.map(|v| Ok(v.unbind())).unwrap_or_else(|| {
                Err(PyErr::new::<pyo3::exceptions::PyKeyError, _>(
                    "Key not found",
                ))
            })
        })
    }

    /// Get item with default
    fn get(
        &self,
        py: Python<'_>,
        key: Py<PyAny>,
        default: Option<Py<PyAny>>,
    ) -> PyResult<Py<PyAny>> {
        match self.dict.bind(py).get_item(key)? {
            Some(v) => Ok(v.unbind()),
            None => Ok(default.unwrap_or_else(|| py.None())),
        }
    }

    /// Check if key exists
    fn __contains__(&self, py: Python<'_>, key: Py<PyAny>) -> PyResult<bool> {
        Ok(self.dict.bind(py).contains(key)?)
    }

    /// Get length
    fn __len__(&self) -> usize {
        Python::attach(|py| self.dict.bind(py).len())
    }

    /// Get keys
    fn keys(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        Ok(self.dict.bind(py).keys().unbind().into())
    }

    /// Get values
    fn values(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        Ok(self.dict.bind(py).values().unbind().into())
    }

    /// Get items
    fn items(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        Ok(self.dict.bind(py).items().unbind().into())
    }

    /// Disable __setitem__ - raise TypeError
    fn __setitem__(&self, _key: Py<PyAny>, _value: Py<PyAny>) -> PyResult<()> {
        Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(
            "object is immutable",
        ))
    }

    /// Disable __delitem__ - raise TypeError
    fn __delitem__(&self, _key: Py<PyAny>) -> PyResult<()> {
        Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(
            "object is immutable",
        ))
    }

    /// Disable clear - raise TypeError
    fn clear(&self) -> PyResult<()> {
        Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(
            "object is immutable",
        ))
    }

    /// Disable setdefault - raise TypeError
    fn setdefault(&self, _key: Py<PyAny>, _default: Option<Py<PyAny>>) -> PyResult<()> {
        Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(
            "object is immutable",
        ))
    }

    /// Disable popitem - raise TypeError
    fn popitem(&self) -> PyResult<()> {
        Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(
            "object is immutable",
        ))
    }

    /// Disable update - raise TypeError
    fn update(&self, _e: Option<Py<PyAny>>, _f: Option<&Bound<'_, PyDict>>) -> PyResult<()> {
        Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(
            "object is immutable",
        ))
    }

    /// Disable pop - raise TypeError
    fn pop(&self, _k: Py<PyAny>, _d: Option<Py<PyAny>>) -> PyResult<()> {
        Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(
            "object is immutable",
        ))
    }
}

/// Freeze an object by making it immutable and thus hashable.
///
/// This function recursively processes objects:
/// - dict -> FrozenDict
/// - list -> tuple
/// - set -> frozenset
/// - Other objects remain unchanged
#[pyfunction]
pub fn freeze(py: Python<'_>, obj: Py<PyAny>) -> PyResult<Py<PyAny>> {
    if let Ok(dict) = obj.bind(py).cast::<PyDict>() {
        // Transform dict into FrozenDict
        // First, recursively freeze all values
        let frozen_dict = PyDict::new(py);
        for (key, value) in dict.iter() {
            let frozen_value = freeze(py, value.into())?;
            frozen_dict.set_item(key, frozen_value)?;
        }
        // Create FrozenDict from the frozen dict
        let frozen = Py::new(py, FrozenDict::new(py, frozen_dict)?)?;
        Ok(frozen.into())
    } else if let Ok(list) = obj.bind(py).cast::<PyList>() {
        // Transform list into tuple
        let mut items = Vec::new();
        for item in list.iter() {
            items.push(freeze(py, item.into())?);
        }
        Ok(PyTuple::new(py, items)?.unbind().into())
    } else if let Ok(set) = obj.bind(py).cast::<PySet>() {
        // Transform set into frozenset
        let mut items = Vec::new();
        for item in set.iter() {
            items.push(freeze(py, item.into())?);
        }
        Ok(PyFrozenSet::new(py, items)?.unbind().into())
    } else {
        // Don't handle other objects
        Ok(obj)
    }
}
