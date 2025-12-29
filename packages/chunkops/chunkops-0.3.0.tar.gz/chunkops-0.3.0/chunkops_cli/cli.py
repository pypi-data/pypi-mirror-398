"""ChunkOps CLI - Production-Grade B2B DevTools CLI"""

import json
import os
import sys
import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.columns import Columns
from rich.text import Text
from rich import box
from rich.prompt import Prompt
from rich.live import Live
from rich.layout import Layout

from chunkops_cli.extractor import PDFExtractor, Chunk
from chunkops_cli.deduper import Deduplicator, DuplicateMatch
from chunkops_cli.config import (
    ChunkOpsConfig, load_config, save_config, get_config_path
)
from chunkops_cli.auth import login, check_auth, get_api_key
from chunkops_cli.cloud import check_semantic_conflicts, get_conflict_summary

app = typer.Typer(
    name="chunkops",
    help="ChunkOps - The CI/CD Pipeline for RAG. Detect conflicts before they become hallucinations.",
    add_completion=False,
)
console = Console()

# ============================================================================
# CONSTANTS
# ============================================================================

VERSION = "0.3.0"

# Conflict action mappings
CONFLICT_ACTIONS = {
    "m": "merge",
    "M": "merge",
    "o": "overwrite", 
    "O": "overwrite",
    "i": "ignore",
    "I": "ignore",
    "s": "skip",
    "S": "skip",
}


# ============================================================================
# UTILITIES
# ============================================================================

def find_documents(directory: str, silent: bool = False, allow_missing: bool = False) -> List[str]:
    """Find all supported document files in a directory"""
    files = []
    path = Path(directory)
    
    if not path.exists():
        if allow_missing:
            return []
        if silent:
            print(f"Error: Directory '{directory}' does not exist", file=sys.stderr)
        else:
            console.print(f"[red]❌[/red] Directory '{directory}' does not exist")
            console.print(f"[dim]Tip: Run 'chunkops init' to set up your project, or specify a path: 'chunkops scan ./your-path'[/dim]")
        sys.exit(1)
    
    if not path.is_dir():
        if allow_missing:
            return []
        if silent:
            print(f"Error: '{directory}' is not a directory", file=sys.stderr)
        else:
            console.print(f"[red]❌[/red] '{directory}' is not a directory")
        sys.exit(1)
    
    # Supported file types
    for ext in ["*.pdf", "*.md", "*.txt", "*.docx"]:
        for file_path in path.rglob(ext):
            files.append(str(file_path))
    
    return sorted(files)


def compute_file_hash(file_path: str) -> str:
    """Compute SHA-256 hash of file"""
    hash_sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_sha.update(chunk)
    return hash_sha.hexdigest()[:16]  # Short hash for display


def extract_subject(text_a: str, text_b: str) -> str:
    """Extract the subject/topic from conflicting texts"""
    # Look for common patterns like "Policy:", headers, or quoted text
    patterns = [
        r'"([^"]+)"',  # Quoted text
        r'(?:Policy|Section|Rule|Clause):\s*([^\n]+)',  # Policy headers
        r'^#+ (.+)$',  # Markdown headers
        r'^([A-Z][^.!?]+(?:Allowance|Policy|Rate|Limit|Rule))',  # Capitalized terms
    ]
    
    for pattern in patterns:
        for text in [text_a, text_b]:
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if match:
                subject = match.group(1).strip()
                if len(subject) > 50:
                    subject = subject[:47] + "..."
                return subject
    
    # Fallback: extract first meaningful phrase
    words = text_a.split()[:5]
    return " ".join(words) if words else "Unknown"


