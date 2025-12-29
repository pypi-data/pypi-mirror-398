"""Data models for profiles"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Profile:
    """Represents a Claude Code API configuration profile"""

    name: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    haiku_model: Optional[str] = None
    sonnet_model: Optional[str] = None
    opus_model: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert profile to dictionary"""
        return {
            "name": self.name,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "haiku_model": self.haiku_model,
            "sonnet_model": self.sonnet_model,
            "opus_model": self.opus_model,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Profile":
        """Create profile from dictionary"""
        return cls(
            name=data["name"],
            base_url=data.get("base_url"),
            api_key=data.get("api_key"),
            haiku_model=data.get("haiku_model"),
            sonnet_model=data.get("sonnet_model"),
            opus_model=data.get("opus_model"),
        )

    def is_complete(self) -> bool:
        """Check if profile has complete required fields"""
        return bool(self.base_url and self.api_key)

    def get_display_info(self) -> str:
        """Get display string for profile"""
        status = "✓" if self.is_complete() else "✗"
        return f"{self.name} [{status}]"
