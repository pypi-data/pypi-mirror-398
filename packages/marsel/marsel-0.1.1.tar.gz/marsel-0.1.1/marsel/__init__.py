"""
Marsel - A lightweight utility library
"""

from ._redis import RedisClient
from .core import Marsel

__version__ = "0.0.1"
__author__ = "Shaxzodbek"
__email__ = "muxtorovshaxzodbek16@gmail.com"

__all__ = ["Marsel", "RedisClient"]