def extract_value(text: str) -> str:
    """Extract the key value/claim from text"""
    # Look for monetary values, numbers, dates
    patterns = [
        r'\$[\d,]+(?:\.\d{2})?(?:/\w+)?',  # Money: $75/day
        r'\d+%',  # Percentages
        r'\d+\s*(?:days?|hours?|weeks?|months?|years?)',  # Durations
        r'\d{1,2}/\d{1,2}/\d{2,4}',  # Dates
        r'(?:true|false|yes|no|enabled|disabled)',  # Booleans
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    
    # Return first line or truncated text
    first_line = text.split('\n')[0].strip()
    if len(first_line) > 60:
        first_line = first_line[:57] + "..."
    return first_line or text[:60]


def get_filename(path: str) -> str:
    """Get clean filename from path"""
    return Path(path).name


# ============================================================================
# CONFLICT DISPLAY
# ============================================================================

def display_conflict_panel(
    conflict: Dict[str, Any],
    index: int,
    total: int
) -> Panel:
    """Create a beautiful conflict panel"""
    file_a = get_filename(conflict.get("file_a", "unknown"))
    file_b = get_filename(conflict.get("file_b", "unknown"))
    text_a = conflict.get("chunk_a_preview", "")
    text_b = conflict.get("chunk_b_preview", "")
    
    subject = extract_subject(text_a, text_b)
    value_a = extract_value(text_a)
    value_b = extract_value(text_b)
    
    # Build the conflict content
    content = Text()
    content.append("Subject: ", style="bold white")
    content.append(f'"{subject}"\n\n', style="white")
    
    # Old value (red, with minus)
    content.append("- ", style="red")
    content.append(f"{file_a}: ", style="red")
    content.append(f"{value_a}\n", style="dim red")
    
    # New value (green, with plus)
    content.append("+ ", style="green")
    content.append(f"{file_b}: ", style="green")
    content.append(f"{value_b}", style="dim green")
    
    severity = conflict.get("severity", "warning")
    border_style = "red" if severity == "critical" else "yellow"
    icon = "⚠" if severity == "critical" else "⚡"
    
    return Panel(
        content,
        title=f"[bold {border_style}]{icon} Conflict Detected[/bold {border_style}]",
        subtitle=f"[dim]{index}/{total}[/dim]",
        border_style=border_style,
        padding=(1, 2),
    )


def prompt_conflict_action() -> str:
    """Prompt user for conflict resolution action"""
    console.print()
    console.print(
        "[bold yellow]?[/bold yellow] Action required: "
        "[[bold]M[/bold]]erge, [[bold]O[/bold]]verwrite, [[bold]I[/bold]]gnore ",
        end=""
    )
    
    # Get single character input
    action = Prompt.ask("", default="i", show_default=False)
    return CONFLICT_ACTIONS.get(action, "ignore")


# ============================================================================
# MAIN SCAN COMMAND
# ============================================================================

@app.command()
def scan(
    path: Optional[str] = typer.Argument(None, help="Path to documents (overrides config)"),
    output: Optional[str] = typer.Option(None, "-o", "--output", help="Output JSON file path"),
    strict: bool = typer.Option(False, "--strict", help="Strict mode: lower thresholds, detect more conflicts"),
    interactive: bool = typer.Option(True, "--interactive/--no-interactive", "-i", help="Interactive conflict resolution"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Verbose output"),
    ci_mode: bool = typer.Option(False, "--ci", help="CI mode (JSON only, no colors)"),
):
    """
    Scan documents for duplicates and semantic conflicts.
    
    Examples:
        chunkops scan ./docs
        chunkops scan ./docs --strict
        chunkops scan ./policies --no-interactive
    """
    # Load config
    config = load_config() or ChunkOpsConfig()
    
    # Override with CLI args
    scan_path = path or config.docs_path
    output_file = output or os.path.join(config.output_path, "scan-report.json")
    
    # Adjust thresholds for strict mode
    if strict:
        config.near_threshold = 0.85  # More sensitive
        config.exact_threshold = 0.98
    
    # CI mode: disable colors and interactivity
    if ci_mode:
        interactive = False
        output_console = Console(force_terminal=False, no_color=True)
    else:
        output_console = console
    
    # =========================================================================
    # PHASE 1: Document Discovery
    # =========================================================================
    
    if not ci_mode:
        console.print()
    
    files = find_documents(scan_path, silent=ci_mode)
    
    if not files:
        if not ci_mode:
            console.print("[red]❌[/red] No documents found. Exiting.")
        sys.exit(1)
    
    # =========================================================================
    # PHASE 2: Analysis
    # =========================================================================
    
    if not ci_mode:
        console.print(f"[bold yellow]⚡[/bold yellow] Analyzing [bold]{len(files)}[/bold] documents ...")
    
    # Exact duplicates (file hash)
    file_hashes: Dict[str, str] = {}
    exact_duplicates = []
    empty_files = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=30),
        TaskProgressColumn(),
        console=output_console,
        disable=ci_mode,
        transient=True
    ) as progress:
        task = progress.add_task("[dim]Hashing files...[/dim]", total=len(files))
        
        for file_path in files:
            try:
                file_size = os.path.getsize(file_path)
                
                if file_size == 0:
                    empty_files.append(file_path)
                    progress.advance(task)
                    continue
                
                file_hash = compute_file_hash(file_path)
                
                if file_hash in file_hashes:
                    exact_duplicates.append({
                        "file_a": file_hashes[file_hash],
                        "file_b": file_path,
                        "hash": file_hash
                    })
                else:
                    file_hashes[file_hash] = file_path
                
                progress.advance(task)
            except Exception as e:
                if verbose:
                    console.print(f"[red]✗[/red] Error: {file_path}: {e}")
                progress.advance(task)
    
    # =========================================================================
    # PHASE 3: Semantic Extraction
    # =========================================================================
    
    if not ci_mode:
        console.print(f"[bold yellow]🔍[/bold yellow] Extracting semantic claims ...")
    
    extractor = PDFExtractor()
    all_chunks: List[Chunk] = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=30),
        TaskProgressColumn(),
        console=output_console,
        disable=ci_mode,
        transient=True
    ) as progress:
        task = progress.add_task("[dim]Processing documents...[/dim]", total=len(files))
        
        for file_path in files:
            try:
                if file_path in empty_files:
                    progress.advance(task)
                    continue
                
                chunks = extractor.process_file(file_path)
                all_chunks.extend(chunks)
                progress.advance(task)
            except Exception as e:
                if verbose and not ci_mode:
                    console.print(f"[red]✗[/red] Error: {file_path}: {e}")
                progress.advance(task)
    
    # =========================================================================
    # PHASE 4: Duplicate Detection
    # =========================================================================
    
    semantic_duplicates: List[DuplicateMatch] = []
    
    if all_chunks:
        deduper = Deduplicator(
            exact_threshold=config.exact_threshold,
            near_threshold=config.near_threshold
        )
        
        if not ci_mode:
            console.print(f"[bold yellow]🧠[/bold yellow] Detecting semantic duplicates ...")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=output_console,
            disable=ci_mode,
            transient=True
        ) as progress:
            task = progress.add_task("[dim]Comparing embeddings...[/dim]", total=None)
            semantic_duplicates = deduper.find_duplicates(all_chunks)
    
    # =========================================================================
    # PHASE 5: Cloud Conflict Detection
    # =========================================================================
    
    conflicts: List[Dict[str, Any]] = []
    
    # Check for conflicts via cloud if authenticated
    if semantic_duplicates and check_auth():
        if not ci_mode:
            console.print(f"[bold yellow]☁️[/bold yellow] Checking for semantic conflicts ...")
        
        conflicts = check_semantic_conflicts(semantic_duplicates, config.api_url)
    
    # If no cloud, generate local conflict analysis
    if not conflicts and semantic_duplicates:
        # Generate pseudo-conflicts from near duplicates for demo
        for dup in semantic_duplicates[:10]:  # Limit to first 10
            if dup.type == "NEAR_DUPLICATE" and dup.similarity >= 0.88:
                conflicts.append({
                    "file_a": dup.file_a,
                    "file_b": dup.file_b,
                    "chunk_a_preview": dup.chunk_a_preview,
                    "chunk_b_preview": dup.chunk_b_preview,
                    "similarity": dup.similarity,
                    "severity": "critical" if dup.similarity >= 0.95 else "warning",
                    "type": "semantic_conflict"
                })
    
    # =========================================================================
    # PHASE 6: Interactive Conflict Resolution
    # =========================================================================
    
    resolutions: List[Dict[str, Any]] = []
    
    if conflicts and interactive and not ci_mode:
        console.print()
        
        for i, conflict in enumerate(conflicts, 1):
            # Display conflict panel
            panel = display_conflict_panel(conflict, i, len(conflicts))
            console.print(panel)
            
            # Prompt for action
            action = prompt_conflict_action()
            
            resolutions.append({
                "conflict_index": i,
                "action": action,
                "file_a": conflict.get("file_a"),
                "file_b": conflict.get("file_b"),
            })
            
            # Show feedback
            action_display = {
                "merge": "[cyan]→ Marked for merge[/cyan]",
                "overwrite": "[green]→ Will keep newer version[/green]",
                "ignore": "[dim]→ Ignored[/dim]",
                "skip": "[dim]→ Skipped[/dim]",
            }
            console.print(action_display.get(action, "[dim]→ Skipped[/dim]"))
            console.print()
    
    # =========================================================================
    # PHASE 7: Generate Report
    # =========================================================================
    
    exact_count = len(exact_duplicates)
    near_count = len([d for d in semantic_duplicates if d.type == "NEAR_DUPLICATE"])
    conflict_summary = get_conflict_summary(conflicts)
    
    report = {
        "version": VERSION,
        "scan_date": datetime.utcnow().isoformat() + "Z",
        "scan_path": scan_path,
        "strict_mode": strict,
        "total_files": len(files),
        "total_chunks": len(all_chunks),
        "empty_files": len(empty_files),
        "exact_duplicates": exact_count,
        "near_duplicates": near_count,
        "semantic_conflicts": conflict_summary["total"],
        "critical_conflicts": conflict_summary["critical"],
        "resolutions": resolutions,
        "summary": {
            "status": "fail" if conflict_summary["critical"] > 0 else "pass",
            "valid_chunks": len(all_chunks) - exact_count,
            "issues_found": exact_count + near_count + conflict_summary["total"],
        }
    }
    
    # =========================================================================
    # PHASE 8: Output Results
    # =========================================================================
    
    if ci_mode:
        # CI: JSON output only
        print(json.dumps(report, indent=2))
        sys.exit(1 if conflict_summary["critical"] > 0 else 0)
    else:
        # Interactive: Beautiful summary
        display_summary(report, conflicts, semantic_duplicates)
    
    # Save report
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    if not ci_mode:
        console.print(f"\n[dim]Report saved to: {output_file}[/dim]")


