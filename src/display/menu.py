"""Menu and overlay rendering for the Pac-Man game."""

from typing import Sequence
import pygame
from engine import HighScoreEntry
from display.constants import (
    BLACK,
    DARK_GRAY,
    LIGHT_GRAY,
    RED,
    WHITE,
    YELLOW,
)


def draw_menu(
    screen: pygame.Surface,
    font: pygame.font.Font,
    large_font: pygame.font.Font,
    screen_width: int,
    screen_height: int,
    menu_selection: int,
    anim_tick: int,
) -> None:
    """Draw Main Menu."""
    scale = max(1.0, min(screen_width / 800, screen_height / 600))
    title = large_font.render("PAC-MAN", True, YELLOW)
    title_rect = title.get_rect(
        center=(screen_width // 2, round(80 * scale))
    )
    screen.blit(title, title_rect)

    options = [
        "Start Game",
        "View Highscores",
        "Instructions",
        "Settings",
        "Exit",
    ]
    for idx, option in enumerate(options):
        color = YELLOW if idx == menu_selection else WHITE
        text = font.render(option, True, color)
        rect = text.get_rect(
            center=(
                screen_width // 2,
                round(180 * scale + idx * 45 * scale),
            )
        )
        screen.blit(text, rect)

        # Draw a small pacman next to selection
        if idx == menu_selection:
            pac_radius = round(10 * scale)
            pac_x = rect.left - round(30 * scale)
            pac_y = rect.centery
            pygame.draw.circle(screen, YELLOW, (pac_x, pac_y), pac_radius)
            # Mouth animation
            if anim_tick % 10 < 5:
                mouth_size = pac_radius
                pygame.draw.polygon(
                    screen,
                    BLACK,
                    [
                        (pac_x, pac_y),
                        (pac_x + mouth_size, pac_y - mouth_size // 2),
                        (pac_x + mouth_size, pac_y + mouth_size // 2),
                    ],
                )


def draw_settings(
    screen: pygame.Surface,
    font: pygame.font.Font,
    large_font: pygame.font.Font,
    screen_width: int,
    screen_height: int,
    resolution_options: Sequence[str],
    current_resolution: int,
    settings_selection: int,
) -> None:
    """Draw settings screen."""
    scale = max(1.0, min(screen_width / 800, screen_height / 600))
    title = large_font.render("SETTINGS", True, YELLOW)
    screen.blit(
        title,
        title.get_rect(center=(screen_width // 2, round(50 * scale))),
    )

    heading = font.render("Resolution", True, WHITE)
    screen.blit(
        heading,
        heading.get_rect(center=(screen_width // 2, round(115 * scale))),
    )

    for idx, option in enumerate(resolution_options):
        color = YELLOW if idx == settings_selection else WHITE
        prefix = "> " if idx == current_resolution else "  "
        text = font.render(f"{prefix}{option}", True, color)
        screen.blit(
            text,
            text.get_rect(
                center=(
                    screen_width // 2,
                    round(160 * scale + idx * 35 * scale),
                )
            ),
        )

    back_idx = len(resolution_options)
    back_color = YELLOW if settings_selection == back_idx else WHITE
    back = font.render("Back", True, back_color)
    screen.blit(
        back,
        back.get_rect(
            center=(
                screen_width // 2,
                round(180 * scale + back_idx * 35 * scale),
            )
        ),
    )

    prompt = font.render(
        "Enter to apply. ESC to return to main menu.", True, LIGHT_GRAY
    )
    screen.blit(
        prompt,
        prompt.get_rect(
            center=(screen_width // 2, screen_height - round(50 * scale))
        ),
    )


def draw_instructions(
    screen: pygame.Surface,
    font: pygame.font.Font,
    large_font: pygame.font.Font,
    screen_width: int,
    screen_height: int,
) -> None:
    """Draw instructions screen."""
    scale = max(1.0, min(screen_width / 800, screen_height / 600))
    title = large_font.render("INSTRUCTIONS", True, YELLOW)
    screen.blit(
        title,
        title.get_rect(center=(screen_width // 2, round(50 * scale))),
    )

    lines = [
        "Use Arrow Keys or WASD to move Pac-Man.",
        "Eat all pacgums (.) to win the level.",
        "Eat super pacgums (o) to make ghosts edible.",
        "Avoid contact with ghosts when they are colored!",
        "",
        "CHEATS (for review):",
        "  [I] - Toggle Invincibility",
        "  [F] - Toggle Ghost Freeze",
        "  [L] - Level Skip",
        "  [G] - Add Extra Life",
        "  [K] - Toggle 2x Speed Multiplier",
        "",
        "Press Enter or ESC to return to main menu.",
    ]

    for idx, line in enumerate(lines):
        color = WHITE if "CHEATS" not in line else RED
        text = font.render(line, True, color)
        screen.blit(
            text,
            text.get_rect(
                center=(
                    screen_width // 2,
                    round(130 * scale + idx * 25 * scale),
                )
            ),
        )


def draw_highscores(
    screen: pygame.Surface,
    font: pygame.font.Font,
    large_font: pygame.font.Font,
    screen_width: int,
    screen_height: int,
    highscores: Sequence[HighScoreEntry],
) -> None:
    """Draw highscores screen."""
    scale = max(1.0, min(screen_width / 800, screen_height / 600))
    title = large_font.render("HIGH SCORES", True, YELLOW)
    screen.blit(
        title,
        title.get_rect(center=(screen_width // 2, round(50 * scale))),
    )

    if not highscores:
        no_scores = font.render("No highscores yet!", True, WHITE)
        screen.blit(
            no_scores,
            no_scores.get_rect(
                center=(screen_width // 2, round(200 * scale))
            ),
        )
    else:
        for idx, entry in enumerate(highscores[:10]):
            fmt = f"{idx + 1}. {entry.name:<15} {entry.score}"
            text = font.render(fmt, True, WHITE)
            screen.blit(
                text,
                text.get_rect(
                    center=(
                        screen_width // 2,
                        round(120 * scale + idx * 30 * scale),
                    )
                ),
            )

    prompt = font.render(
        "Press Enter or ESC to return to main menu.", True, YELLOW
    )
    screen.blit(
        prompt,
        prompt.get_rect(
            center=(screen_width // 2, screen_height - round(50 * scale))
        ),
    )


def draw_pause_overlay(
    screen: pygame.Surface,
    font: pygame.font.Font,
    large_font: pygame.font.Font,
    screen_width: int,
    screen_height: int,
) -> None:
    """Draw pause screen overlay on top of the rendered game."""
    scale = max(1.0, min(screen_width / 800, screen_height / 600))
    # Draw dark overlay
    overlay = pygame.Surface((screen_width, screen_height))
    overlay.set_alpha(150)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))

    title = large_font.render("GAME PAUSED", True, YELLOW)
    screen.blit(
        title,
        title.get_rect(
            center=(
                screen_width // 2,
                screen_height // 2 - round(50 * scale),
            )
        ),
    )

    resume = font.render("Press [R] or ESC to Resume", True, WHITE)
    screen.blit(
        resume,
        resume.get_rect(
            center=(
                screen_width // 2,
                screen_height // 2 + round(10 * scale),
            )
        ),
    )

    menu = font.render("Press [M] to Return to Main Menu", True, WHITE)
    screen.blit(
        menu,
        menu.get_rect(
            center=(
                screen_width // 2,
                screen_height // 2 + round(50 * scale),
            )
        ),
    )


def draw_game_over(
    screen: pygame.Surface,
    font: pygame.font.Font,
    large_font: pygame.font.Font,
    screen_width: int,
    screen_height: int,
    score: int,
    input_name: str,
    anim_tick: int,
) -> None:
    """Draw Game Over name input screen."""
    scale = max(1.0, min(screen_width / 800, screen_height / 600))
    title = large_font.render("GAME OVER", True, RED)
    screen.blit(
        title,
        title.get_rect(center=(screen_width // 2, round(100 * scale))),
    )

    score_text = font.render(f"Final Score: {score}", True, WHITE)
    screen.blit(
        score_text,
        score_text.get_rect(
            center=(screen_width // 2, round(180 * scale))
        ),
    )

    prompt = font.render("Enter your name for Highscores:", True, YELLOW)
    screen.blit(
        prompt,
        prompt.get_rect(center=(screen_width // 2, round(240 * scale))),
    )

    # Draw input field
    input_width = round(300 * scale)
    input_height = round(40 * scale)
    input_rect = pygame.Rect(
        screen_width // 2 - input_width // 2,
        round(280 * scale),
        input_width,
        input_height,
    )
    pygame.draw.rect(screen, DARK_GRAY, input_rect)
    pygame.draw.rect(screen, WHITE, input_rect, max(2, round(2 * scale)))

    name_surf = font.render(input_name, True, WHITE)
    text_padding = round(10 * scale)
    screen.blit(
        name_surf,
        (input_rect.x + text_padding, input_rect.y + round(8 * scale)),
    )

    # Cursor
    if anim_tick % 20 < 10:
        cursor_x = input_rect.x + text_padding + name_surf.get_width()
        pygame.draw.line(
            screen,
            WHITE,
            (cursor_x, input_rect.y + round(8 * scale)),
            (cursor_x, input_rect.y + input_height - round(8 * scale)),
            max(2, round(2 * scale)),
        )

    help_text = font.render("Press ENTER to Save & Exit", True, LIGHT_GRAY)
    screen.blit(
        help_text,
        help_text.get_rect(
            center=(screen_width // 2, round(360 * scale))
        ),
    )


def draw_victory(
    screen: pygame.Surface,
    font: pygame.font.Font,
    large_font: pygame.font.Font,
    screen_width: int,
    screen_height: int,
    score: int,
    input_name: str,
    anim_tick: int,
) -> None:
    """Draw Victory name input screen."""
    scale = max(1.0, min(screen_width / 800, screen_height / 600))
    title = large_font.render("VICTORY!", True, YELLOW)
    screen.blit(
        title,
        title.get_rect(center=(screen_width // 2, round(100 * scale))),
    )

    score_text = font.render(f"Final Score: {score}", True, WHITE)
    screen.blit(
        score_text,
        score_text.get_rect(
            center=(screen_width // 2, round(180 * scale))
        ),
    )

    prompt = font.render("Enter your name for Highscores:", True, YELLOW)
    screen.blit(
        prompt,
        prompt.get_rect(center=(screen_width // 2, round(240 * scale))),
    )

    # Draw input field
    input_width = round(300 * scale)
    input_height = round(40 * scale)
    input_rect = pygame.Rect(
        screen_width // 2 - input_width // 2,
        round(280 * scale),
        input_width,
        input_height,
    )
    pygame.draw.rect(screen, DARK_GRAY, input_rect)
    pygame.draw.rect(screen, WHITE, input_rect, max(2, round(2 * scale)))

    name_surf = font.render(input_name, True, WHITE)
    text_padding = round(10 * scale)
    screen.blit(
        name_surf,
        (input_rect.x + text_padding, input_rect.y + round(8 * scale)),
    )

    # Cursor
    if anim_tick % 20 < 10:
        cursor_x = input_rect.x + text_padding + name_surf.get_width()
        pygame.draw.line(
            screen,
            WHITE,
            (cursor_x, input_rect.y + round(8 * scale)),
            (cursor_x, input_rect.y + input_height - round(8 * scale)),
            max(2, round(2 * scale)),
        )

    help_text = font.render("Press ENTER to Save & Exit", True, LIGHT_GRAY)
    screen.blit(
        help_text,
        help_text.get_rect(
            center=(screen_width // 2, round(360 * scale))
        ),
    )
