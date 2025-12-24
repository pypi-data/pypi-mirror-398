"""
Promptify CLI 
Thin CLI layer - delegates to core modules
"""

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from importlib.metadata import version as package_version, PackageNotFoundError
from pathlib import Path
from typing import Optional
import os

# Import core modules
from promptify.core.validator import InputValidator
from promptify.core.service import PromptifyService
from promptify.core.formatter import RichFormatter, JSONFormatter
from promptify.utils.errors import PromptifyError, ValidationError, ServiceError, ConfigurationError
from promptify.agent.graph import promptify

#Import PromptMasker
from promptmasker import PromptMasker

# Import CLI Helpers
from promptify.cli_supports.PromptifyTUI import PromptifyTUI
from promptify.cli_supports.help_content import HELP_CONTENT
app = typer.Typer(
    name="promptify",
    help="Transform vague prompts into professional specs using AI agents",
    no_args_is_help=True
)
console = Console()

# Dependency injection
validator = InputValidator()
service = PromptifyService(graph=promptify)

masker = PromptMasker()

formatters = {
    "rich": RichFormatter(),
    "json": JSONFormatter()
}


def show_banner():
    """Display banner"""
    try:
        from pyfiglet import Figlet
        fig = Figlet(font='slant')
        banner = fig.renderText('PROMPTIFY')
        console.print(f"[bold cyan]{banner}[/bold cyan]")
    except Exception:
        console.print("[bold cyan]╔═══════════════════════════╗[/bold cyan]")
        console.print("[bold cyan]║      PROMPTIFY v1.0       ║[/bold cyan]")
        console.print("[bold cyan]╚═══════════════════════════╝[/bold cyan]")
    console.print("[dim]Transform vague prompts → Professional specs[/dim]\n")


@app.command()
def refine(
    query: Optional[str] = typer.Argument(None, help="Query to refine"),
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="Read from file", exists=True),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save to file"),
    format: str = typer.Option("tui", "--format", help="Output format: tui|rich|json"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed analysis")
):
    """
    Refine a prompt using AI agents
    
    Examples:
        promptify refine "build a chat app"
        promptify refine --file input.txt
        promptify refine "design database" --verbose
        promptify refine "build api" --format rich
        promptify refine "build api" --format json --output result.json
    """
    
    show_banner()
    
    try:
        # 1. Load config and validate API key dynamically
        from promptify.core.providerSelection.config import PromptifyConfig
        cfg = PromptifyConfig.load()
        provider = cfg.model.provider
        
        # Check specific env vars based on provider
        if provider == "cerebras":
            validator.validate_api_key(os.getenv("CEREBRAS_API_KEY"))
        elif provider == "gemini":
            validator.validate_api_key(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
        elif provider == "openai":
            validator.validate_api_key(os.getenv("OPENAI_API_KEY"))
        elif provider == "anthropic":
            validator.validate_api_key(os.getenv("ANTHROPIC_API_KEY"))
        # local might not need api key or uses a different one

        
        # 2. Get and validate input
        if file:
            console.print(f"[dim] Reading from: {file}[/dim]")
            query = validator.validate_file(file)
        else:
            query = validator.validate_query(query)
        
        # 2.1 Mask sensitive data in query
        masked_output = masker.mask(query)
        if isinstance(masked_output, dict):
            masked_query = masked_output.get("masked_text", query)
            mask_map = masked_output.get("mask_map", {})
        else:
            masked_query = str(masked_output)
            mask_map = {}
        
        # Show input
        console.print(f"[cyan] Query:[/cyan] {masked_query[:100]}{'...' if len(masked_query) > 100 else ''}\n")
        
        # 3. Process with progress spinner
        with Progress(
            console=console,
        ) as progress:
            task = progress.add_task("[Processing] AI Agents working...", total=None)
            result = service.refine(masked_query)
            progress.remove_task(task)
        
        console.print()
        console.print("[green]✔ Processing complete![/green]\n")
        
        result_text = result['final_prompt_draft']
        
        # 4. Display based on format
        if format == "tui":
            # Interactive TUI (default)
            tui = PromptifyTUI(result_text)
            tui.run()
        else:
            # Traditional CLI output (rich or json)
            formatter = formatters.get(format, formatters["rich"])
            output_text = formatter.format_result(result, verbose)
            
            if output_text:  # JSON returns string
                print(output_text)
        
        # 5. Save if requested
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(result_text, encoding='utf-8')
            console.print(f"\n✔ Saved to: [green]{output}[/green]")
        
        console.print("\n[dim]* Done![/dim]")
    
    except ValidationError as e:
        console.print(f"[red]✖ Validation Error:[/red]\n{e}")
        raise typer.Exit(1)
    
    except ConfigurationError as e:
        console.print(f"[red]✖ Configuration Error:[/red]\n{e}")
        raise typer.Exit(1)
    
    except ServiceError as e:
        console.print(f"[red]✖ Service Error:[/red]\n{e}")
        raise typer.Exit(1)
    
    except PromptifyError as e:
        console.print(f"[red]✖ Error:[/red]\n{e}")
        raise typer.Exit(1)
    
    except KeyboardInterrupt:
        console.print("\n[yellow]!  Interrupted[/yellow]")
        raise typer.Exit(0)
    
    except Exception as e:
        console.print(f"[red]✖ Unexpected Error:[/red] {e}")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)

