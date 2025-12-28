"""Configuration for Rainfall."""

from dataclasses import dataclass, field
import os


@dataclass
class RainfallConfig:
    """Configuration for Rainfall execution."""
    
    # API settings
    api_key: str | None = None
    model: str = "gemini-3-flash-preview"
    
    # Generation settings
    temperature: float = 0.2  # Lower = more deterministic
    max_tokens: int = 1024
    
    # Behavior
    verbose: bool = False
    dry_run: bool = False
    
    def __post_init__(self):
        # Fall back to environment variable if no API key provided
        if self.api_key is None:
            self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("RAINFALL_API_KEY")
    
    def validate(self) -> None:
        """Validate the configuration."""
        if not self.api_key and not self.dry_run:
            raise ValueError(
                "No API key found. Set GEMINI_API_KEY environment variable "
                "or pass --api-key to the command."
            )
