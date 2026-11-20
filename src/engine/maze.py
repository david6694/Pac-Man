"""Maze generation and level layout helpers for the Pac-Man engine."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import Enum, IntFlag
from typing import TYPE_CHECKING, Protocol, cast

if TYPE_CHECKING:
    from collections.abc import Iterable

    from .parser import GameConfig, LevelConfig


class MazeGenerationError(Exception):
    """Raised when the external maze generator cannot create a level."""


class MazeGeneratorProtocol(Protocol):
    """Small part of the assigned generator API that the engine needs."""

    maze: list[list[int]]
    shortest_path: str | bool


class Wall(IntFlag):
    """Wall bits used by the assigned A-Maze-ing generator package."""

    NORTH = 1
    EAST = 2
    SOUTH = 4
    WEST = 8


class Tile(str, Enum):
    """Static content placed inside a maze cell."""

    EMPTY = " "
    PACGUM = "."
    SUPER_PACGUM = "o"


@dataclass(frozen=True)
class Position:
    """Position of one object in the maze grid."""

    x: int
    y: int


@dataclass(frozen=True)
class PlayableMaze:
    """Generated maze plus gameplay objects placed in it."""

    width: int
    height: int
    walls: tuple[tuple[int, ...], ...]
    tiles: tuple[tuple[Tile, ...], ...]
    player_spawn: Position
    ghost_spawns: tuple[Position, ...]
    seed: int
    shortest_path: str

    def in_bounds(self, position: Position) -> bool:
        """Return whether a position is inside the maze."""
        return 0 <= position.x < self.width and 0 <= position.y < self.height

    def is_walkable(self, position: Position) -> bool:
        """Return whether a cell can contain moving entities."""
        if not self.in_bounds(position):
            return False
        return self.walls[position.y][position.x] != int(
            Wall.NORTH | Wall.EAST | Wall.SOUTH | Wall.WEST
        )

    def has_wall(self, position: Position, wall: Wall) -> bool:
        """Return whether a cell has the requested wall."""
        if not self.in_bounds(position):
            return True
        return bool(self.walls[position.y][position.x] & wall.value)


def generate_level(config: GameConfig, level_index: int) -> PlayableMaze:
    """Generate and prepare one playable level.

    Args:
        config: Validated game configuration.
        level_index: Zero-based index in ``config.levels``.

    Returns:
        A generated maze with pacgums and spawn points.

    Raises:
        MazeGenerationError: If the level index is invalid or the external
            maze generator fails.
    """
    try:
        level = config.levels[level_index]
    except IndexError as exc:
        message = f"Level #{level_index + 1} is not defined in config."
        raise MazeGenerationError(message) from exc

    seed = _level_seed(config.seed, level, level_index)
    generator = _create_generator(level, config.maze_perfect, seed)
    walls = _freeze_walls(generator.maze)
    shortest_path = generator.shortest_path

    if not isinstance(shortest_path, str):
        shortest_path = ""

    return _build_playable_maze(walls, seed, shortest_path)


def _create_generator(
    level: LevelConfig,
    maze_perfect: bool,
    seed: int,
) -> MazeGeneratorProtocol:
    """Create the external maze generator with clean error handling."""
    try:
        from mazegenerator import MazeGenerator
    except ImportError as exc:
        message = (
            "The mazegenerator package is not installed. Install the assigned "
            "wheel before starting the game."
        )
        raise MazeGenerationError(message) from exc

    try:
        generator = MazeGenerator(
            size=(level.width, level.height),
            perfect=maze_perfect,
            seed=seed,
        )
        return cast(MazeGeneratorProtocol, generator)
    except Exception as exc:
        message = f"Maze generator failed for seed {seed}: {exc}"
        raise MazeGenerationError(message) from exc


def _level_seed(
    default_seed: int,
    level: LevelConfig,
    level_index: int,
) -> int:
    """Return a reproducible seed for a level."""
    if level.seed is not None:
        return int(level.seed)
    return int(default_seed + level_index)


def _freeze_walls(raw_walls: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    """Convert generator output to immutable tuples."""
    return tuple(tuple(cell for cell in row) for row in raw_walls)


def _build_playable_maze(
    walls: tuple[tuple[int, ...], ...],
    seed: int,
    shortest_path: str,
) -> PlayableMaze:
    """Place gameplay objects into generated maze cells."""
    height = len(walls)
    width = len(walls[0]) if height > 0 else 0
    if width == 0 or height == 0:
        raise MazeGenerationError("Maze generator returned an empty maze.")

    player_spawn = _nearest_walkable_cell(
        walls,
        Position(width // 2, height // 2),
    )
    ghost_spawns = _ghost_spawns(walls, width, height)
    super_pacgums = tuple(ghost_spawns)
    tiles = _place_tiles(walls, player_spawn, super_pacgums)

    return PlayableMaze(
        width=width,
        height=height,
        walls=walls,
        tiles=tiles,
        player_spawn=player_spawn,
        ghost_spawns=ghost_spawns,
        seed=seed,
        shortest_path=shortest_path,
    )


def _ghost_spawns(
    walls: tuple[tuple[int, ...], ...],
    width: int,
    height: int,
) -> tuple[Position, ...]:
    """Place ghosts near the four maze corners."""
    corners = (
        Position(0, 0),
        Position(width - 1, 0),
        Position(0, height - 1),
        Position(width - 1, height - 1),
    )
    return tuple(_nearest_walkable_cell(walls, corner) for corner in corners)


def _place_tiles(
    walls: tuple[tuple[int, ...], ...],
    player_spawn: Position,
    super_pacgums: tuple[Position, ...],
) -> tuple[tuple[Tile, ...], ...]:
    """Create the visible content grid for a playable maze."""
    super_cells = set(super_pacgums)
    rows: list[tuple[Tile, ...]] = []

    for y, row in enumerate(walls):
        tiles: list[Tile] = []
        for x, cell in enumerate(row):
            position = Position(x, y)
            tiles.append(
                _tile_for_cell(
                    cell,
                    position,
                    player_spawn,
                    super_cells,
                )
            )
        rows.append(tuple(tiles))

    return tuple(rows)


def _tile_for_cell(
    cell: int,
    position: Position,
    player_spawn: Position,
    super_cells: set[Position],
) -> Tile:
    """Return the initial tile for one maze cell."""
    if _is_closed_cell(cell):
        return Tile.EMPTY
    if position == player_spawn:
        return Tile.EMPTY
    if position in super_cells:
        return Tile.SUPER_PACGUM
    return Tile.PACGUM


def _nearest_walkable_cell(
    walls: tuple[tuple[int, ...], ...],
    start: Position,
) -> Position:
    """Find the nearest cell that is not completely closed by walls."""
    queue: deque[Position] = deque([start])
    visited = {start}

    while queue:
        position = queue.popleft()
        if _is_walkable_cell(walls, position):
            return position
        for neighbor in _neighbors(position):
            if neighbor not in visited and _position_exists(walls, neighbor):
                visited.add(neighbor)
                queue.append(neighbor)

    raise MazeGenerationError("Maze generator returned no walkable cells.")


def _neighbors(position: Position) -> Iterable[Position]:
    """Yield direct neighbors of a position."""
    yield Position(position.x + 1, position.y)
    yield Position(position.x - 1, position.y)
    yield Position(position.x, position.y + 1)
    yield Position(position.x, position.y - 1)


def _position_exists(
    walls: tuple[tuple[int, ...], ...],
    position: Position,
) -> bool:
    """Return whether a position exists in a raw wall grid."""
    height = len(walls)
    width = len(walls[0]) if height > 0 else 0
    return 0 <= position.x < width and 0 <= position.y < height


def _is_walkable_cell(
    walls: tuple[tuple[int, ...], ...],
    position: Position,
) -> bool:
    """Return whether a raw wall-grid cell can be used."""
    return _position_exists(walls, position) and not _is_closed_cell(
        walls[position.y][position.x]
    )


def _is_closed_cell(cell: int) -> bool:
    """Return whether all four directions are blocked."""
    return cell == int(Wall.NORTH | Wall.EAST | Wall.SOUTH | Wall.WEST)
