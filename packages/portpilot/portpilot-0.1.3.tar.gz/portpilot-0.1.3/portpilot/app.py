"""PortPilot - Interactive Terminal UI for Port Management"""

import os
import signal
from datetime import datetime

import psutil
from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Footer, Header, Input, Label, Static


def get_listening_ports():
    """Get all listening ports with process information."""
    connections = []

    for conn in psutil.net_connections(kind="inet"):
        if conn.status == "LISTEN":
            try:
                proc = psutil.Process(conn.pid) if conn.pid else None
                connections.append(
                    {
                        "port": conn.laddr.port,
                        "ip": conn.laddr.ip,
                        "pid": conn.pid or "-",
                        "name": proc.name() if proc else "-",
                        "cmdline": " ".join(proc.cmdline()[:3]) if proc else "-",
                        "user": proc.username() if proc else "-",
                        "created": datetime.fromtimestamp(proc.create_time()).strftime("%H:%M:%S")
                        if proc
                        else "-",
                        "memory": f"{proc.memory_info().rss / 1024 / 1024:.1f}MB" if proc else "-",
                    }
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                connections.append(
                    {
                        "port": conn.laddr.port,
                        "ip": conn.laddr.ip,
                        "pid": conn.pid or "-",
                        "name": "-",
                        "cmdline": "-",
                        "user": "-",
                        "created": "-",
                        "memory": "-",
                    }
                )

    return sorted(connections, key=lambda x: x["port"])


def kill_process(pid: int, force: bool = False) -> tuple[bool, str]:
    """Kill a process by PID."""
    try:
        proc = psutil.Process(pid)
        proc_name = proc.name()

        if force:
            proc.kill()  # SIGKILL
        else:
            proc.terminate()  # SIGTERM

        proc.wait(timeout=3)
        return True, f"Process {proc_name} (PID: {pid}) terminated"
    except psutil.NoSuchProcess:
        return False, f"Process {pid} not found"
    except psutil.AccessDenied:
        return False, f"Access denied for PID {pid}. Try running with sudo."
    except psutil.TimeoutExpired:
        return False, f"Process {pid} didn't terminate in time. Try force kill."
    except Exception as e:
        return False, f"Error: {str(e)}"


class ConfirmKillScreen(ModalScreen):
    """Modal screen for kill confirmation."""

    BINDINGS = [
        Binding("y", "confirm", "Yes"),
        Binding("n", "cancel", "No"),
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, port: int, pid: int, name: str):
        super().__init__()
        self.port = port
        self.pid = pid
        self.name = name

    def compose(self) -> ComposeResult:
        with Container(id="confirm-dialog"):
            yield Static(f"⚠️  Kill process on port {self.port}?", id="confirm-title")
            yield Static(f"Process: {self.name}", classes="confirm-detail")
            yield Static(f"PID: {self.pid}", classes="confirm-detail")
            with Horizontal(id="confirm-buttons"):
                yield Button("Yes [y]", variant="error", id="yes-btn")
                yield Button("No [n]", variant="primary", id="no-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes-btn":
            self.action_confirm()
        else:
            self.action_cancel()

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)


class PortPilotApp(App):
    """Main PortPilot Application."""

    CSS = """
    Screen {
        background: $surface;
    }

    #main-container {
        height: 100%;
    }

    #port-table {
        height: 1fr;
        margin: 1;
        border: solid $primary;
    }

    #status-bar {
        height: 3;
        padding: 1;
        background: $surface-darken-1;
    }

    #filter-container {
        height: 3;
        padding: 0 1;
    }

    #filter-input {
        width: 30;
    }

    #filter-label {
        padding: 1;
        width: auto;
    }

    #stats {
        dock: right;
        padding: 1;
        width: auto;
    }

    #confirm-dialog {
        width: 50;
        height: 12;
        padding: 1 2;
        background: $surface;
        border: thick $error;
    }

    #confirm-title {
        text-align: center;
        text-style: bold;
        padding: 1;
    }

    .confirm-detail {
        text-align: center;
        padding: 0 1;
    }

    #confirm-buttons {
        align: center middle;
        padding-top: 1;
        height: 3;
    }

    #confirm-buttons Button {
        margin: 0 1;
    }

    .status-success {
        color: $success;
    }

    .status-error {
        color: $error;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("k", "kill_selected", "Kill"),
        Binding("K", "force_kill", "Force Kill"),
        Binding("f", "focus_filter", "Filter"),
        Binding("/", "focus_filter", "Filter"),
        Binding("escape", "clear_filter", "Clear Filter"),
    ]

    def __init__(self):
        super().__init__()
        self.connections = []
        self.filter_text = ""
        self.status_message = ""
        self.status_class = ""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="main-container"):
            with Horizontal(id="filter-container"):
                yield Label("🔍 Filter:", id="filter-label")
                yield Input(placeholder="port, name, or pid...", id="filter-input")
                yield Static("", id="stats")
            yield DataTable(id="port-table")
            yield Static("Ready", id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the data table."""
        table = self.query_one("#port-table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True

        table.add_columns("Port", "IP", "PID", "Process", "Command", "User", "Started", "Memory")

        self.action_refresh()

    def action_refresh(self) -> None:
        """Refresh the port list."""
        self.connections = get_listening_ports()
        self.update_table()
        self.update_status("Refreshed", "status-success")

    def update_table(self) -> None:
        """Update the table with current connections."""
        table = self.query_one("#port-table", DataTable)
        table.clear()

        filtered = self.connections
        if self.filter_text:
            filter_lower = self.filter_text.lower()
            filtered = [
                c
                for c in self.connections
                if (
                    filter_lower in str(c["port"])
                    or filter_lower in str(c["name"]).lower()
                    or filter_lower in str(c["pid"])
                    or filter_lower in str(c["cmdline"]).lower()
                )
            ]

        for conn in filtered:
            port_text = Text(str(conn["port"]))

            # Highlight common dev ports
            common_ports = {
                3000: "green",
                3001: "green",  # React/Next.js
                5000: "cyan",
                5001: "cyan",  # Flask
                8000: "yellow",
                8080: "yellow",  # Django/General
                5432: "magenta",  # PostgreSQL
                6379: "red",  # Redis
                27017: "green",  # MongoDB
            }

            if conn["port"] in common_ports:
                port_text.stylize(common_ports[conn["port"]])

            table.add_row(
                port_text,
                conn["ip"],
                str(conn["pid"]),
                conn["name"],
                conn["cmdline"][:40] + ("..." if len(conn["cmdline"]) > 40 else ""),
                conn["user"],
                conn["created"],
                conn["memory"],
            )

        # Update stats
        stats = self.query_one("#stats", Static)
        stats.update(f"📊 {len(filtered)}/{len(self.connections)} ports")

    def update_status(self, message: str, css_class: str = "") -> None:
        """Update the status bar."""
        status = self.query_one("#status-bar", Static)
        status.update(message)
        status.remove_class("status-success", "status-error")
        if css_class:
            status.add_class(css_class)

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle filter input changes."""
        if event.input.id == "filter-input":
            self.filter_text = event.value
            self.update_table()

    def action_focus_filter(self) -> None:
        """Focus the filter input."""
        self.query_one("#filter-input", Input).focus()

    def action_clear_filter(self) -> None:
        """Clear the filter."""
        filter_input = self.query_one("#filter-input", Input)
        filter_input.value = ""
        self.filter_text = ""
        self.update_table()
        self.query_one("#port-table", DataTable).focus()

    def get_selected_connection(self):
        """Get the currently selected connection."""
        table = self.query_one("#port-table", DataTable)
        if table.cursor_row is None:
            return None

        # Get filtered connections
        filtered = self.connections
        if self.filter_text:
            filter_lower = self.filter_text.lower()
            filtered = [
                c
                for c in self.connections
                if (
                    filter_lower in str(c["port"])
                    or filter_lower in str(c["name"]).lower()
                    or filter_lower in str(c["pid"])
                    or filter_lower in str(c["cmdline"]).lower()
                )
            ]

        if 0 <= table.cursor_row < len(filtered):
            return filtered[table.cursor_row]
        return None

    def action_kill_selected(self) -> None:
        """Kill the selected process."""
        conn = self.get_selected_connection()
        if not conn or conn["pid"] == "-":
            self.update_status("No process selected or PID unavailable", "status-error")
            return

        self.push_screen(
            ConfirmKillScreen(conn["port"], conn["pid"], conn["name"]), self.handle_kill_confirm
        )

    def action_force_kill(self) -> None:
        """Force kill the selected process."""
        conn = self.get_selected_connection()
        if not conn or conn["pid"] == "-":
            self.update_status("No process selected or PID unavailable", "status-error")
            return

        success, message = kill_process(int(conn["pid"]), force=True)
        if success:
            self.update_status(
                f"🔥 Force killed: {conn['name']} on port {conn['port']}", "status-success"
            )
            self.action_refresh()
        else:
            self.update_status(f"❌ {message}", "status-error")

    def handle_kill_confirm(self, confirmed: bool) -> None:
        """Handle the kill confirmation result."""
        if not confirmed:
            self.update_status("Kill cancelled", "")
            return

        conn = self.get_selected_connection()
        if not conn:
            return

        success, message = kill_process(int(conn["pid"]))
        if success:
            self.update_status(
                f"✅ Killed: {conn['name']} on port {conn['port']}", "status-success"
            )
            self.action_refresh()
        else:
            self.update_status(f"❌ {message}", "status-error")


def main():
    """Entry point for the application."""
    app = PortPilotApp()
    app.run()


if __name__ == "__main__":
    main()
