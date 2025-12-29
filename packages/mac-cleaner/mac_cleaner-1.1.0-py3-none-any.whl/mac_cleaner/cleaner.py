#!/usr/bin/env python3
"""
Mac Cleaner - Main module with improved security and i18n support.
"""

import os
import shutil
import argparse
import subprocess
import json
import re
import sys
import platform
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple, Callable, Optional

from .i18n import _

# =========================
# Security Validations
# =========================

# Critical system paths that should NEVER be deleted
CRITICAL_PATHS = {
    Path("/"),
    Path("/System"),
    Path("/Library"),
    Path("/usr"),
    Path("/bin"),
    Path("/sbin"),
    Path("/etc"),
    Path("/var"),
    Path("/private"),
    Path("/Applications"),
    Path("/Volumes"),
    Path.home(),
    Path.home() / "Desktop",
    Path.home() / "Documents",
    Path.home() / "Downloads",
    Path.home() / "Pictures",
    Path.home() / "Music",
    Path.home() / "Movies",
    Path.home() / "Library",
}

# Patterns that indicate protected macOS system files
PROTECTED_PATTERNS = [
    r"^com\.apple\.",
    r"^\.DS_Store$",
    r"^\.localized$",
]


def is_macos() -> bool:
    """Check if running on macOS."""
    return platform.system() == "Darwin"


def is_safe_to_delete(path: Path) -> Tuple[bool, str]:
    """
    Check if a path is safe to delete.
    Returns (is_safe, reason_if_not_safe).
    """
    # Check if path is in critical paths
    resolved = path.resolve()
    for critical in CRITICAL_PATHS:
        try:
            if resolved == critical.resolve() or resolved in [critical.resolve()]:
                return False, _("Critical system path")
        except Exception:
            pass

    # Check if path is a parent of critical paths
    for critical in CRITICAL_PATHS:
        try:
            if critical.resolve().is_relative_to(resolved):
                return False, _("Contains critical system paths")
        except Exception:
            pass

    # Check if filename matches protected patterns
    filename = path.name
    for pattern in PROTECTED_PATTERNS:
        if re.match(pattern, filename):
            return False, _("Protected system file")

    # Additional check: ensure path is under user's home or known safe locations
    safe_roots = [
        Path.home() / "Library" / "Caches",
        Path.home() / "Library" / "Logs",
        Path("/tmp"),
        Path("/var/tmp"),
        Path("/private/var/tmp"),
        Path("/private/var/folders"),
    ]

    # Special case: check if it's a known safe path
    is_under_safe_root = False
    try:
        for safe_root in safe_roots:
            if resolved.is_relative_to(safe_root.resolve()):
                is_under_safe_root = True
                break
    except Exception:
        pass

    # If not under a safe root and not explicitly allowed, be cautious
    if not is_under_safe_root and not str(resolved).startswith(str(Path.home())):
        # Allow /tmp and /var/tmp though
        if not any(str(resolved).startswith(str(p)) for p in [Path("/tmp"), Path("/var/tmp"), Path("/private/var/tmp"), Path("/private/var/folders")]):
            return False, _("Outside safe deletion zones")

    return True, ""


# =========================
# Colors (ANSI)
# =========================

RESET = "\033[0m"
BOLD = "\033[1m"

FG_RED = "\033[31m"
FG_GREEN = "\033[32m"
FG_YELLOW = "\033[33m"
FG_BLUE = "\033[34m"
FG_CYAN = "\033[36m"
FG_MAGENTA = "\033[35m"
FG_GRAY = "\033[90m"


def color(text: str, c: str) -> str:
    """Apply ANSI color to text."""
    return f"{c}{text}{RESET}"


def bold(text: str) -> str:
    """Make text bold."""
    return f"{BOLD}{text}{RESET}"


# =========================
# Helpers
# =========================

def expand(p: str) -> Path:
    """Expand user path."""
    return Path(os.path.expanduser(p))


def human_size(num_bytes: int) -> str:
    """Convert bytes to human-readable format."""
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    for u in units:
        if size < 1024.0:
            return f"{size:.1f} {u}"
        size /= 1024.0
    return f"{size:.1f} PB"


