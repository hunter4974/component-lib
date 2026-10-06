from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Conflict:
    """A group of paths that collide under case-insensitive comparison.

    `paths` are stored verbatim from the input (after normalising separators).
    `key` is the lowercased form used to group them, exposed so callers can
    tell which conflicts are "the same" collision.
    """
    key: str
    paths: tuple[str, ...]

    def __post_init__(self) -> None:
        # Keep the invariant obvious: the key must match every member.
        for p in self.paths:
            computed = _key_for(p)
            if computed != self.key:
                raise ValueError(
                    f"Conflict invariant violated: path {p!r} does not "
                    f"match key {self.key!r}"
                )


def _normalise(p: str) -> str:
    """Normalise path separators to POSIX-style.

    We deliberately use forward slashes so that `Foo/Bar` and `Foo\\Bar` are
    treated as the same logical path. On the input side this means a Windows
    user can pass backslash-separated paths and still get correct collisions.
    """
    return p.replace(os.sep, "/") if os.sep != "/" else p


def _components(p: str) -> list[str]:
    """Split a path into its components.

    Empty components are dropped, so `a//b` and `a/b` are equivalent. This
    mirrors how case-sensitive filesystems typically treat repeated slashes.
    """
    return [c for c in p.split("/") if c]


def _key_for(norm: str) -> str:
    prefix = "/" if norm.startswith("/") else ""
    body = "/".join(c.lower() for c in _components(norm))
    if not body:
        return prefix
    return prefix + body


def find_conflicts(paths: list[str]) -> list[Conflict]:
    """Find case-insensitive collisions among the given paths.

    A collision is defined per-component: two paths conflict if, at the same
    depth, their component names differ only in case. So `Foo/bar` and
    `foo/Bar` conflict, but `Foo/bar` and `foo/qux` do not.

    The check is purely lexical. We do not touch the filesystem; if you need
    to verify that the paths actually exist, do that separately.

    Args:
        paths: The paths to check. Forward or backslash separators are both
            accepted; backslashes are normalised to forward slashes.

    Returns:
        A list of `Conflict` objects, one per collision group with at least
        two members. Groups are ordered by their first-seen member, and the
        members within a group retain their original relative order. Paths
        that do not collide with anything are omitted.
    """
    if not isinstance(paths, list):
        raise TypeError("paths must be a list")

    # Group paths by their lowercased, normalised full form.
    # Using a plain dict preserves insertion order in Python 3.7+.
    groups: dict[str, list[str]] = {}
    for p in paths:
        if not isinstance(p, str):
            raise TypeError(f"path must be a str, got {type(p).__name__}")
        norm = _normalise(p)
        key = _key_for(norm)
        groups.setdefault(key, []).append(norm)

    conflicts = [
        Conflict(key=key, paths=tuple(members))
        for key, members in groups.items()
        if len(members) >= 2
    ]
    return conflicts
