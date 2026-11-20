"""Level timer helpers for the Pac-Man engine."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LevelTimer:
    """Track elapsed and remaining time for one level."""

    limit: float
    elapsed: float = 0.0

    @property
    def time_left(self) -> float:
        """Return seconds left before the timer expires."""
        return max(0.0, self.limit - self.elapsed)

    @property
    def is_expired(self) -> bool:
        """Return whether the timer reached its limit."""
        return self.elapsed >= self.limit

    def tick(self, seconds: float) -> bool:
        """Advance time and return whether the timer expired."""
        if seconds <= 0:
            return self.is_expired
        self.elapsed += seconds
        return self.is_expired

    def reset(self) -> None:
        """Restart the timer from zero."""
        self.elapsed = 0.0
