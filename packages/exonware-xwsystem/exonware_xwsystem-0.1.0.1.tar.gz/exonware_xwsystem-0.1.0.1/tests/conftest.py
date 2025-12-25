"""
#exonware/xwsystem/tests/conftest.py

Pytest configuration and fixtures for xwsystem tests.
Provides reusable test data and setup utilities.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.388
Generation Date: 01-Nov-2025
"""

import pytest
from pathlib import Path
import sys
import time

# Ensure src is in path for imports
tests_dir = Path(__file__).resolve().parent
project_root = tests_dir.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

def _install_enterprise_dependency_stubs() -> None:
    """
    Install lightweight stub modules for optional enterprise dependencies.

    The enterprise serializers depend on hefty native libraries (scipy, netCDF4,
    plyvel, ubjson, etc.). In lightweight CI/local environments those packages
    may be absent. To keep tests meaningful without mutating production code,
    we provide focused stubs that emulate just enough behaviour for the unit
    tests. Real installations with the full dependencies ignore these stubs.
    """
    import types
    import pickle
    import json
    from pathlib import Path as _Path

    # ------------------------------------------------------------------ SciPy
    try:
        import scipy  # noqa: F401
    except ImportError:
        scipy_module = types.ModuleType("scipy")
        scipy_module.__xw_test_stub__ = True
        scipy_io_module = types.ModuleType("scipy.io")

        def _savemat(file_path, data, do_compression=False):  # noqa: D401
            path_obj = _Path(file_path)
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            with path_obj.open("wb") as handle:
                pickle.dump(data, handle)

        def _loadmat(file_path):  # noqa: D401
            path_obj = _Path(file_path)
            with path_obj.open("rb") as handle:
                return pickle.load(handle)

        scipy_io_module.savemat = _savemat
        scipy_io_module.loadmat = _loadmat
        scipy_module.io = scipy_io_module
        sys.modules["scipy"] = scipy_module
        sys.modules["scipy.io"] = scipy_io_module

    # ---------------------------------------------------------------- netCDF4
    try:
        import netCDF4  # noqa: F401
    except ImportError:
        netcdf_module = types.ModuleType("netCDF4")
        netcdf_module.__xw_test_stub__ = True

        class _FakeArray(list):
            def tolist(self):  # noqa: D401
                return list(self)

        class _FakeDimension:
            def __init__(self, size):
                self._size = size

            def __len__(self):
                return self._size

        class _FakeVariable:
            def __init__(self, name, dtype, dimensions, dataset):
                object.__setattr__(self, "name", name)
                object.__setattr__(self, "dtype", dtype)
                object.__setattr__(self, "dimensions", tuple(dimensions))
                object.__setattr__(self, "_dataset", dataset)
                object.__setattr__(self, "_attributes", {})
                object.__setattr__(self, "_data", _FakeArray())

            def __setattr__(self, key, value):
                if key in {"name", "dtype", "dimensions", "_dataset", "_attributes", "_data"}:
                    object.__setattr__(self, key, value)
                else:
                    self._attributes[key] = value

            def __getattr__(self, item):
                if item in self._attributes:
                    return self._attributes[item]
                raise AttributeError(item)

            def __setitem__(self, key, value):
                self._data = _FakeArray(value)

            def __getitem__(self, key):
                return self._data

            def ncattrs(self):
                return list(self._attributes.keys())

            @property
            def data(self):
                return self._data

        class _FakeDataset:
            def __init__(self, file_path, mode, format="NETCDF4"):
                object.__setattr__(self, "_file_path", _Path(file_path))
                object.__setattr__(self, "_mode", mode)
                object.__setattr__(self, "_format", format)
                object.__setattr__(self, "dimensions", {})
                object.__setattr__(self, "variables", {})
                object.__setattr__(self, "_attributes", {})
                if mode == "r":
                    self._load()

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                if self._mode in {"w", "a", "r+"}:
                    self._persist()

            def __setattr__(self, key, value):
                if key in {"_file_path", "_mode", "_format", "dimensions", "variables", "_attributes"}:
                    object.__setattr__(self, key, value)
                else:
                    self._attributes[key] = value

            def __getattr__(self, item):
                if item in self._attributes:
                    return self._attributes[item]
                raise AttributeError(item)

            def _persist(self):
                payload = {
                    "dimensions": {name: len(dim) for name, dim in self.dimensions.items()},
                    "variables": {},
                    "attributes": dict(self._attributes),
                }
                for name, var in self.variables.items():
                    payload["variables"][name] = {
                        "data": list(var.data),
                        "dtype": var.dtype,
                        "dimensions": list(var.dimensions),
                        "attributes": dict(var._attributes),
                    }
                self._file_path.parent.mkdir(parents=True, exist_ok=True)
                with self._file_path.open("wb") as handle:
                    pickle.dump(payload, handle)

            def _load(self):
                file_path = self._file_path
                if not file_path.exists():
                    return
                with file_path.open("rb") as handle:
                    payload = pickle.load(handle)
                dims = {name: _FakeDimension(size) for name, size in payload.get("dimensions", {}).items()}
                vars_dict = {}
                for name, info in payload.get("variables", {}).items():
                    fake_var = _FakeVariable(name, info.get("dtype"), info.get("dimensions", ()), self)
                    fake_var._data = _FakeArray(info.get("data", []))
                    fake_var._attributes = dict(info.get("attributes", {}))
                    vars_dict[name] = fake_var
                object.__setattr__(self, "dimensions", dims)
                object.__setattr__(self, "variables", vars_dict)
                object.__setattr__(self, "_attributes", dict(payload.get("attributes", {})))

            def createDimension(self, name, size):
                dim = _FakeDimension(size)
                self.dimensions[name] = dim
                return dim

            def createVariable(self, name, dtype, dimensions):
                var = _FakeVariable(name, dtype, dimensions, self)
                self.variables[name] = var
                return var

            def ncattrs(self):
                return list(self._attributes.keys())

        netcdf_module.Dataset = _FakeDataset
        sys.modules["netCDF4"] = netcdf_module

    # ----------------------------------------------------------------- numpy
    try:
        import numpy  # noqa: F401
    except ImportError:
        numpy_module = types.ModuleType("numpy")
        numpy_module.__xw_test_stub__ = True

        def _identity(value, dtype=None):
            return value

        numpy_module.array = _identity  # type: ignore[attr-defined]
        numpy_module.ndarray = list  # type: ignore[attr-defined]
        sys.modules["numpy"] = numpy_module

    # ----------------------------------------------------------------- plyvel
    try:
        import plyvel  # noqa: F401
    except ImportError:
        plyvel_module = types.ModuleType("plyvel")
        plyvel_module.__xw_test_stub__ = True

        class _FakeDB:
            def __init__(self, path, create_if_missing=True):
                self._path = _Path(path)
                self._data_path = self._path / "__leveldb__.pkl"
                if not self._path.exists():
                    if not create_if_missing:
                        raise FileNotFoundError(f"LevelDB database not found: {self._path}")
                    self._path.mkdir(parents=True, exist_ok=True)
                if self._data_path.exists():
                    with self._data_path.open("rb") as handle:
                        self._data = pickle.load(handle)
                else:
                    if not create_if_missing:
                        raise FileNotFoundError(f"LevelDB database not found: {self._path}")
                    self._data = {}

            def put(self, key_bytes, value_bytes):
                self._data[key_bytes] = value_bytes

            def __iter__(self):
                return iter(self._data.items())

            def close(self):
                self._path.mkdir(parents=True, exist_ok=True)
                with self._data_path.open("wb") as handle:
                    pickle.dump(self._data, handle)

        plyvel_module.DB = _FakeDB
        plyvel_module.Error = RuntimeError
        sys.modules["plyvel"] = plyvel_module

    # ----------------------------------------------------------------- ubjson
    try:
        import ubjson  # noqa: F401
    except ImportError:
        ubjson_module = types.ModuleType("ubjson")
        ubjson_module.__xw_test_stub__ = True

        def _dumpb(data):
            return json.dumps(data).encode("utf-8")

        def _loadb(data):
            return json.loads(data.decode("utf-8"))

        ubjson_module.dumpb = _dumpb
        ubjson_module.loadb = _loadb
        sys.modules["ubjson"] = ubjson_module

    # --------------------------------------------------------------- misc deps
    for optional_module in ("compression", "socks", "wimlib"):
        if optional_module not in sys.modules:
            sys.modules[optional_module] = types.ModuleType(optional_module)

    if "json5" not in sys.modules:
        import re

        json5_module = types.ModuleType("json5")

        def _json5_dumps(data, indent=None):
            return json.dumps(data, indent=indent)

        def _json5_loads(value):
            # Remove single-line and block comments
            no_comments = re.sub(r"//.*?$", "", value, flags=re.MULTILINE)
            no_comments = re.sub(r"/\*.*?\*/", "", no_comments, flags=re.DOTALL)
            # Remove trailing commas before closing braces/brackets
            normalized = re.sub(r",(\s*[}\]])", r"\1", no_comments)
            return json.loads(normalized)

        json5_module.dumps = _json5_dumps
        json5_module.loads = _json5_loads
        sys.modules["json5"] = json5_module

    if "pyarrow" not in sys.modules:
        pyarrow_module = types.ModuleType("pyarrow")
        pyarrow_module.__xw_test_stub__ = True
        sys.modules["pyarrow"] = pyarrow_module
        sys.modules["pyarrow.lib"] = types.ModuleType("pyarrow.lib")
        sys.modules["pyarrow.parquet"] = types.ModuleType("pyarrow.parquet")

    # ------------------------------------------------------------ google proto
    if "google" not in sys.modules:
        google_module = types.ModuleType("google")
        google_module.__path__ = []  # Mark as package
        sys.modules["google"] = google_module
    try:
        import google.protobuf  # noqa: F401
    except ImportError:
        protobuf_module = types.ModuleType("google.protobuf")
        protobuf_module.__xw_test_stub__ = True

        class _StubMessage:
            def SerializeToString(self):
                return b""

            def ParseFromString(self, data):
                return self

        message_module = types.ModuleType("google.protobuf.message")
        message_module.Message = _StubMessage

        json_format_module = types.ModuleType("google.protobuf.json_format")

        def _message_to_json(msg, *args, **kwargs):
            return "{}"

        def _parse_json(value, message_instance, **kwargs):
            return message_instance

        json_format_module.MessageToJson = _message_to_json
        json_format_module.Parse = _parse_json

        protobuf_module.message = message_module
        protobuf_module.json_format = json_format_module

        sys.modules["google.protobuf"] = protobuf_module
        sys.modules["google.protobuf.message"] = message_module
        sys.modules["google.protobuf.json_format"] = json_format_module
        sys.modules["google"].protobuf = protobuf_module  # type: ignore[attr-defined]