def parse_docker_size(size_str: str) -> int:
    """Parse Docker size string to bytes."""
    m = re.match(r"([\d\.]+)([kMGT]?B)", size_str)
    if not m:
        return 0
    value = float(m.group(1))
    unit = m.group(2)
    multipliers = {
        "B": 1,
        "kB": 1000,
        "MB": 1000**2,
        "GB": 1000**3,
        "TB": 1000**4,
    }
    return int(value * multipliers.get(unit, 1))


def docker_is_running() -> bool:
    """Check if Docker is running and responding."""
    if shutil.which("docker") is None:
        return False
    try:
        subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=1,
            check=True
        )
        return True
    except Exception:
        return False


@dataclass
class PathItem:
    """Represents a path with its size and file count."""
    path: Path
    size_bytes: int
    file_count: int


@dataclass
class Category:
    """Represents a category of files to clean."""
    name: str
    description: str
    items: List[PathItem] = field(default_factory=list)

    @property
    def total_size(self) -> int:
        """Total size of all items in category."""
        return sum(i.size_bytes for i in self.items)

    @property
    def total_files(self) -> int:
        """Total number of files in category."""
        return sum(i.file_count for i in self.items)


# =========================
# Progress Bar
# =========================

def print_progress_bar(step: int, total: int, prefix: Optional[str] = None, length: int = 30):
    """Print a progress bar."""
    if prefix is None:
        prefix = _("Scanning")
    if total <= 0:
        total = 1
    fraction = step / total
    if fraction > 1:
        fraction = 1
    filled = int(length * fraction)
    bar = "█" * filled + " " * (length - filled)
    msg = f"{prefix}: |{bar}| {step}/{total}"
    print("\r" + color(msg, FG_CYAN), end="", flush=True)


# =========================
# Scan Logic
# =========================

def safe_walk(path: Path) -> Tuple[int, int]:
    """
    Safely walk a path and calculate total size and file count.
    Returns (size_bytes, file_count).
    """
    if not path.exists():
        return 0, 0

    if path.is_file():
        try:
            return path.stat().st_size, 1
        except OSError:
            return 0, 0

    total_size = 0
    file_count = 0
    try:
        for root, dirs, files in os.walk(path, followlinks=False):
            # Skip symlinks in directories
            dirs[:] = [d for d in dirs if not Path(root, d).is_symlink()]
            for f in files:
                fp = Path(root, f)
                try:
                    total_size += fp.stat().st_size
                    file_count += 1
                except OSError:
                    continue
    except OSError:
        pass
    return total_size, file_count


def add_if_exists(cat: Category, paths: List[Path]) -> None:
    """Add paths to category if they exist."""
    for p in paths:
        if p.exists():
            # Safety check before adding
            is_safe, reason = is_safe_to_delete(p)
            if not is_safe:
                print(color(f"\n[{_('WARNING')}] {_('Skipping protected path')}: {p} ({reason})", FG_YELLOW))
                continue

            size, count = safe_walk(p)
            if count > 0 or p.is_file():
                cat.items.append(PathItem(path=p, size_bytes=size, file_count=count))


def find_node_modules_roots(search_roots: List[Path], max_depth: int = 5) -> List[Path]:
    """
    Find node_modules directories in given roots.
    max_depth limits search depth to avoid infinite searches.
    """
    found: List[Path] = []
    for root in search_roots:
        if not root.exists():
            continue
        start_depth = len(root.parts)
        for dirpath, dirnames, _ in os.walk(root):
            current_depth = len(Path(dirpath).parts)
            if current_depth - start_depth > max_depth:
                dirnames[:] = []
                continue
            if "node_modules" in dirnames:
                nm_path = Path(dirpath) / "node_modules"
                found.append(nm_path)
                # Don't recurse into node_modules
                dirnames.remove("node_modules")
    return found


# -------------------------
# Docker
# -------------------------

