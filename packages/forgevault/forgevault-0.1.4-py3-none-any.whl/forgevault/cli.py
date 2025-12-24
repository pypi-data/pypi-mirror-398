"""
ForgeVault CLI - Command line interface for ForgeVault SDK

Copyright (c) 2025 ForgeVault. All Rights Reserved.

Usage:
    forgevault login                         Authenticate (one time)
    forgevault list                          List all prompts
    forgevault get "prompt name"             Get prompt details
    forgevault run "prompt name" --model     Run a prompt
    forgevault render "prompt name"          Render without execution
    forgevault prompt-versions "name"        Show version history
    forgevault cache clear                   Clear local cache
    forgevault logout                        Sign out
    forgevault version                       Show CLI version
"""

import sys
import os
import json
import getpass
from pathlib import Path
from typing import Optional, List

try:
    import typer
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich import print as rprint
except ImportError:
    print("CLI dependencies not installed. Run: pip install forgevault[cli]")
    sys.exit(1)

from forgevault import Forge, __version__

CLI_USER_AGENT = f"forgevault-cli/{__version__}"
from forgevault.exceptions import (
    ForgeVaultError,
    AuthenticationError,
    PromptNotFoundError,
    ConnectionError
)

# Config file location: ~/.forgevault/config.json
CONFIG_DIR = Path.home() / ".forgevault"
CONFIG_FILE = CONFIG_DIR / "config.json"

app = typer.Typer(
    name="forgevault",
    help="ForgeVault CLI - Manage and run your AI prompts from the command line",
    add_completion=False
)
cache_app = typer.Typer(help="Cache management commands")
app.add_typer(cache_app, name="cache")

console = Console()


# ==================== CONFIG HELPERS ====================

def load_config() -> dict:
    """Load saved config from ~/.forgevault/config.json"""
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except Exception:
            return {}
    return {}


