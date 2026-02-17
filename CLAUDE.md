# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

RabbitMark is a desktop bookmark manager built with PyQt5 and SQLAlchemy/SQLite. It uses tag-based organization instead of folders. It has both a GUI and a CLI interface.

## Build & Development Commands

- **Run GUI**: `uv run rabbitmark` (or `uv run python -m rabbitmark`)
- **Run CLI**: `uv run rabbitmark find|go|copy [args]` (CLI mode activates when args are present)
- **Compile Qt forms**: `make ui` (runs `pyuic5`/`pyrcc5` via `scripts/make-forms.sh`)
- **Lint**: `uv run pylint rabbitmark/` (config in `pylintrc`, max line length 88)
- **Type check**: `uv run mypy rabbitmark/`
- **Tests**: `uv run pytest` or `cd test/behave && uv run behave`
- **Publish**: `make publish`

## Architecture

Three-layer architecture: presentation (gui/ and cli/) → business logic (librm/) → SQLite database.

- **`rabbitmark/__main__.py`** — Entry point. Launches GUI if no args, CLI if args present.
- **`rabbitmark/definitions.py`** — Global constants: version, `NOTAGS` sentinel, `SearchMode` enum.
- **`rabbitmark/librm/`** — Core library. All data operations live here:
  - `models.py` — SQLAlchemy ORM: `Bookmark`, `Tag` (many-to-many), `Config` (key-value store)
  - `database.py` — Session factory (`make_Session()`), SQLite pragmas (WAL mode), platform-specific DB paths
  - `bookmark.py`, `tag.py`, `config.py` — CRUD operations; accept `Session` as first parameter
  - `broken_links.py` — Link checker using `ThreadPoolExecutor` (15 workers)
  - `wayback_snapshot.py` — WayBackMachine CDX API integration
  - `interchange.py` — CSV import/export
- **`rabbitmark/gui/`** — PyQt5 widgets and dialogs
  - `gui/forms/` — Auto-generated from Qt Designer `.ui` files in `designer/`. Do not edit by hand; run `make ui` to regenerate.
- **`rabbitmark/cli/`** — CLI argument parsing and handlers

## Key Conventions

- Library functions in `librm/` take a SQLAlchemy `Session` as their first argument.
- Bookmark names must be unique (duplicates get auto-numbered). URLs are not unique.
- In Qt UI code, use `camelCase` to match Qt's API style; use `snake_case` everywhere else.
- The `RABBITMARK_DATABASE` env var overrides the default database path.
