import click
import psutil
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .app import PortPilotApp, get_listening_ports, kill_process

console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(version="0.1.0", prog_name="portpilot")
def cli(ctx):
    """🛫 PortPilot - Interactive Port Manager for Developers

    Run without arguments to open the interactive TUI.
    """
    if ctx.invoked_subcommand is None:
        # Launch TUI if no command specified
        app = PortPilotApp()
        app.run()


@cli.command()
@click.option("--port", "-p", type=int, help="Filter by specific port")
@click.option("--name", "-n", help="Filter by process name")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list(port, name, as_json):
    """List all listening ports."""
    connections = get_listening_ports()

    # Apply filters
    if port:
        connections = [c for c in connections if c["port"] == port]
    if name:
        connections = [c for c in connections if name.lower() in c["name"].lower()]

    if as_json:
        import json

        click.echo(json.dumps(connections, indent=2))
        return

    if not connections:
        console.print("[yellow]No listening ports found matching criteria[/yellow]")
        return

    table = Table(
        title="🔌 Listening Ports",
        box=box.ROUNDED,
        header_style="bold cyan",
        show_lines=False,
    )

    table.add_column("Port", style="green", justify="right")
    table.add_column("IP", style="dim")
    table.add_column("PID", style="yellow")
    table.add_column("Process", style="cyan")
    table.add_column("User", style="magenta")
    table.add_column("Memory", justify="right")

    for conn in connections:
        table.add_row(
            str(conn["port"]),
            conn["ip"],
            str(conn["pid"]),
            conn["name"],
            conn["user"],
            conn["memory"],
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(connections)} listening ports[/dim]")


@cli.command()
@click.argument("port", type=int)
@click.option("--force", "-f", is_flag=True, help="Force kill (SIGKILL)")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def kill(port, force, yes):
    """Kill process on a specific port."""
    connections = get_listening_ports()
    conn = next((c for c in connections if c["port"] == port), None)

    if not conn:
        console.print(f"[red]No process found listening on port {port}[/red]")
        return

    if conn["pid"] == "-":
        console.print(f"[red]Cannot determine PID for port {port}[/red]")
        return

    # Show what we're about to kill
    console.print(
        Panel(
            f"[bold]Port:[/bold] {conn['port']}\n"
            f"[bold]Process:[/bold] {conn['name']}\n"
            f"[bold]PID:[/bold] {conn['pid']}\n"
            f"[bold]Command:[/bold] {conn['cmdline'][:60]}",
            title="🎯 Target Process",
            border_style="yellow",
        )
    )

    if not yes:
        if not click.confirm("Kill this process?"):
            console.print("[dim]Cancelled[/dim]")
            return

    success, message = kill_process(int(conn["pid"]), force=force)

    if success:
        console.print(f"[green]✅ {message}[/green]")
    else:
        console.print(f"[red]❌ {message}[/red]")


@cli.command()
@click.argument("ports", type=int, nargs=-1, required=True)
@click.option("--force", "-f", is_flag=True, help="Force kill (SIGKILL)")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def killall(ports, force, yes):
    """Kill processes on multiple ports."""
    connections = get_listening_ports()

    targets = []
    for port in ports:
        conn = next((c for c in connections if c["port"] == port), None)
        if conn and conn["pid"] != "-":
            targets.append(conn)
        else:
            console.print(f"[yellow]⚠️  No killable process on port {port}[/yellow]")

    if not targets:
        console.print("[red]No valid targets found[/red]")
        return

    # Show targets
    table = Table(title="🎯 Targets", box=box.SIMPLE)
    table.add_column("Port")
    table.add_column("Process")
    table.add_column("PID")

    for t in targets:
        table.add_row(str(t["port"]), t["name"], str(t["pid"]))

    console.print(table)

    if not yes:
        if not click.confirm(f"Kill {len(targets)} processes?"):
            console.print("[dim]Cancelled[/dim]")
            return

    for t in targets:
        success, message = kill_process(int(t["pid"]), force=force)
        if success:
            console.print(f"[green]✅ Port {t['port']}: {message}[/green]")
        else:
            console.print(f"[red]❌ Port {t['port']}: {message}[/red]")


@cli.command()
@click.argument("port", type=int)
def info(port):
    """Show detailed info about a port."""
    connections = get_listening_ports()
    conn = next((c for c in connections if c["port"] == port), None)

    if not conn:
        console.print(f"[red]No process found listening on port {port}[/red]")
        return

    console.print(
        Panel(
            f"[bold cyan]Port:[/bold cyan] {conn['port']}\n"
            f"[bold cyan]IP:[/bold cyan] {conn['ip']}\n"
            f"[bold cyan]PID:[/bold cyan] {conn['pid']}\n"
            f"[bold cyan]Process:[/bold cyan] {conn['name']}\n"
            f"[bold cyan]Command:[/bold cyan] {conn['cmdline']}\n"
            f"[bold cyan]User:[/bold cyan] {conn['user']}\n"
            f"[bold cyan]Started:[/bold cyan] {conn['created']}\n"
            f"[bold cyan]Memory:[/bold cyan] {conn['memory']}",
            title=f"🔍 Port {port} Details",
            border_style="cyan",
        )
    )

    # Try to get more process info
    if conn["pid"] != "-":
        try:
            proc = psutil.Process(int(conn["pid"]))

            # Get open files
            try:
                files = proc.open_files()[:5]
                if files:
                    console.print("\n[bold]Open Files (first 5):[/bold]")
                    for f in files:
                        console.print(f"  [dim]{f.path}[/dim]")
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass

            # Get connections
            try:
                conns = proc.connections()
                if conns:
                    console.print(f"\n[bold]Total Connections:[/bold] {len(conns)}")
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass


@cli.command()
@click.argument("ports", type=int, nargs=-1)
def watch(ports):
    """Watch specific ports (or all if none specified)."""
    from time import sleep

    console.print("[bold]Watching ports... Press Ctrl+C to stop[/bold]\n")

    try:
        while True:
            connections = get_listening_ports()

            if ports:
                connections = [c for c in connections if c["port"] in ports]

            console.clear()
            console.print(f"[bold cyan]🔌 Port Watch[/bold cyan] [dim](updated)[/dim]\n")

            if not connections:
                console.print("[yellow]No matching ports currently listening[/yellow]")
            else:
                table = Table(box=box.SIMPLE)
                table.add_column("Port", style="green")
                table.add_column("Process", style="cyan")
                table.add_column("PID", style="yellow")
                table.add_column("Memory")

                for conn in connections:
                    table.add_row(str(conn["port"]), conn["name"], str(conn["pid"]), conn["memory"])

                console.print(table)

            console.print("\n[dim]Press Ctrl+C to stop[/dim]")
            sleep(2)

    except KeyboardInterrupt:
        console.print("\n[dim]Stopped watching[/dim]")


def main():
    """Entry point."""
    cli()


if __name__ == "__main__":
    main()
