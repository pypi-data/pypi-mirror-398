"""CLI interface for porthog."""

from datetime import datetime
from typing import Annotated, Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from porthog import __version__
from porthog.ports import (
    ProcessType,
    get_listening_ports,
    get_port_info,
    kill_port,
    kill_ports,
)

app = typer.Typer(
    name="porthog",
    help="Find and kill dev servers hogging your ports.",
    no_args_is_help=False,
    add_completion=False,
)

console = Console()
err_console = Console(stderr=True)

# Colors for different process types
PROCESS_COLORS: dict[ProcessType, str] = {
    ProcessType.NODE: "green",
    ProcessType.PYTHON: "yellow",
    ProcessType.JAVA: "red",
    ProcessType.RUBY: "magenta",
    ProcessType.GO: "cyan",
    ProcessType.RUST: "orange1",
    ProcessType.PHP: "blue",
    ProcessType.DOTNET: "purple",
    ProcessType.OTHER: "white",
}


def format_memory(mb: float) -> str:
    """Format memory in human-readable format."""
    if mb >= 1024:
        return f"{mb / 1024:.1f}GB"
    return f"{mb:.0f}MB"


def format_uptime(create_time: float) -> str:
    """Format process uptime."""
    delta = datetime.now() - datetime.fromtimestamp(create_time)
    hours, remainder = divmod(int(delta.total_seconds()), 3600)
    minutes, _ = divmod(remainder, 60)

    if hours > 24:
        days = hours // 24
        return f"{days}d"
    if hours > 0:
        return f"{hours}h{minutes}m"
    return f"{minutes}m"


def create_ports_table(dev_only: bool = True) -> Table | None:
    """Create a rich table with port information."""
    ports = get_listening_ports(dev_only=dev_only)

    if not ports:
        return None

    table = Table(
        box=box.ROUNDED,
        header_style="bold cyan",
        border_style="dim",
        show_edge=True,
    )

    table.add_column("Port", justify="right", style="bold", width=6)
    table.add_column("PID", justify="right", width=7)
    table.add_column("Type", width=10)
    table.add_column("Process", width=20)
    table.add_column("Command", overflow="ellipsis", max_width=40)
    table.add_column("Mem", justify="right", width=7)
    table.add_column("Up", justify="right", width=6)

    for port_info in ports:
        color = PROCESS_COLORS.get(port_info.process_type, "white")

        type_text = Text(port_info.process_type.value, style=color)
        process_text = Text(port_info.display_name, style=f"bold {color}")

        table.add_row(
            str(port_info.port),
            str(port_info.pid),
            type_text,
            process_text,
            port_info.short_cmd,
            format_memory(port_info.memory_mb),
            format_uptime(port_info.create_time),
        )

    return table


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"porthog [bold cyan]v{__version__}[/]")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Annotated[
        Optional[bool],
        typer.Option("--version", "-v", callback=version_callback, is_eager=True),
    ] = None,
) -> None:
    """Find and kill dev servers hogging your ports.

    Run without arguments to launch the interactive TUI.
    """
    if ctx.invoked_subcommand is None:
        # No subcommand - launch TUI
        from porthog.tui import run_tui

        run_tui()


@app.command("ls")
def list_ports(
    all_ports: Annotated[
        bool,
        typer.Option("--all", "-a", help="Show all listening ports, not just dev ports"),
    ] = False,
) -> None:
    """List all dev server ports."""
    table = create_ports_table(dev_only=not all_ports)

    if table is None:
        console.print("[dim]No dev servers found listening on ports.[/]")
        raise typer.Exit(0)

    title = "All Listening Ports" if all_ports else "Dev Server Ports"
    console.print(Panel(table, title=title, border_style="cyan"))

    # Show hint
    console.print("\n[dim]Tip: Use [bold]porthog kill <port>[/] to kill a process[/]")


