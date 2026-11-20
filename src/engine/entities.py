"""Moving entities used by the Pac-Man engine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .maze import Position, Wall


class Direction(Enum):
    """One movement direction on the maze grid."""

    UP = (0, -1, Wall.NORTH)
    RIGHT = (1, 0, Wall.EAST)
    DOWN = (0, 1, Wall.SOUTH)
    LEFT = (-1, 0, Wall.WEST)

    @property
    def opposite(self) -> Direction:
        """Return the opposite direction."""
        opposites = {
            Direction.UP: Direction.DOWN,
            Direction.RIGHT: Direction.LEFT,
            Direction.DOWN: Direction.UP,
            Direction.LEFT: Direction.RIGHT,
        }
        return opposites[self]

    @property
    def dx(self) -> int:
        """Horizontal movement step."""
        return self.value[0]

    @property
    def dy(self) -> int:
        """Vertical movement step."""
        return self.value[1]

    @property
    def wall(self) -> Wall:
        """Wall that blocks movement in this direction."""
        return self.value[2]


@dataclass
class Entity:
    """A movable object inside the maze."""

    position: Position
    spawn: Position
    direction: Direction

    def reset(self) -> None:
        """Move the entity back to its spawn point."""
        self.position = self.spawn


@dataclass
class Pacman(Entity):
    """Player entity."""


class GhostName(str, Enum):
    """Classic Pac-Man ghost names."""

    BLINKY = "blinky"
    PINKY = "pinky"
    INKY = "inky"
    CLYDE = "clyde"


@dataclass
class Ghost(Entity):
    """Ghost entity."""

    name: GhostName
