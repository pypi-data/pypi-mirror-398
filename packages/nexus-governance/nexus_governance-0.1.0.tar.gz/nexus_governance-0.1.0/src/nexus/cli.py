import os

import click
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Footer, Header, Label

from nexus.core.engine import NexusEngine


class ConfirmationScreen(ModalScreen):
    CSS = """
    ConfirmationScreen {
        align: center middle;
    }
    #dialog {
        grid-size: 2;
        grid-gutter: 1 2;
        grid-rows: 1fr 3;
        padding: 0 1;
        width: 60;
        height: 11;
        border: thick $background 80%;
        background: $surface;
    }
    #question {
        column-span: 2;
        height: 1fr;
        content-align: center middle;
    }
    Button {
        width: 100%;
    }
    """

    def __init__(self, action: str, req_id: str):
        super().__init__()
        self.action = action
        self.req_id = req_id

    def compose(self) -> ComposeResult:
        yield Container(
            Label(
                f"Are you sure you want to {self.action.upper()}?\n\nRequest ID: {self.req_id}",
                id="question",
            ),
            Button(
                "Yes",
                variant="primary" if self.action == "approve" else "error",
                id="yes",
            ),
            Button("Cancel", variant="default", id="cancel"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes":
            self.dismiss(True)
        else:
            self.dismiss(False)


class NexusDashboard(App):
    CSS = """
    DataTable {
        height: 1fr;
        border: solid $accent;
    }
    .status-pending { color: yellow; }
    .status-approved { color: green; }
    .status-denied { color: red; }
    .status-executed { color: blue; }
    .status-expired { color: gray; }
    
    #details {
        height: 8;
        dock: bottom;
        border-top: solid $secondary;
        padding: 1;
        background: $surface-darken-1;
    }
    """

    BINDINGS = [
        Binding("r", "refresh", "Refresh"),
        Binding("a", "approve", "Approve Request"),
        Binding("d", "deny", "Deny Request"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, db_path: str):
        super().__init__()
        self.db_path = db_path
        # Initialize engine to communicate with DB
        self.engine = NexusEngine(db_path=self.db_path)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield DataTable(cursor_type="row")
        yield Vertical(
            Label("Select a request to view details...", id="details_label"),
            id="details",
        )
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Nexus Governance Console"
        self.sub_title = f"Connected to: {self.db_path}"

        table = self.query_one(DataTable)
        table.add_columns(
            "Request ID", "Tool", "Status", "Danger", "Created", "Principal"
        )

        self.refresh_data()
        self.set_interval(2, self.refresh_data)

    def action_refresh(self) -> None:
        self.refresh_data()

    def refresh_data(self) -> None:
        table = self.query_one(DataTable)
        cursor_row = table.cursor_row
        table.clear()

        rows = self.engine.conn.execute(
            """
            SELECT request_id, tool_name, status, danger, created_at, principal_id
            FROM governance_requests
            ORDER BY created_at DESC
            LIMIT 50
            """
        ).fetchall()

        for row in rows:
            req_id, tool, status, danger, created_at, principal = row
            danger = (danger or "unknown").upper()

            status_style = f"[{'yellow' if status == 'PENDING' else 'green' if status == 'APPROVED' else 'red' if status == 'DENIED' else 'blue' if status == 'EXECUTED' else 'gray'}]"
            styled_status = f"{status_style}{status}[/]"

            table.add_row(
                req_id,
                tool,
                styled_status,
                danger,
                str(created_at),
                principal,
                key=req_id,
            )

        if cursor_row is not None and cursor_row < len(rows):
            table.move_cursor(row=cursor_row)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Update the details pane when a row is highlighted."""
        req_id = event.row_key.value
        self.show_details(req_id)

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        req_id = event.row_key.value
        self.show_details(req_id)

    def show_details(self, req_id: str):
        row = self.engine.conn.execute(
            "SELECT args_redacted, tool_version, denied_reason FROM governance_requests WHERE request_id = ?",
            (req_id,),
        ).fetchone()

        if row:
            args, version, reason = row
            detail_text = (
                f"[bold]ID:[/bold] {req_id}  [bold]Version:[/bold] {version}\n"
            )
            detail_text += f"[bold]Args:[/bold] {args}"
            if reason:
                detail_text += f"\n[bold red]Denial Reason:[/bold] {reason}"

            self.query_one("#details_label", Label).update(detail_text)

    def action_approve(self) -> None:
        table = self.query_one(DataTable)
        if table.cursor_row is None:
            self.notify("No request selected", severity="warning")
            return

        req_id = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value

        status = self.engine.conn.execute(
            "SELECT status FROM governance_requests WHERE request_id=?", (req_id,)
        ).fetchone()[0]
        if status != "PENDING":
            self.notify(f"Cannot approve. Status is {status}", severity="error")
            return

        def check_confirm(is_confirmed: bool) -> None:
            if is_confirmed:
                success, msg = self.engine.approve_request(req_id, "operator_cli")
                if success:
                    self.notify(f"Approved {req_id}")
                    self.refresh_data()
                else:
                    self.notify(f"Error: {msg}", severity="error")

        self.push_screen(ConfirmationScreen("approve", req_id), check_confirm)

    def action_deny(self) -> None:
        table = self.query_one(DataTable)
        if table.cursor_row is None:
            self.notify("No request selected", severity="warning")
            return

        req_id = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value

        def check_confirm(is_confirmed: bool) -> None:
            if is_confirmed:
                success, msg = self.engine.deny_request(
                    req_id, "operator_cli", reason="Denied via CLI"
                )
                if success:
                    self.notify(f"Denied {req_id}")
                    self.refresh_data()
                else:
                    self.notify(f"Error: {msg}", severity="error")

        self.push_screen(ConfirmationScreen("deny", req_id), check_confirm)


@click.command()
@click.option("--db", default="nexus.db", help="Path to the Nexus SQLite database.")
def monitor(db):
    if not os.path.exists(db):
        pass

    app = NexusDashboard(db_path=db)
    app.run()


if __name__ == "__main__":
    monitor()
