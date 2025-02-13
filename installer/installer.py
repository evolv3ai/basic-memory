import json
import os
import subprocess
from pathlib import Path

def ensure_uv_installed():
    """Check if uv is installed, install if not."""
    try:
        subprocess.run(['uv', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Installing uv package manager...")
        subprocess.run(['curl', '-LsSf', 'https://github.com/astral-sh/uv/releases/download/0.1.23/uv-installer.sh', '|', 'sh'], shell=True)

def get_config_path():
"""Get Claude Desktop config path for current platform."""
if sys.platform == "darwin":
return Path.home() / 'Library/Application Support/Claude/claude_desktop_config.json'
elif sys.platform == "win32":
return Path.home() / 'AppData/Roaming/Claude/claude_desktop_config.json'
else:
raise RuntimeError(f"Unsupported platform: {sys.platform}")

def update_claude_config():
"""Update Claude Desktop config to include basic-memory."""
config_path = get_config_path()
config_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing config or create new
    if config_path.exists():
        config = json.loads(config_path.read_text())
    else:
        config = {"mcpServers": {}}

    # Add/update basic-memory config
    config['mcpServers']['basic-memory'] = {
        "command": "uvx",
        "args": ["basic-memory"]
    }

    # Write back config
    config_path.write_text(json.dumps(config, indent=2))

def print_completion_message():
    """Show completion message with helpful tips."""
    print("\nInstallation complete! Basic Memory is now available in Claude Desktop.")
    print("Please restart Claude Desktop for changes to take effect.")
    print("\nQuick Start:")
    print("1. You can run sync directly using: uvx basic-memory sync")
    print("2. Optionally, install globally with: uv pip install basic-memory")
    print("\nBuilt with ♥️ by Basic Machines.")

def main():
    print("Welcome to Basic Memory installer")
    ensure_uv_installed()
    print("Configuring Claude Desktop...")
    update_claude_config()
    print_completion_message()

if __name__ == '__main__':
    main()
