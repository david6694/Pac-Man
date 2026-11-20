"""Main game state for the Pac-Man engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .collision import colliding_ghost
from .entities import Direction, Ghost, GhostName, Pacman
from .game_events import GameEvent, GameEventType
from .ghost_movement import (
    GhostMode,
    ghost_mode_for_time,
    move_ghosts,
)
from .highscore import HighScoreEntry, record_highscore
from .level import LevelState, create_level
from .maze import PlayableMaze, Position, Tile
from .movement import move_entity
from .parser import GameConfig
from .power_mode import PowerMode
from .score import ScoreBoard
from .timer import LevelTimer


class GameStatus(str, Enum):
    """High-level state of the current game."""

    READY = "ready"
    PLAYING = "playing"
    LEVEL_CLEARED = "level_cleared"
    WON = "won"
    LOST = "lost"


@dataclass
class Game:
    """Mutable state for one Pac-Man game session."""

    config: GameConfig
    level_index: int = 0
    starting_score: int = 0
    lives: int = field(init=False)
    status: GameStatus = field(default=GameStatus.READY, init=False)
    level: LevelState = field(init=False)
    player: Pacman = field(init=False)
    ghosts: tuple[Ghost, ...] = field(init=False)
    scoreboard: ScoreBoard = field(init=False)
    timer: LevelTimer = field(init=False)
    power_mode: PowerMode = field(default_factory=PowerMode, init=False)
    ghost_mode: GhostMode = field(default=GhostMode.SCATTER, init=False)
    events: list[GameEvent] = field(default_factory=list, init=False)
    invincible: bool = False

    def __post_init__(self) -> None:
        """Create the first level after the config is known."""
        self.lives = self.config.lives
        self.scoreboard = ScoreBoard.from_config(
            self.config,
            value=self.starting_score,
        )
        self.timer = LevelTimer(limit=float(self.config.level_max_time))
        self.add_event(
            GameEventType.GAME_STARTED,
            "Game started.",
        )
        self.load_level(self.level_index)

    @property
    def score(self) -> int:
        """Return the current score value."""
        return self.scoreboard.value

    @property
    def player_position(self) -> Position:
        """Return Pac-Man's current position."""
        return self.player.position

    @property
    def ghost_positions(self) -> tuple[Position, ...]:
        """Return current ghost positions."""
        return tuple(ghost.position for ghost in self.ghosts)

    @property
    def maze(self) -> PlayableMaze:
        """Return the current playable maze."""
        return self.level.maze

    @property
    def elapsed_time(self) -> float:
        """Return seconds elapsed in the current level."""
        return self.timer.elapsed

    @property
    def time_left(self) -> float:
        """Return seconds left before the level timer expires."""
        return self.timer.time_left

    @property
    def remaining_pacgums(self) -> int:
        """Return how many normal or super pacgums are still on the board."""
        return self.level.remaining_pacgums

    def peek_events(self) -> tuple[GameEvent, ...]:
        """Return pending events without clearing them."""
        return tuple(self.events)

    def pop_events(self) -> tuple[GameEvent, ...]:
        """Return pending events and clear the event queue."""
        events = tuple(self.events)
        self.events.clear()
        return events

    def add_event(
        self,
        event_type: GameEventType,
        message: str,
        position: Position | None = None,
        ghost_name: GhostName | None = None,
        score_delta: int = 0,
    ) -> None:
        """Append one display-friendly event."""
        self.events.append(
            GameEvent(
                type=event_type,
                message=message,
                position=position,
                ghost_name=ghost_name,
                score_delta=score_delta,
                score=self.score,
                lives=self.lives,
                level_index=self.level_index,
            )
        )

    def load_level(self, level_index: int) -> None:
        """Generate a level and reset level-local state."""
        self.level_index = level_index
        self.level = create_level(self.config, level_index)
        self.player = Pacman(
            position=self.maze.player_spawn,
            spawn=self.maze.player_spawn,
            direction=Direction.LEFT,
        )
        ghost_names = (
            GhostName.BLINKY,
            GhostName.PINKY,
            GhostName.INKY,
            GhostName.CLYDE,
        )
        self.ghosts = tuple(
            Ghost(
                position=spawn,
                spawn=spawn,
                direction=Direction.LEFT,
                name=ghost_names[index],
            )
            for index, spawn in enumerate(self.maze.ghost_spawns)
        )
        self.timer.reset()
        self.power_mode.reset()
        self.ghost_mode = GhostMode.SCATTER
        self.status = GameStatus.READY
        self.add_event(
            GameEventType.LEVEL_STARTED,
            f"Level {self.level_index + 1} started.",
        )

    def move_player(self, direction: Direction) -> bool:
        """Move Pac-Man one cell if no wall blocks the direction."""
        if self.status in (GameStatus.WON, GameStatus.LOST):
            return False
        if self.status == GameStatus.READY:
            self.status = GameStatus.PLAYING

        previous_position = self.player.position
        if not move_entity(
            self.maze,
            self.player,
            direction,
            allow_reverse=True,
        ):
            return False

        if self.player.position != previous_position:
            self.add_event(
                GameEventType.PLAYER_MOVED,
                "Pac-Man moved.",
                position=self.player.position,
            )
        self.collect_tile(self.player.position)
        self.check_ghost_collision()
        return True

    def collect_tile(self, position: Position) -> None:
        """Collect a pacgum or super pacgum at the current position."""
        tile = self.maze.tiles[position.y][position.x]
        previous_score = self.score
        self.level.collect_tile(position, self.scoreboard)
        score_delta = self.score - previous_score
        if score_delta > 0 and tile == Tile.PACGUM:
            self.add_event(
                GameEventType.PACGUM_EATEN,
                "Pacgum eaten.",
                position=position,
                score_delta=score_delta,
            )
        elif score_delta > 0 and tile == Tile.SUPER_PACGUM:
            self.add_event(
                GameEventType.SUPER_PACGUM_EATEN,
                "Super pacgum eaten.",
                position=position,
                score_delta=score_delta,
            )
        if tile == Tile.SUPER_PACGUM:
            self.start_frightened_mode()
        if self.level.is_cleared:
            self.clear_level()

    def tick(self, seconds: float) -> None:
        """Advance the level timer."""
        if seconds <= 0 or self.status in (GameStatus.WON, GameStatus.LOST):
            return
        if self.status == GameStatus.READY:
            return

        if self.timer.tick(seconds):
            self.lose_life()
            return

        previous_positions = self.ghost_positions
        allow_reverse = self.update_ghost_mode(seconds)
        move_ghosts(
            self.maze,
            self.ghosts,
            self.player,
            self.ghost_mode,
            allow_reverse,
        )
        for ghost, previous_position in zip(
            self.ghosts,
            previous_positions,
            strict=False,
        ):
            if ghost.position != previous_position:
                self.add_event(
                    GameEventType.GHOST_MOVED,
                    f"{ghost.name.value} moved.",
                    position=ghost.position,
                    ghost_name=ghost.name,
                )
        self.check_ghost_collision()

    def start_frightened_mode(self) -> None:
        """Put ghosts into frightened mode after a super pacgum."""
        if not self.power_mode.start(self.level_index):
            return
        self.ghost_mode = GhostMode.FRIGHTENED
        for ghost in self.ghosts:
            ghost.direction = ghost.direction.opposite
        self.add_event(
            GameEventType.POWER_MODE_STARTED,
            "Power mode started.",
        )

    def update_ghost_mode(self, seconds: float) -> bool:
        """Update ghost mode and return whether ghosts may reverse."""
        previous_mode = self.ghost_mode
        if self.power_mode.tick(seconds):
            return previous_mode != GhostMode.FRIGHTENED

        self.ghost_mode = ghost_mode_for_time(
            self.level_index,
            self.elapsed_time,
        )
        if previous_mode == GhostMode.FRIGHTENED:
            self.add_event(
                GameEventType.POWER_MODE_ENDED,
                "Power mode ended.",
            )
        return (
            previous_mode != self.ghost_mode
            and previous_mode != GhostMode.FRIGHTENED
        )

    def check_ghost_collision(self) -> bool:
        """Handle Pac-Man touching a ghost."""
        ghost = colliding_ghost(self.player, self.ghosts)
        if ghost is None:
            return False
        if self.ghost_mode == GhostMode.FRIGHTENED:
            previous_score = self.score
            self.scoreboard.collect_ghost(self.power_mode.eat_ghost())
            score_delta = self.score - previous_score
            ghost.reset()
            self.add_event(
                GameEventType.GHOST_EATEN,
                f"{ghost.name.value} eaten.",
                position=ghost.position,
                ghost_name=ghost.name,
                score_delta=score_delta,
            )
            return True
        if self.invincible:
            return False
        self.lose_life()
        return True

    def lose_life(self) -> None:
        """Remove one life and reset or end the game."""
        self.lives -= 1
        if self.lives <= 0:
            self.status = GameStatus.LOST
            self.add_event(
                GameEventType.LIFE_LOST,
                "Life lost.",
                position=self.player.position,
            )
            self.add_event(
                GameEventType.GAME_LOST,
                "Game lost.",
            )
            return
        self.add_event(
            GameEventType.LIFE_LOST,
            "Life lost.",
            position=self.player.position,
        )
        self.reset_level_positions()

    def reset_level_positions(self) -> None:
        """Reset moving entities without removing already collected pacgums."""
        self.player.reset()
        for ghost in self.ghosts:
            ghost.reset()
        self.timer.reset()
        self.power_mode.reset()
        self.ghost_mode = GhostMode.SCATTER
        self.status = GameStatus.READY

    def clear_level(self) -> None:
        """Move to the next level or finish the game."""
        if self.level_index + 1 >= len(self.config.levels):
            self.status = GameStatus.WON
            self.add_event(
                GameEventType.GAME_WON,
                "Game won.",
            )
            return
        self.status = GameStatus.LEVEL_CLEARED
        self.add_event(
            GameEventType.LEVEL_CLEARED,
            f"Level {self.level_index + 1} cleared.",
        )

    def next_level(self) -> bool:
        """Load the next level after the current one is cleared."""
        if self.status != GameStatus.LEVEL_CLEARED:
            return False
        self.load_level(self.level_index + 1)
        return True

    def record_highscore(self, name: str) -> tuple[HighScoreEntry, ...]:
        """Save the current score and return the updated high score table."""
        highscores = record_highscore(
            self.config.highscore_filename,
            name,
            self.score,
        )
        self.add_event(
            GameEventType.HIGHSCORE_RECORDED,
            "High score recorded.",
        )
        return highscores
