# plex-leon

A tiny CLI to manage media libraries: migrate by TVDB IDs, rename seasons and episodes.

The CLI is subcommand-based with the following utilities:

- `migrate` — move items from library-a to library-c when the TVDB ID exists in library-b
- `season-renamer` — renames season folders in a library to the canonical 'Season NN' form
- `episode-renamer` — renames episode files to `<Show (Year)> - sNNeMM[ -ePP].ext`
- `episode-check` — Compare local episode counts with TVDB data
- `prepare` — organise loose TV episode files into `Season NN` folders and rename them to `Show (Year) - eEE sSS.ext`

Additionally, there is a `help` subcommand that prints a short, human-friendly summary of available commands and their one-line descriptions.

Note: calling `plex-leon` with no subcommand will now launch the interactive `menu` by default. The `menu` lets you select a discovered utility and provides prompts for its arguments.

You can get detailed, command-specific help two ways:

- Using the `help` subcommand:

```bash
plex-leon help migrate
```

- Or using the built-in argparse help for any subcommand:

### episode-check

Compare the number of episodes in your local TV show library with the episode counts from TVDB (The TV Database). Useful to identify shows with missing episodes.

**How it works:**

- Scans the library for show folders containing TVDB IDs: `Show Name (YYYY) {tvdb-12345}`.
- Counts media files in `Season NN` folders (ignores non-media files and `Season 00` specials).
- Fetches episode counts per season from TVDB for the matched series.
- Prints a per-season comparison table highlighting discrepancies.

**Options:**

- `--lib PATH` — Path to the library to check (default: `./data/library-p`)

**Prerequisites:**

- A TVDB API key must be available via the `TVDB_API_KEY` environment variable.

**Examples:**

```bash
# With Poetry (for development)
poetry run plex-leon episode-check

# If installed globally via pip (recommended)
plex-leon episode-check

# Specify a different library
poetry run plex-leon episode-check --lib /path/to/library
```

### prepare
plex-leon migrate --help
```

Both will print detailed usage and options for the selected utility.

Note: commands are discovered automatically from the utility classes, so adding a new utility will make it appear in the CLI and `help` output without manual changes to this README.

Returns `0` on normal completion, `2` if required external tools are missing (preflight check fails). Prints detailed DECISION lines for eligible items (including resolution and size comparisons) and a final summary with total duration.

## How it works

### migrate

Move items from library-a to library-c when the TVDB ID exists in library-b.

**How it works:**

- TVDB IDs are extracted with a case-insensitive pattern: `{tvdb-<digits>}`. Examples:
	- `John Wick (2014) {tvdb-155}.mp4` → `155`
	- `Game of Thrones (2011) {TVDB-121361}` → `121361`
- Hidden entries (starting with `.`) are ignored.
- Library-b is scanned recursively to support a production-like, bucketed layout under A–Z and `0-9` (non-letter starters). Examples:
	- `library-b/A/Avatar (2009) {tvdb-19995}.mp4`
	- `library-b/0-9/[REC] (2007) {tvdb-12345}.mp4`
	- `library-b/0-9/2001 A Space Odyssey (1968) {tvdb-...}.mp4`
- Library-a is scanned at the top level only (both files and folders).
- If an item in library-a has a TVDB ID that also exists anywhere under library-b, it's considered eligible and moved to library-c.
- For movies (files), the destination inside library-c depends on a comparison with the matching item in library-b:
	- `better-resolution/` when the source has a higher pixel count (width×height)
	- `greater-filesize/` when resolution isn't higher but the source file is larger
	- `to-delete/` when neither is true (i.e., the library-b item is as good or better)
	Resolution is read via ffprobe (FFmpeg) first, then mediainfo. If both resolutions are unknown, the tool falls back to file-size comparison only.
- For TV shows (folders), the tool compares episodes individually by matching season and episode numbers (e.g., s01e01) between library-a and library-b. Each episode is moved to the appropriate categorization folder in library-c (`better-resolution/`, `greater-filesize/`, or `to-delete/`) based on the same resolution and size logic as for movies. The show/season/episode folder structure is preserved under the categorization folder. The show folder itself is not moved, only its episodes.
- Moves print what would or did happen and end with a summary line including timing, for example: `Done. Eligible files/folders moved: X; skipped: Y. Took 2.34s.`

**Options:**

- `--lib-a PATH` — Source library (default: `./data/library-a`)
- `--lib-b PATH` — Reference library (default: `./data/library-b`)
- `--lib-c PATH` — Destination library (default: `./data/library-c`)
- `--overwrite` — Replace existing files/folders in library-c
- `--dry-run` — Show planned moves without changing the filesystem
- `--threads N` — Optional thread count for metadata reads (I/O bound). Moderate values (e.g., 4–8) are recommended to avoid disk thrash.
- `--no-resolution` — Skip resolution comparisons (size-only heuristic)

**Performance notes:**

- Resolution probing uses `ffprobe` (FFmpeg) first and falls back to `mediainfo`; use `--no-resolution` to skip and rely on size-only comparison.
- `--threads` warms metadata reads in parallel for I/O-bound speedups.
- When there is no counterpart found in library-b for a given item, resolution probing is skipped entirely to save time.

**Examples:**

```bash
# With Poetry (for development)
poetry run plex-leon migrate --dry-run

