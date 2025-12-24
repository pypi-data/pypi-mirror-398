"""Output formatting strategies"""
from abc import ABC, abstractmethod
from rich.console import Console
from rich.panel import Panel
import json

class OutputFormatter(ABC):
    """Abstract base for output formatters"""
    
    @abstractmethod
    def format_result(self, result: dict, verbose: bool = False) -> str:
        """Format the result"""
        pass

class RichFormatter(OutputFormatter):
    """Rich terminal output with colors and panels"""
    
    def __init__(self):
        self.console = Console()
    
    def format_result(self, result: dict, verbose: bool = False) -> str:
        self.console.print(Panel(
            f"[bold green]{result['intent']}[/bold green]",
            title="Intent",
            border_style="green"
        ))
        
        if verbose:
            self.console.print(Panel(result['critique'], title="Critique"))
            self.console.print(Panel(result['expert_suggestions'], title="Expert"))
        
        self.console.print(Panel(
            result['final_prompt_draft'],
            title="* Refined",
            border_style="magenta"
        ))
        
        return ""  # Rich prints directly

class JSONFormatter(OutputFormatter):
    """JSON output for piping/scripting"""
    
    def format_result(self, result: dict, verbose: bool = False) -> str:
        output = {
            "intent": result["intent"],
            "refined_prompt": result["final_prompt_draft"]
        }
        
        if verbose:
            output["critique"] = result["critique"]
            output["expert_suggestions"] = result["expert_suggestions"]
        
        return json.dumps(output, indent=2)
