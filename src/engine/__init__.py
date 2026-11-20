"""Pac-Man engine package."""

from .api import GameSnapshot, GhostSnapshot, PacmanEngine
from .collision import collect_tile_at, colliding_ghost, touches_ghost
from .entities import Direction, Entity, Ghost, GhostName, Pacman
from .game import Game, GameStatus
from .game_events import GameEvent, GameEventType
from .ghost_movement import (
    GhostMode,
    choose_ghost_direction,
    ghost_mode_for_time,
    ghost_target,
    move_ghost,
    move_ghosts,
    valid_ghost_directions,
)
from .highscore import (
    HighScoreEntry,
    HighScoreError,
    add_highscore,
    load_highscores,
    record_highscore,
    save_highscores,
)
from .level import LevelState, create_level
from .maze import (
    MazeGenerationError,
    PlayableMaze,
    Position,
    Tile,
    Wall,
    generate_level,
)
from .movement import can_move, move_entity, next_position
from .parser import ConfigParserError, GameConfig, LevelConfig, load_config
from .power_mode import PowerMode, frightened_duration
from .score import ScoreBoard
from .timer import LevelTimer

__all__ = [
    "can_move",
    "choose_ghost_direction",
    "collect_tile_at",
    "colliding_ghost",
    "ConfigParserError",
    "Direction",
    "Entity",
    "Game",
    "GameEvent",
    "GameEventType",
    "GameSnapshot",
    "GameConfig",
    "GameStatus",
    "Ghost",
    "GhostMode",
    "GhostName",
    "GhostSnapshot",
    "HighScoreEntry",
    "HighScoreError",
    "add_highscore",
    "create_level",
    "ghost_mode_for_time",
    "ghost_target",
    "frightened_duration",
    "LevelConfig",
    "LevelState",
    "LevelTimer",
    "load_highscores",
    "MazeGenerationError",
    "move_ghost",
    "move_ghosts",
    "move_entity",
    "next_position",
    "Pacman",
    "PacmanEngine",
    "PlayableMaze",
    "Position",
    "PowerMode",
    "record_highscore",
    "save_highscores",
    "ScoreBoard",
    "Tile",
    "touches_ghost",
    "valid_ghost_directions",
    "Wall",
    "generate_level",
    "load_config",
]
