"""Sprite loading and animation helper for the Pac-Man GUI."""

from pathlib import Path
import pygame
from engine import GhostMode, GhostName, Direction

# Caches
_SPRITES_LOADED = False
_LOADED_TILE_SIZE = 0
PACMAN_CHOMP: list[pygame.Surface] = []
GHOSTS: dict[GhostName, dict[Direction, list[pygame.Surface]]] = {}
EDIBLE_BLUE: list[pygame.Surface] = []
EDIBLE_WHITE: list[pygame.Surface] = []
EYES: dict[Direction, pygame.Surface] = {}


def load_sprites(tile_size: int) -> None:
    """Load all sprite images and scale them to the tile size."""
    global _SPRITES_LOADED, _LOADED_TILE_SIZE
    if _SPRITES_LOADED and _LOADED_TILE_SIZE == tile_size:
        return

    PACMAN_CHOMP.clear()
    GHOSTS.clear()
    EDIBLE_BLUE.clear()
    EDIBLE_WHITE.clear()
    EYES.clear()

    base_path = Path(__file__).parent.parent.parent / "pacman_sprite"
    pacman_path = base_path / "pacman"
    ghosts_path = base_path / "ghosts"

    # 1. Load Pacman chomping frames
    for i in range(1, 4):
        p_img = pygame.image.load(
            str(pacman_path / f"pacman_{i}.png")
        ).convert_alpha()
        p_scaled = pygame.transform.scale(p_img, (tile_size, tile_size))
        PACMAN_CHOMP.append(p_scaled)

    # 2. Ghost mappings
    ghost_colors_map = {
        GhostName.BLINKY: "red",
        GhostName.PINKY: "pink",
        GhostName.INKY: "blue",
        GhostName.CLYDE: "orange",
    }

    direction_map = {
        Direction.UP: "up",
        Direction.DOWN: "down",
        Direction.LEFT: "left",
        Direction.RIGHT: "right",
    }

    # 3. Load Normal Ghost sprites
    for ghost_name, color_str in ghost_colors_map.items():
        GHOSTS[ghost_name] = {}
        for direction, dir_str in direction_map.items():
            GHOSTS[ghost_name][direction] = []
            for frame in (1, 2):
                filename = f"ghost_{color_str}_{dir_str}_{frame}.png"
                img = pygame.image.load(
                    str(ghosts_path / filename)
                ).convert_alpha()
                scaled = pygame.transform.scale(img, (tile_size, tile_size))
                GHOSTS[ghost_name][direction].append(scaled)

    # 4. Load Edible / Frightened Ghost sprites
    for frame in (1, 2):
        eb_img = pygame.image.load(
            str(ghosts_path / f"edible_blue_{frame}.png")
        ).convert_alpha()
        EDIBLE_BLUE.append(
            pygame.transform.scale(eb_img, (tile_size, tile_size))
        )

        ew_img = pygame.image.load(
            str(ghosts_path / f"edible_white_{frame}.png")
        ).convert_alpha()
        EDIBLE_WHITE.append(
            pygame.transform.scale(ew_img, (tile_size, tile_size))
        )

    # 5. Load Eaten Ghost eyes
    for direction, dir_str in direction_map.items():
        eyes_img = pygame.image.load(
            str(ghosts_path / f"eyes_{dir_str}.png")
        ).convert_alpha()
        EYES[direction] = pygame.transform.scale(
            eyes_img, (tile_size, tile_size)
        )

    _SPRITES_LOADED = True
    _LOADED_TILE_SIZE = tile_size


def get_pacman_sprite(
    direction: Direction, anim_tick: int
) -> pygame.Surface:
    """Retrieve and rotate the current Pac-Man movement animation frame."""
    # 4-stage chomping cycle: closed -> half-open -> open -> half-open
    cycle = (anim_tick // 3) % 4
    if cycle == 0:
        frame = PACMAN_CHOMP[0]
    elif cycle == 1:
        frame = PACMAN_CHOMP[1]
    elif cycle == 2:
        frame = PACMAN_CHOMP[2]
    else:
        frame = PACMAN_CHOMP[1]

    # Rotate based on direction (default is facing RIGHT)
    angle = 0
    if direction == Direction.UP:
        angle = 90
    elif direction == Direction.LEFT:
        angle = 180
    elif direction == Direction.DOWN:
        angle = 270

    if angle != 0:
        return pygame.transform.rotate(frame, angle)
    return frame


def get_ghost_sprite(
    ghost_name: GhostName,
    direction: Direction,
    ghost_mode: GhostMode,
    power_mode_flashing: bool,
    anim_tick: int,
) -> pygame.Surface:
    """Retrieve the current animated ghost sprite based on mode/direction."""
    # Alternate frames every 8 ticks
    frame_idx = (anim_tick // 8) % 2

    if ghost_mode == GhostMode.FRIGHTENED:
        # Frightened flashing (cycles between white and blue)
        if power_mode_flashing and (anim_tick // 8) % 2 == 0:
            return EDIBLE_WHITE[frame_idx]
        return EDIBLE_BLUE[frame_idx]

    # Normal ghost movement sprite
    return GHOSTS[ghost_name][direction][frame_idx]
