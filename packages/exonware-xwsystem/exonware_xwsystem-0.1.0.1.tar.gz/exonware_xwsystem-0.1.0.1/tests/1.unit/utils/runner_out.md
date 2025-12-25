# Test Runner Output

**Library:** xwsystem  
**Layer:** 1.unit  
**Generated:** 08-Nov-2025 14:51:01  
**Description:** Utils lazy mode regression tests

---

---
# xwsystem - Utils lazy mode regression tests
---
**Test Directory:** `D:\OneDrive\DEV\exonware\xwsystem\tests\1.unit\utils`
**Output File:** `D:\OneDrive\DEV\exonware\xwsystem\tests\1.unit\utils\runner_out.md`

**Discovered:** 1 test file(s)

## Running Tests
```bash
C:\Users\muham\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe -m pytest -v --tb=short d:\OneDrive\DEV\exonware\xwsystem\tests\1.unit\utils -m xwsystem_unit
```
**Working directory:** `D:\OneDrive\DEV\exonware\xwsystem\tests\1.unit`

### Test Output
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-8.4.2, pluggy-1.6.0 -- C:\Users\muham\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe
cachedir: .pytest_cache
rootdir: d:\OneDrive\DEV\exonware\xwsystem\tests
configfile: pytest.ini
plugins: anyio-4.11.0, asyncio-1.2.0, zarr-3.1.3
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 2 items

utils\test_lazy_mode_example.py::test_lazy_mode_demo_enables_and_restores_configuration PASSED [ 50%]
utils\test_lazy_mode_example.py::test_config_package_lazy_install_enabled_respects_install_hook_flag PASSED [100%]

============================== warnings summary ===============================
C:\Users\muham\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\defusedxml\__init__.py:30
  C:\Users\muham\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\defusedxml\__init__.py:30: DeprecationWarning: defusedxml.cElementTree is deprecated, import from defusedxml.ElementTree instead.
    from . import cElementTree

utils\test_lazy_mode_example.py:60
  d:\OneDrive\DEV\exonware\xwsystem\tests\1.unit\utils\test_lazy_mode_example.py:60: PytestUnknownMarkWarning: Unknown pytest.mark.xwsystem_unit - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.xwsystem_unit

utils\test_lazy_mode_example.py:88
  d:\OneDrive\DEV\exonware\xwsystem\tests\1.unit\utils\test_lazy_mode_example.py:88: PytestUnknownMarkWarning: Unknown pytest.mark.xwsystem_unit - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.xwsystem_unit

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 2 passed, 3 warnings in 0.53s ========================

```

### Summary

```
======================== 2 passed, 3 warnings in 0.53s ========================
```

**Status:** ✅ PASSED

