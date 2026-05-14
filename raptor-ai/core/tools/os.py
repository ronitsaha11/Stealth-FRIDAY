import os
import subprocess
import logging

logger = logging.getLogger("core-tools-os")

APP_MAP = {
    "gmail": "https://mail.google.com",
    "browser": "Google Chrome",
    "chrome": "Google Chrome",
    "safari": "Safari",
    "firefox": "Firefox",
    "terminal": "Terminal",
    "code": "Visual Studio Code",
    "vs code": "Visual Studio Code",
    "notes": "Notes",
    "music": "Music",
    "calendar": "Calendar"
}

def _open_app(app_name: str) -> str:
    # Normalize input: lowercase, strip punctuation, trim
    clean_name = app_name.lower().strip().strip(".,")
    
    # Map to canonical name or URL
    target = APP_MAP.get(clean_name, clean_name)
    logger.info(f"[DEBUG] _open_app called with: '{app_name}', mapped to: '{target}'")
    
    # Special case: Gmail URL
    if target.startswith("http"):
        try:
            subprocess.run(["open", target], check=True)
            return f"Opening Gmail in your browser."
        except Exception as e:
            return f"Failed to open browser for Gmail: {e}"

    try:
        subprocess.run(["open", "-a", target], check=True, capture_output=True)
        return f"Successfully opened '{target}'."
    except subprocess.CalledProcessError as e:
        # Fallback: if it's not a common name, try the original name just in case mapping was wrong
        if target != clean_name:
             try:
                subprocess.run(["open", "-a", clean_name], check=True, capture_output=True)
                return f"Successfully opened '{clean_name}'."
             except: pass
        return f"Failed to open '{target}'. App might not be installed or name is incorrect."

def _search_files(query: str) -> str:
    try:
        result = subprocess.run(["mdfind", "-name", query], capture_output=True, text=True, check=True)
        files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
        if not files:
            return f"No files found matching '{query}'"
        limited_files = files[:20]
        output = "\n".join(limited_files)
        if len(files) > 20: 
            output += f"\n... and {len(files) - 20} more."
        return f"Found files:\n{output}"
    except subprocess.CalledProcessError as e:
        return f"Failed to search for files. Error: {e}"

def _create_folder(path: str) -> str:
    try:
        if not path:
            return "Path cannot be empty"
        full_path = os.path.abspath(os.path.expanduser(path))
        os.makedirs(full_path, exist_ok=True)
        return f"Successfully created folder at {full_path}"
    except Exception as e:
        return f"Failed to create folder. Error: {e}"

def _run_command(command: str) -> str:
    blocklist = ["rm", "sudo", "mkfs", "dd", "chmod", "chown", "shutdown", "reboot", "mv", "cp"]
    command_lower = command.lower()
    tokens = command_lower.split()
    if "rm -rf" in command_lower or "rm -f" in command_lower:
        return "Destructive commands like 'rm -rf' are strictly prohibited."
    if any(blocked == token for blocked in blocklist for token in tokens):
        return "Execution of this command is restricted for safety reasons."
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=15)
        output = result.stdout
        if result.stderr: 
            output += f"\nErrors:\n{result.stderr}"
        return output.strip() if output.strip() else "Command executed successfully with no output."
    except subprocess.TimeoutExpired:
        return "Command execution timed out after 15 seconds."
    except Exception as e:
        return f"Failed to execute command. Error: {e}"


def register(mcp):
    @mcp.tool(name="open_app")
    def open_app(app_name: str) -> str:
        """Open a macOS application by name."""
        return _open_app(app_name)

    @mcp.tool(name="search_files")
    def search_files(query: str) -> str:
        """Search for files in the system matching the query."""
        return _search_files(query)

    @mcp.tool(name="create_folder")
    def create_folder(path: str) -> str:
        """Create a new directory at the specified path."""
        return _create_folder(path)

    @mcp.tool(name="run_command")
    def run_command(command: str) -> str:
        """Run a shell command safely."""
        return _run_command(command)
