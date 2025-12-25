# IO Module Unit Tests

**Following GUIDELINES_TEST.md** - Test structure mirrors the io module organization.

## Test Structure

This test suite follows eXonware's hierarchical testing standards as defined in `GUIDELINES_TEST.md`.

### Directory Structure

```
tests/
├── 0.core/
│   └── io/                               # Core IO tests (fast, high-value)
│       ├── test_core_xwsystem_io.py
│       ├── runner.py
│       └── data/
│
├── 1.unit/
│   └── io_tests/                         # Unit tests (mirrors io/ structure)
│       ├── __init__.py
│       ├── conftest.py
│       ├── runner.py
│       │
│       ├── test_contracts.py             # io/contracts.py tests
│       ├── test_facade.py                # io/facade.py tests
│       ├── test_defs.py                  # io/defs.py tests
│       ├── test_errors.py                # io/errors.py tests
│       │
│       ├── codec_tests/                  # io/codec/ tests
│       │   ├── test_contracts.py
│       │   ├── test_base.py
│       │   └── test_registry.py
│       │
│       ├── serialization_tests/          # io/serialization/ tests
│       │   ├── test_contracts.py
│       │   ├── test_base.py
│       │   ├── test_registry.py
│       │   └── formats_tests/
│       │       ├── text_tests/           # JSON, YAML, TOML, XML, CSV
│       │       ├── binary_tests/         # MessagePack, Pickle, BSON
│       │       ├── schema_tests/         # Protobuf, Avro, Parquet
│       │       ├── scientific_tests/     # HDF5, Feather, Zarr
│       │       └── database_tests/       # SQLite, LMDB, Shelve
│       │
│       ├── archive_tests/                # io/archive/ tests
│       │   ├── test_base.py
│       │   ├── test_archivers.py
│       │   └── test_archive_files.py
│       │
│       ├── common_tests/                 # io/common/ tests
│       ├── file_tests/                   # io/file/ tests
│       ├── folder_tests/                 # io/folder/ tests
│       ├── stream_tests/                 # io/stream/ tests
│       └── filesystem_tests/             # io/filesystem/ tests
│
├── 2.integration/
│   └── io_tests/                         # Integration tests
│       ├── test_end_to_end.py
│       └── test_codec_integration.py
│
└── 3.advance/                            # Advance tests (v1.0.0+)
    ├── test_security.py                  # Priority #1
    ├── test_usability.py                 # Priority #2
    ├── test_maintainability.py           # Priority #3
    ├── test_performance.py               # Priority #4
    └── test_extensibility.py             # Priority #5
```

## Running Tests

### Run All IO Unit Tests
```bash
python tests/1.unit/io_tests/runner.py
```

### Run Specific Test Files
```bash
# Test IO contracts
pytest tests/1.unit/io_tests/test_contracts.py -v

# Test XWIO facade
pytest tests/1.unit/io_tests/test_facade.py -v

# Test codec foundation
pytest tests/1.unit/io_tests/codec_tests/ -v

# Test serialization
pytest tests/1.unit/io_tests/serialization_tests/ -v

# Test archive operations
pytest tests/1.unit/io_tests/archive_tests/ -v
```

### Run by Marker
```bash
# Run all xwsystem unit tests
pytest -m xwsystem_unit -v

# Run all xwsystem unit tests in io_tests directory
pytest tests/1.unit/io_tests/ -m xwsystem_unit -v
```

## Test Coverage

### Current Coverage

- ✅ **Contracts** - All IO interfaces and enums
- ✅ **Facade** - XWIO unified interface
- ✅ **Codec Foundation** - ICodec, ACodec, UniversalCodecRegistry
- ✅ **Serialization Foundation** - ISerialization, ASerialization, SerializationRegistry
- ✅ **Archive Foundation** - AArchiver, AArchiveFile, XWZipArchiver, XWTarArchiver
- ✅ **Serialization Formats** - JSON, YAML (examples)
- ✅ **Integration** - End-to-end workflows

### To Be Added

- ⏳ Additional format-specific tests (TOML, XML, CSV, etc.)
- ⏳ File operations tests
- ⏳ Folder operations tests
- ⏳ Stream operations tests
- ⏳ Common utilities tests
- ⏳ Filesystem tests

## Test Principles

Following GUIDELINES_TEST.md:

1. **Mirror Structure** - Tests mirror the source code structure
2. **Clear Naming** - `test_<module>_<feature>.py`
3. **Proper Markers** - `@pytest.mark.xwsystem_unit`
4. **Isolation** - Each test is independent
5. **Fast Execution** - Unit tests run quickly (< 100ms each)
6. **No External Dependencies** - Use mocks for external services
7. **Comprehensive Coverage** - Test both success and failure paths

## Test Markers

All tests use appropriate markers from `pytest.ini`:

- `xwsystem_unit` - Unit tests for individual components
- `xwsystem_core` - Core functionality tests (in 0.core/)
- `xwsystem_integration` - Integration tests (in 2.integration/)
- `xwsystem_security` - Security-specific tests (Priority #1)
- `xwsystem_performance` - Performance benchmarks (Priority #4)

## Architecture Validation

These tests validate the **I→A→XW pattern**:

- **I (Interface)** - `ICodec`, `ISerialization`, `IArchiver`, `IArchiveFile`
- **A (Abstract)** - `ACodec`, `ASerialization`, `AArchiver`, `AArchiveFile`
- **XW (Concrete)** - `XWJsonSerializer`, `XWZipArchiver`, etc.

## Backward Compatibility

Tests verify backward compatibility aliases:

- `JsonSerializer` → `XWJsonSerializer`
- `ZipArchiver` → `XWZipArchiver`
- `TarArchiver` → `XWTarArchiver`

## Contributing

When adding new tests:

1. Follow the mirror structure (match `io/` module layout)
2. Use appropriate markers (`@pytest.mark.xwsystem_unit`)
3. Add docstrings explaining test purpose
4. Test both success and failure cases
5. Update this README with new coverage

---

**Company:** eXonware.com  
**Author:** Eng. Muhammad AlShehri  
**Email:** connect@exonware.com

