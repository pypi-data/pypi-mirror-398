# tinydb-rust

[English](README.md) | [简体中文](README.zh.md)

A high-performance Rust reimplementation of the [TinyDB](https://github.com/msiemens/tinydb) library, providing memory safety and improved performance while maintaining API compatibility with the original Python implementation.

## ⚠️ Early Development Status

**This project is currently in Alpha (0.1.0) and under active development.**

- ✅ Core utility functions are implemented (LRUCache, FrozenDict, freeze)
- 🚧 Full TinyDB functionality is being developed
- ⚠️ **Not recommended for production use yet**

## Features

### Currently Implemented

- **LRUCache**: A least-recently-used cache implementation compatible with TinyDB's utils
- **FrozenDict**: An immutable, hashable dictionary for stable query hashing
- **freeze()**: Utility function to recursively freeze Python objects (dict→FrozenDict, list→tuple, set→frozenset)

### Planned Features

- Full TinyDB database implementation
- JSON storage backend
- Query system
- Middleware support
- High-performance operations through Rust

## Installation

### From PyPI (when available)

```bash
pip install tinydb-rust
```

### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/tinydb-rust.git
cd tinydb-rust

# Install using maturin
pip install maturin
maturin develop
```

## Usage

### LRUCache

```python
from tinydb_rust.utils import LRUCache

# Create a cache with capacity
cache = LRUCache(capacity=3)
cache["a"] = 1
cache["b"] = 2
cache["c"] = 3

# Access moves item to most recently used
_ = cache["a"]

# Adding new item removes least recently used
cache["d"] = 4  # "b" is removed

print(cache.lru)  # ["c", "a", "d"]
```

### FrozenDict

```python
from tinydb_rust.utils import FrozenDict

# Create a frozen (immutable) dictionary
frozen = FrozenDict({"key": "value"})

# Can be used as dictionary key
cache = {}
cache[frozen] = "some value"

# Modifications raise TypeError
# frozen["new_key"] = "value"  # TypeError: object is immutable
```

### freeze()

```python
from tinydb_rust.utils import freeze

# Recursively freeze objects
data = [1, 2, {"nested": [3, 4]}, {5, 6}]
frozen = freeze(data)

# Returns: (1, 2, FrozenDict({'nested': (3, 4)}), frozenset({5, 6}))
```

## Requirements

- Python >= 3.8
- Rust (for building from source)

## Development

### Setup Development Environment

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Build the project
maturin build
```

### Project Structure

```
tinydb-rust/
├── src/              # Rust source code
│   ├── lib.rs       # Main module
│   └── utils.rs     # Utility functions
├── python/          # Python package
│   └── tinydb_rust/
├── tests/           # Test suite
└── Cargo.toml       # Rust dependencies
```

## Performance

This Rust implementation aims to provide significant performance improvements over the pure Python TinyDB, especially for:

- Large dataset operations
- Complex queries
- High-frequency read/write operations

Benchmarks will be added as the project matures.

## Contributing

Contributions are welcome! This project is in early development, so there are many opportunities to help:

- Implement missing features
- Write tests
- Improve documentation
- Report bugs
- Suggest improvements

Please feel free to open issues or submit pull requests.

## Roadmap

- [x] Core utility functions (LRUCache, FrozenDict, freeze)
- [ ] Database implementation
- [ ] Storage backends (JSON, memory)
- [ ] Query system
- [ ] Middleware support
- [ ] Full API compatibility with TinyDB
- [ ] Performance benchmarks
- [ ] Documentation and examples

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [TinyDB](https://github.com/msiemens/tinydb) - The original Python implementation
- [PyO3](https://github.com/PyO3/pyo3) - Rust bindings for Python
- [Maturin](https://github.com/PyO3/maturin) - Build tool for Rust-Python projects

## Author

morninghao (morning.haoo@gmail.com)
