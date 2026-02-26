#!/usr/bin/env python3
import os
import sys
import json
from pathlib import Path
import shutil

HOME = Path.home()
CONFIG_DIR = HOME / ".openhands"
CONFIG_FILE = CONFIG_DIR / "openhands.config.json"

def detect_shell_profile() -> Path:
    shell = os.environ.get("SHELL", "")
    if "zsh" in shell:
        return HOME / ".zshrc"
    if "bash" in shell:
        return HOME / ".bashrc"
    return HOME / ".profile"

def get_trae_commands_path():
    # Windows
    appdata = os.getenv("APPDATA")
    if appdata:
        path = Path(appdata) / "Trae" / "User" / "commands.json"
        return path
    return None

def ensure_trae_commands_file(path: Path):
    if not path.exists():
        print(f"[info] Trae commands.json not found. Creating new one at {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump({"commands": []}, f, indent=4)
    else:
        # Backup existing file
        backup = path.with_suffix(".backup.json")
        shutil.copy(path, backup)
        print(f"[info] Backed up existing commands.json to {backup}")

def add_trae_commands():
    commands_path = get_trae_commands_path()
    if not commands_path:
        print("[warn] Could not locate Trae commands.json path.")
        return

    ensure_trae_commands_file(commands_path)

    with open(commands_path, "r") as f:
        data = json.load(f)

    if "commands" not in data:
        data["commands"] = []

    new_commands = [
        {
            "name": "OpenHands: Run Task File",
            "command": "openhands run ${file}",
            "type": "terminal"
        },
        {
            "name": "OpenHands: Start Server",
            "command": "openhands serve",
            "type": "terminal"
        },
        {
            "name": "OpenHands: Validate Config",
            "command": "type %USERPROFILE%\\.openhands\\openhands.config.json",
            "type": "terminal"
        }
    ]

    for cmd in new_commands:
        if not any(c.get("name") == cmd["name"] for c in data["commands"]):
            data["commands"].append(cmd)

    with open(commands_path, "w") as f:
        json.dump(data, f, indent=4)

    print(f"[info] Added OpenHands commands to Trae at {commands_path}")
    print("[next] Restart Trae to load the new commands.")

def write_config(google_key: str, openrouter_key: str):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config = {
        "models": {
            "gemini-long": {
                "provider": "google",
                "model": "gemini-1.5-flash",
                "api_key_env": "GOOGLE_API_KEY"
            },
            "gemini-fast": {
                "provider": "google",
                "model": "gemini-2.5-flash",
                "api_key_env": "GOOGLE_API_KEY"
            },
            "deepseek-coder": {
                "provider": "openrouter",
                "model": "deepseek/deepseek-chat",
                "api_key_env": "OPENROUTER_API_KEY"
            }
        },
        "routing": {
            "long_context": "gemini-long",
            "coding": "deepseek-coder",
            "fast_chat": "gemini-fast"
        }
    }
    with CONFIG_FILE.open("w") as f:
        json.dump(config, f, indent=4)
    print(f"[info] Wrote OpenHands config to {CONFIG_FILE}")

def append_env_vars(google_key: str, openrouter_key: str):
    profile = detect_shell_profile()
    lines = []
    if google_key:
        lines.append(f'export GOOGLE_API_KEY="{google_key}"')
    if openrouter_key:
        lines.append(f'export OPENROUTER_API_KEY="{openrouter_key}"')

    if not lines:
        print("[info] No keys provided, skipping env var write.")
        return

    with profile.open("a") as f:
        f.write("\n# OpenHands hybrid model keys\n")
        for line in lines:
            f.write(line + "\n")

    print(f"[info] Appended API keys to {profile}")
    print(f"[next] Run: source {profile}  (or restart your terminal)")

def main():
    print("""
=========================================
 OpenHands Hybrid Setup (Trae-friendly)
=========================================

This script will:
 - Create ~/.openhands/openhands.config.json
 - Append your API keys to your shell profile
 - Create Trae's commands.json if missing
 - Inject OpenHands commands into Trae
 - Back up existing Trae settings
""")

    cont = input("Continue? (y/n): ").strip().lower()
    if cont != "y":
        print("Aborting.")
        sys.exit(0)

    print("\nEnter API keys (leave blank to skip a provider):")
    google_key = input("Google Gemini API key: ").strip()
    openrouter_key = input("OpenRouter API key (DeepSeek V3): ").strip()

    write_config(google_key, openrouter_key)
    append_env_vars(google_key, openrouter_key)
    add_trae_commands()

    print("""
=========================================
 Setup Complete
=========================================

Next steps:
 1. Restart Trae IDE
 2. You will now see:
      - OpenHands: Run Task File
      - OpenHands: Start Server
      - OpenHands: Validate Config
 3. Start OpenHands:
      openhands serve
 4. Run any task file:
      OpenHands: Run Task File

You're fully ready.
""")

if __name__ == "__main__":
    main()
