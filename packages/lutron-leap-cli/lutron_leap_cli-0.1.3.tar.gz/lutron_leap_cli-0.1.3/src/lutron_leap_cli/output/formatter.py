"""Output formatting with Rich and JSON support."""

import json
from typing import Any, Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel


class OutputFormatter:
    """Handles output formatting between Rich tables and JSON."""

    def __init__(self, json_output: bool = False, verbose: bool = False):
        self.json_output = json_output
        self.verbose = verbose
        self.console = Console()
        self.error_console = Console(stderr=True)

    def print(self, content: Any) -> None:
        """Print content - as JSON if json_output, else Rich."""
        if self.json_output:
            if hasattr(content, "to_dict"):
                content = content.to_dict()
            elif hasattr(content, "model_dump"):
                content = content.model_dump()
            self.console.print(json.dumps(content, indent=2, default=str))
        else:
            self.console.print(content)

    def print_table(self, table: Table, data: list[dict]) -> None:
        """Print a Rich table or JSON list."""
        if self.json_output:
            self.console.print(json.dumps(data, indent=2, default=str))
        else:
            self.console.print(table)

    def print_success(self, message: str, data: Optional[dict] = None) -> None:
        """Print success message."""
        if self.json_output:
            output = {"success": True, "message": message}
            if data:
                output.update(data)
            self.console.print(json.dumps(output, indent=2, default=str))
        else:
            self.console.print(f"[green]✓[/green] {message}")

    def print_error(self, message: str, data: Optional[dict] = None) -> None:
        """Print error message."""
        if self.json_output:
            output = {"success": False, "error": message}
            if data:
                output.update(data)
            self.error_console.print(json.dumps(output, indent=2, default=str))
        else:
            self.error_console.print(f"[red]✗[/red] {message}")

    def print_warning(self, message: str) -> None:
        """Print warning message."""
        if self.json_output:
            self.error_console.print(json.dumps({"warning": message}, indent=2))
        else:
            self.error_console.print(f"[yellow]![/yellow] {message}")

    def print_info(self, message: str) -> None:
        """Print info message (only in verbose mode for non-JSON)."""
        if self.json_output:
            return  # Skip info in JSON mode
        if self.verbose:
            self.console.print(f"[dim]{message}[/dim]")

    def print_panel(
        self, content: str, title: str, data: Optional[dict] = None
    ) -> None:
        """Print a Rich panel or JSON object."""
        if self.json_output:
            output = {"title": title, "content": content}
            if data:
                output.update(data)
            self.console.print(json.dumps(output, indent=2, default=str))
        else:
            self.console.print(Panel(content, title=title))


# Global formatter instance (set by CLI)
_formatter: Optional[OutputFormatter] = None


def get_formatter() -> OutputFormatter:
    """Get the global formatter instance."""
    global _formatter
    if _formatter is None:
        _formatter = OutputFormatter()
    return _formatter


def set_formatter(formatter: OutputFormatter) -> None:
    """Set the global formatter instance."""
    global _formatter
    _formatter = formatter
