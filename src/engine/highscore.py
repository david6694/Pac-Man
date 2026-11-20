"""High score persistence for the Pac-Man engine."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


MAX_HIGHSCORES = 10
MAX_PLAYER_NAME_LENGTH = 10


class HighScoreError(Exception):
    """Raised when high scores cannot be saved."""


@dataclass(frozen=True)
class HighScoreEntry:
    """One saved high score."""

    name: str
    score: int


def load_highscores(path: str | Path) -> tuple[HighScoreEntry, ...]:
    """Load high scores from disk."""
    highscore_path = Path(path)
    try:
        raw_content = highscore_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ()
    except OSError:
        return ()

    if not raw_content.strip():
        return ()

    try:
        raw_scores = json.loads(raw_content)
    except json.JSONDecodeError:
        return ()

    return _sorted_scores(_parse_entries(raw_scores))


def save_highscores(
    path: str | Path,
    scores: tuple[HighScoreEntry, ...],
) -> None:
    """Save high scores to disk."""
    highscore_path = Path(path)
    highscore_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [asdict(entry) for entry in _sorted_scores(scores)]

    try:
        highscore_path.write_text(
            json.dumps(payload, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise HighScoreError(
            f"Unable to save high scores to {highscore_path}: {exc}"
        ) from exc


def add_highscore(
    scores: tuple[HighScoreEntry, ...],
    name: str,
    score: int,
) -> tuple[HighScoreEntry, ...]:
    """Add one score and return the sorted high score table."""
    entry = HighScoreEntry(name=_clean_name(name), score=max(0, score))
    return _sorted_scores((*scores, entry))


def record_highscore(
    path: str | Path,
    name: str,
    score: int,
) -> tuple[HighScoreEntry, ...]:
    """Load, add, save, and return the updated high score table."""
    scores = add_highscore(load_highscores(path), name, score)
    save_highscores(path, scores)
    return scores


def _parse_entries(raw_scores: Any) -> tuple[HighScoreEntry, ...]:
    """Convert raw JSON data to high score entries."""
    if not isinstance(raw_scores, list):
        return ()

    entries: list[HighScoreEntry] = []
    for raw_score in raw_scores:
        entry = _parse_entry(raw_score)
        if entry is not None:
            entries.append(entry)
    return tuple(entries)


def _parse_entry(raw_score: Any) -> HighScoreEntry | None:
    """Convert one raw JSON entry to a high score entry."""
    if not isinstance(raw_score, dict):
        return None

    raw_name = raw_score.get("name")
    raw_points = raw_score.get("score")
    if not isinstance(raw_name, str):
        return None
    if isinstance(raw_points, bool) or not isinstance(raw_points, int):
        return None

    return HighScoreEntry(
        name=_clean_name(raw_name),
        score=max(0, raw_points),
    )


def _sorted_scores(
    scores: tuple[HighScoreEntry, ...],
) -> tuple[HighScoreEntry, ...]:
    """Return scores sorted from highest to lowest."""
    return tuple(
        sorted(scores, key=lambda entry: entry.score, reverse=True)[
            :MAX_HIGHSCORES
        ]
    )


def _clean_name(name: str) -> str:
    """Return a display-safe high score name."""
    cleaned = "".join(
        character for character in name.strip()
        if character.isalnum() or character == " "
    )
    if not cleaned:
        return "Player"
    return cleaned[:MAX_PLAYER_NAME_LENGTH]
