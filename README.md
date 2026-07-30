# dotenv-merge-cli

A small, dependency-free command-line tool that merges two or more
`.env`-style files into one, with later files overriding earlier keys.

## Why

Real projects end up with more than one env file — a shared `base.env`
plus per-environment overrides like `staging.env` or `production.env`.
Merging them by hand is error-prone and throws away the comments and
layout of the original file. `dotenv-merge-cli` merges them properly:
it keeps the base file's comments, blank lines, and key order intact,
only swapping in values that actually changed, and clearly marks any
brand-new keys a later file introduces.

## Install

```bash
pip install .
```

This installs a `dotenv-merge-cli` command on your PATH.

## Usage

```bash
dotenv-merge-cli base.env override.env [more.env ...]
```

The first file is the base — its structure is preserved. Each file after
it overrides matching keys from the ones before it, in order.

Given `base.env`:

```
# Base application config
APP_NAME=myapp
DEBUG=false

# Database
DATABASE_URL=postgres://localhost/dev
DATABASE_POOL_SIZE=5
```

and `production.env`:

```
DEBUG=false
DATABASE_URL=postgres://prod-host/myapp
SENTRY_DSN=https://example.ingest.sentry.io/123
```

running:

```bash
dotenv-merge-cli base.env production.env
```

prints:

```
# Base application config
APP_NAME=myapp
DEBUG=false

# Database
DATABASE_URL=postgres://prod-host/myapp
DATABASE_POOL_SIZE=5

# --- from production.env ---
SENTRY_DSN=https://example.ingest.sentry.io/123
```

`DATABASE_URL` was overridden in place, everything else in the base file
was left untouched (including comments and blank lines), and the new
`SENTRY_DSN` key was appended at the end under a comment noting where it
came from.

### Writing to a file

```bash
dotenv-merge-cli base.env production.env --out .env
```

Running that again without `--force` refuses to clobber the existing
`.env`:

```
dotenv-merge-cli: .env already exists, use --force to overwrite
```

Pass `--force` to overwrite it intentionally:

```bash
dotenv-merge-cli base.env production.env --out .env --force
```

### Options

| Flag       | Description                                       |
|------------|-----------------------------------------------------|
| `--out`    | Write the merged result to a file instead of stdout |
| `--force`  | Allow `--out` to overwrite an existing file          |

### Exit codes

- `0` — merge completed successfully
- `1` — a file could not be read, or `--out` exists and `--force` wasn't given
- `2` — fewer than two files were provided

## Development

```bash
pip install -e .
python -m unittest discover -s tests -v
```

## License

All rights reserved. This code is public for viewing and reference only —
no license is granted to use, copy, modify, or redistribute it. See
[LICENSE](LICENSE) for details.
