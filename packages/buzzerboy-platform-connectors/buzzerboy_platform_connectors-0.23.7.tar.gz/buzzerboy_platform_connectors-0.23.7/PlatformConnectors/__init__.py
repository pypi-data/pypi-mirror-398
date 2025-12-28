"""
Buzzerboy Platform Connectors

A Python utility library that parses integration JSON configurations into usable Django settings keys.
"""

__version__ = "0.5.3"
__author__ = "Buzzerboy Inc"
__email__ = "info@buzzerboy.com"

# Import main modules for easier access
from . import PlatformConnectors
from . import PlatformHelpers
from . import PackageMaker

__all__ = [
    'PlatformConnectors',
    'PlatformHelpers', 
    'PackageMaker'
]
