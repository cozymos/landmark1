import json
import os
import sys
from typing import Dict, List, Tuple, Any, Optional
import logging

# Check for command-line arguments (--test-mode and --debug)
# Parse command line arguments before initializing streamlit
test_mode_enabled = False
debug_enabled = False

# First check environment variables
if os.environ.get("TEST_MODE") == "1":
    test_mode_enabled = True
if os.environ.get("DEBUG") == "1":
    debug_enabled = True

# Then check command line arguments (they override environment variables)
# Look for arguments after -- (streamlit passes these through)
if "--" in sys.argv:
    args_index = sys.argv.index("--")
    user_args = sys.argv[args_index + 1 :]
    if "--test-mode" in user_args:
        test_mode_enabled = True
    if "--debug" in user_args:
        debug_enabled = True

# Set up logging level based on debug setting
log_level = logging.DEBUG if debug_enabled else logging.INFO


# Define a filter to exclude noisy logs
class NoiseFilter(logging.Filter):
    def filter(self, record):
        # Filter out noisy debug logs
        if record.levelno == logging.DEBUG and record.name.startswith(
            ("watchdog", "urllib3", "PIL")
        ):
            return False

        # Filter out specific StreamlitAPI warnings
        if (
            record.levelno == logging.WARNING
            and record.name.startswith("streamlit")
            and (
                "missing ScriptRunContext" in record.getMessage()
                or "to view this Streamlit app on a browser"
                in record.getMessage()
            )
        ):
            return False

        return True


# Configure logging
logging.basicConfig(
    level=log_level, format="%(name)s:%(levelname)s: %(message)s"
)
# Add the noise filter to the root logger
logging.getLogger().addFilter(NoiseFilter())


def enable_test_mode():
    """Enable test mode by setting environment variable"""
    os.environ["TEST_MODE"] = "1"


def is_test_mode_enabled():
    """Check if app is running in test mode"""
    return os.environ.get("TEST_MODE") == "1"


def load_config():
    """Load configuration from config.json"""
    try:
        # Get the absolute path to the config file at project root
        # Since utils/config_utils.py is in the utils dir, we need to go up one level
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config.json",
        )
        logging.debug(f"Looking for config at: {config_path}")
        with open(config_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.warning(f"Failed to load config.json: {str(e)}")
        # Return empty config if file not found or invalid
        return {}


def get_test_landmarks():
    """Get test landmark data"""
    config = load_config()
    return config.get("test_landmarks", {})


def get_test_center(name="san_francisco") -> Optional[Dict]:
    """
    Get test center data with radius

    Returns:
        Dict with lat, lon, and radius_km or None if not found
    """
    config = load_config()
    centers = config.get("test_centers", {})
    return centers.get(name)
