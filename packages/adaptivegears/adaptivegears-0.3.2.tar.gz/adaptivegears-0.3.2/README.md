# adaptivegears

CLI tools for data engineering workflows. Part of the [AdaptiveGears](https://adaptivegears.studio) ecosystem.

## Why

We document patterns in our knowledge base. But patterns without tools are just theory.

This library closes the loop: tools we actually use at work become the examples in our articles. When we write about UUID v7 for time-sortable identifiers, we're using `adaptivegears uuid -7`. When we document PostgreSQL introspection, we're running `adaptivegears pg list`.

The constraint: keep it practical. All dependencies included - no extras to manage.

## Install

```bash
uvx adaptivegears --help
```

No install needed. [uvx](https://docs.astral.sh/uv/guides/tools/) runs it directly from PyPI.

## Commands

### uuid

Generate UUIDs. v4 by default, v7 for time-sortable.

```bash
uvx adaptivegears uuid           # v4
uvx adaptivegears uuid -7        # v7 (time-sortable)
uvx adaptivegears uuid -7 -n 5   # multiple
```

### pg

PostgreSQL utilities. Uses libpq environment variables.

```bash
export PGDATABASE=mydb PGHOST=localhost PGUSER=postgres

uvx adaptivegears pg list                # tables in public schema
uvx adaptivegears pg list -s myschema    # different schema
uvx adaptivegears pg list --json         # machine-readable
```

## Claude Code

These tools work well with [Claude Code](https://claude.ai/claude-code).

For repetitive tasks, Claude Code tends to write solutions from scratch. It usually works. But edge cases accumulate in places you wouldn't expect - bit layouts, parsing quirks, format inconsistencies.

This library provides polished alternatives. Instead of generating throwaway scripts, Claude Code can reach for tested implementations. The `--json` flag ensures consistent output for further processing.

The tools grow from patterns we've already debugged. Less re-invention, fewer surprises, fewer tokens.

## Links

- [Knowledge Base](https://adaptivegears.studio)
- [GitHub](https://github.com/adaptivegears)
