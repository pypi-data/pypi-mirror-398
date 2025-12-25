# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`master-mind` (package name: `su_master_mind`) is a Python CLI tool for managing dependencies and datasets for Sorbonne University Master MIND courses. It handles course-specific Python package installations and dataset downloads for various AI/ML courses including deep learning (deepl), reinforcement learning (rl), large language models (llm), advanced deep learning (adl), and information retrieval (rital).

## Build and Development Commands

### Installation and Package Management

```bash
# Install master-mind itself (base dependencies only)
pip install -e .

# Build the package
poetry build
# or using pyproject-build:
python -m build

# Run the CLI tool
master-mind --help
```

### Publishing to PyPI

**One-time setup:**

Edit the Hatch configuration file:
- **macOS**: `~/Library/Application Support/hatch/config.toml`
- **Linux**: `~/.config/hatch/config.toml`
- **Windows**: `%USERPROFILE%\AppData\Local\hatch\config.toml`

```toml
[publish]

[publish.index]

[publish.index.repos.su-master-mind]
url = "https://upload.pypi.org/legacy/"
user = "__token__"
auth = "pypi-YOUR_PROJECT_SPECIFIC_TOKEN_HERE"
```

Replace `YOUR_PROJECT_SPECIFIC_TOKEN_HERE` with your project-specific PyPI API token.

**To publish a new version:**

The project uses Calendar Versioning (CalVer) with format `YYYY.MM.DD.N` where N auto-increments for multiple releases on the same day.

```bash
# Update version to today's date (auto-increments N)
hatch version release

# Check current version
hatch version

# Clean dist directory to ensure only current version is published
rm -rf dist/

# Build the package
hatch build
# or using pyproject-build:
python -m build

# Publish using the configured repository
hatch publish -r su-master-mind

# Alternative: using twine
twine upload dist/*
```

Notes:
- `hatch version release` automatically updates `master_mind/__version__.py`
- The `-r su-master-mind` flag is required to use the configured repository
- Hatch doesn't support setting a default repository name in `pyproject.toml`

**For CI/CD (alternative):**

```bash
export HATCH_INDEX_USER="__token__"
export HATCH_INDEX_AUTH="pypi-YOUR_TOKEN_HERE"
hatch publish
```

### Code Quality

```bash
# Run pre-commit hooks (black formatting, flake8 linting)
pre-commit run --all-files

# Run black formatter directly
black master_mind/

# Run flake8 linter directly
flake8 master_mind/
```

Note: flake8 is configured with flake8-print and flake8-fixme plugins.

### Testing

There are currently no automated tests in this repository.

## Architecture

### CLI Structure

The CLI is built with Click and organized into command groups:

- `master-mind courses add/rm/list` - Manage which courses a student is enrolled in
- `master-mind update` - Install/update Python packages for enrolled courses
- `master-mind download-datasets` - Download datasets for enrolled courses
- `master-mind rl stk-race` - Run SuperTuxKart racing simulations (RL course specific)

Available courses: `deepl`, `rl`, `llm`, `adl`, `rital` (defined in `CLASS_NAMES` in `__main__.py`)

### Core Components

**Configuration (`configuration.py`)**
- Stores user's enrolled courses in `~/.config/master-mind/isir/config.json` (via appdirs)
- Validates course names against available installers in `install.py`
- Uses JSON format with a `courses` array

**Package Installation (`install.py`)**
- Manages course-specific package installations using `uv pip install` or `pip install` with extras
- Optional dependencies defined in `pyproject.toml` under `[tool.poetry.dependencies]` and `[tool.poetry.extras]`
- Single function `install_courses(courses)` installs all configured courses in one command
- Example: if user has configured `rl` and `deepl`, runs `uv pip install su_master_mind[deepl,rl]` (single command)
- Dependency hierarchy: all course extras include the full `deep` dependency set
- `get_pip_command()` automatically detects and uses `uv` if available, falls back to `pip`
- RL course requires `swig` to be installed system-wide (pre-flight check before installation)
- Ensures global dependency consistency by letting the package manager resolve all dependencies in a single command

**Dataset Management (`datasets.py`)**
- Uses `datamaestro` to download and prepare datasets
- Uses `datasets` (Hugging Face) for some datasets (IMDB, CelebA)
- Pre-downloads transformer models using `AutoTokenizer` and model classes
- Functions mirror course names: `rital()`, `llm()`, `amal()` (note: `amal` not in CLASS_NAMES)

**Auto-update (`utils.py`)**
- Checks PyPI for newer versions of `su_master_mind`
- If newer version available, automatically installs it with configured course extras and re-runs the original command
- Reads user's configured courses from Configuration to include in the update command
- Uses `importlib.metadata.version()` to get current version
- Uses `requests` to query PyPI JSON API
- Updates with proper extras: `su_master_mind[rl,llm]==<version>` if courses are configured

### RL-Specific Components

