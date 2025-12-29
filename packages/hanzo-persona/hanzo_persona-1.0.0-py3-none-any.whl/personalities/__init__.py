"""
Hanzo Persona - Unified programmer personality profiles.
"""

from .personality_loader import (
    PersonalityLoader,
    loader,
    get_all_personalities,
    get_personality,
    list_personality_names,
    count_personalities,
)

__all__ = [
    "PersonalityLoader",
    "loader",
    "get_all_personalities",
    "get_personality",
    "list_personality_names",
    "count_personalities",
]

__version__ = "1.0.0"