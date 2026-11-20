"""Maze rendering for the Pac-Man game."""

import pygame
from engine import Tile, Wall, GameSnapshot, Position
from display.constants import BLUE, YELLOW


def draw_maze_lines(
    screen: pygame.Surface,
    wall_val: int,
    px: int,
    py: int,
    sz: int,
) -> None:
    """Draw line bounds for stylized retro walls."""
    if wall_val & Wall.NORTH.value:
        pygame.draw.line(screen, BLUE, (px, py), (px + sz, py), 2)
    if wall_val & Wall.EAST.value:
        pygame.draw.line(screen, BLUE, (px + sz, py), (px + sz, py + sz), 2)
    if wall_val & Wall.SOUTH.value:
        pygame.draw.line(screen, BLUE, (px, py + sz), (px + sz, py + sz), 2)
    if wall_val & Wall.WEST.value:
        pygame.draw.line(screen, BLUE, (px, py), (px, py + sz), 2)


def draw_maze_grid(
    screen: pygame.Surface,
    snapshot: GameSnapshot,
    collected_pacgums: set[Position],
    tile_size: int,
    anim_tick: int,
    y_offset: int,
    x_offset: int = 0,
) -> None:
    """Draw maze corridors and pacgums."""
    pacgum_radius = max(2, tile_size // 8)
    super_pacgum_radius = max(4, tile_size // 4)

    for y in range(snapshot.height):
        for x in range(snapshot.width):
            wall_val = snapshot.walls[y][x]
            px = x * tile_size + x_offset
            py = y * tile_size + y_offset

            tile = snapshot.tiles[y][x]

            # If tile is a wall
            if wall_val > 0:
                draw_maze_lines(screen, wall_val, px, py, tile_size)

            # Draw Pacgums (if they are not collected yet)
            is_eaten = Position(x, y) in collected_pacgums
            if tile == Tile.PACGUM and not is_eaten:
                pygame.draw.circle(
                    screen,
                    YELLOW,
                    (px + tile_size // 2, py + tile_size // 2),
                    pacgum_radius,
                )
            elif tile == Tile.SUPER_PACGUM and not is_eaten:
                # Flash animation for super pacgum
                if anim_tick % 15 < 10:
                    pygame.draw.circle(
                        screen,
                        YELLOW,
                        (px + tile_size // 2, py + tile_size // 2),
                        super_pacgum_radius,
                    )
