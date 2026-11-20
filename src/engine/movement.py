"""Movement helpers for maze entities."""

from __future__ import annotations

from .entities import Direction, Entity
from .maze import PlayableMaze, Position


def next_position(position: Position, direction: Direction) -> Position:
    """Return the position reached by moving one cell in a direction."""
    return Position(position.x + direction.dx, position.y + direction.dy)


def can_move(
    maze: PlayableMaze,
    position: Position,
    direction: Direction,
) -> bool:
    """Return whether an entity can move from a position in a direction."""
    if maze.has_wall(position, direction.wall):
        return False
    return maze.is_walkable(next_position(position, direction))


def can_entity_move(
    maze: PlayableMaze,
    entity: Entity,
    direction: Direction,
    allow_reverse: bool = False,
) -> bool:
    """Return whether an entity can move in a direction."""
    if not allow_reverse and direction == entity.direction.opposite:
        return False
    return can_move(maze, entity.position, direction)


def move_entity(
    maze: PlayableMaze,
    entity: Entity,
    direction: Direction,
    allow_reverse: bool = False,
) -> bool:
    """Move an entity one cell if the maze allows it."""
    if not can_entity_move(maze, entity, direction, allow_reverse):
        return False
    entity.position = next_position(entity.position, direction)
    entity.direction = direction
    return True
