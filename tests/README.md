# Testing Framework for Landmarks Locator

This directory contains testing utilities for the Landmarks Locator application.

## Overview

The testing framework allows for testing various components of the application without relying on external APIs or services. It utilizes test fixtures defined in `config.json` at the project root.

## Test Mode

The application can run in test mode by setting the `TEST_MODE` environment variable to `1`. In test mode:

- The Google Places API client is not initialized, preventing external API calls
- Test landmarks from `config.json` are used instead of real API responses
- Cache operations work with test data

## Components

### Test Runner

`test_runner.py` - A command-line utility for running various tests:

```bash
# Run all tests
python test_runner.py --test all

# Run specific test categories
python test_runner.py --test coords  # Test coordinate utilities
python test_runner.py --test places  # Test Google Places handler
python test_runner.py --test cache   # Test cache manager

# Enable verbose output
python test_runner.py --test all --verbose

# Output results in JSON format
python test_runner.py --test all --json
```

### Configuration

Tests use the configuration defined in `config.json` at the project root:

- `test_landmarks` - Predefined landmarks for testing
- `test_centers` - Test center coordinates with search radius

### Debug Mode

Enable debug logging by setting the `DEBUG` environment variable to `1`.

## Running the App in Test Mode

To run the main application in test mode:

```bash
TEST_MODE=1 DEBUG=1 streamlit run main.py
```

This will:
1. Enable test mode to use predefined test landmarks
2. Enable debug logging for more detailed output

## Adding New Tests

To add new tests:
1. Update the test_runner.py file
2. Add a new option to the `--test` choices
3. Implement the test logic in the run_test function