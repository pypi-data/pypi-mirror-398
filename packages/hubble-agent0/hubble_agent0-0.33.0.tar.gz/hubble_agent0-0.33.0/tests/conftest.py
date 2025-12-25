"""
Pytest configuration file for Agent0 SDK tests.
Sets up logging to debug level for agent0_sdk only.
"""

import logging
import sys

# Configure logging: root logger at WARNING to suppress noisy dependencies
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Set debug level ONLY for agent0_sdk loggers
logging.getLogger('agent0_sdk').setLevel(logging.DEBUG)
logging.getLogger('agent0_sdk.core').setLevel(logging.DEBUG)