**STK Racing (`master_mind/rld/stk.py`)**
- Runs SuperTuxKart races with student-submitted agents
- Loads agents from zip files, directories, or Python modules
- Each agent must have `pystk_actor.py` with:
  - `env_name` - gymnasium environment ID (must be `pystk2_gymnasium.envs:STKRaceEnv`)
  - `player_name` - display name
  - `get_actor(params, obs_space, action_space)` - factory function
  - Optional `get_wrappers()` - environment wrappers
- Agents stored in `pystk_actor.pth` (PyTorch saved parameters, optional)
- Uses BBRL (BlackBox RL) framework with gymnasium environments
- Supports interactive debugging modes and live visualization

**Live Visualization (`master_mind/rld/stk_graph.py`)**
- Provides real-time 3D visualization of STK races using Dash/Plotly
- Shows track, kart positions, items, and agent observations
- Runs on http://localhost:8050 by default
- Uses quaternion math to transform coordinates to global view
- Visualization includes: track paths, start point, kart position, other karts, and items by type

## Course Requirements Structure

Requirements are defined as optional dependencies in `pyproject.toml` using **self-referencing extras**:

- `deep` - Base requirements (PyTorch, TensorFlow, Jupyter, scientific stack, datamaestro, experimaestro)
- `rl` - Includes `su_master_mind[deep]` + bbrl_utils, box2d, pyglet, pystk2-gymnasium==0.7.*, moviepy<2, dash
- `deepl` - Includes `su_master_mind[deep]` + optuna, pytorch-lightning, transformers, NLP tools
- `adl` - Includes `su_master_mind[deep]` + scikit-image for SIREN
- `rital` - Includes `su_master_mind[deep]` + experimaestro-ir, pyserini
- `llm` - Includes `su_master_mind[deep]` + bertviz, gensim, transformers, evaluate

Install using: `uv pip install su_master_mind[rl,deepl]` or `pip install su_master_mind[rl,deepl]`

**Self-referencing extras** (supported since pip 21.2): Each course extra references `su_master_mind[deep]` to automatically include all base dependencies, eliminating redundancy and ensuring consistency. The package manager resolves the dependency tree, automatically including `deep` when any course extra is installed.

## Important Implementation Details

### Build System

The project uses **Hatch** as the build backend (PEP 621 compliant):
- Build configuration in `pyproject.toml` with `build-backend = "hatchling.build"`
- Build dependencies include `hatch-calver` for calendar versioning
- Package directory configured in `[tool.hatch.build.targets.wheel]`: `packages = ["master_mind"]`
  - Required because package name (`su_master_mind`) differs from directory name (`master_mind`)
- **Dynamic versioning**: Uses CalVer scheme (`YYYY.MM.DD.MICRO`) via `hatch-calver`
  - Version stored in `master_mind/__version__.py`
  - Update with `hatch version release` (auto-increments for same-day releases)
- Core dependencies declared in `[project.dependencies]` (click, packaging, appdirs, requests)
- Optional dependencies for courses defined in `[project.optional-dependencies]`
- **Self-referencing extras**: Each course extra references `su_master_mind[deep]` to include base dependencies
- Example: `llm = ["su_master_mind[deep]", "bertviz", "gensim", ...]`
- CLI entry point in `[project.scripts]`: `master-mind = "master_mind.__main__:main"`
- Requires Python >= 3.10

### Agent Loading Pattern

The `load_player()` function in `stk.py` supports three input formats:
1. Directory with `stk_actor/pystk_actor.py` structure
2. Python module name (importable)
3. ZIP file containing `pystk_actor.py` and optionally `pystk_actor.pth`

Player names can be overridden using `@:` syntax: `path/to/agent@:CustomName`

The function:
- Creates temporary directories for extracted/linked agents
- Manipulates `sys.path` to enable imports
- Returns a tuple: `(player_name, wrappers_factory, actor_factory)`

### Error Handling in Races

The `--error-handling` flag wraps agent exceptions in `AgentException` to identify which agent failed and at what stage (loading, initialization, or action selection). Without this flag, exceptions propagate normally for debugging.

### Environment Wrappers

Agents use a two-level wrapper system:
1. Gymnasium environment wrappers from the environment spec (`env_spec.additional_wrappers`)
2. Custom wrappers from the agent's `get_wrappers()` function
The `MonoAgentWrapperAdapter` allows per-agent environment customization.

### Race Interaction Modes

The `stk-race` command supports three interaction modes:
- `none` - No interaction, just run the race
- `interactive` - Pause after each step, allow inspecting observations by index
- `map` - Launch live 3D visualization server and pause after each step

### Version Constraints

- `pystk2-gymnasium` must be exactly version 0.7.* (enforced in `stk-race` command with assertion)
- `moviepy` must be < 2 (version 2+ has breaking changes)
- `pyglet` must be < 2
- Python >= 3.10 required
- `torch` >= 2.5
- `tensorflow` >= 2.10 (with special handling for Apple Silicon via tensorflow-macos)
