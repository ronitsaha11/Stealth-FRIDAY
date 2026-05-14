"""OS-level automation tools for Raptor — Windows-compatible."""

import os
import subprocess
import logging
import webbrowser
import shutil

logger = logging.getLogger("core-tools-os")

# ── Windows application name → executable / known path map ──

# Chrome may be installed in multiple places — resolve at runtime
def _find_chrome() -> str:
    """Return the path to Chrome exe, checking all common install locations."""
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Google\Chrome\Application\chrome.exe"),
        os.path.join(os.environ.get("PROGRAMFILES", ""), r"Google\Chrome\Application\chrome.exe"),
        os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), r"Google\Chrome\Application\chrome.exe"),
    ]
    for path in candidates:
        if path and os.path.isfile(path):
            return path
    return shutil.which("chrome") or shutil.which("chrome.exe") or ""


# Shell-safe built-in executables: ONLY these go through shell start
# to avoid the Windows "cannot find" error dialog on unknown names.
_SHELL_SAFE_BUILTINS = {
    "taskmgr", "explorer", "control", "notepad", "calc", "mspaint",
    "snippingtool", "cmd", "powershell", "regedit", "mmc",
    "msedge", "iexplore",
}

APP_MAP_WIN = {
    # Browsers
    "chrome":           None,          # resolved at runtime via _find_chrome()
    "google chrome":    None,
    "browser":          None,          # same
    "firefox":          r"C:\Program Files\Mozilla Firefox\firefox.exe",
    "edge":             "msedge",
    "microsoft edge":   "msedge",

    # System utilities
    "task manager":     "taskmgr",
    "taskmanager":      "taskmgr",
    "file explorer":    "explorer",
    "explorer":         "explorer",
    "control panel":    "control",
    "settings":         "ms-settings:",
    "notepad":          "notepad",
    "calculator":       "calc",
    "paint":            "mspaint",
    "snipping tool":    "snippingtool",
    "cmd":              "cmd",
    "command prompt":   "cmd",
    "powershell":       "powershell",
    "device manager":   "devmgmt.msc",
    "disk management":  "diskmgmt.msc",
    "event viewer":     "eventvwr.msc",
    "services":         "services.msc",
    "registry editor":  "regedit",
    "regedit":          "regedit",

    # Dev tools
    "vs code":              "code",
    "visual studio code":   "code",
    "code":                 "code",
    "git bash":             r"C:\Program Files\Git\git-bash.exe",

    # Other browsers
    "brave":        os.path.join(os.environ.get("LOCALAPPDATA", ""), r"BraveSoftware\Brave-Browser\Application\brave.exe"),
    "opera":        os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Programs\Opera\opera.exe"),

    # Communication
    "discord":      os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Discord\app.exe"),
    "slack":        "slack",
    "zoom":         os.path.join(os.environ.get("APPDATA", ""), r"Zoom\bin\Zoom.exe"),
    "telegram":     os.path.join(os.environ.get("APPDATA", ""), r"Telegram Desktop\Telegram.exe"),
    "whatsapp":     "WhatsApp",

    # Media & gaming
    "spotify":      os.path.join(os.environ.get("APPDATA", ""), r"Spotify\Spotify.exe"),
    "vlc":          r"C:\Program Files\VideoLAN\VLC\vlc.exe",
    "steam":        r"C:\Program Files (x86)\Steam\steam.exe",

    # Web shortcuts
    "gmail":        "https://mail.google.com",
    "youtube":      "https://youtube.com",
    "google":       "https://google.com",
    "whatsapp web": "https://web.whatsapp.com",
}


