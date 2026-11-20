"""Display-friendly events emitted by the game engine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .entities import GhostName
from .maze import Position


class GameEventType(str, Enum):
    """Kinds of events the display layer can react to."""

    GAME_STARTED = "game_started"
    LEVEL_STARTED = "level_started"
    PLAYER_MOVED = "player_moved"
    PACGUM_EATEN = "pacgum_eaten"
    SUPER_PACGUM_EATEN = "super_pacgum_eaten"
    POWER_MODE_STARTED = "power_mode_started"
    POWER_MODE_ENDED = "power_mode_ended"
    GHOST_MOVED = "ghost_moved"
    GHOST_EATEN = "ghost_eaten"
    LIFE_LOST = "life_lost"
    LEVEL_CLEARED = "level_cleared"
    GAME_WON = "game_won"
    GAME_LOST = "game_lost"
    HIGHSCORE_RECORDED = "highscore_recorded"


@dataclass(frozen=True)
class GameEvent:
    """One engine event for the display layer."""

    type: GameEventType
    message: str
    position: Position | None = None
    ghost_name: GhostName | None = None
    score_delta: int = 0
    score: int = 0
    lives: int = 0
    level_index: int = 0