def get_docker_reclaimable_bytes() -> int:
    """Get reclaimable space from Docker."""
    if shutil.which("docker") is None:
        return 0
    try:
        proc = subprocess.run(
            ["docker", "system", "df", "--format", "{{json .}}"],
            capture_output=True,
            text=True,
            check=True,
        )
    except Exception:
        return 0

    total = 0
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            info = json.loads(line)
        except Exception:
            continue
        rec = info.get("Reclaimable", "")
        if not rec or rec.startswith("0B"):
            continue
        first = rec.split()[0]
        total += parse_docker_size(first)
    return total


# -------------------------
# Category Scanners (for parallel execution)
# -------------------------

def _scan_temp_files() -> Category:
    """Scan temporary files."""
    cat = Category(
        _("Temporary Files"),
        _("System and app temporary files")
    )
    add_if_exists(cat, [
        Path("/tmp"),
        Path("/var/tmp"),
        Path("/private/var/tmp"),
        Path("/private/var/folders"),
    ])
    return cat


def _scan_logs() -> Category:
    """Scan system log files."""
    cat = Category(
        _("System Log Files"),
        _("System and application logs")
    )
    add_if_exists(cat, [
        expand("~/Library/Logs"),
        Path("/var/log"),
        Path("/Library/Logs"),
    ])
    return cat


def _scan_homebrew() -> Category:
    """Scan Homebrew cache."""
    cat = Category(
        _("Homebrew Cache"),
        _("Homebrew caches and downloads")
    )
    add_if_exists(cat, [
        expand("~/Library/Caches/Homebrew"),
        Path("/Library/Caches/Homebrew"),
        Path("/opt/homebrew/var/homebrew"),
    ])
    return cat


def _scan_browser_cache() -> Category:
    """Scan browser caches."""
    cat = Category(
        _("Browser Cache"),
        _("Web browser caches")
    )
    add_if_exists(cat, [
        expand("~/Library/Caches/com.apple.Safari"),
        expand("~/Library/Caches/Google/Chrome"),
        expand("~/Library/Caches/Firefox"),
        expand("~/Library/Caches/Mozilla"),
        expand("~/Library/Caches/BraveSoftware"),
        expand("~/Library/Caches/Microsoft Edge"),
    ])
    return cat


def _scan_node_modules() -> Category:
    """Scan node_modules directories."""
    cat = Category(
        _("Node Modules"),
        _("node_modules found in projects")
    )
    roots = [
        expand("~/Projects"),
        expand("~/Documents"),
        expand("~/workspace"),
        expand("~/Work"),
        expand("~/Developer"),
    ]
    dirs = find_node_modules_roots(roots, max_depth=5)
    add_if_exists(cat, dirs)
    return cat


def _scan_user_cache() -> Category:
    """Scan user cache files."""
    cat = Category(
        _("User Cache Files"),
        _("User caches (excluding com.apple.*)")
    )
    root = expand("~/Library/Caches")
    if root.exists():
        for child in root.iterdir():
            if child.name.startswith("com.apple."):
                continue
            size, files = safe_walk(child)
            if size > 0:
                cat.items.append(PathItem(child, size, files))
    return cat


def _scan_dev_cache() -> Category:
    """Scan development cache."""
    cat = Category(
        _("Development Cache"),
        _("Xcode, npm, pip, yarn caches, etc.")
    )
    add_if_exists(cat, [
        expand("~/Library/Developer/Xcode/DerivedData"),
        expand("~/Library/Developer/Xcode/Archives"),
        expand("~/Library/Developer/Xcode/iOS DeviceSupport"),
        expand("~/Library/Caches/CocoaPods"),
        expand("~/.npm"),
        expand("~/.cache/yarn"),
        expand("~/.cache/pip"),
        expand("~/.pnpm-store"),
        expand("~/.cargo/registry"),
        expand("~/.gradle/caches"),
    ])
    return cat


def _scan_docker() -> Tuple[Category, Optional[str]]:
    """Scan Docker data. Returns (category, warning_message)."""
    cat = Category(
        _("Docker Data"),
        _("Unused Docker images and volumes")
    )
    warning = None

    if not docker_is_running():
        warning = f"[{_('WARNING')}] {_('Docker is not running. Cannot calculate reclaimable space.')}"
        reclaimable = 0
    else:
        reclaimable = get_docker_reclaimable_bytes()

    cat.items.append(
        PathItem(path=Path("[Docker]"), size_bytes=reclaimable, file_count=0)
    )
    return cat, warning


