"""Profile storage management"""

import json
import shutil
from pathlib import Path
from typing import List, Optional

from .models import Profile


class ProfileManager:
    """Manages profile storage"""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize profile manager

        Args:
            config_dir: Custom config directory (defaults to ~/.config/claude-profile-switcher)
        """
        if config_dir is None:
            config_dir = Path.home() / ".config" / "claude-profile-switcher"

        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.profiles_file = self.config_dir / "profiles.json"

        # Initialize predefined profiles if first run
        self._initialize_predefined_profiles()

    def _initialize_predefined_profiles(self) -> None:
        """Copy predefined profiles on first run"""
        if not self.profiles_file.exists():
            # Get the predefined profiles file from package directory
            package_dir = Path(__file__).parent
            predefined_file = package_dir / "predefined_profiles.json"

            if predefined_file.exists():
                try:
                    shutil.copy(predefined_file, self.profiles_file)
                except Exception:
                    # If copy fails, create empty profiles file
                    self.save_profiles([])

    def get_predefined_profiles(self) -> List[Profile]:
        """Get predefined profiles from package

        Returns:
            List of predefined profiles
        """
        package_dir = Path(__file__).parent
        predefined_file = package_dir / "predefined_profiles.json"

        if not predefined_file.exists():
            return []

        try:
            with open(predefined_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [Profile.from_dict(p) for p in data]
        except (json.JSONDecodeError, KeyError, TypeError):
            return []

    def load_profiles(self) -> List[Profile]:
        """Load profiles from storage

        Returns:
            List of profiles, empty list if file doesn't exist
        """
        if not self.profiles_file.exists():
            return []

        try:
            with open(self.profiles_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [Profile.from_dict(p) for p in data]
        except (json.JSONDecodeError, KeyError, TypeError):
            return []

    def save_profiles(self, profiles: List[Profile]) -> None:
        """Save profiles to storage

        Args:
            profiles: List of profiles to save
        """
        data = [p.to_dict() for p in profiles]
        with open(self.profiles_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_profile(self, profile: Profile) -> None:
        """Add a new profile

        Args:
            profile: Profile to add
        """
        profiles = self.load_profiles()
        profiles.append(profile)
        self.save_profiles(profiles)

    def update_profile(self, name: str, updated_profile: Profile) -> bool:
        """Update an existing profile

        Args:
            name: Name of profile to update
            updated_profile: New profile data

        Returns:
            True if profile was updated, False if not found
        """
        profiles = self.load_profiles()
        for i, profile in enumerate(profiles):
            if profile.name == name:
                profiles[i] = updated_profile
                self.save_profiles(profiles)
                return True
        return False

    def delete_profile(self, name: str) -> bool:
        """Delete a profile

        Args:
            name: Name of profile to delete

        Returns:
            True if profile was deleted, False if not found
        """
        profiles = self.load_profiles()
        original_length = len(profiles)
        profiles = [p for p in profiles if p.name != name]

        if len(profiles) < original_length:
            self.save_profiles(profiles)
            return True
        return False

    def get_profile(self, name: str) -> Optional[Profile]:
        """Get a profile by name

        Args:
            name: Profile name

        Returns:
            Profile if found, None otherwise
        """
        profiles = self.load_profiles()
        for profile in profiles:
            if profile.name == name:
                return profile
        return None
