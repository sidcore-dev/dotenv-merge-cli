"""Pure merge logic for dotenv-merge-cli.

No file I/O lives here — everything takes text in and returns text out,
which keeps it easy to unit test.
"""
from __future__ import annotations

import re

# Matches a KEY=VALUE assignment line, capturing the pieces we need to
# reconstruct the line with a substituted value while leaving everything
# else (indentation, `export `, spacing around `=`) untouched.
_ASSIGNMENT_RE = re.compile(
    r"^(?P<indent>[ \t]*)"
    r"(?P<export>export[ \t]+)?"
    r"(?P<key>[A-Za-z_][A-Za-z0-9_]*)"
    r"(?P<eq>[ \t]*=[ \t]*)"
    r"(?P<rest>.*)$"
)


def is_comment_or_blank(line: str) -> bool:
    """True if a raw line is empty/whitespace-only or a `#` comment."""
    stripped = line.strip()
    return stripped == "" or stripped.startswith("#")


def split_value_and_trailer(rest: str) -> tuple[str, str]:
    """Split the text after `KEY=` into (value, trailer).

    `value` is the raw value token as written, including surrounding
    quotes if any. `trailer` is everything that follows it verbatim -
    typically empty, or trailing whitespace plus an inline `# comment`.
    """
    if not rest:
        return "", ""

    quote = rest[0]
    if quote in ("'", '"'):
        end = 1
        while end < len(rest):
            if rest[end] == quote and rest[end - 1] != "\\":
                end += 1
                break
            end += 1
        else:
            # Unterminated quote: treat the whole remainder as the value.
            return rest, ""
        return rest[:end], rest[end:]

    # Unquoted value: runs until a ` #` style inline comment, or EOL.
    idx = 0
    while idx < len(rest):
        if rest[idx] == "#" and (idx == 0 or rest[idx - 1] in (" ", "\t")):
            break
        idx += 1
    value = rest[:idx].rstrip(" \t")
    trailer = rest[len(value):]
    return value, trailer


def parse_env_file(text: str) -> dict[str, str]:
    """Parse KEY=VALUE pairs out of `.env`-style text.

    Returns a mapping of key to its raw value token (quotes preserved,
    trailing inline comments stripped). Comment lines, blank lines, and
    an optional leading `export ` keyword are handled; unparsable lines
    are silently skipped.
    """
    result: dict[str, str] = {}
    for raw_line in text.splitlines():
        if is_comment_or_blank(raw_line):
            continue
        match = _ASSIGNMENT_RE.match(raw_line)
        if not match:
            continue
        value, _trailer = split_value_and_trailer(match.group("rest"))
        result[match.group("key")] = value
    return result


def merge_env_files(files: list[tuple[str, str]]) -> str:
    """Merge `.env`-style file contents, later files overriding earlier ones.

    `files` is a list of (label, text) pairs. The first entry is the base:
    its comments, blank lines, and key ordering are preserved verbatim,
    with only the value substituted for keys a later file overrides. Keys
    introduced by later files that the base file never had are appended
    at the end, grouped under a `# --- from <label> ---` comment per file.
    """
    if not files:
        return ""

    base_label, base_text = files[0]
    override_files = files[1:]

    final_values: dict[str, str] = dict(parse_env_file(base_text))
    base_keys = set(final_values)

    per_file_keys: list[tuple[str, dict[str, str]]] = []
    for label, text in override_files:
        keys = parse_env_file(text)
        per_file_keys.append((label, keys))
        final_values.update(keys)

    # Track which file first introduces each key that wasn't in the base,
    # preserving both file order and within-file key order.
    new_key_order: dict[str, list[str]] = {}
    seen_new_keys: set[str] = set()
    for label, keys in per_file_keys:
        for key in keys:
            if key in base_keys or key in seen_new_keys:
                continue
            seen_new_keys.add(key)
            new_key_order.setdefault(label, []).append(key)

    output_lines: list[str] = []
    for raw_line in base_text.splitlines():
        if is_comment_or_blank(raw_line):
            output_lines.append(raw_line)
            continue
        match = _ASSIGNMENT_RE.match(raw_line)
        if not match:
            output_lines.append(raw_line)
            continue
        key = match.group("key")
        old_value, trailer = split_value_and_trailer(match.group("rest"))
        new_value = final_values.get(key, old_value)
        if new_value != old_value:
            output_lines.append(
                f"{match.group('indent')}"
                f"{match.group('export') or ''}"
                f"{key}"
                f"{match.group('eq')}"
                f"{new_value}"
                f"{trailer}"
            )
        else:
            output_lines.append(raw_line)

    for label, keys in new_key_order.items():
        if output_lines and output_lines[-1] != "":
            output_lines.append("")
        output_lines.append(f"# --- from {label} ---")
        for key in keys:
            output_lines.append(f"{key}={final_values[key]}")

    result = "\n".join(output_lines)
    if not result.endswith("\n"):
        result += "\n"
    return result