# -------------------------
# Discover Categories
# -------------------------

def discover_categories(progress_cb: Optional[Callable] = None) -> List[Category]:
    """
    Discover all cleanable categories using parallel scanning.
    Returns list of Category objects.
    """
    # Define scanner order for consistent display
    scanner_order = [
        ("temp", _scan_temp_files),
        ("logs", _scan_logs),
        ("homebrew", _scan_homebrew),
        ("browser", _scan_browser_cache),
        ("node", _scan_node_modules),
        ("user_cache", _scan_user_cache),
        ("dev", _scan_dev_cache),
        ("docker", _scan_docker),
    ]

    results: dict = {}
    docker_warning: Optional[str] = None
    completed = 0
    lock = threading.Lock()
    total = len(scanner_order)

    def run_scanner(name: str, scanner: Callable):
        nonlocal completed, docker_warning
        try:
            result = scanner()
            # Docker returns a tuple (category, warning)
            if name == "docker":
                cat, warning = result
                if warning:
                    with lock:
                        nonlocal docker_warning
                        docker_warning = warning
                return name, cat
            return name, result
        finally:
            with lock:
                nonlocal completed
                completed += 1
                if progress_cb:
                    progress_cb(completed, total)

    # Run scanners in parallel with 4 workers
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(run_scanner, name, scanner): name
            for name, scanner in scanner_order
        }
        for future in as_completed(futures):
            name, category = future.result()
            results[name] = category

    # Print Docker warning if any
    if docker_warning:
        print(color(f"\n{docker_warning}\n", FG_YELLOW))

    # Return categories in original order, filtering empty ones
    categories = []
    for name, _ in scanner_order:
        if name in results and results[name].items:
            categories.append(results[name])

    return categories


# =========================
# UI & Cleanup
# =========================

def prompt_select_indices(max_index: int, allow_all: bool = True, allow_quit: bool = False) -> Optional[List[int]]:
    """
    Prompt user to select category indices.
    Returns None if user wants to quit (when allow_quit=True).
    Returns empty list if nothing selected.
    """
    while True:
        raw = input(color(f"> {_('Selection')}: ", FG_GREEN)).strip().lower()
        if not raw:
            return []
        # Check for quit commands
        if allow_quit and raw in ("q", "quit", "exit", "salir"):
            return None
        if allow_all and raw in ("all", "todo", "todos"):
            return list(range(max_index))
        parts = raw.split(",")
        result = []
        ok = True
        for p in parts:
            p = p.strip()
            if not p.isdigit():
                ok = False
                break
            v = int(p) - 1
            if v < 0 or v >= max_index:
                ok = False
                break
            result.append(v)
        if ok:
            return sorted(set(result))
        print(color(_("Invalid input."), FG_RED))


def confirm(prompt: str) -> bool:
    """Ask user for confirmation."""
    ans = input(color(f"{prompt} [y/N]: ", FG_YELLOW)).strip().lower()
    return ans in ("y", "yes", "s", "si", "sí")


def display_categories(categories: List[Category]) -> None:
    """Display the list of categories with their sizes."""
    print("\n" + bold(_("Categories found:")))
    for i, cat in enumerate(categories, 1):
        print(color(
            f"{i:2d}) {cat.name:30s}  {human_size(cat.total_size)} ({len(cat.items)} items)",
            FG_BLUE
        ))


def display_summary(selected_items: List[PathItem]) -> int:
    """Display summary of selected items. Returns total size in bytes."""
    total = sum(i.size_bytes for i in selected_items)
    print("\n" + bold("=" * 50))
    print(color(f"{_('Summary')}:", FG_CYAN))
    for i in selected_items:
        print(color(f"- {i.path}  {human_size(i.size_bytes)}", FG_BLUE))
    print(color(f"{_('Total')}: {human_size(total)}", FG_GREEN))
    print(bold("=" * 50))
    return total


