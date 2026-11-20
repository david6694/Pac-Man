*This project has been created as part of the 42 curriculum by arvella, dgarrido.*

# Pac-Man

## Description

Pac-Man is a Python remake of the classic arcade game. The player moves through a maze, eats pacgums and super-pacgums, avoids ghosts, and tries to clear all configured levels before losing all lives.

The project is split into two main parts:

- `src/engine/`: game rules, configuration loading, maze generation, scoring, timers, collisions, ghost movement, and highscores.
- `src/display/`: Pygame rendering, menus, sprites, HUD, pause screen, game-over screen, and victory screen.

The game uses the assigned A-Maze-ing package from `mazegenerator-00001-py3-none-any.whl` to generate mazes.

## Instructions

Install dependencies:

```sh
make install
```

Run the game with the default configuration:

```sh
make run
```

Run the game manually with another JSON config:

```sh
python3 pac-man.py path/to/config.json
```

The program expects exactly one argument: a JSON configuration file. Missing arguments, missing files, invalid extensions, and invalid JSON are reported with clear error messages instead of Python tracebacks.

Debug with `pdb`:

```sh
make debug
```

Run code quality checks:

```sh
make lint
```

Create a distributable source package:

```sh
make build
```

The build output is `dist/pacman.tar.gz`.

## Controls

- Arrow keys or `WASD`: move Pac-Man.
- `Esc`: pause during the game, or leave menu screens.
- `R`: resume from the pause menu.
- `M`: return to the main menu from the pause menu.
- `Enter` or `Space`: validate a menu choice.

Cheat controls for peer review:

- `I`: toggle invincibility.
- `F`: toggle ghost freeze.
- `L`: skip the current level.
- `G`: add one life.
- `K`: toggle double speed.

## Configuration

The default configuration is [config/default.json](config/default.json). The loader accepts JSON with comments:

- lines or fragments starting with `#`
- `//` comments
- `/* ... */` block comments

Unknown keys are ignored. Invalid values are clamped or replaced by safe defaults when possible.

Main keys:

- `highscore_filename`: JSON file used for persistent scores.
- `lives`: starting lives, clamped between safe values.
- `points_per_pacgum`: score gained for a normal pacgum.
- `points_per_super_pacgum`: score gained for a super-pacgum.
- `points_per_ghost`: base score gained for eating a ghost.
- `pacgum`: project scoring/config value kept configurable.
- `seed`: default seed for generated levels.
- `level_max_time`: time limit per level.
- `maze_perfect`: passed to the maze generator. The default is `false` for Pac-Man-compatible corridors.
- `levels`: list of level definitions with `width`, `height`, and optional `seed`.

The first level uses a fixed seed, so it is reproducible. Later levels can omit their seed and are derived from the configured base seed and level index.

## Highscore

Highscores are stored in JSON, by default in [data/highscores.json](data/highscores.json). The system:

- loads scores at game start
- saves scores after the player wins or loses and enters a name
- keeps only the top 10 scores
- stores non-negative integer scores
- accepts player names made of alphanumeric characters and spaces
- trims saved names to 10 characters
- recovers cleanly from missing or invalid highscore files

JSON was chosen because it is easy to inspect during evaluation and simple to regenerate if the file is removed.

## Maze Generation

The project uses the assigned `mazegenerator` wheel as-is. The engine imports `MazeGenerator` from the installed package and adapts its output into a playable Pac-Man level.

The integration lives in [src/engine/maze.py](src/engine/maze.py). It:

- creates the external generator with the configured size, seed, and `maze_perfect` value
- converts generated wall data into immutable tuples
- places Pac-Man near the center
- places the four ghosts near the four maze corners
- places super-pacgums near the ghost corner positions
- fills walkable corridors with pacgums
- reports generator failures with a clean `MazeGenerationError`

## Implementation

The game loop is driven by [pac-man.py](pac-man.py). It owns the Pygame window, menu states, rendering timing, player input, and cheat controls.

The engine is exposed through `PacmanEngine` in [src/engine/api.py](src/engine/api.py). The display asks for snapshots instead of mutating engine internals directly. This keeps the game rules testable and separates rendering from game state.

Main engine responsibilities:

- `parser.py`: reads and validates config files.
- `maze.py`: integrates the external maze generator.
- `level.py`: tracks pacgums and level-local state.
- `game.py`: owns the session state, lives, progression, collisions, and events.
- `ghost_movement.py`: chooses ghost targets and movement.
- `score.py`: applies scoring rules.
- `power_mode.py`: handles frightened-mode timing.
- `timer.py`: tracks level time limits.
- `highscore.py`: loads, sanitizes, sorts, and saves scores.

Main display responsibilities:

- `menu.py`: draws menus and end screens.
- `maze.py`: draws walls, pacgums, and super-pacgums.
- `ghost.py`: draws ghost sprites.
- `sprites.py`: loads and selects Pac-Man and ghost sprites.
- `constants.py`: centralizes colors.

## General Software Architecture

The project follows a small MVC-style organization:

- Model: engine dataclasses and state in `src/engine`.
- View: Pygame drawing helpers in `src/display`.
- Controller: input handling and state transitions in `pac-man.py`.

The display receives immutable snapshots from the engine. One-shot effects such as pacgum collection, level changes, life loss, or highscore recording are represented as game events. This makes the display code easier to understand and avoids duplicating game rules in the UI layer.

## Project Management

The project-management notes are available in
[project_management/](project_management/). They contain the team organization
and task tracking.

## Packaging

The root Makefile contains a `build` rule:

```sh
make build
```

It creates `dist/pacman.tar.gz`, excluding local development folders such as `.git`, `.venv`, caches, and previous build outputs. The archive contains the source code, sprites, configuration, Makefile, README, and the assigned maze generator wheel so the package can be regenerated during peer review.

The package can then be uploaded as a free private or unlisted build on a gaming platform such as Itch.io.

## Resources

Classic references:

- Pygame documentation: https://www.pygame.org/docs/
- Python `dataclasses`: https://docs.python.org/3/library/dataclasses.html
- Python `json`: https://docs.python.org/3/library/json.html
- Python `pathlib`: https://docs.python.org/3/library/pathlib.html
- mypy documentation: https://mypy.readthedocs.io/
- flake8 documentation: https://flake8.pycqa.org/

AI usage:

- AI was used to discuss architecture, documentation wording, validation checks, and small implementation fixes.
- AI-generated suggestions were reviewed against the subject and tested locally with commands such as `make install`, `make lint`, `py_compile`, JSON validation, and smoke tests.
- The team remains responsible for understanding and explaining every submitted file.
