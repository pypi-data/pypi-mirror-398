"""TUI interface for porthog using Textual."""

from datetime import datetime

from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer, Header, Label, Static

from porthog.ports import (
    PortInfo,
    ProcessType,
    get_listening_ports,
    kill_port,
)

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


class ConfirmDialog(ModalScreen[bool]):
    """A modal dialog for confirming actions."""

    BINDINGS = [
        Binding("y", "confirm", "Yes"),
        Binding("n", "cancel", "No"),
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, message: str, port_info: PortInfo) -> None:
        super().__init__()
        self.message = message
        self.port_info = port_info

    def compose(self) -> ComposeResult:
        color = PROCESS_COLORS.get(self.port_info.process_type, "white")
        yield Container(
            Vertical(
                Label(self.message, id="confirm-message"),
                Label(
                    f"Port {self.port_info.port} - {self.port_info.display_name} (PID {self.port_info.pid})",
                    id="confirm-details",
                ),
                Horizontal(
                    Label("[y] Yes  ", classes="confirm-btn"),
                    Label("[n] No", classes="confirm-btn"),
                    id="confirm-buttons",
                ),
                id="confirm-dialog",
            ),
            id="confirm-container",
        )

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)


class StatusBar(Static):
    """A status bar to show messages."""

    def set_message(self, message: str, style: str = "") -> None:
        self.update(Text(message, style=style))

    def clear(self) -> None:
        self.update("")


class PortHogApp(App[None]):
    """Main TUI application."""

    CSS = """
    Screen {
        background: $surface;
    }

    #main-container {
        height: 100%;
        padding: 0 1;
    }

    DataTable {
        height: 1fr;
        margin-bottom: 1;
    }

    DataTable > .datatable--cursor {
        background: $accent;
        color: $text;
    }

    StatusBar {
        height: 1;
        padding: 0 1;
        background: $surface-darken-1;
    }

    #confirm-container {
        align: center middle;
        width: 100%;
        height: 100%;
    }

    #confirm-dialog {
        width: 60;
        height: auto;
        padding: 1 2;
        background: $surface;
        border: thick $primary;
    }

    #confirm-message {
        text-align: center;
        margin-bottom: 1;
        text-style: bold;
    }

    #confirm-details {
        text-align: center;
        margin-bottom: 1;
        color: $text-muted;
    }

    #confirm-buttons {
        align: center middle;
        height: 1;
        margin-top: 1;
    }

    .confirm-btn {
        margin: 0 2;
    }

    #empty-message {
        width: 100%;
        height: 100%;
        content-align: center middle;
        text-style: italic;
        color: $text-muted;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("ctrl+c", "quit", "Quit", show=False),
        Binding("r", "refresh", "Refresh"),
        Binding("k", "kill", "Kill"),
        Binding("K", "kill_force", "Force Kill"),
        Binding("a", "toggle_all", "All Ports"),
    ]

    TITLE = "porthog"
    SUB_TITLE = "Dev Server Port Manager"

    def __init__(self) -> None:
        super().__init__()
        self.show_all_ports = False
        self.ports_data: list[PortInfo] = []

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            DataTable(id="ports-table"),
            StatusBar(id="status-bar"),
            id="main-container",
        )
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the table when the app starts."""
        self.refresh_table()

    def refresh_table(self) -> None:
        """Refresh the ports table."""
        table = self.query_one("#ports-table", DataTable)
        status = self.query_one("#status-bar", StatusBar)

        # Clear existing data
        table.clear(columns=True)

        # Add columns
        table.add_column("Port", key="port", width=6)
        table.add_column("PID", key="pid", width=8)
        table.add_column("Type", key="type", width=10)
        table.add_column("Process", key="process", width=20)
        table.add_column("Command", key="command")
        table.add_column("Mem", key="memory", width=8)
        table.add_column("Up", key="uptime", width=8)

        # Get ports
        self.ports_data = get_listening_ports(dev_only=not self.show_all_ports)

        if not self.ports_data:
            status.set_message("No dev servers found", "dim italic")
            return

        # Add rows
        for port_info in self.ports_data:
            color = PROCESS_COLORS.get(port_info.process_type, "white")

            table.add_row(
                str(port_info.port),
                str(port_info.pid),
                Text(port_info.process_type.value, style=color),
                Text(port_info.display_name, style=f"bold {color}"),
                Text(port_info.short_cmd, style="dim"),
                format_memory(port_info.memory_mb),
                format_uptime(port_info.create_time),
                key=str(port_info.port),
            )

        mode = "all ports" if self.show_all_ports else "dev ports"
        status.set_message(f"Found {len(self.ports_data)} listening ({mode})")

    def get_selected_port_info(self) -> PortInfo | None:
        """Get the PortInfo for the currently selected row."""
        table = self.query_one("#ports-table", DataTable)

        if not self.ports_data or table.cursor_row is None:
            return None

        if table.cursor_row >= len(self.ports_data):
            return None

        return self.ports_data[table.cursor_row]

    def action_refresh(self) -> None:
        """Refresh the ports list."""
        self.refresh_table()

    def action_toggle_all(self) -> None:
        """Toggle between dev ports and all ports."""
        self.show_all_ports = not self.show_all_ports
        self.refresh_table()

    def action_kill(self) -> None:
        """Kill the selected process (graceful)."""
        self._do_kill(force=False)

    def action_kill_force(self) -> None:
        """Force kill the selected process."""
        self._do_kill(force=True)

    def _do_kill(self, force: bool) -> None:
        """Kill the selected process."""
        port_info = self.get_selected_port_info()

        if port_info is None:
            status = self.query_one("#status-bar", StatusBar)
            status.set_message("No process selected", "yellow")
            return

        action = "Force kill" if force else "Kill"

        def handle_confirm(confirmed: bool | None) -> None:
            if confirmed:
                success, message = kill_port(port_info.port, force=force)
                status = self.query_one("#status-bar", StatusBar)
                if success:
                    status.set_message(message, "green")
                    self.refresh_table()
                else:
                    status.set_message(message, "red")

        self.push_screen(
            ConfirmDialog(f"{action} this process?", port_info),
            handle_confirm,
        )

def run_tui() -> None:
    """Run the TUI application."""
    app = PortHogApp()
    app.run()


if __name__ == "__main__":
    run_tui()