# If installed globally via pip (recommended)
plex-leon migrate --dry-run

# Specify custom paths and actually move files (Poetry)
poetry run plex-leon migrate --lib-a /path/a --lib-b /path/b --lib-c /path/c --overwrite
# Or, if installed globally:
plex-leon migrate --lib-a /path/a --lib-b /path/b --lib-c /path/c --overwrite

# Use 8 threads for faster metadata reads
poetry run plex-leon migrate --threads 8
# Or global:
plex-leon migrate --threads 8
```

### season-renamer

Renames season folders in a library to the canonical 'Season NN' form.

**How it works:**

- Renames season folders like 'season 01', 'Staffel 01', 'Satffel 01', or any folder with a single number to the canonical 'Season NN' form.
- Works recursively through the library.
- Supports typos and numbers >= 100.
- Only subfolders inside show folders are considered for renaming; top-level show folders (even if they contain digits, e.g., 'Game of Thrones 2011') are never renamed.
- For case-only renames (e.g., 'season 01' → 'Season 01'), a two-step swap is performed: first, the folder is renamed to `.plexleon_swap_Season NN`, then to `Season NN`.
- If a canonical `Season NN` already exists, contents are merged non-destructively (conflicts are moved to a `.plexleon_conflicts` subfolder).
- No folders or files are deleted or overwritten by default.

**Options:**

- `--lib PATH` — Library path to process (required)
- `--dry-run` — Show planned renames without changing the filesystem

**Examples:**

```bash
# With Poetry (for development)
poetry run plex-leon season-renamer --lib ./data/library-b --dry-run

# If installed globally via pip (recommended)
plex-leon season-renamer --lib ./data/library-b --dry-run

# Actually rename all season folders in a library (Poetry)
poetry run plex-leon season-renamer --lib ./data/library-b
# Or global:
plex-leon season-renamer --lib ./data/library-b
```

### episode-renamer

Renames episode files to the canonical format `<Show (Year)> - sNNeMM[ -ePP].ext`.

**How it works:**

- The show title and year are taken from the parent show folder (e.g., `Code Geass (2006) {tvdb-79525}` → `Code Geass (2006)`).
- The episode id is parsed from the original filename (supports `s01e01`, `S01E01`, and double-episodes like `S01E01-E02`) and normalized to lowercase.
- Any additional episode title text in the filename is removed.
- Case-only changes (e.g., `S01E01` → `s01e01`) are performed via a safe two-step rename using a hidden swap file to avoid filesystem issues.

**Options:**

- `--lib PATH` — Library path to process (required)
- `--dry-run` — Show planned renames without changing the filesystem

**Examples:**

```bash
# With Poetry (for development)
poetry run plex-leon episode-renamer --lib ./data/library-e --dry-run

# If installed globally via pip (recommended)
plex-leon episode-renamer --lib ./data/library-e --dry-run

# Actually rename episodes (Poetry)
poetry run plex-leon episode-renamer --lib ./data/library-e
# Or global:
plex-leon episode-renamer --lib ./data/library-e
```

### prepare

Organise loose TV episode files into `Season NN` folders and rename them to `Show (Year) - s01e01.ext`.

**How it works:**

- Validates show folders (TVDB id must be present, duplicate detection).
- Organises loose TV episode files into canonical `Season NN` folders.
- Renames episodes to `<Show (Year)> - s01e01.ext` (season before episode).
- Only processes files that pass validation checks.

**Options:**

- `--lib PATH` — Library path to process (required)
- `--dry-run` — Show planned changes without modifying the filesystem

**Examples:**

```bash
# With Poetry (for development)
poetry run plex-leon prepare --lib ./data/library-p --dry-run