def _launch_windows(target: str) -> bool:
    """
    Try to launch a Windows target safely.
    Returns True on success, False if we are confident it will fail.
    NEVER calls bare `start` on unknown names to avoid the Windows error dialog.
    """
    if not target:
        return False

    # 1. URL → default browser
    if target.startswith("http://") or target.startswith("https://"):
        webbrowser.open(target)
        return True

    # 2. ms-settings: URI (e.g. ms-settings:)
    if target.startswith("ms-"):
        try:
            subprocess.Popen(["cmd", "/c", "start", "", target])
            return True
        except Exception:
            return False

    # 3. .msc snap-ins (device manager, services, etc.)
    if target.endswith(".msc"):
        try:
            subprocess.Popen(["mmc", target],
                             creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
            return True
        except Exception:
            # fallback via shell — .msc names are safe
            try:
                subprocess.Popen(["cmd", "/c", "start", "", target])
                return True
            except Exception:
                return False

    # 4. Absolute path that actually exists
    #    Use os.startfile first — it's the Windows-native launcher and handles
    #    GUI apps (Chrome, Brave, Spotify, etc.) that Popen can silently fail on.
    if os.path.isabs(target) and os.path.isfile(target):
        try:
            os.startfile(target)
            return True
        except Exception:
            try:
                subprocess.Popen(
                    [target],
                    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                )
                return True
            except Exception:
                return False

    # 5. Known executable on PATH
    exe_on_path = shutil.which(target) or shutil.which(target + ".exe")
    if exe_on_path:
        try:
            subprocess.Popen([exe_on_path],
                             creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
            return True
        except Exception:
            pass

    # 6. Shell-start ONLY for known-safe Windows built-ins
    #    (avoids the "Windows cannot find 'X'" error dialog for unknown names)
    if target.lower() in _SHELL_SAFE_BUILTINS:
        try:
            subprocess.Popen(["cmd", "/c", "start", "", target])
            return True
        except Exception:
            return False

    # Unknown target — do NOT attempt shell start (would show error dialog)
    return False


def _open_app(app_name: str) -> str:
    """Open an application or system utility by name (Windows-aware)."""
    clean_name = app_name.lower().strip().rstrip(".,?!")
    logger.info(f"[OS] open_app called: '{app_name}' -> clean: '{clean_name}'")

    # 1. Runtime resolution for Chrome (multiple install locations)
    if clean_name in {"chrome", "google chrome", "browser"}:
        chrome_path = _find_chrome()
        if chrome_path:
            if _launch_windows(chrome_path):
                return "Opened Google Chrome."
        # Chrome not found as app — open a URL instead
        webbrowser.open("https://google.com")
        return "Chrome not found. Opened default browser instead."

    # 2. Firefox — check both Program Files locations
    if clean_name == "firefox":
        for ff_path in [
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
        ]:
            if os.path.isfile(ff_path) and _launch_windows(ff_path):
                return "Opened Firefox."
        webbrowser.open("https://google.com")
        return "Firefox not found. Opened default browser instead."

    # 3. Curated map lookup
    target = APP_MAP_WIN.get(clean_name)

    # 4. Fuzzy partial key match
    if target is None:
        for key, val in APP_MAP_WIN.items():
            if clean_name in key or key in clean_name:
                target = val
                logger.info(f"[OS] fuzzy-matched '{clean_name}' -> '{key}': {val}")
                break

    # 5. Use clean_name as-is if nothing matched (PATH lookup will handle it)
    if target is None:
        target = clean_name

    if target and _launch_windows(target):
        return f"Opened {app_name.title()}."

    return (
        f"I couldn't open '{app_name}'. It may not be installed "
        f"or I don't recognise it on this Windows system."
    )


def _search_files(query: str) -> str:
    """Search for files by name using Windows 'where' / directory walk."""
    search_dirs = [
        os.path.expanduser("~/Desktop"),
        os.path.expanduser("~/Downloads"),
        os.path.expanduser("~/Documents"),
    ]
    matches = []
    for search_dir in search_dirs:
        if not os.path.isdir(search_dir):
            continue
        for root, _dirs, files in os.walk(search_dir):
            for filename in files:
                if query.lower() in filename.lower():
                    matches.append(os.path.join(root, filename))
            if len(matches) >= 20:
                break
        if len(matches) >= 20:
            break

    if not matches:
        return f"No files found matching '{query}' in Desktop, Downloads, or Documents."
    output = "\n".join(matches[:20])
    if len(matches) == 20:
        output += "\n... (showing first 20 results)"
    return f"Found files:\n{output}"


def _create_folder(path: str) -> str:
    """Create a new directory at the specified path."""
    if not path:
        return "Path cannot be empty."
    full_path = os.path.abspath(os.path.expanduser(path))
    try:
        os.makedirs(full_path, exist_ok=True)
        return f"Created folder at {full_path}."
    except Exception as e:
        return f"Failed to create folder: {e}"


def _run_command(command: str) -> str:
    """Run a shell command safely (Windows PowerShell)."""
    blocklist = ["rm", "rmdir", "del", "format", "shutdown", "reboot",
                 "mkfs", "dd", "chmod", "chown", "sudo"]
    command_lower = command.lower()
    tokens = command_lower.split()
    if any(blocked == token for blocked in blocklist for token in tokens):
        return "Execution of this command is restricted for safety reasons."
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
        output = result.stdout
        if result.stderr:
            output += f"\nErrors:\n{result.stderr}"
        return output.strip() or "Command executed successfully with no output."
    except subprocess.TimeoutExpired:
        return "Command execution timed out after 15 seconds."
    except Exception as e:
        return f"Failed to execute command: {e}"


def register(mcp):
    @mcp.tool(name="open_app")
    def open_app(app_name: str) -> str:
        """Open a Windows application or system utility by name."""
        return _open_app(app_name)

    @mcp.tool(name="search_files")
    def search_files(query: str) -> str:
        """Search for files matching the query."""
        return _search_files(query)

    @mcp.tool(name="create_folder")
    def create_folder(path: str) -> str:
        """Create a new directory at the specified path."""
        return _create_folder(path)

    @mcp.tool(name="run_command")
    def run_command(command: str) -> str:
        """Run a shell command safely."""
        return _run_command(command)