_install_enterprise_dependency_stubs()


# ============================================================================
# BASIC DATA FIXTURES
# ============================================================================

@pytest.fixture
def simple_dict_data():
    """Simple dictionary test data."""
    return {
        'name': 'Alice',
        'age': 30,
        'city': 'New York',
        'active': True
    }


@pytest.fixture
def nested_data():
    """Complex nested hierarchical test data."""
    return {
        'users': [
            {
                'id': 1,
                'name': 'Alice',
                'profile': {
                    'email': 'alice@example.com',
                    'preferences': {'theme': 'dark'}
                }
            }
        ],
        'metadata': {
            'version': 1.0,
            'created': '2024-01-01'
        }
    }


@pytest.fixture
def simple_data():
    """Simple data for basic tests."""
    return {"key": "value", "number": 42, "boolean": True}


@pytest.fixture
def complex_data():
    """Complex nested data for advanced tests."""
    return {
        "users": [
            {"id": 1, "name": "John", "settings": {"theme": "dark"}},
            {"id": 2, "name": "Jane", "settings": {"theme": "light"}}
        ],
        "metadata": {"version": "1.0", "created": "2024-01-01"}
    }


# ============================================================================
# CACHING-SPECIFIC FIXTURES
# ============================================================================

@pytest.fixture
def cache_test_data():
    """Standard test data for caching operations."""
    return {
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'key4': 'value4',
        'key5': 'value5',
    }


