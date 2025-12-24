from dataclasses import dataclass
from typing import List

@dataclass
class CommandInfo:
    name: str
    description: str
    examples: List[str] = None

@dataclass
class CLIHelpContent:
    commands: List[CommandInfo]
    usage: str
    options: List[tuple[str, str]]

HELP_CONTENT = CLIHelpContent(
    commands=[
        CommandInfo("refine", "Refine a prompt using AI agents", [
            "promptify refine 'build a chat app'",
            "promptify refine --file input.txt",
            "promptify refine 'design database' --verbose",
            "promptify refine 'build api' --format rich",
            "promptify refine 'build api' --format json --output result.json"
        ]),
        CommandInfo("config", "Configure Promptify settings", [
            "promptify config --provider openai --model gpt-4",
            "promptify config --show"
        ]),
        CommandInfo("version", "Show version information"),
        CommandInfo("commands", "Show available commands"),
        CommandInfo("help", "Show help information"),
        CommandInfo("exit", "Exit the application"),
    ],
    usage="promptify <command> [options]",
    options=[
        ("--help", "Show help information"),
        ("--version", "Show version information"),
        ("--config", "Configure Promptify settings"),
        ("--exit", "Exit the application"),
    ]
)
