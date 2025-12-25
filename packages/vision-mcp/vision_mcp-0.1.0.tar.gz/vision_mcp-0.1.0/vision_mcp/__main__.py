import os
import json
from pathlib import Path
import sys
from dotenv import load_dotenv
import argparse

load_dotenv()


def get_claude_config_path() -> Path | None:
    """Get the Claude config directory based on platform."""
    if sys.platform == "win32":
        path = Path(Path.home(), "AppData", "Roaming", "Claude")
    elif sys.platform == "darwin":
        path = Path(Path.home(), "Library", "Application Support", "Claude")
    elif sys.platform.startswith("linux"):
        path = Path(
            os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"), "Claude"
        )
    else:
        return None

    if path.exists():
        return path
    return None


def get_python_path():
    return sys.executable


def generate_config(api_key: str | None = None):
    final_api_key = api_key or os.environ.get("OPENAI_API_KEY")
    final_api_base = os.environ.get("OPENAI_API_BASE")
    final_model = os.environ.get("OPENAI_MODEL")

    if not final_api_key:
        print("Error: OPENAI_API_KEY is required.")
        sys.exit(1)

    config = {
        "mcpServers": {
            "Vision": {
                "command": "uvx",
                "args": [
                    "vision-mcp",
                ],
                "env": {
                    "OPENAI_API_KEY": final_api_key,
                    "OPENAI_API_BASE": final_api_base or "https://api.openai.com",
                    "OPENAI_MODEL": final_model or "gpt-4o"
                },
            }
        }
    }

    return config


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--print",
        action="store_true",
        help="Print config to screen instead of writing to file",
    )
    parser.add_argument(
        "--api-key",
        help="API key (alternatively, set OPENAI_API_KEY environment variable)",
    )
    parser.add_argument(
        "--config-path",
        type=Path,
        help="Custom path to Claude config directory",
    )
    args = parser.parse_args()

    config = generate_config(args.api_key)

    if args.print:
        print(json.dumps(config, indent=2))
    else:
        claude_path = args.config_path if args.config_path else get_claude_config_path()
        if claude_path is None:
            print(
                "Could not find Claude config path automatically. Please specify it using --config-path argument."
            )
            sys.exit(1)

        claude_path.mkdir(parents=True, exist_ok=True)
        print("Writing config to", claude_path / "claude_desktop_config.json")
        with open(claude_path / "claude_desktop_config.json", "w") as f:
            json.dump(config, f, indent=2)
