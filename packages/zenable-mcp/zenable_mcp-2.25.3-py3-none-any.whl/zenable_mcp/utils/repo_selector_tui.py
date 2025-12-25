"""Textual TUI for selecting git repositories."""

from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Center, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Input, Label, SelectionList, Static
from textual.widgets.selection_list import Selection


class ConfirmScreen(ModalScreen[bool]):
    """Modal confirmation screen."""

    CSS = """
    ConfirmScreen {
        align: center middle;
        background: rgba(3, 7, 18, 0.85);
    }

    #confirm-dialog {
        width: 60;
        height: auto;
        border: thick #374151;
        background: #1f2937;
        padding: 1 2;
    }

    #confirm-question {
        width: 100%;
        content-align: center middle;
        padding: 1;
        text-style: bold;
        color: #f9fafb;
    }

    #confirm-buttons {
        width: 100%;
        height: auto;
        align: center middle;
        padding: 1;
    }

    Button {
        margin: 0 1;
    }

    .button--primary {
        background: #007F7F;
        color: #f9fafb;
    }

    .button--primary:hover {
        background: #009999;
    }

    .button--default {
        background: #374151;
        color: #d1d5db;
    }

    .button--default:hover {
        background: #4b5563;
    }
    """

    def __init__(self, question: str):
        super().__init__()
        self.question = question

    def compose(self) -> ComposeResult:
        """Compose the confirmation dialog."""
        with Vertical(id="confirm-dialog"):
            yield Label(self.question, id="confirm-question")
            with Center(id="confirm-buttons"):
                yield Button("Yes (y/Enter)", variant="primary", id="yes")
                yield Button("No (n/Esc)", variant="default", id="no")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "yes":
            self.dismiss(True)
        else:
            self.dismiss(False)

    def on_key(self, event) -> None:
        """Handle key presses for confirmation."""
        if event.key in ("y", "enter"):
            self.dismiss(True)
            event.prevent_default()
            event.stop()
        elif event.key in ("n", "escape"):
            self.dismiss(False)
            event.prevent_default()
            event.stop()