# If installed globally via pip (recommended)
plex-leon prepare --lib ./data/library-p --dry-run

# Apply changes to data/library-p (Poetry)
poetry run plex-leon prepare --lib ./data/library-p
# Or global:
plex-leon prepare --lib ./data/library-p
```

## Requirements & Installation

- Python 3.14+
- External tools on PATH (validated at startup): `ffprobe` (from FFmpeg) and `mediainfo`

Below are a few supported ways to install the external tools and the Python package itself.

### System packages

Debian / Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg mediainfo
```

macOS (Homebrew):

```bash
brew update
brew install ffmpeg mediainfo
```

Windows using winget (Windows Package Manager):

```powershell
winget install Gyan.FFmpeg
winget install MediaArea.MediaInfo
```

### Install the Python package

Recommended (global pip):

```bash
pip install plex-leon
# run the CLI directly without Poetry
plex-leon --help
```

For development (Poetry):

```bash
# create virtualenv and install deps defined in pyproject.toml
poetry install
# run commands inside the virtualenv
poetry run plex-leon --help
```

Alternative (pip editable / development):

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
plex-leon --help
```

### Notes

- The CLI validates that `ffprobe` and `mediainfo` are present on PATH at startup and will exit with code `2` if they are missing.
- If you use Poetry the project is already configured; otherwise the `pip install -e .` route will install the package in editable/development mode.


## Development

### Guidelines

Follow these lightweight conventions when contributing and releasing:

- Semantic versioning: use tags like `v2.4.0` for releases and increment MAJOR.MINOR.PATCH appropriately.
- Commit messages: prefer a conventional commit style (e.g., `feat:`, `fix:`, `chore:`, `test:`). This keeps the changelog tidy.
	- When a change is scoped to a specific utility, prefer scoped commits, e.g. `feat(prepare):` or `test(season-renamer):` so the changed area is immediately obvious in the changelog.
- Releases: update `README.md` and `CHANGELOG.md` before tagging a release. Keep changelog entries under headings: `Added`, `Changed`, `Fixed`, `Tests`.

### Devcontainer

This repo can be used inside a development container (devcontainer) for a reproducible development environment. The devcontainer provides:

- a consistent Python 3.14 environment
- preinstalled development tools (linting, pytest, optional editors integration)

To use the devcontainer:

1. Open the repository in VS Code with the Remote - Containers extension installed.
2. Choose "Reopen in Container" from the Command Palette. VS Code will build the devcontainer image and open a workspace with all tools installed.

### Testing

This project contains unit and integration tests under `tests/`.

Run all tests locally using Poetry (recommended):

```bash
poetry run pytest -q
```

Run only unit tests:

```bash
poetry run pytest -q tests/unittests
```

#### Test library generator

The integration tests include helper generators that can create sample library data under `data/` for local testing. See `tests/integration/generators` for scripts and examples.

Note: in this project the "integration tests" are not standard pytest cases — they are generator scripts that create a test environment under `data/` and let you run `plex-leon` against that environment to validate behavior.

How to use the integration generators locally:

1. Create or activate your virtualenv and install the package (Poetry recommended):

```bash
poetry install
poetry run python tests/integration/generators/migrate_tlg.py
poetry run python tests/integration/generators/episode_renamer_tlg.py
poetry run python tests/integration/generators/season_renamer_tlg.py
poetry run python tests/integration/generators/prepare_tlg.py
```

2. Inspect the generated folder (e.g., `./data/library-a`, `./data/library-b`, ...) to confirm files are present.

3. Run plex-leon against the generated data (dry-run first):

```bash
poetry run plex-leon migrate --dry-run
poetry run plex-leon episode-renamer --dry-run
poetry run plex-leon season-renamer --dry-run
poetry run plex-leon prepare --dry-run
```

4. Validate the decisions printed by the tool (DECISION lines and final summary). 

Note: when you use the provided test generators the utilities already default to the test library paths (for example `prepare` defaults to `data/library-p`). You therefore don't need to pass `--lib` flags when running the utilities against the generated data unless you put the generated data in a non-standard location.

#### Coverage

Generate coverage reports (HTML + lcov + xml + json) with the project's Poetry script:

```bash
poetry run coverage
# results will be available under data/coverage/
```

You can open `data/coverage/html/index.html` to view the HTML report in a browser.