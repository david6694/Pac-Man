"""Super pacgum powered-mode state."""

from __future__ import annotations

from dataclasses import dataclass


FLASHING_SECONDS = 2.0


@dataclass
class PowerMode:
    """Track frightened-mode timing and ghost-eating combo."""

    duration: float = 0.0
    time_left: float = 0.0
    ghosts_eaten: int = 0

    @property
    def is_active(self) -> bool:
        """Return whether ghosts are frightened."""
        return self.time_left > 0.0

    @property
    def is_flashing(self) -> bool:
        """Return whether frightened mode is close to ending."""
        return 0.0 < self.time_left <= FLASHING_SECONDS

    def start(self, level_index: int) -> bool:
        """Start power mode for a level and return whether it is active."""
        self.duration = frightened_duration(level_index)
        self.time_left = self.duration
        self.ghosts_eaten = 0
        return self.is_active

    def tick(self, seconds: float) -> bool:
        """Advance power-mode time and return whether it is still active."""
        if seconds <= 0 or not self.is_active:
            return self.is_active
        self.time_left = max(0.0, self.time_left - seconds)
        return self.is_active

    def reset(self) -> None:
        """Stop power mode."""
        self.time_left = 0.0
        self.ghosts_eaten = 0

    def eat_ghost(self) -> int:
        """Return the current combo index, then advance it."""
        combo_index = self.ghosts_eaten
        self.ghosts_eaten += 1
        return combo_index


def frightened_duration(level_index: int) -> float:
    """Return frightened duration for a zero-based project level."""
    level_number = level_index + 1
    if level_number > 10:
        return 0.0
    if level_number == 1:
        return 6.0
    if level_number <= 4:
        return 5.0
    if level_number <= 6:
        return 4.0
    return 3.0
