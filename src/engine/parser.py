"""Configuration parser for the Pac-Man engine."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


LOGGER = logging.getLogger(__name__)

DEFAULT_HIGHSCORE_FILENAME = "data/highscores.json"
DEFAULT_LEVELS: tuple[dict[str, int], ...] = (
    {"width": 21, "height": 21, "seed": 42},
    {"width": 23, "height": 23},
    {"width": 25, "height": 25},
    {"width": 27, "height": 27},
    {"width": 29, "height": 29},
    {"width": 31, "height": 31},
    {"width": 33, "height": 33},
    {"width": 35, "height": 35},
    {"width": 37, "height": 37},
    {"width": 39, "height": 39},
)


@dataclass(frozen=True)
class LevelConfig:
    """Validated settings for one generated maze level."""

    width: int
    height: int
    seed: int | None = None


@dataclass(frozen=True)
class GameConfig:
    """Validated game settings consumed by the engine."""

    highscore_filename: Path = Path(DEFAULT_HIGHSCORE_FILENAME)
    lives: int = 3
    points_per_pacgum: int = 10
    points_per_super_pacgum: int = 50
    points_per_ghost: int = 200
    pacgum: int = 42
    seed: int = 42
    level_max_time: int = 90
    maze_perfect: bool = False
    levels: tuple[LevelConfig, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)


class ConfigParserError(Exception):
    """Raised when a configuration file cannot be loaded at all."""


def load_config(config_path: str | Path) -> GameConfig:
    """Load and validate a game configuration file.

    Args:
        config_path: Path to a JSON configuration file. Lines and inline
            fragments using ``#``, ``//``, or ``/* ... */`` comments are
            ignored.

    Returns:
        A validated ``GameConfig`` using safe defaults for missing or faulty
        values.

    Raises:
        ConfigParserError: If the file is missing, unreadable, or not valid
            JSON after comment removal.
    """
    path = Path(config_path)
    raw_config = _read_config(path)
    data = _decode_json(raw_config, path)
    if not isinstance(data, dict):
        raise ConfigParserError(f"{path}: root value must be a JSON object.")
    return _build_config(data)


def _read_config(path: Path) -> str:
    """Read a config file and convert file errors into clean parser errors."""
    if path.suffix.lower() != ".json":
        raise ConfigParserError(
            f"{path}: configuration file must be a .json file."
        )
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        message = f"{path}: unable to read config file: {exc}"
        raise ConfigParserError(message) from exc


def _decode_json(raw_config: str, path: Path) -> Any:
    """Decode JSON after removing comments."""
    try:
        return json.loads(_strip_json_comments(raw_config))
    except json.JSONDecodeError as exc:
        message = (
            f"{path}: invalid JSON at line {exc.lineno}, "
            f"column {exc.colno}."
        )
        raise ConfigParserError(message) from exc


def _build_config(data: dict[str, Any]) -> GameConfig:
    """Build a validated configuration from raw JSON data."""
    warnings: list[str] = []

    highscore_filename = Path(
        _string_value(
            data,
            "highscore_filename",
            DEFAULT_HIGHSCORE_FILENAME,
            warnings,
        )
    )
    lives = _int_value(
        data,
        "lives",
        3,
        minimum=1,
        maximum=9,
        warnings=warnings,
    )
    points_per_pacgum = _int_value(
        data,
        "points_per_pacgum",
        10,
        minimum=0,
        warnings=warnings,
    )
    points_per_super_pacgum = _int_value(
        data,
        "points_per_super_pacgum",
        50,
        minimum=0,
        warnings=warnings,
    )
    points_per_ghost = _int_value(
        data,
        "points_per_ghost",
        200,
        minimum=0,
        warnings=warnings,
    )
    pacgum = _int_value(data, "pacgum", 42, minimum=1, warnings=warnings)
    seed = _int_value(data, "seed", 42, minimum=0, warnings=warnings)
    level_max_time = _int_value(
        data,
        "level_max_time",
        90,
        minimum=15,
        warnings=warnings,
    )
    maze_perfect = _bool_value(data, "maze_perfect", False, warnings)
    levels = _level_values(data.get("levels", DEFAULT_LEVELS), warnings)

    for warning in warnings:
        LOGGER.warning(warning)

    return GameConfig(
        highscore_filename=highscore_filename,
        lives=lives,
        points_per_pacgum=points_per_pacgum,
        points_per_super_pacgum=points_per_super_pacgum,
        points_per_ghost=points_per_ghost,
        pacgum=pacgum,
        seed=seed,
        level_max_time=level_max_time,
        maze_perfect=maze_perfect,
        levels=levels,
        warnings=tuple(warnings),
    )


def _strip_json_comments(raw_config: str) -> str:
    """Remove JSON comments without touching comment markers inside strings."""
    result: list[str] = []
    index = 0
    in_string = False
    escaped = False
    in_line_comment = False
    in_block_comment = False

    while index < len(raw_config):
        current = raw_config[index]
        following = (
            raw_config[index + 1]
            if index + 1 < len(raw_config)
            else ""
        )

        if in_line_comment:
            if current == "\n":
                in_line_comment = False
                result.append(current)
            index += 1
            continue

        if in_block_comment:
            if current == "*" and following == "/":
                in_block_comment = False
                index += 2
            else:
                if current == "\n":
                    result.append(current)
                index += 1
            continue

        if in_string:
            result.append(current)
            if escaped:
                escaped = False
            elif current == "\\":
                escaped = True
            elif current == '"':
                in_string = False
            index += 1
            continue

        if current == '"':
            in_string = True
            result.append(current)
            index += 1
            continue

        if current == "#":
            in_line_comment = True
            index += 1
            continue

        if current == "/" and following == "/":
            in_line_comment = True
            index += 2
            continue

        if current == "/" and following == "*":
            in_block_comment = True
            index += 2
            continue

        result.append(current)
        index += 1

    return "".join(result)


def _string_value(
    data: dict[str, Any],
    key: str,
    default: str,
    warnings: list[str],
) -> str:
    """Return a non-empty string setting or a default."""
    value = data.get(key, default)
    if isinstance(value, str) and value.strip():
        return value
    warnings.append(f"Invalid '{key}', using default value {default!r}.")
    return default


def _int_value(
    data: dict[str, Any],
    key: str,
    default: int,
    minimum: int,
    warnings: list[str],
    maximum: int | None = None,
) -> int:
    """Return a clamped integer setting or a default."""
    value = data.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int):
        warnings.append(f"Invalid '{key}', using default value {default}.")
        return default
    if value < minimum:
        warnings.append(f"'{key}' too small, clamped to {minimum}.")
        return minimum
    if maximum is not None and value > maximum:
        warnings.append(f"'{key}' too large, clamped to {maximum}.")
        return maximum
    return value


def _bool_value(
    data: dict[str, Any],
    key: str,
    default: bool,
    warnings: list[str],
) -> bool:
    """Return a boolean setting or a default."""
    value = data.get(key, default)
    if isinstance(value, bool):
        return value
    warnings.append(f"Invalid '{key}', using default value {default}.")
    return default


def _level_values(
    raw_levels: Any,
    warnings: list[str],
) -> tuple[LevelConfig, ...]:
    """Validate level definitions from raw config data."""
    if not isinstance(raw_levels, list) or not raw_levels:
        warnings.append("Invalid 'levels', using default levels.")
        raw_levels = list(DEFAULT_LEVELS)

    levels: list[LevelConfig] = []
    for index, raw_level in enumerate(raw_levels, start=1):
        if not isinstance(raw_level, dict):
            warnings.append(f"Invalid level #{index}, skipped.")
            continue
        level = _level_value(raw_level, index, warnings)
        if level is not None:
            levels.append(level)

    if not levels:
        warnings.append("No valid levels found, using default levels.")
        return _default_level_values(warnings)

    return tuple(levels)


def _default_level_values(warnings: list[str]) -> tuple[LevelConfig, ...]:
    """Build validated default level settings."""
    levels: list[LevelConfig] = []
    for index, level in enumerate(DEFAULT_LEVELS, start=1):
        parsed_level = _level_value(level, index, warnings)
        if parsed_level is not None:
            levels.append(parsed_level)
    return tuple(levels)


def _level_value(
    raw_level: dict[str, Any],
    index: int,
    warnings: list[str],
) -> LevelConfig | None:
    """Validate one level entry."""
    width = raw_level.get("width", 21)
    height = raw_level.get("height", 21)
    seed = raw_level.get("seed")

    if isinstance(width, bool) or not isinstance(width, int):
        warnings.append(f"Invalid width for level #{index}, using 21.")
        width = 21
    if isinstance(height, bool) or not isinstance(height, int):
        warnings.append(f"Invalid height for level #{index}, using 21.")
        height = 21

    width = _odd_dimension(width, "width", index, warnings)
    height = _odd_dimension(height, "height", index, warnings)

    if seed is not None and (
        isinstance(seed, bool) or not isinstance(seed, int)
    ):
        warnings.append(f"Invalid seed for level #{index}, ignoring it.")
        seed = None

    return LevelConfig(width=width, height=height, seed=seed)


def _odd_dimension(
    value: int,
    key: str,
    level_index: int,
    warnings: list[str],
) -> int:
    """Clamp maze dimensions to safe odd values."""
    if value < 5:
        warnings.append(f"Level #{level_index} {key} too small, clamped to 5.")
        value = 5
    if value % 2 == 0:
        value += 1
        warnings.append(f"Level #{level_index} {key} made odd: {value}.")
    return value
