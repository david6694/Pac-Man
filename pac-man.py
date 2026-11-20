#!/usr/bin/env python3
"""Main entry point for the Pac-Man game with a Pygame-based GUI."""

import sys
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Make sure src is in the import path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import pygame and engine modules
import pygame  # noqa: E402
from engine import (  # noqa: E402
    Direction,
    GameStatus,
    GhostName,
    PacmanEngine,
    Position,
)
from engine.highscore import load_highscores  # noqa: E402
from engine.highscore import MAX_PLAYER_NAME_LENGTH  # noqa: E402

from display.constants import BLACK, WHITE, YELLOW, RED  # noqa: E402
from display.ghost import draw_ghost_entity  # noqa: E402
from display.maze import draw_maze_grid  # noqa: E402
from display.menu import (  # noqa: E402
    draw_menu,
    draw_settings,
    draw_instructions,
    draw_highscores,
    draw_pause_overlay,
    draw_game_over,
    draw_victory,
)
from display.sprites import (  # noqa: E402
    load_sprites,
    get_pacman_sprite,
)


RENDER_FPS = 60
MOVES_PER_SECOND = 6
ANIMATION_TICKS_PER_SECOND = 15
RESPAWN_READY_DELAY = 0.5
HUD_HEIGHT = 56
SETTINGS_PATH = Path("data/settings.json")
SETTINGS_RESOLUTION_KEY = "resolution_index"
BASE_SCREEN_WIDTH = 800
BASE_SCREEN_HEIGHT = 600
DEFAULT_TILE_SIZE = 24
MIN_TILE_SIZE = 10
MAX_TILE_SIZE = 48
RESOLUTION_OPTIONS: list[tuple[str, tuple[int, int] | None]] = [
    ("Auto", None),
    ("800 x 600", (800, 600)),
    ("1024 x 768", (1024, 768)),
    ("1280 x 720", (1280, 720)),
    ("1366 x 768", (1366, 768)),
    ("1920 x 1080", (1920, 1080)),
]


@dataclass
class RenderTrack:
    """Grid positions used to interpolate one moving sprite."""

    previous: Position
    current: Position


