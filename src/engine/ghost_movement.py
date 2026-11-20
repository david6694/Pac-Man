"""Ghost movement rules for the Pac-Man engine."""

from __future__ import annotations

from enum import Enum

from .entities import Direction, Ghost, GhostName, Pacman
from .maze import PlayableMaze, Position
from .movement import can_entity_move, move_entity, next_position


class GhostMode(str, Enum):
    """Classic ghost behavior modes."""

    CHASE = "chase"
    SCATTER = "scatter"
    FRIGHTENED = "frightened"


DIRECTION_PRIORITY = (
    Direction.UP,
    Direction.LEFT,
    Direction.DOWN,
    Direction.RIGHT,
)


def valid_ghost_directions(
    maze: PlayableMaze,
    ghost: Ghost,
    allow_reverse: bool = False,
) -> tuple[Direction, ...]:
    """Return directions the ghost can take from its current cell."""
    directions = tuple(
        direction
        for direction in DIRECTION_PRIORITY
        if can_entity_move(maze, ghost, direction, allow_reverse)
    )
    if directions:
        return directions
    if allow_reverse:
        return ()
    return valid_ghost_directions(maze, ghost, allow_reverse=True)


def choose_ghost_direction(
    maze: PlayableMaze,
    ghost: Ghost,
    target: Position,
    mode: GhostMode,
    allow_reverse: bool = False,
) -> Direction | None:
    """Choose a direction using classic targeting rules."""
    directions = valid_ghost_directions(maze, ghost, allow_reverse)
    if not directions:
        return None

    if mode == GhostMode.FRIGHTENED:
        return _frightened_direction(directions, ghost.position)

    return min(
        directions,
        key=lambda direction: _distance(
            next_position(ghost.position, direction),
            target,
        ),
    )


def move_ghost(
    maze: PlayableMaze,
    ghost: Ghost,
    target: Position,
    mode: GhostMode,
    allow_reverse: bool = False,
) -> bool:
    """Move one ghost one cell according to its current mode."""
    if allow_reverse:
        opposite = ghost.direction.opposite
        if can_entity_move(maze, ghost, opposite, allow_reverse=True):
            return move_entity(maze, ghost, opposite, allow_reverse=True)

    direction = choose_ghost_direction(
        maze,
        ghost,
        target,
        mode,
        allow_reverse,
    )
    if direction is None:
        return False
    return move_entity(
        maze,
        ghost,
        direction,
        allow_reverse or direction == ghost.direction.opposite,
    )


def move_ghosts(
    maze: PlayableMaze,
    ghosts: tuple[Ghost, ...],
    player: Pacman,
    mode: GhostMode,
    allow_reverse: bool = False,
) -> None:
    """Move every ghost one cell using classic personality targets."""
    blinky = _ghost_by_name(ghosts, GhostName.BLINKY)
    for ghost in ghosts:
        target = ghost_target(maze, ghost, player, blinky, mode)
        move_ghost(maze, ghost, target, mode, allow_reverse)


def ghost_target(
    maze: PlayableMaze,
    ghost: Ghost,
    player: Pacman,
    blinky: Ghost | None,
    mode: GhostMode,
) -> Position:
    """Return the target tile for one ghost in its current mode."""
    if mode == GhostMode.SCATTER:
        return _scatter_target(maze, ghost.name)
    if mode == GhostMode.FRIGHTENED:
        return ghost.position
    if ghost.name == GhostName.BLINKY:
        return player.position
    if ghost.name == GhostName.PINKY:
        return _ahead_of_player(player, 4)
    if ghost.name == GhostName.INKY:
        return _inky_target(player, blinky)
    if ghost.name == GhostName.CLYDE:
        if _distance(ghost.position, player.position) >= 8:
            return player.position
        return _scatter_target(maze, GhostName.CLYDE)
    return player.position


def ghost_mode_for_time(level_index: int, elapsed: float) -> GhostMode:
    """Return scatter or chase mode for the current level time."""
    for mode, duration in _mode_schedule(level_index):
        if elapsed < duration:
            return mode
        elapsed -= duration
    return GhostMode.CHASE


def _distance(first: Position, second: Position) -> int:
    """Return Manhattan distance between two grid positions."""
    return abs(first.x - second.x) + abs(first.y - second.y)


def _mode_schedule(level_index: int) -> tuple[tuple[GhostMode, float], ...]:
    """Return classic scatter/chase durations for a zero-based level index."""
    level_number = level_index + 1
    if level_number == 1:
        return (
            (GhostMode.SCATTER, 7.0),
            (GhostMode.CHASE, 20.0),
            (GhostMode.SCATTER, 7.0),
            (GhostMode.CHASE, 20.0),
            (GhostMode.SCATTER, 5.0),
            (GhostMode.CHASE, 20.0),
            (GhostMode.SCATTER, 5.0),
        )
    if level_number <= 4:
        long_chase = 1033.0
        first_scatter = 7.0
    else:
        long_chase = 1037.0
        first_scatter = 5.0
    return (
        (GhostMode.SCATTER, first_scatter),
        (GhostMode.CHASE, 20.0),
        (GhostMode.SCATTER, first_scatter),
        (GhostMode.CHASE, 20.0),
        (GhostMode.SCATTER, 5.0),
        (GhostMode.CHASE, long_chase),
        (GhostMode.SCATTER, 1.0 / 60.0),
    )


def _scatter_target(maze: PlayableMaze, ghost_name: GhostName) -> Position:
    """Return each ghost's scatter corner."""
    corners = {
        GhostName.BLINKY: Position(maze.width - 1, 0),
        GhostName.PINKY: Position(0, 0),
        GhostName.INKY: Position(maze.width - 1, maze.height - 1),
        GhostName.CLYDE: Position(0, maze.height - 1),
    }
    return corners[ghost_name]


def _ahead_of_player(player: Pacman, tiles: int) -> Position:
    """Return a tile several cells in front of Pac-Man."""
    return Position(
        player.position.x + player.direction.dx * tiles,
        player.position.y + player.direction.dy * tiles,
    )


def _inky_target(player: Pacman, blinky: Ghost | None) -> Position:
    """Return Inky's vector target using Pac-Man and Blinky."""
    if blinky is None:
        return _ahead_of_player(player, 2)

    ahead = _ahead_of_player(player, 2)
    vector_x = ahead.x - blinky.position.x
    vector_y = ahead.y - blinky.position.y
    return Position(ahead.x + vector_x, ahead.y + vector_y)


def _frightened_direction(
    directions: tuple[Direction, ...],
    position: Position,
) -> Direction:
    """Pick a deterministic pseudo-random frightened direction."""
    index = abs(position.x * 31 + position.y * 17) % len(directions)
    return directions[index]


def _ghost_by_name(
    ghosts: tuple[Ghost, ...],
    name: GhostName,
) -> Ghost | None:
    """Return the ghost with the requested name."""
    for ghost in ghosts:
        if ghost.name == name:
            return ghost
    return None