def save_config(config: dict):
    """Save config to ~/.forgevault/config.json"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))
    # Set restrictive permissions (owner read/write only)
    CONFIG_FILE.chmod(0o600)


def get_api_key() -> Optional[str]:
    """Get API key from: 1) env var, 2) saved config"""
    # Environment variable takes priority
    env_key = os.getenv("FORGEVAULT_API_KEY")
    if env_key:
        return env_key
    
    # Fall back to saved config
    config = load_config()
    return config.get("api_key")


def get_client() -> Forge:
    """Get ForgeVault client, handling auth errors gracefully"""
    api_key = get_api_key()
    
    if not api_key:
        console.print("[red]Authentication Error:[/red] No API key found")
        console.print("\nLogin first (one time only):")
        console.print("  [cyan]forgevault login[/cyan]")
        console.print("\nOr set environment variable:")
        console.print("  export FORGEVAULT_API_KEY=fv_your_key")
        raise typer.Exit(1)
    
    try:
        return Forge(api_key=api_key, user_agent=CLI_USER_AGENT)
    except AuthenticationError as e:
        console.print(f"[red]Authentication Error:[/red] {e}")
        console.print("\nYour credentials may be invalid. Try logging in again:")
        console.print("  [cyan]forgevault login[/cyan]")
        raise typer.Exit(1)


def handle_error(e: Exception):
    """Handle errors with nice formatting"""
    if isinstance(e, AuthenticationError):
        console.print(f"[red]Authentication Error:[/red] {e}")
        console.print("\nCheck your API key is valid.")
    elif isinstance(e, PromptNotFoundError):
        console.print(f"[red]Prompt Not Found:[/red] {e}")
        console.print("\nUse [cyan]forgevault list[/cyan] to see available prompts.")
    elif isinstance(e, ConnectionError):
        console.print(f"[red]Connection Error:[/red] Could not reach ForgeVault API")
        console.print("\nPossible causes:")
        console.print("  • Server is not running")
        console.print("  • Wrong API URL")
        console.print("  • No internet connection")
        console.print("\nIf running locally, start your backend server first.")
    elif isinstance(e, ForgeVaultError):
        console.print(f"[red]Error:[/red] {e}")
        if "Invalid response" in str(e) or "Empty response" in str(e):
            console.print("\nThe server returned an unexpected response.")
            console.print("Make sure:")
            console.print("  • Your backend server is running")
            console.print("  • The API URL is correct")
            console.print(f"\nCurrent API URL: [dim]{os.getenv('FORGEVAULT_BASE_URL', 'https://forgevault.onrender.com/api/v1')}[/dim]")
    else:
        console.print(f"[red]Unexpected Error:[/red] {e}")
        console.print("\n[dim]If this persists, check:[/dim]")
        console.print("  • Is your backend server running?")
        console.print("  • Is the API URL correct?")
    raise typer.Exit(1)


def _print_usage_stats(data: dict):
    """Pretty print token usage, cost, and latency stats"""
    token_usage = data.get("token_usage", {})
    input_cost = data.get("input_cost")
    output_cost = data.get("output_cost")
    total_cost = data.get("estimated_cost")
    latency = data.get("latency_ms")
    
    if not token_usage and not total_cost and not latency:
        return
    
    console.print()
    
    if token_usage:
        prompt_tokens = token_usage.get('prompt_tokens', 0)
        completion_tokens = token_usage.get('completion_tokens', 0)
        total_tokens = token_usage.get('total_tokens', 0)
        console.print("[bold cyan][Tokens][/bold cyan]")
        console.print(f"     Prompt Tokens:     [cyan]{prompt_tokens:,}[/cyan]")
        console.print(f"     Completion Tokens: [cyan]{completion_tokens:,}[/cyan]")
        console.print(f"     Total Tokens:      [bold cyan]{total_tokens:,}[/bold cyan]")
        console.print()
    
    if total_cost is not None:
        in_cost = f"${input_cost:.6f}" if input_cost else "$0.000000"
        out_cost = f"${output_cost:.6f}" if output_cost else "$0.000000"
        tot_cost = f"${total_cost:.6f}" if total_cost else "$0.000000"
        console.print("[bold yellow][Cost][/bold yellow]")
        console.print(f"     Input Cost:  [yellow]{in_cost}[/yellow]")
        console.print(f"     Output Cost: [yellow]{out_cost}[/yellow]")
        console.print(f"     Total Cost:  [bold yellow]{tot_cost}[/bold yellow]")
        console.print()
    
    if latency:
        latency_str = f"{latency:,.0f}ms" if latency < 1000 else f"{latency/1000:.2f}s"
        console.print("[bold magenta][Latency][/bold magenta]")
        console.print(f"     {latency_str}")


def _print_variables(variables: dict):
    """Pretty print variables in a vertical format"""
    if not variables:
        return
    console.print("\n[bold cyan][Variables][/bold cyan]")
    for key, value in variables.items():
        console.print(f"     [magenta]{key}[/magenta]: [green]{value}[/green]")


def _print_json(data):
    """Pretty print JSON data with syntax highlighting"""
    json_str = json.dumps(data, indent=2, default=str)
    syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
    console.print(syntax)


# ==================== AUTH COMMANDS ====================

@app.command("login")
def login(
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", help="Pass credentials directly (will prompt if not provided)", hidden=True)
):
    """
    Authenticate with ForgeVault (one time setup).
    
    Examples:
        forgevault login
    """
    # If no key provided, prompt securely
    if not api_key:
        console.print("[cyan]Enter your ForgeVault API key[/cyan]")
        console.print("[dim](Get your key from https://forgevault.onrender.com/settings)[/dim]\n")
        try:
            api_key = getpass.getpass("API Key: ")
        except KeyboardInterrupt:
            console.print("\n[yellow]Cancelled[/yellow]")
            raise typer.Exit(0)
    
    if not api_key or not api_key.strip():
        console.print("[red]✗ No API key provided[/red]")
        raise typer.Exit(1)
    
    api_key = api_key.strip()
    
    if not api_key.startswith("fv_"):
        console.print("[yellow]Warning:[/yellow] API key should start with 'fv_'")
    
    # Test the key first
    console.print("[dim]Verifying...[/dim]")
    try:
        forge = Forge(api_key=api_key, user_agent=CLI_USER_AGENT)
        # Try a simple operation to verify
        forge.list_prompts(limit=1)
        forge.close()
    except AuthenticationError:
        console.print("[red]✗ Invalid API key[/red]")
        console.print("Please check your key and try again.")
        raise typer.Exit(1)
    except typer.Exit:
        raise
    except Exception as e:
        # Connection errors are OK - key format is valid
        if "connect" not in str(e).lower():
            console.print(f"[yellow]Warning:[/yellow] Could not verify key: {e}")
    
    # Save the key
    config = load_config()
    config["api_key"] = api_key
    save_config(config)
    
    console.print("[green]✓ Logged in successfully![/green]")
    console.print("\n[bold]Quick Start:[/bold]")
    console.print("  [cyan]forgevault list[/cyan]                     List your prompts")
    console.print("  [cyan]forgevault get \"prompt name\"[/cyan]        View prompt details")
    console.print("  [cyan]forgevault run \"prompt name\" --model gpt-4o[/cyan]")
    console.print("  [cyan]forgevault --help[/cyan]                   See all commands")


@app.command("logout")
def logout():
    """
    Sign out and remove saved credentials.
    
    Examples:
        forgevault logout
    """
    config = load_config()
    
    if "api_key" not in config:
        console.print("[yellow]Not logged in[/yellow]")
        return
    
    del config["api_key"]
    save_config(config)
    
    console.print("[green]✓ Logged out successfully[/green]")


@app.command("whoami")
def whoami():
    """
    Show current authentication status.
    
    Examples:
        forgevault whoami
    """
    config = load_config()
    env_key = os.getenv("FORGEVAULT_API_KEY")
    saved_key = config.get("api_key")
    
    console.print("[cyan]ForgeVault Status[/cyan]\n")
    
    # Auth status
    if env_key:
        console.print("[green]✓ Authenticated[/green] (environment variable)")
    elif saved_key:
        console.print("[green]✓ Authenticated[/green]")
    else:
        console.print("[red]✗ Not authenticated[/red]")
        console.print("\n[dim]Login with:[/dim]")
        console.print("  [cyan]forgevault login[/cyan]")
    


# ==================== MAIN COMMANDS ====================

@app.command("list")
def list_prompts(
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum prompts to show"),
    output_json: bool = typer.Option(False, "--json", "-j", help="Output as JSON")
):
    """
    List all prompts in your workspace.
    
    Examples:
        forgevault list
        forgevault list --limit 10
        forgevault list --json
    """
    try:
        forge = get_client()
        prompts = forge.list_prompts(limit=limit)
        
        if output_json:
            _print_json(prompts)
            return
        
        if not prompts:
            console.print("[yellow]No prompts found.[/yellow]")
            console.print("Create prompts at [cyan]https://forgevault.onrender.com[/cyan]")
            return
        
        table = Table(title="Your Prompts", show_header=True, header_style="bold cyan")
        table.add_column("Name", style="green", no_wrap=False)
        table.add_column("Type", style="blue")
        table.add_column("Version", style="magenta")
        table.add_column("Updated", style="dim")
        
        for p in prompts:
            updated = str(p.get("updated_at", ""))[:10] if p.get("updated_at") else "-"
            table.add_row(
                p.get("name", "-"),
                p.get("prompt_type", "-"),
                p.get("version", "-")[:8] if p.get("version") else "-",
                updated
            )
        
        console.print(table)
        console.print(f"\n[dim]Showing {len(prompts)} prompt(s)[/dim]")
        
    except Exception as e:
        handle_error(e)


@app.command("get")
def get_prompt(
    name: str = typer.Argument(..., help="Prompt name (use quotes for spaces)"),
    version: Optional[str] = typer.Option(None, "--version", "-v", help="Specific version"),
    output_json: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    show_full: bool = typer.Option(False, "--full", "-f", help="Show full prompt content")
):
    """
    Get details of a specific prompt.
    
    Examples:
        forgevault get "sql data generator"
        forgevault get "customer support" --version abc123
        forgevault get "my prompt" --full
        forgevault get "my prompt" --json
    """
    try:
        forge = get_client()
        prompt = forge.get_prompt(prompt_name=name, version=version)
        
        if output_json:
            data = {
                "id": prompt.id,
                "name": prompt.name,
                "description": prompt.description,
                "use_case": prompt.use_case,
                "prompt_type": prompt.prompt_type,
                "version": prompt.version,
                "variables": [{"name": v.name, "type": v.type, "required": v.required} for v in prompt.variables],
                "system_prompt": prompt.system_prompt,
                "user_prompt": prompt.user_prompt,
                "few_shot_examples": prompt.few_shot_examples
            }
            _print_json(data)
            return
        
        # Basic info first
        console.print(f"[cyan]Prompt:[/cyan]   [bold green]{prompt.name}[/bold green]")
        console.print(f"[cyan]Version:[/cyan]  {prompt.version[:12] if prompt.version else 'latest'}...")
        console.print(f"[cyan]ID:[/cyan]       {prompt.id}")
        
        # Prompt Details
        console.print(f"\n[bold cyan][Description][/bold cyan]")
        console.print(f"  {prompt.description or 'No description'}")
        
        console.print(f"\n[bold cyan][Use Case][/bold cyan]")
        console.print(f"  {prompt.use_case or 'No use case'}")
        
        console.print(f"\n[bold cyan][Type][/bold cyan]")
        console.print(f"  {prompt.prompt_type}")
        
        # Variables section
        console.print(f"\n[bold cyan][Variables][/bold cyan]")
        if prompt.variables:
            for v in prompt.variables:
                opt = "" if v.required else " [dim](optional)[/dim]"
                console.print(f"  • [magenta]{v.name}[/magenta] [dim]({v.type})[/dim]{opt}")
        else:
            console.print("  [dim]None[/dim]")
        
        # Content preview or full
        if show_full:
            if prompt.system_prompt:
                console.print(Panel(prompt.system_prompt, title="[yellow]System Prompt[/yellow]", border_style="yellow"))
            
            if prompt.user_prompt:
                console.print(Panel(prompt.user_prompt, title="[blue]User Prompt[/blue]", border_style="blue"))
            
            if prompt.few_shot_examples:
                console.print(Panel(prompt.few_shot_examples, title="[magenta]Few-Shot Examples[/magenta]", border_style="magenta"))
        else:
            # Preview only in boxes
            if prompt.system_prompt:
                preview = prompt.system_prompt[:300] + "..." if len(prompt.system_prompt) > 300 else prompt.system_prompt
                console.print(Panel(preview, title="[yellow]System Prompt [dim][Preview][/dim][/yellow]", border_style="yellow"))
            
            if prompt.user_prompt:
                preview = prompt.user_prompt[:300] + "..." if len(prompt.user_prompt) > 300 else prompt.user_prompt
                console.print(Panel(preview, title="[blue]User Prompt [dim][Preview][/dim][/blue]", border_style="blue"))
            
            console.print(f"\n[dim]Use --full to see complete content[/dim]")
        
    except Exception as e:
        handle_error(e)


@app.command("run")
def run_prompt(
    name: str = typer.Argument(..., help="Prompt name (use quotes for spaces)"),
    model: str = typer.Option(..., "--model", "-m", help="Model to use (e.g., gpt-4o, claude-sonnet-4-20250514)"),
    var: Optional[List[str]] = typer.Option(None, "--var", "-V", help="Variable as key=value"),
    version: Optional[str] = typer.Option(None, "--version", "-v", help="Specific version"),
    temperature: Optional[float] = typer.Option(None, "--temperature", "-t", help="Temperature (0-2)"),
    max_tokens: Optional[int] = typer.Option(None, "--max-tokens", help="Max tokens"),
    output_json: bool = typer.Option(False, "--json", "-j", help="Output as JSON with metadata"),
    stream: bool = typer.Option(False, "--stream", help="Stream output in real-time"),
    strict: bool = typer.Option(False, "--strict", "-s", help="Validate all required variables before running")
):
    """
    Run a prompt with the specified model.
    
    Examples:
        forgevault run "sql data generator" --model gpt-4o --var table=users
        forgevault run "customer support" -m claude-sonnet-4-20250514 -V name=John -V issue="refund request"
        forgevault run "my prompt" --model gpt-4o --temperature 0.7
        forgevault run "my prompt" --model gpt-4o --json
    """
    try:
        forge = get_client()
        
        # Parse variables
        variables = {}
        if var:
            for v in var:
                if "=" not in v:
                    console.print(f"[red]Invalid variable format:[/red] {v}")
                    console.print("Use format: --var key=value")
                    raise typer.Exit(1)
                key, value = v.split("=", 1)
                variables[key.strip()] = value.strip()
        
        # Show what we're doing
        if not output_json:
            console.print(f"[cyan]Prompt:[/cyan]      {name}")
            console.print(f"[cyan]Model:[/cyan]       {model}")
            if version:
                console.print(f"[cyan]Version:[/cyan]     {version}")
            if temperature is not None:
                console.print(f"[cyan]Temperature:[/cyan] {temperature}")
            if max_tokens is not None:
                console.print(f"[cyan]Max Tokens:[/cyan]  {max_tokens}")
            _print_variables(variables)
            console.print()
        
        if strict:
            prompt = forge.get_prompt(prompt_name=name, version=version)
            missing = prompt.validate_variables(variables)
            if missing:
                console.print(f"[yellow]Missing variables:[/yellow] {', '.join(missing)}")
                console.print("\nExpected variables for this prompt:")
                for v in prompt.variables:
                    status = "[red]*[/red]" if v.required else "[dim](optional)[/dim]"
                    console.print(f"  --var {v.name}=<value> {status}")
                raise typer.Exit(1)
        
    except typer.Exit:
        raise  # Re-raise Exit without handling
    except Exception as e:
        handle_error(e)
        return
    
    # Run it (outside try block for cleaner error handling)
    try:
        if stream:
            # Streaming mode
            console.print("\n[bold green][Output][/bold green]\n")
            full_output = []
            stream_metadata = None
            for item in forge.run_prompt_stream(
                model=model,
                prompt_name=name,
                variables=variables,
                version=version,
                temperature=temperature,
                max_tokens=max_tokens,
                return_metadata=True
            ):
                if isinstance(item, dict) and item.get("type") == "metadata":
                    stream_metadata = item
                else:
                    console.print(item, end="")
                    full_output.append(item)
            console.print("\n")
            
            # Show metadata
            if stream_metadata:
                _print_usage_stats(stream_metadata)
            
            if output_json:
                output = {
                    "prompt_name": name,
                    "model": model,
                    "variables": variables,
                    "output": "".join(full_output),
                    **(stream_metadata or {})
                }
                _print_json(output)
        else:
            # Non-streaming mode - call run_prompt directly (single API call)
            with console.status("[bold green]Executing prompt..."):
                result = forge.run_prompt(
                    model=model,
                    prompt_name=name,
                    variables=variables,
                    version=version,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    return_metadata=True
                )
            
            if output_json:
                _print_json(result)
            else:
                console.print("\n[bold green][Output][/bold green]\n")
                console.print(result.get("output", ""))
                _print_usage_stats(result)
        
    except Exception as e:
        handle_error(e)


@app.command("prompt-versions")
def get_prompt_versions(
    name: str = typer.Argument(..., help="Prompt name (use quotes for spaces)"),
    output_json: bool = typer.Option(False, "--json", "-j", help="Output as JSON")
):
    """
    Show version history for a prompt.
    
    Lists all versions with their commit messages.
    
    Examples:
        forgevault prompt-versions "SQL Query Generator"
        forgevault prompt-versions "my prompt" --json
    """
    try:
        forge = get_client()
        versions = forge.get_versions(prompt_name=name)
        
        if output_json:
            _print_json(versions)
            return
        
        if not versions:
            console.print(f"[yellow]No versions found for '{name}'[/yellow]")
            return
        
        console.print(f"\n[cyan]Version History:[/cyan] {name}\n")
        
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Version", style="dim")
        table.add_column("Commit Message")
        table.add_column("Created", style="dim")
        
        for v in versions:
            version_id = v.get("version", "")[:12]  # Truncate long IDs
            message = v.get("commit_message", "-")
            created = v.get("created_at", "-")
            if created and created != "-":
                # Format date nicely if present
                created = created[:10] if len(created) > 10 else created
            table.add_row(version_id, message, created)
        
        console.print(table)
        console.print(f"\n[dim]Total: {len(versions)} version(s)[/dim]")
        
    except typer.Exit:
        raise
    except Exception as e:
        handle_error(e)


@app.command("render")
def render_prompt(
    name: str = typer.Argument(..., help="Prompt name (use quotes for spaces)"),
    var: Optional[List[str]] = typer.Option(None, "--var", "-V", help="Variable as key=value"),
    version: Optional[str] = typer.Option(None, "--version", "-v", help="Specific version"),
    output_json: bool = typer.Option(False, "--json", "-j", help="Output as JSON")
):
    """
    Render a prompt with variables (no LLM call).
    
    Useful for previewing what will be sent to the model.
    
    Examples:
        forgevault render "sql data generator" --var table=users
        forgevault render "my prompt" -V name=John --json
    """
    try:
        forge = get_client()
        
        # Parse variables
        variables = {}
        if var:
            for v in var:
                if "=" not in v:
                    console.print(f"[red]Invalid variable format:[/red] {v}")
                    raise typer.Exit(1)
                key, value = v.split("=", 1)
                variables[key.strip()] = value.strip()
        
        # Show what we're rendering
        if not output_json:
            console.print(f"[cyan]Prompt:[/cyan]    {name}")
            if version:
                console.print(f"[cyan]Version:[/cyan]   {version}")
            _print_variables(variables)
            console.print()
        
        result = forge.render_prompt(
            prompt_name=name,
            variables=variables,
            version=version
        )
        
        if output_json:
            _print_json(result)
            return
        
        messages = result.get("messages", [])
        
        console.print(f"\n[bold cyan]Rendered:[/bold cyan] {name} → {len(messages)} message(s)")
        
        for i, msg in enumerate(messages):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            role_color = "yellow" if role == "system" else "blue" if role == "user" else "magenta"
            role_title = f"[{role_color}]{role.upper()}[/{role_color}]"
            console.print(Panel(content, title=role_title, border_style=role_color))
        
    except Exception as e:
        handle_error(e)


# ==================== CACHE COMMANDS ====================

@cache_app.command("clear")
def cache_clear(
    prompt: Optional[str] = typer.Option(None, "--prompt", "-p", help="Clear specific prompt only")
):
    """
    Clear the local prompt cache.
    
    Examples:
        forgevault cache clear
        forgevault cache clear --prompt "my prompt"
    """
    try:
        forge = get_client()
        forge.invalidate_cache(prompt=prompt)
        
        if prompt:
            console.print(f"[green]✓ Cache cleared for:[/green] {prompt}")
        else:
            console.print("[green]✓ Cache cleared[/green]")
        
    except Exception as e:
        handle_error(e)


@cache_app.command("stats")
def cache_stats():
    """
    Show cache statistics.
    
    Examples:
        forgevault cache stats
    """
    try:
        forge = get_client()
        stats = forge.cache_stats()
        
        if not stats.get("enabled"):
            console.print("[yellow]Cache is disabled[/yellow]")
            return
        
        console.print("[cyan]Cache Statistics[/cyan]")
        for key, value in stats.items():
            console.print(f"  {key}: {value}")
        
    except Exception as e:
        handle_error(e)


# ==================== UTILITY COMMANDS ====================

@app.command("version")
def show_version():
    """Show ForgeVault CLI version."""
    console.print(f"ForgeVault CLI v{__version__}")


@app.callback()
def main():
    """
    ForgeVault CLI - Manage and run AI prompts from the command line.
    
    Get started:
        1. Login (one time): forgevault login
        2. List prompts:     forgevault list
        3. Run a prompt:     forgevault run "my prompt" --model gpt-4o
    
    For help on any command:
        forgevault <command> --help
    """
    pass


if __name__ == "__main__":
    app()

