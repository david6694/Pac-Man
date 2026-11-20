# Engine API for the Display

This file explains what the display code can do with `src/engine/api.py`.
The display should use `PacmanEngine` as the public entry point instead of
calling the lower-level engine modules directly.

## Basic usage

```python
from src.engine.api import Direction, GameStatus, PacmanEngine

engine = PacmanEngine("config/default.json")

# Draw the current game state.
snapshot = engine.snapshot()

# Move Pac-Man when the player presses a key.
engine.move(Direction.LEFT)

# Advance timers and ghosts once per frame.
engine.tick(delta_seconds)

# React to score changes, life loss, level clear, etc.
events = engine.pop_events()
```

## Actions the Display Can Call

### `PacmanEngine(config_path)`

Creates one game session from a config file.

- `config_path`: path to a JSON config, usually `"config/default.json"`.
- The first level is generated during creation.
- The event queue starts with `game_started` and `level_started`.

### `snapshot() -> GameSnapshot`

Returns a read-only object containing everything needed to draw the game.
Call it after inputs and ticks, then render from the returned values.

Important fields:

- `width`, `height`: maze size in cells.
- `walls`: grid of wall flags, indexed as `walls[y][x]`.
- `tiles`: grid of visible cell content, indexed as `tiles[y][x]`.
- `player_position`: Pac-Man position with `.x` and `.y`.
- `ghosts`: tuple of ghosts, each with `.name` and `.position`.
- `score`: current score.
- `lives`: remaining lives.
- `level_index`: zero-based level number. Display `level_index + 1` to users.
- `status`: current game state.
- `ghost_mode`: current ghost behavior mode.
- `time_left`: seconds remaining in the level.
- `elapsed_time`: seconds elapsed in the current level.
- `remaining_pacgums`: number of pacgums and super pacgums still on the board.
- `power_mode_active`: `True` while Pac-Man can eat ghosts.
- `power_mode_flashing`: `True` near the end of power mode.

### `tick(seconds) -> None`

Advances the game clock and ghost movement.

- `seconds` should be the frame delta time, for example `1 / 60`.
- Does nothing if `seconds <= 0`.
- Does nothing while the game is still `ready`; the first player movement starts play.
- Does nothing after the game is `won` or `lost`.
- Can create events such as `ghost_moved`, `life_lost`, `power_mode_ended`,
  or `game_lost`.

### `move(direction) -> bool`

Moves Pac-Man one cell in the requested direction.

- `direction` must be one of `Direction.UP`, `Direction.DOWN`,
  `Direction.LEFT`, or `Direction.RIGHT`.
- Returns `True` when the move was accepted.
- Returns `False` if a wall blocks the move or if the game is already won/lost.
- The first successful move changes the status from `ready` to `playing`.
- Can collect pacgums, start power mode, eat ghosts, lose a life, clear a
  level, or win the game.

### Direction helper methods

These call `move(...)` with the matching direction:

- `move_up() -> bool`
- `move_down() -> bool`
- `move_left() -> bool`
- `move_right() -> bool`

They are useful if the display input code prefers direct methods instead of
passing the `Direction` enum.

### `next_level() -> bool`

Loads the next level after the current level is cleared.

- Call this only when `snapshot().status == GameStatus.LEVEL_CLEARED`.
- Returns `True` if the next level was loaded.
- Returns `False` if the game is not waiting on a level transition.
- Loading a level resets positions, timer, power mode, and ghost mode.
- It also adds a `level_started` event.

### `peek_events() -> tuple[GameEvent, ...]`

Reads pending events without clearing them.

Use this when the display wants to inspect events but keep them available for
another part of the UI.

### `pop_events() -> tuple[GameEvent, ...]`

Reads pending events and clears the queue.

This is usually the best choice once per frame after `move(...)` and
`tick(...)`. The display can use events for animations, sounds, messages, or
screen transitions.

### `record_highscore(name) -> tuple[HighScoreEntry, ...]`

Saves the current score under a player name and returns the updated high score
table.

- Empty names become `"Player"`.
- Names are trimmed to 10 characters.
- Scores are sorted highest first.
- Only the top 10 scores are kept.
- Adds a `highscore_recorded` event.

## Snapshot Types

### Positions

Positions use grid coordinates:

```python
position.x  # column
position.y  # row
```

The top-left cell is `(0, 0)`.

### Tiles

`snapshot.tiles[y][x]` is a `Tile` value:

- `Tile.EMPTY`: no item.
- `Tile.PACGUM`: normal pacgum.
- `Tile.SUPER_PACGUM`: power pacgum.

After Pac-Man collects a pacgum, the matching tile becomes empty in future
snapshots.

### Walls

`snapshot.walls[y][x]` is an integer made of wall flags:

- `Wall.NORTH`
- `Wall.EAST`
- `Wall.SOUTH`
- `Wall.WEST`

Example:

```python
from src.engine.api import Wall

cell_walls = snapshot.walls[y][x]
has_north_wall = bool(cell_walls & Wall.NORTH)
```

A display can draw walls by checking these flags for each cell.

### Ghosts

Each ghost snapshot has:

- `name`: one of `blinky`, `pinky`, `inky`, `clyde`.
- `position`: grid position with `.x` and `.y`.

## Game Status Values

`snapshot.status` is a `GameStatus`:

- `GameStatus.READY`: level is loaded, waiting for the first player move.
- `GameStatus.PLAYING`: normal gameplay.
- `GameStatus.LEVEL_CLEARED`: all pacgums are eaten; display can call
  `next_level()`.
- `GameStatus.WON`: final level completed.
- `GameStatus.LOST`: no lives left.

## Event Types

Each event has:

- `type`: event kind.
- `message`: short human-readable message.
- `position`: optional related position.
- `ghost_name`: optional related ghost.
- `score_delta`: points gained by this event, if any.
- `score`: score after the event.
- `lives`: lives after the event.
- `level_index`: zero-based level index when the event happened.

Possible event types:

- `game_started`
- `level_started`
- `player_moved`
- `pacgum_eaten`
- `super_pacgum_eaten`
- `power_mode_started`
- `power_mode_ended`
- `ghost_moved`
- `ghost_eaten`
- `life_lost`
- `level_cleared`
- `game_won`
- `game_lost`
- `highscore_recorded`

## Recommended Display Loop

```python
engine = PacmanEngine("config/default.json")

while running:
    for input_event in input_events:
        if input_event == "up":
            engine.move_up()
        elif input_event == "down":
            engine.move_down()
        elif input_event == "left":
            engine.move_left()
        elif input_event == "right":
            engine.move_right()

    engine.tick(delta_seconds)

    for event in engine.pop_events():
        handle_event(event)

    snapshot = engine.snapshot()
    draw(snapshot)

    if snapshot.status == GameStatus.LEVEL_CLEARED:
        show_level_clear_screen()
        # When ready to continue:
        # engine.next_level()
```

## Notes for the Display Team

- Use `snapshot()` as the source of truth for drawing.
- Use events only for things that happen once, like sounds, animations, or
  temporary messages.
- Do not modify fields inside snapshots. They are frozen display-safe data.
- `tick(...)` moves ghosts, but only after gameplay has started.
- Player movement is grid-based: one accepted move changes Pac-Man by one cell.
- The API currently does not expose a pause or restart action.
