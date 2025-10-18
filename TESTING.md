# Testing Guide for Hot Water Tank Temperature Control System

## Overview

This project includes a comprehensive test suite to ensure reliability and catch errors before deployment. The test suite covers temperature control logic, configuration management, hardware integration, and error handling.

## Test Suite Summary

**Total Tests: 68 (all passing)**

### Test Files

All test files are located in the `tests/` directory:

1. **tests/test_control.py** (30 tests) - Temperature control logic
2. **tests/test_config.py** (18 tests) - Configuration management
3. **tests/test_evok.py** (20 tests) - Hardware API client
4. **tests/test_api.py** - Flask API endpoints (requires Python <3.13 due to eventlet compatibility)

## Running Tests

### Quick Start

```bash
# Using the custom test runner
./run_tests.py

# Using pytest directly
venv/bin/python -m pytest

# Run specific test file
venv/bin/python -m pytest tests/test_control.py

# Run with verbose output
venv/bin/python -m pytest -v

# Run with coverage report
venv/bin/python -m pytest --cov=. --cov-report=html
```

### Test Runner Options

```bash
# Verbose output
./run_tests.py -v 2

# Quiet mode
./run_tests.py -q

# Run specific module
./run_tests.py -m test_control

# Skip summary
./run_tests.py --no-summary
```

## Test Coverage

### Temperature Control Tests (`test_control.py`)

**Purpose:** Verify core temperature control logic including hysteresis, safety limits, and pump management.

**Key Tests:**
- ✓ Sensor discovery and failure handling
- ✓ Temperature reading and averaging
- ✓ Hysteresis-based heating control
- ✓ Safety limits (max temperature protection)
- ✓ Pump delay timing and shutdown
- ✓ Manual override functionality
- ✓ Edge cases (extreme temps, zero hysteresis, sensor failures)

**Critical Scenarios Tested:**
1. Heating turns ON when temperature drops below (setpoint - hysteresis)
2. Heating turns OFF when temperature rises above (setpoint + hysteresis)
3. Heating disables when temperature exceeds max safety limit
4. Pump shutdown delayed by 60 seconds after heating stops
5. Manual override mode bypasses automatic control

### Configuration Tests (`test_config.py`)

**Purpose:** Ensure configuration loading, saving, validation, and persistence work correctly.

**Key Tests:**
- ✓ Default value initialization
- ✓ Setting and getting configuration values
- ✓ File persistence (save/load)
- ✓ Corrupted file handling
- ✓ Missing file handling
- ✓ Read-only file error handling
- ✓ Special characters in strings
- ✓ Concurrent modifications

**Critical Scenarios Tested:**
1. Config survives corrupted JSON gracefully (uses defaults)
2. Config persists across application restarts
3. Invalid values are handled without crashing
4. File permission errors don't crash the application

### Evok Client Tests (`test_evok.py`)

**Purpose:** Verify hardware API communication, sensor reading, relay control, and error handling.

**Key Tests:**
- ✓ Sensor discovery and filtering (DS18B20 only)
- ✓ Temperature reading from sensors
- ✓ Relay control (ON/OFF)
- ✓ Network error handling
- ✓ Timeout handling
- ✓ Malformed JSON responses
- ✓ HTTP error codes (400, 401, 403, 404, 500, 503)
- ✓ WebSocket connection management

**Critical Scenarios Tested:**
1. Network failures don't crash the application
2. Timeouts return None gracefully
3. Invalid sensor data is handled
4. Relay control failures are logged
5. Multiple sensor types are correctly filtered

## Test Design Principles

### 1. **Isolation**
- Each test is independent and doesn't affect others
- Mock objects used for external dependencies (hardware, network)
- Temporary config files used to avoid side effects

### 2. **Comprehensiveness**
- Happy path scenarios
- Error conditions
- Edge cases
- Boundary values

### 3. **Reliability**
- Tests are deterministic
- No external dependencies
- No timing-dependent flakiness (except timezone tests which use tolerance)