@pytest.fixture
def large_cache_dataset():
    """Large dataset for performance testing (1,000 items)."""
    return {f'key_{i}': f'value_{i}' for i in range(1000)}


@pytest.fixture
def very_large_cache_dataset():
    """Very large dataset for stress testing (10,000 items)."""
    return {f'key_{i}': f'value_{i}' for i in range(10000)}


@pytest.fixture
def multilingual_cache_data():
    """Multilingual and emoji data for Unicode testing."""
    return {
        "english": "Hello World",
        "chinese": "你好世界",
        "arabic": "مرحبا بالعالم",
        "emoji": "🚀🎉✅❌🔥💯",
        "special": "Special chars: åäö ñ ç ß €",
        "mixed": "Mixed: Hello 世界 🌍 مرحبا"
    }


@pytest.fixture
def edge_case_keys():
    """Edge case keys for robustness testing."""
    return [
        "",  # Empty string
        " ",  # Single space
        "a" * 100,  # Long key
        "key with spaces",
        "key-with-dashes",
        "key_with_underscores",
        "key.with.dots",
        "123",  # Numeric string
        "CamelCaseKey",
        "UPPERCASE_KEY",
    ]


@pytest.fixture
def malicious_inputs():
    """Malicious input patterns for security testing."""
    return [
        "../../../etc/passwd",  # Path traversal
        "<script>alert('xss')</script>",  # XSS attempt
        "'; DROP TABLE cache; --",  # SQL injection pattern
        "\x00\x01\x02",  # Null bytes
        "A" * 10000,  # Very long input
        {"depth": {"very": {"deep": {"nested": "data" * 100}}}},  # Deep nesting
    ]


# ============================================================================
# DIRECTORY FIXTURES
# ============================================================================

@pytest.fixture
def test_data_dir():
    """Get the test data directory."""
    return Path(__file__).parent / "0.core" / "data"


@pytest.fixture
def temp_test_dir(tmp_path):
    """Create a temporary directory for test files."""
    test_dir = tmp_path / "test_data"
    test_dir.mkdir()
    return test_dir


# ============================================================================
# PERFORMANCE FIXTURES
# ============================================================================

@pytest.fixture
def performance_timer():
    """Fixture for timing operations."""
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            
        def start(self):
            self.start_time = time.time()
            
        def stop(self):
            self.end_time = time.time()
            
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()

