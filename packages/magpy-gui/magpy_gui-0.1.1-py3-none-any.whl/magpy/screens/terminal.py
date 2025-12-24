"""
Terminal Screen widget for embedded bioamla CLI access.

Provides a terminal-like interface for running bioamla commands with
command history and auto-completion.
"""

from __future__ import annotations

import subprocess
import sys
from typing import List, Optional

from PyQt6.QtCore import Qt, QProcess, pyqtSignal, QSettings
from PyQt6.QtGui import QFont, QTextCursor, QKeyEvent, QColor
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPlainTextEdit,
    QLineEdit,
    QCompleter,
    QLabel,
    QPushButton,
)


class TerminalOutput(QPlainTextEdit):
    """Read-only terminal output display."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.setReadOnly(True)
        self.setMaximumBlockCount(10000)  # Limit history

        # Set monospace font
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)

        # Styling
        self.setStyleSheet(
            """
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
                padding: 8px;
            }
            """
        )

    def append_output(self, text: str, color: Optional[str] = None):
        """Append text to the output."""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        if color:
            html = f'<span style="color: {color};">{text}</span>'
            cursor.insertHtml(html)
        else:
            cursor.insertText(text)

        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def append_line(self, text: str, color: Optional[str] = None):
        """Append a line to the output."""
        self.append_output(text + "\n", color)

    def append_error(self, text: str):
        """Append error text in red."""
        self.append_line(text, "#f44336")

    def append_success(self, text: str):
        """Append success text in green."""
        self.append_line(text, "#4caf50")

    def append_info(self, text: str):
        """Append info text in blue."""
        self.append_line(text, "#2196f3")

    def append_command(self, text: str):
        """Append command echo in yellow."""
        self.append_line(f"$ {text}", "#ffd54f")


class CommandInput(QLineEdit):
    """Command input with history navigation."""

    command_entered = pyqtSignal(str)  # Emitted when Enter is pressed
    history_up = pyqtSignal()  # Up arrow pressed
    history_down = pyqtSignal()  # Down arrow pressed

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.setPlaceholderText("Enter bioamla command...")

        # Set monospace font
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)

        # Styling
        self.setStyleSheet(
            """
            QLineEdit {
                background-color: #252526;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 8px;
            }
            QLineEdit:focus {
                border-color: #007acc;
            }
            """
        )

    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            text = self.text().strip()
            if text:
                self.command_entered.emit(text)
                self.clear()
        elif event.key() == Qt.Key.Key_Up:
            self.history_up.emit()
        elif event.key() == Qt.Key.Key_Down:
            self.history_down.emit()
        else:
            super().keyPressEvent(event)


class TerminalScreen(QWidget):
    """
    Embedded terminal for bioamla CLI access.

    Features:
    - QPlainTextEdit-based terminal emulator
    - Command history (up/down arrows)
    - Auto-completion for bioamla commands
    - Real-time output streaming
    """

    # Available bioamla commands (for auto-completion)
    BIOAMLA_COMMANDS = [
        "analyze",
        "batch",
        "classify",
        "detect",
        "help",
        "indices",
        "info",
        "list",
        "normalize",
        "process",
        "record",
        "resample",
        "segment",
        "spectrogram",
        "train",
        "trim",
        "version",
    ]

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self._history: List[str] = []
        self._history_index: int = 0
        self._current_process: Optional[QProcess] = None
        self._max_history: int = 100

        self._setup_ui()
        self._setup_completer()
        self._load_history()

    def _setup_ui(self):
        """Set up the terminal UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setStyleSheet("background-color: #252526;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 4, 8, 4)

        title = QLabel("Terminal")
        title.setStyleSheet("color: #d4d4d4; font-weight: bold;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #3c3c3c;
                color: #d4d4d4;
                border: none;
                padding: 4px 12px;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
            }
            """
        )
        clear_btn.clicked.connect(self._clear_output)
        header_layout.addWidget(clear_btn)

        layout.addWidget(header)

        # Output area
        self._output = TerminalOutput()
        layout.addWidget(self._output, stretch=1)

        # Input area
        input_container = QWidget()
        input_container.setStyleSheet("background-color: #252526;")
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(8, 4, 8, 8)

        prompt = QLabel("$")
        prompt.setStyleSheet("color: #4caf50; font-weight: bold;")
        input_layout.addWidget(prompt)

        self._input = CommandInput()
        self._input.command_entered.connect(self._execute_command)
        self._input.history_up.connect(self._history_previous)
        self._input.history_down.connect(self._history_next)
        input_layout.addWidget(self._input)

        layout.addWidget(input_container)

        # Welcome message
        self._output.append_info("MagPy Terminal - bioamla CLI interface")
        self._output.append_line("Type 'help' for available commands.\n")

    def _setup_completer(self):
        """Set up command auto-completion."""
        completer = QCompleter(self.BIOAMLA_COMMANDS)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._input.setCompleter(completer)

    def _load_history(self):
        """Load command history from settings."""
        settings = QSettings("MagPy", "MagPy")
        history = settings.value("terminal/history", [])
        if isinstance(history, list):
            self._history = history[-self._max_history:]
        self._history_index = len(self._history)

    def _save_history(self):
        """Save command history to settings."""
        settings = QSettings("MagPy", "MagPy")
        settings.setValue("terminal/history", self._history[-self._max_history:])

    def _add_to_history(self, command: str):
        """Add a command to history."""
        # Don't add duplicates of the last command
        if not self._history or self._history[-1] != command:
            self._history.append(command)
            if len(self._history) > self._max_history:
                self._history.pop(0)
        self._history_index = len(self._history)
        self._save_history()

    def _history_previous(self):
        """Navigate to previous command in history."""
        if self._history and self._history_index > 0:
            self._history_index -= 1
            self._input.setText(self._history[self._history_index])

    def _history_next(self):
        """Navigate to next command in history."""
        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            self._input.setText(self._history[self._history_index])
        elif self._history_index == len(self._history) - 1:
            self._history_index = len(self._history)
            self._input.clear()

    def _execute_command(self, command: str):
        """Execute a terminal command."""
        self._add_to_history(command)
        self._output.append_command(command)

        # Handle built-in commands
        if command.lower() == "clear":
            self._clear_output()
            return
        elif command.lower() == "help":
            self._show_help()
            return
        elif command.lower() == "history":
            self._show_history()
            return

        # Execute bioamla command
        self._run_bioamla_command(command)

    def _run_bioamla_command(self, command: str):
        """Run a bioamla CLI command."""
        # Kill any existing process
        if self._current_process is not None:
            self._current_process.kill()

        self._current_process = QProcess(self)
        self._current_process.readyReadStandardOutput.connect(self._on_stdout)
        self._current_process.readyReadStandardError.connect(self._on_stderr)
        self._current_process.finished.connect(self._on_process_finished)

        # Run bioamla via Python module
        args = ["-m", "bioamla"] + command.split()
        self._current_process.start(sys.executable, args)

        # Disable input while running
        self._input.setEnabled(False)

    def _on_stdout(self):
        """Handle stdout from the process."""
        if self._current_process:
            data = self._current_process.readAllStandardOutput()
            text = bytes(data).decode("utf-8", errors="replace")
            self._output.append_output(text)

    def _on_stderr(self):
        """Handle stderr from the process."""
        if self._current_process:
            data = self._current_process.readAllStandardError()
            text = bytes(data).decode("utf-8", errors="replace")
            self._output.append_output(text, "#f44336")

    def _on_process_finished(self, exit_code: int, exit_status: QProcess.ExitStatus):
        """Handle process completion."""
        self._current_process = None
        self._input.setEnabled(True)
        self._input.setFocus()

        if exit_code != 0:
            self._output.append_error(f"Process exited with code {exit_code}")
        self._output.append_line("")

    def _clear_output(self):
        """Clear the terminal output."""
        self._output.clear()
        self._output.append_info("Terminal cleared.\n")

    def _show_help(self):
        """Show help message."""
        help_text = """
Available commands:
  clear     - Clear the terminal
  help      - Show this help message
  history   - Show command history

bioamla commands:
  analyze <file>        - Analyze audio file
  detect <file>         - Detect acoustic events
  indices <file>        - Compute acoustic indices
  info <file>           - Show file information
  normalize <file>      - Normalize audio
  resample <file> <rate>- Resample audio
  spectrogram <file>    - Generate spectrogram
  trim <file> <start> <end> - Trim audio

For more help, run: bioamla <command> --help
"""
        self._output.append_line(help_text)

    def _show_history(self):
        """Show command history."""
        if not self._history:
            self._output.append_line("No command history.\n")
            return

        self._output.append_line("Command history:")
        for i, cmd in enumerate(self._history[-20:], 1):  # Show last 20
            self._output.append_line(f"  {i:3d}  {cmd}")
        self._output.append_line("")

    def write_output(self, text: str):
        """Write text to the terminal output (for external use)."""
        self._output.append_output(text)

    def write_line(self, text: str, color: Optional[str] = None):
        """Write a line to the terminal output (for external use)."""
        self._output.append_line(text, color)
