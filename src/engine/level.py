"""Level state helpers for the Pac-Man engine."""

from __future__ import annotations

from dataclasses import dataclass, field

from .collision import collect_tile_at
from .maze import PlayableMaze, Position, Tile, generate_level
from .parser import GameConfig
from .score import ScoreBoard


@dataclass
class LevelState:
    """Generated level plus mutable board state."""

    index: int
    maze: PlayableMaze
    collected_pacgums: set[Position] = field(default_factory=set)

    @property
    def remaining_pacgums(self) -> int:
        """Return how many normal or super pacgums are still on the board."""
        total = 0
        for y, row in enumerate(self.maze.tiles):
            for x, tile in enumerate(row):
                position = Position(x, y)
                if tile in (Tile.PACGUM, Tile.SUPER_PACGUM):
                    if position not in self.collected_pacgums:
                        total += 1
        return total

    @property
    def is_cleared(self) -> bool:
        """Return whether every pacgum was collected."""
        return self.remaining_pacgums == 0

    def collect_tile(
        self,
        position: Position,
        scoreboard: ScoreBoard,
    ) -> bool:
        """Collect a tile on this level and update the score."""
        return collect_tile_at(
            self.maze,
            position,
            self.collected_pacgums,
            scoreboard,
        )


def create_level(config: GameConfig, level_index: int) -> LevelState:
    """Generate a level state from validated game config."""
    return LevelState(
        index=level_index,
        maze=generate_level(config, level_index),
    )
