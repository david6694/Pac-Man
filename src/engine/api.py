"""Simple public API for the display layer."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .entities import Direction, GhostName
from .game import Game, GameStatus
from .game_events import GameEvent
from .ghost_movement import GhostMode
from .highscore import HighScoreEntry
from .maze import Position, Tile, Wall
from .parser import load_config


@dataclass(frozen=True)
class GhostSnapshot:
    """Display-safe ghost state."""

    name: GhostName
    position: Position
    direction: Direction


@dataclass(frozen=True)
class GameSnapshot:
    """Display-safe game state."""

    width: int
    height: int
    walls: tuple[tuple[int, ...], ...]
    tiles: tuple[tuple[Tile, ...], ...]
    player_position: Position
    player_direction: Direction
    ghosts: tuple[GhostSnapshot, ...]
    score: int
    lives: int
    level_index: int
    status: GameStatus
    ghost_mode: GhostMode
    time_left: float
    elapsed_time: float
    remaining_pacgums: int
    power_mode_active: bool
    power_mode_flashing: bool


class PacmanEngine:
    """One-file facade for display code."""

    def __init__(self, config_path: str | Path) -> None:
        """Create an engine from a config file path."""
        self.config = load_config(config_path)
        self.game = Game(self.config)

    def snapshot(self) -> GameSnapshot:
        """Return everything the display needs to draw the game."""
        return GameSnapshot(
            width=self.game.maze.width,
            height=self.game.maze.height,
            walls=self.game.maze.walls,
            tiles=self.game.maze.tiles,
            player_position=self.game.player_position,
            player_direction=self.game.player.direction,
            ghosts=tuple(
                GhostSnapshot(
                    name=ghost.name,
                    position=ghost.position,
                    direction=ghost.direction,
                )
                for ghost in self.game.ghosts
            ),
            score=self.game.score,
            lives=self.game.lives,
            level_index=self.game.level_index,
            status=self.game.status,
            ghost_mode=self.game.ghost_mode,
            time_left=self.game.time_left,
            elapsed_time=self.game.elapsed_time,
            remaining_pacgums=self.game.remaining_pacgums,
            power_mode_active=self.game.power_mode.is_active,
            power_mode_flashing=self.game.power_mode.is_flashing,
        )

    def tick(self, seconds: float) -> None:
        """Advance timers and ghost movement."""
        self.game.tick(seconds)

    def move(self, direction: Direction) -> bool:
        """Move Pac-Man one cell in a direction."""
        return self.game.move_player(direction)

    def move_up(self) -> bool:
        """Move Pac-Man up."""
        return self.move(Direction.UP)

    def move_down(self) -> bool:
        """Move Pac-Man down."""
        return self.move(Direction.DOWN)

    def move_left(self) -> bool:
        """Move Pac-Man left."""
        return self.move(Direction.LEFT)

    def move_right(self) -> bool:
        """Move Pac-Man right."""
        return self.move(Direction.RIGHT)

    def next_level(self) -> bool:
        """Start the next level after a level-clear event."""
        return self.game.next_level()

    def peek_events(self) -> tuple[GameEvent, ...]:
        """Read pending events without clearing them."""
        return self.game.peek_events()

    def pop_events(self) -> tuple[GameEvent, ...]:
        """Read pending events and clear them."""
        return self.game.pop_events()

    def record_highscore(self, name: str) -> tuple[HighScoreEntry, ...]:
        """Save the current score under a player name."""
        return self.game.record_highscore(name)


__all__ = [
    "Direction",
    "GameEvent",
    "GameSnapshot",
    "GameStatus",
    "GhostMode",
    "GhostName",
    "GhostSnapshot",
    "HighScoreEntry",
    "PacmanEngine",
    "Position",
    "Tile",
    "Wall",
]
