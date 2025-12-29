#!/usr/bin/env python3
"""
Unified personality loader for Hanzo ecosystem.
Loads personalities from the centralized JSON file.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

# Find the personality data file
PERSONA_DIR = Path(__file__).parent
PERSONALITY_FILE = PERSONA_DIR / "all_personalities.json"

class PersonalityLoader:
    """Load and manage personalities from centralized JSON."""

    def __init__(self, file_path: Optional[Path] = None):
        """Initialize loader with optional custom path."""
        self.file_path = file_path or PERSONALITY_FILE
        self._personalities: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        """Load personalities from JSON file."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Personality file not found: {self.file_path}")

        with open(self.file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Convert list to dict for easy lookup
        for personality in data:
            self._personalities[personality['name']] = personality

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all personalities as a list."""
        return list(self._personalities.values())

    def get(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific personality by name."""
        return self._personalities.get(name)

    def filter_by_tags(self, tags: List[str]) -> List[Dict[str, Any]]:
        """Filter personalities by tags."""
        results = []
        for personality in self._personalities.values():
            if any(tag in personality.get('tags', []) for tag in tags):
                results.append(personality)
        return results

    def get_names(self) -> List[str]:
        """Get all personality names."""
        return list(self._personalities.keys())

    def count(self) -> int:
        """Get total number of personalities."""
        return len(self._personalities)

# Global instance for easy import
loader = PersonalityLoader()

# Convenience functions
def get_all_personalities() -> List[Dict[str, Any]]:
    """Get all personalities."""
    return loader.get_all()

def get_personality(name: str) -> Optional[Dict[str, Any]]:
    """Get a specific personality."""
    return loader.get(name)

def list_personality_names() -> List[str]:
    """List all personality names."""
    return loader.get_names()

def count_personalities() -> int:
    """Count total personalities."""
    return loader.count()

if __name__ == "__main__":
    # Test the loader
    print(f"Loaded {count_personalities()} personalities")
    print(f"Available personalities: {', '.join(list_personality_names()[:10])}...")

    # Test specific personality
    linus = get_personality("linus")
    if linus:
        print(f"\nExample - {linus['name']}: {linus['programmer']}")
        print(f"Philosophy: {linus.get('philosophy', 'N/A')}")