### 4. **Clarity**
- Descriptive test names
- Clear docstrings
- Focused tests (one concept per test)

## Common Test Patterns

### Mocking Hardware

```python
from unittest.mock import Mock

# Create mock Evok client
mock_evok = Mock()
mock_evok.get_temperature.return_value = 50.0
mock_evok.set_relay.return_value = True

# Use in controller
controller = TemperatureController(mock_evok, config)
```

### Testing Configuration

```python
# Use temporary config file
self.temp_fd, self.temp_config_path = tempfile.mkstemp(suffix='.json')
SystemConfig.CONFIG_FILE = self.temp_config_path
config = SystemConfig()
```

### Testing Control Logic

```python
# Set initial conditions
controller.average_temperature = 57.0
controller.heating_active = False

# Execute logic
controller.update_heating_control()

# Verify results
assert controller.heating_active == True
mock_evok.set_relay.assert_called_with('1_01', True)
```

## Known Issues

### Python 3.13 Compatibility
- `test_api.py` has issues with eventlet on Python 3.13
- This affects Flask-SocketIO tests
- Core functionality tests (control, config, evok) work fine
- Production deployment uses Python 3.11 which doesn't have this issue

### Workaround
Skip API tests when running on Python 3.13:
```bash
python -m pytest tests/test_control.py tests/test_config.py tests/test_evok.py
```

## Test Maintenance

### Adding New Tests

1. **Create test file** following naming convention `test_*.py`
2. **Use unittest.TestCase** or pytest functions
3. **Add descriptive docstrings** for each test
4. **Mock external dependencies** (hardware, network, database)
5. **Run tests** to ensure they pass
6. **Update this document** with new test coverage

### Debugging Failing Tests

```bash
# Run single test with verbose output
pytest tests/test_control.py::TestTemperatureController::test_hysteresis_heating_on -v -s

# Show local variables on failure
pytest --showlocals

# Drop into debugger on failure
pytest --pdb
```

### Best Practices

1. **Always run tests before committing code**
2. **Add tests for new features**
3. **Add regression tests for bug fixes**
4. **Keep tests fast** (mock slow operations)
5. **Don't test implementation details** (test behavior)
6. **Use descriptive assertion messages**

## Continuous Integration

### Pre-commit Checklist
- [ ] All tests pass: `./run_tests.py`
- [ ] No new warnings
- [ ] Test coverage maintained or improved
- [ ] New features have tests
- [ ] Bug fixes have regression tests

### Future Enhancements
- [ ] Add integration tests with real hardware (test environment)
- [ ] Add performance tests
- [ ] Add stress tests (long-running scenarios)
- [ ] Add UI/E2E tests
- [ ] Set up CI/CD pipeline (GitHub Actions)
- [ ] Add code coverage reporting
- [ ] Add mutation testing

## Test Statistics

```
Test Suite Breakdown:
├── tests/test_control.py      30 tests (44%)
├── tests/test_config.py       18 tests (26%)
├── tests/test_evok.py         20 tests (30%)
└── tests/test_api.py          (skipped on Python 3.13)

Total: 68 tests passing
Execution Time: < 1 second
Code Coverage: ~85% (estimated)
```

## Troubleshooting

### Tests Fail with "config.json" issues
**Solution:** Delete `config.json` before running tests
```bash
rm -f config.json && pytest
```

### Tests Fail with Import Errors
**Solution:** Ensure virtual environment is activated and dependencies installed
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Mock Assertions Fail
**Solution:** Check that manual_override is disabled in test setUp
```python
self.config.set('manual_override', False)
```

## Resources

- [Python unittest documentation](https://docs.python.org/3/library/unittest.html)
- [pytest documentation](https://docs.pytest.org/)
- [unittest.mock documentation](https://docs.python.org/3/library/unittest.mock.html)

## Support

For issues or questions about tests:
1. Check this documentation first
2. Review test code for examples
3. Check test output for specific error messages
4. Consult project maintainer if needed