def display_summary(report: dict, conflicts: List, duplicates: List):
    """Display beautiful summary"""
    console.print()
    
    # Summary table
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="bold")
    table.add_column()
    
    table.add_row("📄 Files scanned:", str(report["total_files"]))
    table.add_row("📝 Total chunks:", str(report["total_chunks"]))
    
    if report["empty_files"] > 0:
        table.add_row("⚠️  Empty files:", f"[yellow]{report['empty_files']}[/yellow]")
    
    if report["exact_duplicates"] > 0:
        table.add_row("🔴 Exact duplicates:", f"[red]{report['exact_duplicates']}[/red]")
    
    if report["near_duplicates"] > 0:
        table.add_row("🟡 Near duplicates:", f"[yellow]{report['near_duplicates']}[/yellow]")
    
    if report["semantic_conflicts"] > 0:
        table.add_row(
            "🚨 Conflicts:", 
            f"[red]{report['semantic_conflicts']}[/red] "
            f"([bold red]{report['critical_conflicts']} critical[/bold red])"
        )
    
    console.print("[bold]Summary:[/bold]")
    console.print(table)
    
    # Status badge
    if report["summary"]["status"] == "pass":
        console.print(f"\n[green]✅[/green] [bold green]{report['summary']['valid_chunks']} Chunks Validated[/bold green]")
    else:
        console.print(f"\n[red]❌[/red] [bold red]Validation Failed[/bold red] - {report['critical_conflicts']} critical conflict(s)")
        console.print("[dim]Run 'chunkops login' to resolve conflicts in the dashboard[/dim]")
    
    # Cloud upsell if not authenticated
    if not check_auth() and report["near_duplicates"] > 0:
        console.print()
        console.print(Panel(
            "[bold]💡 Tip:[/bold] Run [cyan]chunkops login[/cyan] to enable:\n"
            "  • AI-powered semantic conflict detection\n"
            "  • Cloud dashboard for conflict resolution\n"
            "  • Team collaboration features",
            border_style="blue",
            padding=(0, 2)
        ))