def get_version():
    try:
        return package_version("pfy")
    except PackageNotFoundError:
        import tomllib 
        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        return data["project"]["version"] 

@app.command()
def version():
    """Show version information"""
    show_banner()
    console.print("[bold]Version:[/bold] " + get_version())
    console.print("[bold]Framework:[/bold] LangGraph + Python")
    console.print("[bold]Agents:[/bold] Triage → Critic → Expert → Smith")

@app.command()
def commands():
    """Show available commands with examples"""
    show_banner()
    
    # Commands section
    console.print("[bold]Available commands:[/bold]")
    for cmd in HELP_CONTENT.commands:
        console.print(f"  {cmd.name}: {cmd.description}")
    console.print()
    
    # Usage section
    console.print("[bold]Usage:[/bold]")
    console.print(f"  {HELP_CONTENT.usage}")
    console.print()
    
    # Options section
    console.print("[bold]Options:[/bold]")
    for flag, desc in HELP_CONTENT.options:
        console.print(f"  {flag}: {desc}")
    console.print()
    
    # Examples section (only for commands that have them)
    console.print("[bold]Examples:[/bold]")
    for cmd in HELP_CONTENT.commands:
        if cmd.examples:
            for example in cmd.examples:
                console.print(f"  {example}")

@app.command()
def config(
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Set LLM provider (cerebras, openai, anthropic, local)"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Set model name"),
    temperature: Optional[float] = typer.Option(None, "--temp", "-t", help="Set temperature (0.0 - 1.0)"),
    verbose: Optional[bool] = typer.Option(None, "--verbose/--no-verbose", help="Enable/disable verbose mode"),
    show: bool = typer.Option(False, "--show", help="Show current configuration")
):
    """
    Configure Promptify settings
    
    Examples:
        promptify config            # Launch Interactive UI
        promptify config --show
        promptify config --provider openai --model gpt-4
    """
    
    # If no arguments provided, run Interactive TUI
    if not any([provider, model, temperature, verbose is not None, show]):
        from promptify.cli_supports.ConfigTUI import ConfigTUI
        app = ConfigTUI()
        app.run()
        return

    from promptify.core.providerSelection.config import PromptifyConfig
    
    # Load existing config
    cfg = PromptifyConfig.load()
    
    # Update if arguments are provided
    updated = False
    
    if provider:
        cfg.model.provider = provider
        updated = True
        console.print(f"[green]Set provider to: {provider}[/green]")
        
    if model:
        cfg.model.model = model
        updated = True
        console.print(f"[green]Set model to: {model}[/green]")
        
    if temperature is not None:
        cfg.model.temperature = temperature
        updated = True
        console.print(f"[green]Set temperature to: {temperature}[/green]")
        
    if verbose is not None:
        cfg.verbose = verbose
        updated = True
        status = "enabled" if verbose else "disabled"
        console.print(f"[green]Verbose mode {status}[/green]")
    
    # Save if changed
    if updated:
        cfg.save()
        console.print("[dim]Configuration saved.[/dim]\n")
    
    # Show config if requested or just saved (and not using TUI)
    if show or updated:
        console.print("[bold]Current Configuration:[/bold]")
        console.print(f"  Provider:    [cyan]{cfg.model.provider}[/cyan]")
        console.print(f"  Model:       [cyan]{cfg.model.model}[/cyan]")
        console.print(f"  Temperature: [cyan]{cfg.model.temperature}[/cyan]")
        console.print(f"  Verbose:     [cyan]{cfg.verbose}[/cyan]")
        console.print(f"  API Key:     [dim]{'Set in .env' if cfg.model.api_key or os.getenv('CEREBRAS_API_KEY') or os.getenv('OPENAI_API_KEY') else 'Missing'}[/dim]")


if __name__ == "__main__":
    app()