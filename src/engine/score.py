"""Score handling for the Pac-Man engine."""

from __future__ import annotations

from dataclasses import dataclass

from .maze import Tile
from .parser import GameConfig


@dataclass
class ScoreBoard:
    """Mutable score plus configured scoring rules."""

    points_per_pacgum: int
    points_per_super_pacgum: int
    points_per_ghost: int
    value: int = 0

    @classmethod
    def from_config(
        cls,
        config: GameConfig,
        value: int = 0,
    ) -> ScoreBoard:
        """Create a scoreboard from validated game config."""
        return cls(
            points_per_pacgum=config.points_per_pacgum,
            points_per_super_pacgum=config.points_per_super_pacgum,
            points_per_ghost=config.points_per_ghost,
            value=value,
        )

    def collect_tile(self, tile: Tile) -> bool:
        """Add points for a tile and return whether it was collectible."""
        if tile == Tile.PACGUM:
            self.value += self.points_per_pacgum
            return True
        if tile == Tile.SUPER_PACGUM:
            self.value += self.points_per_super_pacgum
            return True
        return False

    def collect_ghost(self, combo_index: int = 0) -> None:
        """Add points for eating one frightened ghost."""
        self.value += self.points_per_ghost * (2 ** combo_index)