# ============================================================================
# OTHER COMMANDS
# ============================================================================

@app.command()
def init(
    docs_path: Optional[str] = typer.Option(None, "--docs-path", "-d", help="Path to documents"),
    output_path: str = typer.Option("./chunkops-reports", "--output-path", "-o", help="Reports path"),
):
    """Initialize ChunkOps in your project. Creates chunkops.yaml config file."""
    console.print("\n[bold cyan]🚀 ChunkOps Setup[/bold cyan]\n")
    
    config_path = get_config_path()
    if config_path.exists():
        console.print(f"[yellow]⚠️[/yellow] Config already exists: {config_path}")
        if not typer.confirm("Overwrite?", default=False):
            return
    
    # Auto-detect documents
    if not docs_path:
        for path in ["./docs", "./data", "./documents", "."]:
            p = Path(path)
            if p.exists() and p.is_dir():
                count = sum(len(list(p.rglob(f"*.{ext}"))) for ext in ["pdf", "md", "txt"])
                if count > 0:
                    console.print(f"[dim]Found {count} documents in: {path}[/dim]")
                    if typer.confirm(f"Use '{path}'?", default=True):
                        docs_path = path
                        break
        
        if not docs_path:
            docs_path = typer.prompt("Documents path", default="./docs")
    
    config = ChunkOpsConfig(docs_path=docs_path, output_path=output_path)
    save_config(config)
    
    console.print(f"\n[green]✅[/green] Config created: [cyan]{config_path}[/cyan]\n")
    console.print(Panel(
        "[bold]Next steps:[/bold]\n\n"
        "1. [cyan]chunkops scan[/cyan] - Analyze documents\n"
        "2. [cyan]chunkops login[/cyan] - Enable cloud features\n"
        "3. [cyan]chunkops ci[/cyan] - Add to CI/CD pipeline",
        title="🎯 Ready",
        border_style="green"
    ))


