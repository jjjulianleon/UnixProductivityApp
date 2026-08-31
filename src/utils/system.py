"""
Platform layer - the only module that knows whether we are on Linux or macOS.

Everything OS-specific lives here: data/config locations, opening files in the
default app, desktop notifications and the Obsidian vault location.
"""
import os
import subprocess
import sys
from pathlib import Path

IS_MAC = sys.platform == "darwin"


def data_dir(name: str = "UniDex") -> Path:
    """Writable app data directory (database, backups). Created if missing."""
    base = Path.home() / "Library" / "Application Support" if IS_MAC \
        else Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    path = base / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_dir(name: str = "UniDex") -> Path:
    """Config directory (json settings). Created if missing."""
    base = Path.home() / "Library" / "Application Support" if IS_MAC \
        else Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    path = base / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def obsidian_vault() -> Path:
    """
    Root of the Obsidian vault.

    $UNIDEX_OBSIDIAN_VAULT wins; otherwise the first location that exists
    (macOS keeps vaults in iCloud Drive by default), falling back to
    ~/Documents/Obsidian so writes still land somewhere sensible.
    """
    override = os.environ.get("UNIDEX_OBSIDIAN_VAULT")
    if override:
        return Path(override).expanduser()

    candidates = [Path.home() / "Documents" / "Obsidian"]
    if IS_MAC:
        candidates.insert(0, Path.home() / "Library" / "Mobile Documents" /
                          "iCloud~md~obsidian" / "Documents")
    for path in candidates:
        if path.exists():
            return path
    return Path.home() / "Documents" / "Obsidian"


def open_path(path) -> None:
    """Open a file/URL with the desktop's default handler."""
    opener = "open" if IS_MAC else "xdg-open"
    try:
        subprocess.Popen([opener, str(path)])
    except FileNotFoundError:
        pass


def notify(title: str, message: str, urgency: str = "normal",
           app_name: str = "UniDex", icon: str = None) -> bool:
    """Send a desktop notification. Returns True if it was delivered."""
    if IS_MAC:
        # osascript takes an AppleScript string literal: escape \ and " only.
        def esc(text):
            return text.replace("\\", "\\\\").replace('"', '\\"')

        script = (f'display notification "{esc(message)}" '
                  f'with title "{esc(app_name)}" subtitle "{esc(title)}"')
        if urgency == "critical":
            script += ' sound name "Glass"'
        cmd = ["osascript", "-e", script]
    else:
        cmd = ["notify-send", "-u", urgency, "-a", app_name, title, message]
        if icon:
            cmd += ["-i", icon]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def demo():
    assert data_dir().is_dir()
    assert config_dir().is_dir()
    assert obsidian_vault().is_absolute()

    os.environ["UNIDEX_OBSIDIAN_VAULT"] = "~/tmp/vault"
    assert obsidian_vault() == Path.home() / "tmp" / "vault"
    del os.environ["UNIDEX_OBSIDIAN_VAULT"]

    if IS_MAC:
        assert data_dir().parent.name == "Application Support"
    else:
        assert ".local" in str(data_dir())

    assert notify("Self test", 'quotes " and \\ backslash survive')
    print("system.py OK on", sys.platform)


if __name__ == "__main__":
    demo()
