"""
pytest configuration for wait-ci tests.
"""

import sys
from pathlib import Path

# Add src to path so all tests can import wait_ci
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
