# Path Component Case Conflict Checker

Detects case-insensitive path collisions that would break when transferring files between case-insensitive filesystems (macOS HFS+, Windows NTFS) and case-sensitive ones (Linux ext4, XFS).

## Usage

```python
from path_component_case_conflict_checker import find_conflicts

conflicts = find_conflicts(["src/Foo/bar.py", "src/foo/bar.py"])
# conflicts is a list of Conflict objects, each with `.key` and `.paths`
for c in conflicts:
    print(c.key, c.paths)
```

`find_conflicts(paths: list[str]) -> list[Conflict]` takes a list of path strings and returns a list of `Conflict` instances. Each `Conflict` has two fields:

- `key: str` — the lowercased, normalised form of the colliding path.
- `paths: tuple[str, ...]` — the original paths (with separators normalised to `/`) that map to that key.

A collision is defined per-component: two paths conflict if, at the same depth, their component names differ only in case. So `Foo/bar` and `foo/Bar` conflict, but `Foo/bar` and `foo/qux` do not.

## Why this exists

When you zip up a project on macOS and hand it to a Linux CI server, paths like `Models/User.py` and `models/user.py` collapse on one side and silently overwrite each other on the other. This library scans a list of paths and tells you, up front, which ones would collide.

The check is purely lexical — we never touch the filesystem. The trade-off is that you must pass in the paths you want checked. The win is that the function is deterministic, fast, and safe to run anywhere.

## Edge cases

Backslash separators (Windows paths) are normalised to forward slashes internally. Empty path components from repeated slashes are collapsed: `a//b` and `a/b` are treated as the same path.

Case folding uses Python's `str.lower()`. This handles most ASCII and accented Latin characters correctly, but it does not perform full Unicode case folding. For example, `Straße` and `STRASSE` do not collide under `.lower()` because `ß.lower()` stays `ß` while `SS.lower()` stays `ss`. If you need full case-folding semantics, normalise your input before calling this function.

Leading and trailing slashes are preserved as path context: `/foo` and `foo` are not considered the same path, because they point to different locations.