class RepoSelectorApp(App[list[Path] | str | None]):
    """Textual app for selecting repositories with multi-select support."""

    TITLE = ""

    CSS = """
    Screen {
        background: #030712;
    }

    #title {
        width: 100%;
        content-align: center middle;
        background: #1f2937;
        color: #f9fafb;
        padding: 1;
        text-style: bold;
    }

    #filter-container {
        height: auto;
        margin: 0 2;
        padding: 0;
    }

    #filter-input {
        width: 100%;
        border: solid #374151;
        background: #1f2937;
        color: #f9fafb;
        display: none;
    }

    #filter-input.visible {
        display: block;
    }

    #selection-container {
        height: 1fr;
        border: solid #374151;
        margin: 1 2;
        background: #030712;
    }

    SelectionList {
        height: 100%;
        background: #030712;
        color: #f9fafb;
    }

    SelectionList:focus {
        border: solid #007F7F;
    }

    SelectionList > .selection-list--button {
        background: #030712;
        color: #d1d5db;
    }

    SelectionList > .selection-list--button-highlighted {
        background: #1f2937;
        color: #f9fafb;
    }

    SelectionList > .selection-list--button-selected {
        background: #007F7F;
        color: #f9fafb;
    }

    SelectionList > .selection-list--button-selected.selection-list--button-highlighted {
        background: #009999;
        color: #f9fafb;
    }

    #status-bar {
        dock: bottom;
        height: 1;
        background: #1f2937;
        color: #d1d5db;
        padding: 0 2;
    }

    Footer {
        background: #030712;
        color: #6b7280;
    }

    Header {
        background: #1f2937;
        color: #f9fafb;
    }
    """

    BINDINGS = [
        Binding("c", "continue", "Continue", priority=True),
        Binding("a", "select_all", "Select All"),
        Binding("n", "deselect_all", "Deselect All"),
        Binding("/", "filter", "Filter"),
        Binding("q,escape", "quit", "Quit"),
        Binding("enter", "toggle_current", "Toggle", show=False),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("G", "handle_shift_g", "Go to", show=False),
        Binding("1", "press_one", "Line", show=False),
    ]

    def __init__(
        self,
        repos: list[Path],
        start_path: Path,
        allow_all: bool = True,
        allow_global: bool = True,
        max_visible_repos: int = 40,
    ):
        super().__init__()
        self.repos = repos
        self.start_path = start_path
        self.allow_all = allow_all
        self.allow_global = allow_global
        self.max_visible_repos = max_visible_repos
        self.selection_list: SelectionList | None = None
        self.filter_input: Input | None = None
        self.one_pressed: bool = False
        self.filter_active: bool = False
        self.current_filter: str = ""

    def _build_selections(self, filter_text: str = "") -> list[Selection]:
        """Build selection list with optional filtering."""
        selections = []

        # Filter repos if needed
        filtered_repos = self.repos
        if filter_text:
            filter_lower = filter_text.lower()
            filtered_repos = [
                repo for repo in self.repos if filter_lower in str(repo).lower()
            ]

        # Limit visible repos
        visible_repos = filtered_repos[: self.max_visible_repos]
        total_filtered = len(filtered_repos)

        # Add repo selections
        for repo in visible_repos:
            try:
                display_name = str(repo.relative_to(self.start_path))
            except ValueError:
                display_name = str(repo)
            selections.append(Selection(display_name, repo, initial_state=False))

        # Add info if some repos are hidden
        if total_filtered > len(visible_repos):
            hidden_count = total_filtered - len(visible_repos)
            selections.append(
                Selection(
                    f"─── {hidden_count} more match{'es' if hidden_count != 1 else ''} (refine filter to see more) ───",
                    None,
                    initial_state=False,
                    disabled=True,
                )
            )

        # Add separator before special options
        selections.append(Selection("─" * 50, None, initial_state=False, disabled=True))

        # Add "select all" helper option if enabled
        if self.allow_all:
            # filtered_repos only contains Path objects (actual repos), not special options
            display_count = len(filtered_repos) if filter_text else len(self.repos)
            selections.append(
                Selection(
                    f"Select all {display_count} repositories"
                    + (" matching filter" if filter_text else ""),
                    "select_all_repos",
                    initial_state=False,
                )
            )

        # Add action options at the bottom
        if self.allow_global:
            selections.append(
                Selection(
                    "✓ Install globally (in home directory)",
                    "global",
                    initial_state=False,
                )
            )

        selections.append(
            Selection(
                "✓ Continue with selected repositories",
                "continue",
                initial_state=False,
            )
        )

        return selections

    def compose(self) -> ComposeResult:
        """Compose the UI."""
        yield Header()
        yield Static("Setup Zenable", id="title")

        # Add filter input (initially hidden)
        with Vertical(id="filter-container"):
            yield Input(
                placeholder="Type to filter repos... (Enter to apply, Esc to cancel)",
                id="filter-input",
            )

        # Build initial selections
        selections = self._build_selections()

        with Vertical(id="selection-container"):
            yield SelectionList(*selections)

        yield Static("", id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize after mounting."""
        self.selection_list = self.query_one(SelectionList)
        self.filter_input = self.query_one("#filter-input", Input)
        self.update_status_bar()
        # Explicitly focus the selection list so navigation keys work immediately
        self.selection_list.focus()

    def on_key(self, event) -> None:
        """Handle key presses to reset one_pressed mode and manage filter."""
        # Handle Escape to cancel filter when filter is active
        if event.key == "escape" and self.filter_active:
            self._cancel_filter()
            event.prevent_default()
            event.stop()
            return

        # Reset one_pressed if any key other than '1' or 'G' is pressed
        if event.key not in ("1", "G") and self.one_pressed:
            self.one_pressed = False

    def on_selection_list_selected_changed(
        self, event: SelectionList.SelectedChanged
    ) -> None:
        """Update status bar when selection changes."""
        self.update_status_bar()

        # Check if "Select all X repositories" was selected
        if "select_all_repos" in event.selection_list.selected:
            # Select all repository items (respecting filter if active)
            repos_to_select = self.repos
            if self.current_filter:
                filter_lower = self.current_filter.lower()
                repos_to_select = [
                    repo for repo in self.repos if filter_lower in str(repo).lower()
                ]

            for repo in repos_to_select:
                try:
                    event.selection_list.select(repo)
                except (ValueError, LookupError):
                    # Item not in current list (filtered out)
                    pass
            # Deselect the "select_all_repos" option itself
            event.selection_list.deselect("select_all_repos")

        # Check if "Continue" was selected
        if "continue" in event.selection_list.selected:
            # Deselect it first so user can change their mind
            event.selection_list.deselect("continue")
            self.action_continue()

        # Check if "Install globally" was selected
        if "global" in event.selection_list.selected:
            # Deselect it first so user can change their mind
            event.selection_list.deselect("global")
            # Confirm global installation
            self.action_confirm_global()

    def update_status_bar(self) -> None:
        """Update the status bar with current selection count."""
        if not self.selection_list:
            return

        selected = self.selection_list.selected
        # Filter out special values and separators
        repo_count = sum(1 for s in selected if isinstance(s, Path))

        status_bar = self.query_one("#status-bar", Static)

        # Build status message
        status_parts = []
        if repo_count > 0:
            status_parts.append(
                f"{repo_count} {'repository' if repo_count == 1 else 'repositories'} selected"
            )
        else:
            status_parts.append("No repositories selected")

        # Show filter indicator if filter is active (even when input is hidden)
        if self.current_filter:
            status_parts.append(f"[Filtered: '{self.current_filter}']")

        status_bar.update(" | ".join(status_parts))

    def action_toggle_current(self) -> None:
        """Toggle the currently highlighted item (Enter key behavior)."""
        if self.selection_list:
            highlighted = self.selection_list.highlighted
            if highlighted is not None:
                self.selection_list.toggle(highlighted)

    def action_continue(self) -> None:
        """Process selection and exit."""
        if not self.selection_list:
            return

        selected = self.selection_list.selected

        # Remove "continue" from selected if present
        selected = [s for s in selected if s != "continue"]

        if not selected:
            self.notify("Please select at least one repository", severity="warning")
            return

        # Filter out separator and special options
        repos = [s for s in selected if isinstance(s, Path)]
        if not repos:
            self.notify("Please select at least one repository", severity="warning")
            return

        # Show confirmation for selected repositories
        self.action_confirm_repos(repos)

    def action_select_all(self) -> None:
        """Select all repository items (not special options)."""
        if self.selection_list:
            # Only select actual repository paths, not special options
            for repo in self.repos:
                self.selection_list.select(repo)

    def action_deselect_all(self) -> None:
        """Deselect all items."""
        if self.selection_list:
            self.selection_list.deselect_all()

    def action_filter(self) -> None:
        """Show filter input and focus it."""
        if self.filter_input:
            self.filter_active = True
            # Restore current filter value if one exists
            self.filter_input.value = self.current_filter
            self.filter_input.add_class("visible")
            self.filter_input.focus()

    def _cancel_filter(self) -> None:
        """Cancel filter input and clear filter."""
        if self.filter_input:
            self.filter_active = False
            self.filter_input.remove_class("visible")
            self.filter_input.value = ""
            self.current_filter = ""
            self._rebuild_selection_list("")
            if self.selection_list:
                self.selection_list.focus()

    def _commit_filter(self) -> None:
        """Commit the current filter and return focus to selection list."""
        if self.filter_input:
            self.filter_active = False
            self.filter_input.remove_class("visible")
            # Keep current_filter and the filtered list
            self.update_status_bar()  # Update to show filter indicator
            if self.selection_list:
                # Highlight the first item in the filtered list
                self.selection_list.highlighted = 0
                self.selection_list.focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle filter input changes."""
        if event.input.id == "filter-input":
            self.current_filter = event.value
            self._rebuild_selection_list(self.current_filter)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in filter input - commit the filter."""
        if event.input.id == "filter-input":
            self._commit_filter()

    def _rebuild_selection_list(self, filter_text: str) -> None:
        """Rebuild the selection list with filtered repos."""
        if not self.selection_list:
            return

        # Save current selections
        previously_selected = set(self.selection_list.selected)

        # Clear and rebuild
        self.selection_list.clear_options()
        new_selections = self._build_selections(filter_text)

        # Add new selections
        for selection in new_selections:
            self.selection_list.add_option(selection)

        # Restore selections that still exist
        for value in previously_selected:
            if isinstance(value, Path):
                try:
                    self.selection_list.select(value)
                except (ValueError, LookupError):
                    # Item not in filtered list
                    pass

    def action_quit(self) -> None:
        """Quit the app without selecting."""
        self.exit(None)

    def action_cursor_down(self) -> None:
        """Move cursor down in the selection list."""
        if self.selection_list:
            self.selection_list.action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up in the selection list."""
        if self.selection_list:
            self.selection_list.action_cursor_up()

    def action_press_one(self) -> None:
        """Handle pressing '1' - waiting for Shift+G to go to top."""
        self.one_pressed = True
        self.notify("Press Shift+G to go to top", timeout=1)

    def action_handle_shift_g(self) -> None:
        """Handle Shift+G - go to end, or to top if '1' was pressed."""
        if self.one_pressed:
            # '1' was pressed before - go to top
            if self.selection_list:
                self.selection_list.action_first()
            self.one_pressed = False
        else:
            # Just Shift+G - go to end
            if self.selection_list:
                self.selection_list.action_last()

    def action_confirm_global(self) -> None:
        """Confirm global installation."""
        self.push_screen(
            ConfirmScreen("Do you want to install the Zenable tools system-wide?"),
            lambda result: self._on_global_confirm(result),
        )

    def action_confirm_repos(self, repos: list[Path]) -> None:
        """Confirm installation in selected repositories."""
        repo_count = len(repos)
        if repo_count == 1:
            message = "Install in 1 repository?"
        elif repo_count == len(self.repos):
            message = f"Install in all {repo_count} repositories?"
        else:
            message = f"Install in {repo_count} repositories?"

        self.push_screen(
            ConfirmScreen(message),
            lambda result: self._on_repos_confirm(result, repos),
        )

    def _on_global_confirm(self, result: bool) -> None:
        """Handle global installation confirmation result."""
        if result:
            self.exit("global")
        else:
            # Reset status bar
            self.update_status_bar()

    def _on_repos_confirm(self, result: bool, repos: list[Path]) -> None:
        """Handle repository selection confirmation result."""
        if result:
            self.exit(repos)
        else:
            # Reset status bar
            self.update_status_bar()
