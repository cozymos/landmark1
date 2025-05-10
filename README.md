# Landmarks Locator

An advanced Streamlit-based geospatial exploration platform that enables intelligent landmark discovery through comprehensive geographical insights and interactive data visualization.

## Overview

The application provides a dynamic geographical experience with sophisticated data integration, leveraging multiple APIs and machine learning to deliver landmark recommendations and rich multimedia information. Features include:

- Interactive map-based exploration
- Landmark discovery and details
- Offline caching mechanism for disconnected use
- Distance calculations and radius-based search
- Flexible testing framework with test fixtures

## Project Structure

```
LandmarkLocator/
├── main.py                # Main application entry point
├── .streamlit/            # Streamlit configuration
│   └── config.toml        # Streamlit server configuration
├── components/            # Application components
│   ├── cache_manager.py   # Manages caching landmarks and images
│   ├── google_places.py   # Google Places API integration
│   └── map_viewer.py      # Map rendering utilities
├── utils/                 # Utility functions
│   ├── config_utils.py    # Configuration and test mode utilities
│   └── coord_utils.py     # Coordinate parsing and manipulation
├── tests/                 # Testing framework
│   ├── test_runner.py     # Test runner utility
│   └── cache/             # Test cache directory
├── cache/                 # Cache directory for landmarks and images
├── config.json            # Application configuration and test fixtures
└── README.md              # This file
```

## Installation

### 1. Setup Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/landmarks-locator.git
cd landmarks-locator

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
# Or install directly:
pip install streamlit folium streamlit-folium geopy googlemaps requests
```

### 3. Configure Environment Variables

```bash
# Unix/Linux/macOS
export GOOGLE_MAPS_API_KEY=your_api_key_here

# Windows (Command Prompt)
set GOOGLE_MAPS_API_KEY=your_api_key_here

# Windows (PowerShell)
$env:GOOGLE_MAPS_API_KEY="your_api_key_here"
```

## Running the Application

### Standard Mode

```bash
streamlit run main.py
```

### Test Mode

Run the application using test fixtures without making API calls:

```bash
TEST_MODE=1 streamlit run main.py -- --test-mode
```

Or with debug logging:

```bash
TEST_MODE=1 DEBUG=1 streamlit run main.py -- --test-mode --debug
```

### Command-line Parameters

The application supports the following command-line parameters:

- `--test-mode`: Enable test mode to use test landmarks from config.json
- `--debug`: Enable debug logging
- `--server.port=XXXX`: Run on a specific port
- `--server.address=X.X.X.X`: Bind to a specific address

## Testing Framework

### Overview

The testing framework allows for testing various components of the application without relying on external APIs or services. It utilizes test fixtures defined in `config.json` at the project root.

### Running Tests

```bash
# Run all tests
cd tests && python test_runner.py --test all

# Run specific test categories
python test_runner.py --test coords  # Test coordinate utilities
python test_runner.py --test places  # Test Google Places handler
python test_runner.py --test cache   # Test cache manager

# Enable verbose output
python test_runner.py --test all --verbose

# Output results in JSON format
python test_runner.py --test all --json
```

### Test Mode Features

When running in test mode:

- The Google Places API client is not initialized, preventing external API calls
- Test landmarks from `config.json` are used instead of real API responses
- Cache operations work with test data stored in the shared cache directory

### Adding New Tests

To add new tests:
1. Update the test_runner.py file
2. Add a new option to the `--test` choices
3. Implement the test logic in the run_test function

## Features

- **Interactive Map**: Pan, zoom, and explore locations
- **Landmark Discovery**: Find landmarks near any location
- **Location Search**: Enter coordinates in decimal or DMS format
- **Distance Display**: Show distance circle around current point
- **Detailed Information**: View images and details about landmarks
- **Offline Caching**: Access landmarks even when offline

## Configuration

The application uses a `config.json` file for configuration, including:

- `test_landmarks`: Pre-defined landmarks for testing
- `test_centers`: Center locations with search radius for testing

## Troubleshooting

1. **Map Not Loading**: Check internet connection
2. **No Landmarks**: Verify API keys and test mode settings
3. **API Errors**: Check error messages in console or logs
4. **Cache Issues**: Clear the cache directory and restart
5. **Port Conflicts**: Use the --server.port parameter to change ports

## Development Guidelines

1. Use the radius-based search approach throughout the codebase
2. Follow the component-based architecture 
3. Run tests before submitting changes
4. Use the test mode for development without API access
5. Update test fixtures as needed