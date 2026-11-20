"""Ghost rendering for the Pac-Man game using sprites."""

import pygame
from engine import GhostSnapshot, GameSnapshot
from display.sprites import get_ghost_sprite


def draw_ghost_entity(
    screen: pygame.Surface,
    ghost: GhostSnapshot,
    snapshot: GameSnapshot,
    tile_size: int,
    anim_tick: int,
    y_offset: int,
    x_offset: int = 0,
    pixel_position: tuple[float, float] | None = None,
) -> None:
    """Draw individual ghost on screen using its current sprite frame."""
    tx: float
    ty: float
    if pixel_position is None:
        tx = ghost.position.x * tile_size + x_offset
        ty = ghost.position.y * tile_size + y_offset
    else:
        tx, ty = pixel_position

    ghost_surf = get_ghost_sprite(
        ghost.name,
        ghost.direction,
        snapshot.ghost_mode,
        snapshot.power_mode_flashing,
        anim_tick,
    )
    screen.blit(ghost_surf, (round(tx), round(ty)))