def cleanup_selected(selected_items: List[PathItem]) -> None:
    """Execute cleanup for selected items."""
    print(color(f"\n{_('Starting deletion...')}", FG_CYAN))

    for item in selected_items:
        p = item.path

        # Special case: Docker
        if str(p) == "[Docker]":
            if not docker_is_running():
                print(color(f"[{_('SKIPPED')}] {_('Docker is not running, will not execute docker system prune.')}", FG_YELLOW))
                continue

            print(color(_("Executing docker system prune -af --volumes..."), FG_YELLOW))
            try:
                subprocess.run(
                    ["docker", "system", "prune", "-af", "--volumes"],
                    check=True
                )
                print(color(_("Docker cleaned."), FG_GREEN))
            except Exception as e:
                print(color(f"[{_('ERROR')}] {_('Docker prune failed')}: {e}", FG_RED))
            continue

        # Normal file/directory cases
        try:
            # Final safety check before deletion
            is_safe, reason = is_safe_to_delete(p)
            if not is_safe:
                print(color(f"[{_('SKIPPED')}] {_('Protected path')}: {p} ({reason})", FG_GRAY))
                continue

            if p.name.startswith("com.apple."):
                print(color(f"[{_('SKIPPED')}] {_('Skipping protected path')}: {p}", FG_GRAY))
                continue

            if p.is_dir() and not p.is_symlink():
                shutil.rmtree(p, ignore_errors=False)
            else:
                p.unlink(missing_ok=True)

            print(color(f"{_('Deleted')}: {p}", FG_GREEN))

        except PermissionError:
            print(color(f"[{_('SKIPPED')}] {_('Permission denied')}: {p}", FG_YELLOW))
        except OSError as e:
            if "Operation not permitted" in str(e):
                print(color(f"[{_('SKIPPED')}] {_('Protected by macOS')}: {p}", FG_GRAY))
            else:
                print(color(f"[{_('ERROR')}] {p}: {e}", FG_RED))

    print(color(f"\n{_('Cleanup completed.')}", FG_GREEN))


def interactive_cleanup(dry_run: bool = False):
    """Interactive cleanup process with loop to continue cleaning."""
    # Check if running on macOS
    if not is_macos():
        print(color(_("This tool is designed for macOS only."), FG_RED))
        sys.exit(1)

    first_scan = True

    while True:
        # Scan categories
        if first_scan:
            print(bold(color(_("Scanning categories..."), FG_CYAN)))
        else:
            print(bold(color(f"\n{_('Refreshing categories...')}", FG_CYAN)))

        categories = discover_categories(progress_cb=print_progress_bar)
        print()
        first_scan = False

        if not categories:
            print(color(_("No categories with data found."), FG_YELLOW))
            break

        # Display categories
        display_categories(categories)

        # Prompt for selection (with quit option)
        print(color(f"\n{_('Select categories (e.g., 1,3,5 or all, q to quit)')}: ", FG_GRAY))
        indices = prompt_select_indices(len(categories), allow_quit=True)

        # User wants to quit
        if indices is None:
            print(color(f"\n{_('Goodbye!')}", FG_GREEN))
            break

        # Nothing selected, continue loop
        if not indices:
            print(color(_("Nothing selected."), FG_YELLOW))
            continue

        # Gather selected items
        selected_items: List[PathItem] = []
        for idx in indices:
            selected_items.extend(categories[idx].items)

        # Display summary
        display_summary(selected_items)

        # Handle dry-run mode
        if dry_run:
            print(color(_("Dry-run: nothing will be deleted."), FG_YELLOW))
            continue

        # Confirm deletion
        if not confirm(_("Delete all of the above?")):
            print(color(_("Cancelled."), FG_YELLOW))
            continue

        # Execute cleanup
        cleanup_selected(selected_items)

        # Loop continues - will rescan and show updated sizes


# =========================
# Entry Point
# =========================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description=_("Mac Cleaner - Safe disk cleaning utility for macOS"),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=_("Simulate without deleting anything")
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.1.0"
    )

    args = parser.parse_args()
    interactive_cleanup(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
