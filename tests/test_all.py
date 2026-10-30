"""
Unit test entry point for test runners (e.g. python -m unittest).
"""

import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from validation import TestToyHashCollisionSuite

if __name__ == "__main__":
    import unittest
    unittest.main()
