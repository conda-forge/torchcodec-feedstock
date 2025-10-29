#!/usr/bin/env python
"""
remove_symlinks_from_test.py

Walk %SRC_DIR%/test/resources and replace symbolic links (or Windows
reparse points/junctions) with the files or directories they point to by
copying the target contents in-place.

This script is intended to be run in the build/test environment where the
environment variable SRC_DIR is set (for example, by conda-build). It
attempts to handle both POSIX symlinks and Windows reparse points.
"""
from __future__ import annotations

import os
import sys
import shutil
from pathlib import Path
from typing import Optional

def is_reparse_point(path: Path) -> bool:
    """Return True if path is a reparse point on Windows or a symlink on POSIX."""
    try:
        if path.is_symlink():
            return True
    except OSError:
        # On some platforms/path conditions is_symlink may raise; fallthrough
        pass

    if os.name == 'nt':
        # On Windows, also consider reparse points (junctions) that
        # pathlib.Path.is_symlink() may not identify. Use GetFileAttributesW
        # to detect FILE_ATTRIBUTE_REPARSE_POINT.
        try:
            import ctypes

            FILE_ATTRIBUTE_REPARSE_POINT = 0x0400
            GetFileAttributesW = ctypes.windll.kernel32.GetFileAttributesW
            GetFileAttributesW.argtypes = [ctypes.c_wchar_p]
            GetFileAttributesW.restype = ctypes.c_uint32
            attrs = GetFileAttributesW(str(path))
            if attrs == 0xFFFFFFFF:
                return False
            return bool(attrs & FILE_ATTRIBUTE_REPARSE_POINT)
        except Exception:
            return False

    return False


def resolve_target(path: Path) -> Optional[Path]:
    """Return the resolved target Path for a symlink/reparse point.

    If the target cannot be resolved, return None.
    """
    try:
        # For standard symlinks, readlink() returns the target (may be relative)
        if path.is_symlink():
            tgt = os.readlink(str(path))
            tgt_path = (path.parent / tgt).resolve()
            return tgt_path
    except OSError:
        pass

    return None


def replace_link_with_target(link: Path) -> bool:
    """Replace the symlink/junction at `link` with the contents of its target.

    Returns True on success, False on failure/skipped.
    """
    target = resolve_target(link)
    if not target or not target.exists():
        print(f"Warning: cannot resolve target for link: {link}")
        return False

    try:
        # Remove the link first
        if link.exists() or link.is_symlink():
            # On Windows, for junctions, unlink may fail — use rmdir/file delete
            try:
                if link.is_dir() and not link.is_symlink():
                    # Some junctions appear as dirs but not symlinks; use rmdir
                    link.rmdir()
                else:
                    link.unlink()
            except Exception:
                # last resort: use shutil.rmtree for directories (force)
                if link.is_dir():
                    shutil.rmtree(str(link), ignore_errors=True)
                else:
                    try:
                        link.unlink()
                    except Exception:
                        pass

        # Now copy target to the link location
        if target.is_dir():
            shutil.copytree(str(target), str(link), dirs_exist_ok=True)
        else:
            # Ensure parent exists
            link.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(target), str(link))

        print(f"Replaced link: {link} -> {target}")
        return True
    except Exception as exc:
        print(f"Error replacing link {link}: {exc}")
        return False


def main() -> int:
    # If we're not on Windows, nothing to do here. Exit successfully so
    # cross-platform runs won't attempt Windows-specific reparse handling.
    if os.name != 'nt':
        print('Not running on Windows; skipping symlink replacement.')
        return 0

    src_dir = os.environ.get('SRC_DIR')
    if not src_dir:
        print('ERROR: SRC_DIR environment variable is not set')
        return 2

    root = Path(src_dir) / 'test' / 'resources'
    if not root.exists():
        print(f'No resources directory found at {root}. Nothing to do.')
        return 0

    # Walk the tree and collect reparse points/symlinks. We collect first to
    # avoid issues when modifying the tree while iterating.
    links = []
    for p in root.rglob('*'):
        try:
            if is_reparse_point(p):
                links.append(p)
        except Exception:
            # Ignore entries that cannot be inspected
            continue

    if not links:
        print('No symlinks/reparse points found. Nothing to do.')
        return 0

    success = True
    for link in sorted(links, key=lambda p: len(str(p)), reverse=True):
        # process deeper paths first to avoid clobbering directories
        ok = replace_link_with_target(link)
        if not ok:
            success = False

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