class PacmanGUI:
    """Handles Pygame rendering, menus, and user input for Pac-Man."""

    def __init__(self, config_path: str) -> None:
        """Initialize the GUI and load game engine."""
        pygame.init()
        pygame.display.set_caption("Pac-Man")
        self.clock = pygame.time.Clock()

        self.config_path = config_path
        try:
            self.engine = PacmanEngine(config_path)
        except Exception as e:
            print(f"Error loading configuration: {e}", file=sys.stderr)
            sys.exit(1)

        # Highscores
        self.highscore_path = self.engine.config.highscore_filename
        self.highscores = list(load_highscores(self.highscore_path))

        # Tile size and font
        self.ui_scale = 1.0
        self.hud_height = HUD_HEIGHT
        self.maze_x_offset = 0
        self.maze_y_offset = HUD_HEIGHT
        self.tile_size = DEFAULT_TILE_SIZE
        self.font = pygame.font.SysFont("Comic Sans MS", 20)
        self.large_font = pygame.font.SysFont("Comic Sans MS", 36)

        self.settings_path = SETTINGS_PATH
        self.resolution_index = self.load_resolution_setting()
        self.screen_width = 0
        self.screen_height = 0
        self.screen = pygame.Surface((1, 1))
        self.apply_resolution()

        # Game state machine
        self.state = "menu"
        self.menu_selection = 0
        self.settings_selection = self.resolution_index
        self.input_name = ""
        self.cheat_invincibility = False
        self.cheat_ghost_freeze = False
        self.cheat_speed_multiplier = 1.0
        self.engine.game.invincible = self.cheat_invincibility
        self.buffered_direction: Direction | None = None

        # Animation state
        self.anim_tick = 0
        self.animation_accumulator = 0.0
        self.movement_accumulator = 0.0
        self.respawn_ready_delay = 0.0
        self.player_render_track: RenderTrack
        self.ghost_render_tracks: dict[GhostName, RenderTrack]
        self.reset_render_tracks()

    def run(self) -> None:
        """Main game loop."""
        running = True
        while running:
            dt = self.clock.tick(RENDER_FPS) / 1000.0  # seconds passed
            self.update_animation(dt)

            running = self.handle_events()

            playing = GameStatus.PLAYING
            snapshot = self.engine.snapshot()
            is_game = self.state == "game"
            if is_game:
                self.update_respawn_ready_delay(dt)
            if is_game and snapshot.status == playing:
                self.update_game_logic(dt)
            else:
                self.movement_accumulator = 0.0
                self.reset_render_tracks(snapshot)

            self.draw()

        pygame.quit()

    def update_animation(self, dt: float) -> None:
        """Advance animation ticks independently from render FPS."""
        animation_step = 1.0 / ANIMATION_TICKS_PER_SECOND
        self.animation_accumulator += dt
        while self.animation_accumulator >= animation_step:
            self.anim_tick = (self.anim_tick + 1) % 30
            self.animation_accumulator -= animation_step

    def update_game_logic(self, dt: float) -> None:
        """Advance Pac-Man and ghosts at a fixed grid movement rate."""
        movement_step = 1.0 / MOVES_PER_SECOND
        speed = max(1.0, self.cheat_speed_multiplier)

        self.movement_accumulator += dt * speed
        while self.movement_accumulator >= movement_step:
            before = self.engine.snapshot()
            self.move_pacman_auto()
            tick_seconds = movement_step / speed
            if not self.cheat_ghost_freeze:
                self.engine.tick(tick_seconds)
            else:
                self.engine.game.timer.tick(tick_seconds)
                self.engine.game.power_mode.tick(tick_seconds)
            after = self.engine.snapshot()
            self.update_render_tracks(before, after)
            self.update_respawn_delay_from_snapshots(before, after)
            self.movement_accumulator -= movement_step

    def update_respawn_ready_delay(self, dt: float) -> None:
        """Count down the post-collision delay before input is accepted."""
        if self.respawn_ready_delay <= 0:
            return
        self.respawn_ready_delay = max(0.0, self.respawn_ready_delay - dt)

    def update_respawn_delay_from_snapshots(
        self,
        before: Any,
        after: Any,
    ) -> None:
        """Start the respawn delay after Pac-Man loses a life."""
        if after.status == GameStatus.READY and after.lives < before.lives:
            self.respawn_ready_delay = RESPAWN_READY_DELAY

    def reset_render_tracks(self, snapshot: Any | None = None) -> None:
        """Snap render positions to the current engine positions."""
        if snapshot is None:
            snapshot = self.engine.snapshot()
        self.player_render_track = RenderTrack(
            snapshot.player_position,
            snapshot.player_position,
        )
        self.ghost_render_tracks = {
            ghost.name: RenderTrack(ghost.position, ghost.position)
            for ghost in snapshot.ghosts
        }

    def update_render_tracks(self, before: Any, after: Any) -> None:
        """Start interpolation tracks after one grid logic step."""
        if after.status != GameStatus.PLAYING:
            self.reset_render_tracks(after)
            return

        self.player_render_track = RenderTrack(
            before.player_position,
            after.player_position,
        )
        previous_ghosts = {
            ghost.name: ghost.position for ghost in before.ghosts
        }
        self.ghost_render_tracks = {
            ghost.name: RenderTrack(
                previous_ghosts.get(ghost.name, ghost.position),
                ghost.position,
            )
            for ghost in after.ghosts
        }

    def movement_progress(self) -> float:
        """Return how far the current rendered move has visually advanced."""
        movement_step = 1.0 / MOVES_PER_SECOND
        return min(1.0, max(0.0, self.movement_accumulator / movement_step))

    def interpolated_grid_position(
        self,
        track: RenderTrack,
        progress: float,
    ) -> tuple[float, float]:
        """Blend between two grid cells for smooth rendering."""
        return (
            track.previous.x
            + (track.current.x - track.previous.x) * progress,
            track.previous.y
            + (track.current.y - track.previous.y) * progress,
        )

    def handle_events(self) -> bool:
        """Handle user inputs. Returns False if game is exited."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if self.state == "menu":
                    if event.key in (pygame.K_UP, pygame.K_w):
                        self.menu_selection = (self.menu_selection - 1) % 5
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.menu_selection = (self.menu_selection + 1) % 5
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.select_menu_option()
                    elif event.key == pygame.K_ESCAPE:
                        return False

                elif self.state == "settings":
                    self.handle_settings_key(event.key)

                elif self.state in ("instructions", "highscores"):
                    if event.key in (
                        pygame.K_ESCAPE,
                        pygame.K_RETURN,
                        pygame.K_SPACE,
                    ):
                        self.state = "menu"

                elif self.state == "game":
                    snapshot = self.engine.snapshot()
                    if event.key == pygame.K_ESCAPE:
                        self.state = "pause"
                    # Cheat codes
                    elif event.key == pygame.K_i:
                        self.toggle_invincibility()
                    elif event.key == pygame.K_f:  # Freeze ghosts
                        self.cheat_ghost_freeze = (
                            not self.cheat_ghost_freeze
                        )
                    elif event.key == pygame.K_l:  # Level skip
                        self.engine.game.clear_level()
                    elif event.key == pygame.K_g:  # Add lives
                        self.engine.game.lives += 1
                    elif event.key == pygame.K_k:  # Speed toggle
                        if self.cheat_speed_multiplier == 1.0:
                            self.cheat_speed_multiplier = 2.0
                        else:
                            self.cheat_speed_multiplier = 1.0

                    # Player controls
                    controls_ok = (GameStatus.PLAYING, GameStatus.READY)
                    if snapshot.status in controls_ok:
                        direction = None
                        if event.key in (pygame.K_UP, pygame.K_w):
                            direction = Direction.UP
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            direction = Direction.DOWN
                        elif event.key in (pygame.K_LEFT, pygame.K_a):
                            direction = Direction.LEFT
                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            direction = Direction.RIGHT

                        if direction is not None:
                            if snapshot.status == GameStatus.READY:
                                if self.respawn_ready_delay > 0:
                                    continue
                                before = self.engine.snapshot()
                                self.engine.move(direction)
                                after = self.engine.snapshot()
                                self.update_render_tracks(before, after)
                            else:
                                self.buffered_direction = direction

                elif self.state == "pause":
                    if event.key in (pygame.K_ESCAPE, pygame.K_r):
                        self.state = "game"
                    elif event.key == pygame.K_m:
                        self.state = "menu"

                elif self.state in ("game_over", "victory"):
                    if event.key == pygame.K_BACKSPACE:
                        self.input_name = self.input_name[:-1]
                    elif event.key == pygame.K_RETURN:
                        if self.input_name.strip():
                            # Record high score
                            self.engine.record_highscore(self.input_name)
                            # Reload high scores
                            h_path = self.highscore_path
                            self.highscores = list(load_highscores(h_path))
                            self.state = "menu"
                            self.input_name = ""
                    else:
                        is_ok = (
                            event.unicode.isalnum()
                            or event.unicode == " "
                        )
                        name_has_room = (
                            len(self.input_name) < MAX_PLAYER_NAME_LENGTH
                        )
                        if name_has_room and is_ok:
                            self.input_name += event.unicode

        return True

    def select_menu_option(self) -> None:
        """Execute action based on current menu selection."""
        if self.menu_selection == 0:  # Start game
            # Reset engine
            self.engine = PacmanEngine(self.config_path)
            self.state = "game"
            self.cheat_invincibility = False
            self.cheat_ghost_freeze = False
            self.cheat_speed_multiplier = 1.0
            self.engine.game.invincible = self.cheat_invincibility
            self.buffered_direction = None
            self.animation_accumulator = 0.0
            self.movement_accumulator = 0.0
            self.respawn_ready_delay = 0.0
            self.reset_render_tracks()
        elif self.menu_selection == 1:  # View highscores
            self.highscores = list(load_highscores(self.highscore_path))
            self.state = "highscores"
        elif self.menu_selection == 2:  # Instructions
            self.state = "instructions"
        elif self.menu_selection == 3:  # Settings
            self.settings_selection = self.resolution_index
            self.state = "settings"
        elif self.menu_selection == 4:  # Exit
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    def toggle_invincibility(self) -> None:
        """Toggle ghost-collision invincibility."""
        self.cheat_invincibility = not self.cheat_invincibility
        self.engine.game.invincible = self.cheat_invincibility

    def handle_settings_key(self, key: int) -> None:
        """Handle keyboard navigation in the settings screen."""
        option_count = len(RESOLUTION_OPTIONS) + 1
        if key in (pygame.K_UP, pygame.K_w):
            self.settings_selection = (
                self.settings_selection - 1
            ) % option_count
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.settings_selection = (
                self.settings_selection + 1
            ) % option_count
        elif key in (pygame.K_ESCAPE,):
            self.state = "menu"
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.settings_selection == len(RESOLUTION_OPTIONS):
                self.state = "menu"
            else:
                self.resolution_index = self.settings_selection
                self.apply_resolution()
                self.save_settings()

    def apply_resolution(self) -> None:
        """Apply the selected window resolution and matching tile size."""
        snapshot = self.engine.snapshot()
        _, resolution = RESOLUTION_OPTIONS[self.resolution_index]

        if resolution is None:
            self.ui_scale = 1.0
            self.tile_size = DEFAULT_TILE_SIZE
            self.screen_width = max(600, snapshot.width * self.tile_size)
            self.screen_height = max(
                500, snapshot.height * self.tile_size + self.hud_height
            )
        else:
            self.screen_width, self.screen_height = resolution
            self.ui_scale = max(
                1.0,
                min(
                    self.screen_width / BASE_SCREEN_WIDTH,
                    self.screen_height / BASE_SCREEN_HEIGHT,
                ),
            )

        self.font = pygame.font.SysFont(
            "Comic Sans MS", round(20 * self.ui_scale)
        )
        self.large_font = pygame.font.SysFont(
            "Comic Sans MS", round(36 * self.ui_scale)
        )
        self.hud_height = round(HUD_HEIGHT * self.ui_scale)

        if resolution is not None:
            available_height = self.screen_height - self.hud_height
            tile_size = min(
                MAX_TILE_SIZE,
                self.screen_width // snapshot.width,
                available_height // snapshot.height,
            )
            self.tile_size = max(MIN_TILE_SIZE, tile_size)

        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height)
        )
        maze_width = snapshot.width * self.tile_size
        maze_height = snapshot.height * self.tile_size
        self.maze_x_offset = max(0, (self.screen_width - maze_width) // 2)
        available_height = max(0, self.screen_height - self.hud_height)
        self.maze_y_offset = self.hud_height + max(
            0, (available_height - maze_height) // 2
        )
        load_sprites(self.tile_size)

    def load_resolution_setting(self) -> int:
        """Return the saved resolution index when settings.json is valid."""
        try:
            raw_settings = self.settings_path.read_text(encoding="utf-8")
            settings = json.loads(raw_settings)
        except (OSError, json.JSONDecodeError):
            return 0

        value = settings.get(SETTINGS_RESOLUTION_KEY)
        if isinstance(value, bool) or not isinstance(value, int):
            return 0
        if not 0 <= value < len(RESOLUTION_OPTIONS):
            return 0
        return value

    def save_settings(self) -> None:
        """Persist user settings under data/settings.json."""
        try:
            raw_settings = self.settings_path.read_text(encoding="utf-8")
            payload = json.loads(raw_settings)
        except (OSError, json.JSONDecodeError):
            payload = {}

        if not isinstance(payload, dict):
            payload = {}
        payload[SETTINGS_RESOLUTION_KEY] = self.resolution_index

        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings_path.write_text(
            json.dumps(payload, indent=2) + "\n",
            encoding="utf-8",
        )

    def move_pacman_auto(self) -> None:
        """Advance Pac-Man in the buffered or current direction."""
        if self.buffered_direction is not None:
            # Try to turn in the buffered direction
            if self.engine.move(self.buffered_direction):
                self.buffered_direction = None
                return

        # Continue in current direction
        self.engine.move(self.engine.game.player.direction)

    def draw(self) -> None:
        """Render current state on the screen."""
        self.screen.fill(BLACK)

        if self.state == "menu":
            draw_menu(
                self.screen,
                self.font,
                self.large_font,
                self.screen_width,
                self.screen_height,
                self.menu_selection,
                self.anim_tick,
            )
        elif self.state == "instructions":
            draw_instructions(
                self.screen,
                self.font,
                self.large_font,
                self.screen_width,
                self.screen_height,
            )
        elif self.state == "settings":
            draw_settings(
                self.screen,
                self.font,
                self.large_font,
                self.screen_width,
                self.screen_height,
                [label for label, _ in RESOLUTION_OPTIONS],
                self.resolution_index,
                self.settings_selection,
            )
        elif self.state == "highscores":
            draw_highscores(
                self.screen,
                self.font,
                self.large_font,
                self.screen_width,
                self.screen_height,
                self.highscores,
            )
        elif self.state == "game":
            self.draw_game()
        elif self.state == "pause":
            self.draw_pause()
        elif self.state == "game_over":
            score = self.engine.snapshot().score
            draw_game_over(
                self.screen,
                self.font,
                self.large_font,
                self.screen_width,
                self.screen_height,
                score,
                self.input_name,
                self.anim_tick,
            )
        elif self.state == "victory":
            score = self.engine.snapshot().score
            draw_victory(
                self.screen,
                self.font,
                self.large_font,
                self.screen_width,
                self.screen_height,
                score,
                self.input_name,
                self.anim_tick,
            )

        pygame.display.flip()

    def draw_game_hud(self, snapshot: Any) -> None:
        """Draw HUD display."""
        score_text = self.font.render(
            f"Score: {snapshot.score}", True, WHITE
        )
        padding = round(20 * self.ui_scale)
        top = round(15 * self.ui_scale)
        hud_center_y = top + self.font.get_height() // 2
        self.screen.blit(score_text, (padding, top))

        lives_text = self.font.render(
            f"Lives: {snapshot.lives}", True, WHITE
        )
        self.screen.blit(
            lives_text,
            (
                self.screen_width - lives_text.get_width() - padding,
                top,
            ),
        )

        level_idx = snapshot.level_index + 1
        level_text = self.font.render(
            f"Level: {level_idx}", True, WHITE
        )
        self.screen.blit(
            level_text,
            level_text.get_rect(
                center=(
                    self.screen_width // 2 - round(70 * self.ui_scale),
                    hud_center_y,
                )
            ),
        )

        time_text = self.font.render(
            f"Time: {int(snapshot.time_left)}s", True, WHITE
        )
        self.screen.blit(
            time_text,
            time_text.get_rect(
                center=(
                    self.screen_width // 2 + round(70 * self.ui_scale),
                    hud_center_y,
                )
            ),
        )

        # Draw Cheats active HUD
        cheat_status = []
        if self.cheat_invincibility:
            cheat_status.append("INVINCIBLE")
        if self.cheat_ghost_freeze:
            cheat_status.append("FROZEN")
        if self.cheat_speed_multiplier > 1.0:
            cheat_status.append("SPEED_2X")
        if cheat_status:
            fmt = f"CHEATS: {', '.join(cheat_status)}"
            cheat_text = self.font.render(fmt, True, RED)
            self.screen.blit(
                cheat_text, (padding, round(45 * self.ui_scale))
            )

    def draw_moving_entities(
        self, snapshot: Any, x_offset: int, y_offset: int
    ) -> None:
        """Draw player and ghosts."""
        # Draw Player (Pac-man)
        progress = self.movement_progress()
        p_grid_x, p_grid_y = self.interpolated_grid_position(
            self.player_render_track,
            progress,
        )
        pacman_surf = get_pacman_sprite(
            snapshot.player_direction, self.anim_tick
        )
        tx = p_grid_x * self.tile_size + x_offset
        ty = p_grid_y * self.tile_size + y_offset
        self.screen.blit(pacman_surf, (round(tx), round(ty)))

        # Draw moving ghosts
        for ghost in snapshot.ghosts:
            track = self.ghost_render_tracks.get(
                ghost.name,
                RenderTrack(ghost.position, ghost.position),
            )
            ghost_grid_x, ghost_grid_y = self.interpolated_grid_position(
                track,
                progress,
            )
            draw_ghost_entity(
                self.screen,
                ghost,
                snapshot,
                self.tile_size,
                self.anim_tick,
                y_offset,
                x_offset,
                (
                    ghost_grid_x * self.tile_size + x_offset,
                    ghost_grid_y * self.tile_size + y_offset,
                ),
            )

    def draw_game(self) -> None:
        """Draw main gameplay screen."""
        snapshot = self.engine.snapshot()

        # Handle Game Engine state transitions here dynamically
        if snapshot.status == GameStatus.LOST:
            self.state = "game_over"
            return
        elif snapshot.status == GameStatus.WON:
            self.state = "victory"
            return
        elif snapshot.status == GameStatus.LEVEL_CLEARED:
            # Advance to next level automatically
            self.engine.next_level()
            self.apply_resolution()
            self.reset_render_tracks()
            return

        self.draw_game_hud(snapshot)

        draw_maze_grid(
            self.screen,
            snapshot,
            self.engine.game.level.collected_pacgums,
            self.tile_size,
            self.anim_tick,
            self.maze_y_offset,
            self.maze_x_offset,
        )
        self.draw_moving_entities(
            snapshot, self.maze_x_offset, self.maze_y_offset
        )

        # Ready state overlay
        if snapshot.status == GameStatus.READY:
            ready_text = self.large_font.render("READY!", True, YELLOW)
            self.screen.blit(
                ready_text,
                ready_text.get_rect(
                    center=(
                        self.screen_width // 2,
                        self.screen_height // 2,
                    )
                ),
            )

    def draw_pause(self) -> None:
        """Draw pause screen overlay."""
        # Draw game first
        self.draw_game()

        draw_pause_overlay(
            self.screen,
            self.font,
            self.large_font,
            self.screen_width,
            self.screen_height,
        )


def main() -> None:
    """Main execution entry point."""
    if len(sys.argv) != 2:
        print("Usage: python3 pac-man.py config.json", file=sys.stderr)
        sys.exit(1)

    config_path = sys.argv[1]
    if not Path(config_path).is_file():
        fmt = f"Error: configuration file '{config_path}' not found."
        print(fmt, file=sys.stderr)
        sys.exit(1)

    gui = PacmanGUI(config_path)
    try:
        gui.run()
    except KeyboardInterrupt:
        pygame.quit()
        sys.exit(0)


if __name__ == "__main__":
    main()
