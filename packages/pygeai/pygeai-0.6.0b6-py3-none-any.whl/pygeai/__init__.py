import logging
import os
import sys
from pathlib import Path

__author__ = 'Globant'
__version__ = '0.6.0'

# Add vendor directory to Python path
package_root = Path(__file__).parent
vendor_path = str(package_root / 'vendor')
if vendor_path not in sys.path:
    sys.path.insert(0, vendor_path)

# Recommended handler for libraries.
# Reference: https://docs.python.org/3.3/howto/logging.html#configuring-logging-for-a-library
logger = logging.getLogger('geai')
logger.addHandler(logging.NullHandler())