@app.command("info")
def info(
    port: Annotated[int, typer.Argument(help="Port number to inspect")],
) -> None:
    """Get detailed info about a specific port."""
    port_info = get_port_info(port)

    if port_info is None:
        err_console.print(f"[red]No process found listening on port {port}[/]")
        raise typer.Exit(1)

    color = PROCESS_COLORS.get(port_info.process_type, "white")

    # Create detailed info panel
    info_text = Text()
    info_text.append("Port:      ", style="dim")
    info_text.append(f"{port_info.port}\n", style="bold")
    info_text.append("PID:       ", style="dim")
    info_text.append(f"{port_info.pid}\n")
    info_text.append("Process:   ", style="dim")
    info_text.append(f"{port_info.name}\n", style=color)
    info_text.append("Type:      ", style="dim")
    info_text.append(f"{port_info.process_type.value}\n", style=color)
    if port_info.framework:
        info_text.append("Framework: ", style="dim")
        info_text.append(f"{port_info.framework}\n", style=f"bold {color}")
    info_text.append("User:      ", style="dim")
    info_text.append(f"{port_info.user}\n")
    info_text.append("Memory:    ", style="dim")
    info_text.append(f"{format_memory(port_info.memory_mb)}\n")
    info_text.append("Uptime:    ", style="dim")
    info_text.append(f"{format_uptime(port_info.create_time)}\n")
    info_text.append("\nCommand:\n", style="dim")
    info_text.append(port_info.cmdline, style="italic")

    console.print(Panel(info_text, title=f"Port {port}", border_style=color))


@app.command("kill")
def kill(
    ports: Annotated[
        list[int],
        typer.Argument(help="Port number(s) to kill"),
    ],
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Force kill (SIGKILL instead of SIGTERM)"),
    ] = False,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompt"),
    ] = False,
) -> None:
    """Kill process(es) listening on specified port(s)."""
    if not ports:
        err_console.print("[red]No ports specified[/]")
        raise typer.Exit(1)

    # Show what we're about to kill
    port_infos = []
    for port in ports:
        info = get_port_info(port)
        if info:
            port_infos.append(info)
        else:
            console.print(f"[yellow]No process found on port {port}[/]")

    if not port_infos:
        raise typer.Exit(1)

    # Confirm
    if not yes:
        console.print("\n[bold]About to kill:[/]\n")
        for info in port_infos:
            color = PROCESS_COLORS.get(info.process_type, "white")
            console.print(
                f"  Port [bold]{info.port}[/] - [{color}]{info.display_name}[/] (PID {info.pid})"
            )

        console.print()
        if not typer.confirm("Proceed?"):
            raise typer.Abort()

    # Kill the processes
    results = kill_ports([p.port for p in port_infos], force=force)

    for port, success, message in results:
        if success:
            console.print(f"[green]{message}[/]")
        else:
            err_console.print(f"[red]{message}[/]")


@app.command("kill-all")
def kill_all(
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Force kill (SIGKILL instead of SIGTERM)"),
    ] = False,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompt"),
    ] = False,
) -> None:
    """Kill ALL dev server processes (use with caution!)."""
    ports = get_listening_ports(dev_only=True)

    if not ports:
        console.print("[dim]No dev servers found.[/]")
        raise typer.Exit(0)

    console.print(f"\n[bold red]About to kill {len(ports)} dev server(s):[/]\n")

    for info in ports:
        color = PROCESS_COLORS.get(info.process_type, "white")
        console.print(
            f"  Port [bold]{info.port}[/] - [{color}]{info.display_name}[/] (PID {info.pid})"
        )

    console.print()

    if not yes:
        if not typer.confirm("[bold red]This will kill ALL dev servers. Proceed?[/]"):
            raise typer.Abort()

    results = kill_ports([p.port for p in ports], force=force)

    success_count = sum(1 for _, success, _ in results if success)
    console.print(f"\n[green]Killed {success_count}/{len(ports)} processes[/]")


if __name__ == "__main__":
    app()
