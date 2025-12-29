"""Claude Code settings.json management"""

import json
from pathlib import Path
from typing import Optional

from .models import Profile


class ClaudeConfigManager:
    """Manages Claude Code settings.json"""

    def __init__(self, settings_path: Optional[Path] = None):
        """Initialize config manager

        Args:
            settings_path: Path to settings.json (defaults to ~/.claude/settings.json)
        """
        if settings_path is None:
            settings_path = Path.home() / ".claude" / "settings.json"

        self.settings_path = Path(settings_path)

    def load_settings(self) -> dict:
        """Load settings.json

        Returns:
            Settings dictionary, empty dict if file doesn't exist
        """
        if not self.settings_path.exists():
            return {}

        try:
            with open(self.settings_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, TypeError):
            return {}

    def save_settings(self, settings: dict) -> None:
        """Save settings.json

        Args:
            settings: Settings dictionary to save
        """
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)

    def get_current_env(self) -> dict:
        """Get current env configuration from settings.json

        Returns:
            Current env configuration, empty dict if not found
        """
        settings = self.load_settings()
        return settings.get("env", {})

    def apply_profile(self, profile: Profile) -> None:
        """Apply a profile to Claude Code settings

        Args:
            profile: Profile to apply

        Note:
            If base_url or api_key is None in the profile, those fields
            won't be modified in the settings. Same for model configurations.
        """
        settings = self.load_settings()

        if "env" not in settings:
            settings["env"] = {}

        env = settings["env"]

        # Apply base URL and API key if provided
        if profile.base_url is not None:
            env["ANTHROPIC_BASE_URL"] = profile.base_url

        if profile.api_key is not None:
            env["ANTHROPIC_AUTH_TOKEN"] = profile.api_key

        # Apply model configurations if provided
        env["ANTHROPIC_SMALL_FAST_MODEL"] = profile.haiku_model
        env["ANTHROPIC_DEFAULT_HAIKU_MODEL"] = profile.haiku_model
        env["ANTHROPIC_DEFAULT_SONNET_MODEL"] = profile.sonnet_model
        env["ANTHROPIC_MODEL"] = profile.opus_model
        env["ANTHROPIC_DEFAULT_OPUS_MODEL"] = profile.opus_model

        if profile.haiku_model is None:
            del env["ANTHROPIC_SMALL_FAST_MODEL"]
            del env["ANTHROPIC_DEFAULT_HAIKU_MODEL"]
            
        if profile.sonnet_model is None:
            del env["ANTHROPIC_DEFAULT_SONNET_MODEL"]

        if profile.opus_model is None:
            del env["ANTHROPIC_MODEL"]
            del env["ANTHROPIC_DEFAULT_OPUS_MODEL"]

        self.save_settings(settings)

    def identify_current_profile(self, profiles: list[Profile]) -> Optional[str]:
        """Identify which profile is currently active

        Args:
            profiles: List of profiles to match against

        Returns:
            Name of matching profile, or None if custom/not found
        """
        current_env = self.get_current_env()

        # Get current values
        current_base_url = current_env.get("ANTHROPIC_BASE_URL")
        current_api_key = current_env.get("ANTHROPIC_AUTH_TOKEN")
        current_haiku = current_env.get("ANTHROPIC_DEFAULT_HAIKU_MODEL")
        current_sonnet = current_env.get("ANTHROPIC_DEFAULT_SONNET_MODEL")
        current_opus = current_env.get("ANTHROPIC_DEFAULT_OPUS_MODEL")

        # Try to find a matching profile
        for profile in profiles:
            # Check base_url and api_key match
            if profile.base_url and profile.base_url != current_base_url:
                continue
            if profile.api_key and profile.api_key != current_api_key:
                continue

            # Check models match (only if specified in profile)
            if profile.haiku_model and profile.haiku_model != current_haiku:
                continue
            if profile.sonnet_model and profile.sonnet_model != current_sonnet:
                continue
            if profile.opus_model and profile.opus_model != current_opus:
                continue

            # Found a match
            return profile.name

        # No match found - it's a custom configuration
        return None

    def get_current_profile_display(self, profiles: list[Profile]) -> str:
        """Get display name of current profile

        Args:
            profiles: List of profiles to match against

        Returns:
            Profile name or "Custom" if no match
        """
        profile_name = self.identify_current_profile(profiles)
        return profile_name if profile_name else "Custom"