@app.command()
def auth(api_key: Optional[str] = typer.Option(None, "--api-key", help="API key")):
    """Authenticate with ChunkOps Cloud."""
    if api_key:
        from chunkops_cli.auth import save_api_key
        save_api_key(api_key)
        console.print("[green]✅[/green] API key saved!")
        return
    login()


@app.command()
def login(api_key: Optional[str] = typer.Option(None, "--api-key", help="API key")):
    """Alias for 'auth'. Authenticate with ChunkOps Cloud."""
    auth(api_key=api_key)


@app.command()
def ci(
    path: Optional[str] = typer.Argument(None, help="Documents path"),
    output: Optional[str] = typer.Option(None, "-o", "--output", help="Output file"),
    fail_on_critical: bool = typer.Option(True, "--fail-on-critical/--no-fail", help="Exit 1 on critical"),
):
    """
    CI/CD mode: Silent JSON output with exit codes.
    
    Example GitHub Actions:
        - run: chunkops ci ./docs
    """
    scan(path=path, output=output, ci_mode=True, interactive=False, verbose=False, strict=False)


@app.command()
def version():
    """Show version information."""
    console.print(f"chunkops [bold cyan]{VERSION}[/bold cyan]")
    console.print("[dim]https://chunkops.ai[/dim]")


@app.command()
def status():
    """Show current configuration and authentication status."""
    config = load_config()
    authenticated = check_auth()
    
    console.print("\n[bold]ChunkOps Status[/bold]\n")
    
    table = Table(show_header=False, box=box.SIMPLE)
    table.add_column(style="bold")
    table.add_column()
    
    if config:
        table.add_row("Config:", "[green]Found[/green]")
        table.add_row("  Documents:", config.docs_path)
        table.add_row("  Output:", config.output_path)
    else:
        table.add_row("Config:", "[yellow]Not found[/yellow] (run 'chunkops init')")
    
    if authenticated:
        table.add_row("Cloud:", "[green]Authenticated[/green]")
    else:
        table.add_row("Cloud:", "[dim]Not connected[/dim] (run 'chunkops login')")
    
    console.print(table)
    console.print()


def main():
    """Main entry point"""
    app()


if __name__ == "__main__":
    main()
