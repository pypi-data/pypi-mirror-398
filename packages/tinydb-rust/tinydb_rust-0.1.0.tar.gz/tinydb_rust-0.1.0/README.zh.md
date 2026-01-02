# tinydb-rust

[English](README.md) | [简体中文](README.zh.md)

[TinyDB](https://github.com/msiemens/tinydb) 库的高性能 Rust 重实现，在保持与原始 Python 实现 API 兼容的同时，提供内存安全性和更高的性能。

## ⚠️ 早期开发状态

**本项目目前处于 Alpha (0.1.0) 阶段，正在积极开发中。**

- ✅ 核心工具函数已实现（LRUCache、FrozenDict、freeze）
- 🚧 完整的 TinyDB 功能正在开发中
- ⚠️ **目前不建议用于生产环境**

## 特性

### 已实现功能

- **LRUCache**: 与 TinyDB 的 utils 兼容的最近最少使用缓存实现
- **FrozenDict**: 不可变的、可哈希的字典，用于稳定的查询哈希
- **freeze()**: 递归冻结 Python 对象的工具函数（dict→FrozenDict，list→tuple，set→frozenset）

### 计划功能

- 完整的 TinyDB 数据库实现
- JSON 存储后端
- 查询系统
- 中间件支持
- 通过 Rust 实现的高性能操作

## 安装

### 从 PyPI 安装（发布后）

```bash
pip install tinydb-rust
```

### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/tinydb-rust.git
cd tinydb-rust

# 使用 maturin 安装
pip install maturin
maturin develop
```

## 使用方法

### LRUCache

```python
from tinydb_rust.utils import LRUCache

# 创建带容量的缓存
cache = LRUCache(capacity=3)
cache["a"] = 1
cache["b"] = 2
cache["c"] = 3

# 访问会将项目移至最近使用位置
_ = cache["a"]

# 添加新项目会移除最近最少使用的项目
cache["d"] = 4  # "b" 被移除

print(cache.lru)  # ["c", "a", "d"]
```

### FrozenDict

```python
from tinydb_rust.utils import FrozenDict

# 创建冻结（不可变）字典
frozen = FrozenDict({"key": "value"})

# 可以用作字典键
cache = {}
cache[frozen] = "some value"

# 修改会抛出 TypeError
# frozen["new_key"] = "value"  # TypeError: object is immutable
```

### freeze()

```python
from tinydb_rust.utils import freeze

# 递归冻结对象
data = [1, 2, {"nested": [3, 4]}, {5, 6}]
frozen = freeze(data)

# 返回: (1, 2, FrozenDict({'nested': (3, 4)}), frozenset({5, 6}))
```

## 要求

- Python >= 3.8
- Rust（从源码构建时需要）

## 开发

### 设置开发环境

```bash
# 安装依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/

# 构建项目
maturin build
```

### 项目结构

```
tinydb-rust/
├── src/              # Rust 源代码
│   ├── lib.rs       # 主模块
│   └── utils.rs     # 工具函数
├── python/          # Python 包
│   └── tinydb_rust/
├── tests/           # 测试套件
└── Cargo.toml       # Rust 依赖
```

## 性能

这个 Rust 实现旨在比纯 Python 的 TinyDB 提供显著的性能提升，特别是在以下场景：

- 大数据集操作
- 复杂查询
- 高频读写操作

随着项目成熟，将添加性能基准测试。

## 贡献

欢迎贡献！本项目处于早期开发阶段，有很多机会可以帮助：

- 实现缺失的功能
- 编写测试
- 改进文档
- 报告错误
- 提出改进建议

欢迎提交 issue 或 pull request。

## 路线图

- [x] 核心工具函数（LRUCache、FrozenDict、freeze）
- [ ] 数据库实现
- [ ] 存储后端（JSON、内存）
- [ ] 查询系统
- [ ] 中间件支持
- [ ] 与 TinyDB 的完整 API 兼容性
- [ ] 性能基准测试
- [ ] 文档和示例

## 许可证

本项目采用 MIT 许可证 - 详见 LICENSE 文件。

## 致谢

- [TinyDB](https://github.com/msiemens/tinydb) - 原始 Python 实现
- [PyO3](https://github.com/PyO3/pyo3) - Python 的 Rust 绑定
- [Maturin](https://github.com/PyO3/maturin) - Rust-Python 项目构建工具

## 作者

morninghao (morning.haoo@gmail.com)

