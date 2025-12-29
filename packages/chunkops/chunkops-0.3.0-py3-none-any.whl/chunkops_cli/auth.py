"""Authentication for ChunkOps CLI"""

import webbrowser
import time
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .config import save_api_key, load_api_key

console = Console()


def login(api_url: str = "https://console.chunkops.ai") -> Optional[str]:
    """
    Authenticate user by opening browser and getting API key
    
    Returns:
        API key if successful, None otherwise
    """
    console.print("\n[bold cyan]ChunkOps Authentication[/bold cyan]\n")
    
    # Generate auth URL (in production, this would be a real OAuth flow)
    auth_url = f"{api_url}/cli-auth"
    
    console.print(Panel(
        "[bold]Opening browser for authentication...[/bold]\n\n"
        "If the browser doesn't open, visit:\n"
        f"[link={auth_url}]{auth_url}[/link]\n\n"
        "After authenticating, you'll receive an API key.\n"
        "Paste it below when prompted.",
        title="🔐 Login",
        border_style="cyan"
    ))
    
    # Open browser
    try:
        webbrowser.open(auth_url)
    except Exception:
        console.print(f"[yellow]⚠️[/yellow] Could not open browser. Please visit: {auth_url}")
    
    # Prompt for API key
    console.print("\n[bold]Enter your API key:[/bold]")
    api_key = input().strip()
    
    if not api_key:
        console.print("[red]❌[/red] No API key provided. Authentication cancelled.")
        return None
    
    # Validate API key format (basic check)
    if not api_key.startswith("chk_"):
        console.print("[yellow]⚠️[/yellow] API key format looks incorrect. Expected format: chk_...")
        response = input("Continue anyway? (y/N): ").strip().lower()
        if response != 'y':
            return None
    
    # Save API key
    save_api_key(api_key)
    
    console.print("\n[green]✅[/green] [bold]Authentication successful![/bold]")
    console.print("API key saved to ~/.chunkops/credentials\n")
    
    return api_key


def get_api_key() -> Optional[str]:
    """Get API key from credentials or config"""
    # Try credentials file first
    api_key = load_api_key()
    if api_key:
        return api_key
    
    # Try config file
    from .config import load_config
    config = load_config()
    if config and config.api_key:
        return config.api_key
    
    return None


def check_auth() -> bool:
    """Check if user is authenticated"""
    api_key = get_api_key()
    return api_key is not None

