"""Collision helpers for Pac-Man gameplay rules."""

from __future__ import annotations

from .entities import Ghost, Pacman
from .maze import PlayableMaze, Position
from .score import ScoreBoard


def collect_tile_at(
    maze: PlayableMaze,
    position: Position,
    collected_positions: set[Position],
    scoreboard: ScoreBoard,
) -> bool:
    """Collect the tile at a position if it gives points."""
    if position in collected_positions:
        return False

    tile = maze.tiles[position.y][position.x]
    if not scoreboard.collect_tile(tile):
        return False

    collected_positions.add(position)
    return True


def colliding_ghost(
    player: Pacman,
    ghosts: tuple[Ghost, ...],
) -> Ghost | None:
    """Return the first ghost touching Pac-Man, if any."""
    for ghost in ghosts:
        if player.position == ghost.position:
            return ghost
    return None


def touches_ghost(player: Pacman, ghosts: tuple[Ghost, ...]) -> bool:
    """Return whether Pac-Man is touching a ghost."""
    return colliding_ghost(player, ghosts) is not None
