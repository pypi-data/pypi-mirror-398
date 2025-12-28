"""Entry point for the Qudix application."""

from __future__ import annotations

import argparse
import base64
import os
import sys
from pathlib import Path
from typing import Optional

from . import __version__
from prompt_toolkit.application import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.clipboard import ClipboardData, InMemoryClipboard
from prompt_toolkit.formatted_text import AnyFormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HSplit, Layout, VSplit, Window
from prompt_toolkit.layout.containers import Container
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension as D
from prompt_toolkit.selection import SelectionType
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Button, Label, TextArea, Dialog
import subprocess
import shutil


APP_STYLE = Style.from_dict(
    {
        "toolbar": "bg:#30343f #f0f0f0",
        "toolbar-title": "bold",
        "toolbar-path": "italic",
        "button": "bg:#505665 #f0f0f0",
        "button.focused": "bg:#8ab6d6 #101820",
        "status": "bg:#1f2229 #d7dae0",
        "status.error": "bg:#501616 #f8f8f8",
        "status.success": "bg:#165016 #f8f8f8",
        "divider": "fg:#4a4e59",
        "textarea": "bg:#111216 #f8f8f2",
    }
)


def _is_ssh_session() -> bool:
    """Detect if running in an SSH session (works on all platforms)."""
    return bool(
        os.environ.get("SSH_CONNECTION")
        or os.environ.get("SSH_CLIENT")
        or os.environ.get("SSH_TTY")
    )


def _osc52_write(text: str) -> bool:
    """Write text to host clipboard via OSC52 escape sequence.

    Works over SSH when the terminal emulator supports OSC52.
    Supported terminals include: iTerm2, kitty, WezTerm, Alacritty,
    Windows Terminal, foot, tmux (with set-clipboard on), and more.

    Emits both BEL-terminated and ST-terminated sequences for maximum
    compatibility across different terminal emulators.

    Returns True if the sequence was written successfully.
    """
    if not text:
        return False
    try:
        encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")
    except Exception:
        return False
    # OSC 52 with clipboard selection 'c' (system clipboard)
    # BEL (\x07) terminator - most common
    seq_bel = f"\x1b]52;c;{encoded}\x07"
    # ST (\x1b\\) terminator - better for some terminals
    seq_st = f"\x1b]52;c;{encoded}\x1b\\"
    try:
        sys.stdout.write(seq_bel)
        sys.stdout.write(seq_st)
        sys.stdout.flush()
        return True
    except Exception:
        return False


class OSC52Clipboard:
    """Clipboard that uses OSC52 escape sequences for SSH sessions.

    This allows copy/cut operations to transfer text to the host OS clipboard
    when running over SSH, provided the terminal emulator supports OSC52.

    Supported on all platforms (macOS, Linux, Windows) as long as the
    terminal emulator on the host machine supports OSC52.

    For paste operations, since OSC52 read is not reliably supported by
    terminals (for security reasons), this clipboard maintains internal
    state. Users can paste from their terminal using Ctrl+Shift+V or
    their terminal's native paste, which uses bracketed paste mode.
    """

    def __init__(self) -> None:
        self._data = ClipboardData(text="")

    def set_data(self, data: ClipboardData) -> None:
        """Copy text to both internal storage and host clipboard via OSC52."""
        text = getattr(data, "text", "")
        try:
            self._data = ClipboardData(text=text)
        except Exception:
            self._data = ClipboardData(text=str(text))
        # Send to host clipboard via OSC52
        _osc52_write(text)

    def get_data(self) -> ClipboardData:
        """Get clipboard data from internal storage.

        Note: OSC52 read is not supported by most terminals for security.
        Users should use terminal's native paste (Ctrl+Shift+V) to paste
        from the host clipboard, which uses bracketed paste mode.
        """
        return self._data


# Keymap configuration
# Toggle to show keymap hints in button labels and to enable related shortcuts.
KEYMAPS_ENABLED: bool = False

# Declare keymap display text and binding spec for toolbar actions.
# - display: human-friendly hint appended to button text when enabled
# - binding: prompt_toolkit key binding spec used to register the shortcut
KEYMAPS: dict[str, dict[str, object]] = {
    "undo": {"display": "", "binding": None},
    "redo": {"display": "", "binding": None},
    "cut": {"display": "F5", "binding": "f5"},
    "copy": {"display": "F6", "binding": "f6"},
    "paste": {"display": "F7", "binding": "f7"},
    "delete": {"display": "F8", "binding": "f8"},
}


def _with_key_hint(text: str, key_display: str) -> str:
    """Return button label with key hint appended when enabled and present."""
    if KEYMAPS_ENABLED and key_display:
        return f"{text} ({key_display})"
    return text


class QudixApplication:
    """Encapsulates the prompt_toolkit application and editing actions."""

    def __init__(self, initial_text: str = "", file_path: Optional[Path] = None) -> None:
        self.path = file_path
        # Prefer a system clipboard so copy/paste integrates with the OS.
        self.clipboard = self._create_system_clipboard()
        self.text_area = TextArea(
            text=initial_text,
            scrollbar=True,
            line_numbers=True,
            focus_on_click=True,
            style="class:textarea",
        )
        self._dirty: bool = False
        self._scroll_fix_prev_cursor_pos: Optional[int] = None
        self._last_vertical_scroll: Optional[int] = None
        self._last_cursor_row: Optional[int] = None
        self._status_text: AnyFormattedText = ""
        self._status_tag: str = "status"
        self._confirm_exit: bool = False
        # Custom undo/redo stacks to ensure reliable redo behavior.
        self._undo_stack: list[tuple[str, int]] = []
        self._redo_stack: list[tuple[str, int]] = []
        self._restoring_state: bool = False
        self._snapshot_text: str = initial_text
        self._snapshot_cursor: int = 0
        self.status_control = FormattedTextControl(self._render_status, show_cursor=False)
        self.status_bar = Window(
            content=self.status_control,
            height=1,
            style="class:status",
            dont_extend_height=True,
        )

        self._application = self._create_application()
        self._application.before_render += self._on_before_render
        self._set_status("Ready")
        self.text_area.buffer.on_text_changed += self._on_text_changed
        # Initialize snapshot to current buffer state.
        try:
            self._snapshot_text = self.text_area.buffer.text
            self._snapshot_cursor = self.text_area.buffer.cursor_position
        except Exception:
            self._snapshot_text = initial_text
            self._snapshot_cursor = 0

    def _create_system_clipboard(self):
        """Create a clipboard that integrates with the OS when possible.

        When running over SSH, uses OSC52 escape sequences to transfer
        clipboard content to/from the host OS. This works on all platforms
        (macOS, Linux, Windows) as long as the terminal emulator supports OSC52.

        For local sessions, tries prompt_toolkit's PyperclipClipboard first,
        then falls back to platform-specific implementations.
        If all fail, use in-memory.
        """
        # Use OSC52 for SSH sessions on ALL platforms (macOS, Linux, Windows)
        # OSC52 is supported by modern terminals: iTerm2, kitty, WezTerm,
        # Alacritty, Windows Terminal, foot, tmux (with set-clipboard on), etc.
        if _is_ssh_session():
            return OSC52Clipboard()

        # For local sessions, try prompt_toolkit's pyperclip integration.
        if not sys.platform.startswith("win"):
            try:
                from prompt_toolkit.clipboard.pyperclip import PyperclipClipboard  # type: ignore
                return PyperclipClipboard()
            except Exception:
                pass

        # macOS fallback using pbcopy/pbpaste (common on macOS systems).
        if sys.platform == "darwin":
            class MacOSClipboard:
                def set_data(self, data: ClipboardData) -> None:
                    text = getattr(data, "text", "")
                    try:
                        subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=False)
                    except Exception:
                        # If pbcopy fails, we can't do much; ignore.
                        pass

                def get_data(self) -> ClipboardData:
                    out = b""
                    try:
                        res = subprocess.run(["pbpaste"], capture_output=True, check=False)
                        out = res.stdout or b""
                    except Exception:
                        out = b""
                    try:
                        text = out.decode("utf-8", errors="replace")
                    except Exception:
                        text = ""
                    return ClipboardData(text=text)

            return MacOSClipboard()

        # Windows support: prefer built-ins (clip.exe for set, PowerShell for get).
        if sys.platform.startswith("win"):
            class WindowsClipboard:
                def _powershell_cmd(self) -> list[str]:
                    # Prefer Windows PowerShell if available; else PowerShell Core.
                    return ["powershell", "-NoProfile", "-Command"]

                def set_data(self, data: ClipboardData) -> None:
                    text = getattr(data, "text", "")
                    text = text.replace("\r\n", "\n").replace("\r", "\n")
                    win_text = text.replace("\n", "\r\n")
                    try:
                        # Use clip.exe, available on most Windows systems.
                        clip_path = shutil.which("clip") or "clip"
                        subprocess.run([clip_path], input=win_text.encode("utf-8"), check=False)
                        return
                    except Exception:
                        pass
                    # Fallback to PowerShell Set-Clipboard reading stdin.
                    try:
                        cmd = self._powershell_cmd() + [
                            "$in = [Console]::In.ReadToEnd(); Set-Clipboard -Value $in",
                        ]
                        subprocess.run(cmd, input=win_text.encode("utf-8"), check=False)
                    except Exception:
                        pass

                def get_data(self) -> ClipboardData:
                    # Use PowerShell Get-Clipboard.
                    text = ""
                    for exe in ("powershell", "pwsh"):
                        try:
                            if not shutil.which(exe):
                                continue
                            cmd = [exe, "-NoProfile", "-Command", "Get-Clipboard"]
                            res = subprocess.run(cmd, capture_output=True, check=False)
                            out = res.stdout or b""
                            text = out.decode("utf-8", errors="replace")
                            text = text.replace("\r\n", "\n").replace("\r", "\n")
                            break
                        except Exception:
                            continue
                    return ClipboardData(text=text)

            return WindowsClipboard()

        # Linux support: try wl-clipboard, xclip, then xsel.
        if sys.platform.startswith("linux") or sys.platform.startswith("freebsd"):
            class LinuxClipboard:
                def set_data(self, data: ClipboardData) -> None:
                    text = getattr(data, "text", "")
                    encoded = text.encode("utf-8")
                    # Prefer Wayland tools if present.
                    try:
                        if shutil.which("wl-copy"):
                            subprocess.run(["wl-copy", "-n"], input=encoded, check=False)
                            return
                    except Exception:
                        pass
                    # X11 options.
                    try:
                        if shutil.which("xclip"):
                            subprocess.run(["xclip", "-selection", "clipboard"], input=encoded, check=False)
                            return
                    except Exception:
                        pass
                    try:
                        if shutil.which("xsel"):
                            subprocess.run(["xsel", "-b", "-i"], input=encoded, check=False)
                            return
                    except Exception:
                        pass

                def get_data(self) -> ClipboardData:
                    text = ""
                    # Prefer Wayland tools if present.
                    try:
                        if shutil.which("wl-paste"):
                            res = subprocess.run(["wl-paste", "-n"], capture_output=True, check=False)
                            out = res.stdout or b""
                            text = out.decode("utf-8", errors="replace")
                            return ClipboardData(text=text)
                    except Exception:
                        pass
                    # X11 options.
                    try:
                        if shutil.which("xclip"):
                            res = subprocess.run(["xclip", "-selection", "clipboard", "-o"], capture_output=True, check=False)
                            out = res.stdout or b""
                            text = out.decode("utf-8", errors="replace")
                            return ClipboardData(text=text)
                    except Exception:
                        pass
                    try:
                        if shutil.which("xsel"):
                            res = subprocess.run(["xsel", "-b", "-o"], capture_output=True, check=False)
                            out = res.stdout or b""
                            text = out.decode("utf-8", errors="replace")
                            return ClipboardData(text=text)
                    except Exception:
                        pass
                    return ClipboardData(text=text)

            # If none of the commands exist, fall back to in-memory clipboard.
            if not (shutil.which("wl-copy") or shutil.which("xclip") or shutil.which("xsel") or shutil.which("wl-paste")):
                return InMemoryClipboard()
            return LinuxClipboard()

        # Fallback: in-memory clipboard only.
        return InMemoryClipboard()

    def _render_status(self) -> AnyFormattedText:
        path_text = f"File: {self.path}" if self.path else "File: (untitled)"
        message = self._status_text.strip()
        return f" {path_text}   Status: {message}"

    def _path_label_text(self) -> str:
        return f"File: {self.path}" if self.path else "File: (untitled)"

    def _create_toolbar(self) -> Container:
        cut_button = Button(
            _with_key_hint("Cut", str(KEYMAPS["cut"]["display"])),
            handler=self.cut_selection,
            left_symbol="",
            right_symbol="",
        )
        copy_button = Button(
            _with_key_hint("Copy", str(KEYMAPS["copy"]["display"])),
            handler=self.copy_selection,
            left_symbol="",
            right_symbol="",
        )
        paste_button = Button(
            _with_key_hint("Paste", str(KEYMAPS["paste"]["display"])),
            handler=self.paste_clipboard,
            left_symbol="",
            right_symbol="",
        )
        delete_button = Button(
            _with_key_hint("Delete", str(KEYMAPS["delete"]["display"])),
            handler=self.delete_selection,
            left_symbol="",
            right_symbol="",
        )
        undo_button = Button(
            _with_key_hint("Undo", str(KEYMAPS["undo"]["display"])),
            handler=self.undo_action,
            left_symbol="",
            right_symbol="",
        )
        redo_button = Button(
            _with_key_hint("Redo", str(KEYMAPS["redo"]["display"])),
            handler=self.redo_action,
            left_symbol="",
            right_symbol="",
        )

        spacer = Window(width=D(weight=1), height=1, char=" ")

        return VSplit(
            [
                Label("Qudix", style="class:toolbar-title"),
                undo_button,
                redo_button,
                cut_button,
                copy_button,
                paste_button,
                delete_button,
                spacer,
            ],
            padding=1,
            style="class:toolbar",
            height=1,
        )

    def _create_key_bindings(self) -> KeyBindings:
        kb = KeyBindings()

        @kb.add("c-x", eager=True)
        def _(event) -> None:
            # If no unsaved changes, exit immediately.
            if not self._dirty:
                event.app.exit()
                return
            # If unsaved, require a second confirmation press.
            if self._confirm_exit:
                event.app.exit()
            else:
                self._confirm_exit = True
                self._set_status(
                    "Warning! You are about to exit without saving. Ctrl + X will quit the program.",
                    error=True,
                )

        @kb.add("c-s")
        def _(event) -> None:
            self.save()

        # Toolbar action keymaps (conditionally enabled).
        if KEYMAPS_ENABLED and (binding := KEYMAPS["cut"]["binding"]):
            @kb.add(binding)  # type: ignore[arg-type]
            def _(event) -> None:
                self.cut_selection()

        if KEYMAPS_ENABLED and (binding := KEYMAPS["copy"]["binding"]):
            @kb.add(binding)  # type: ignore[arg-type]
            def _(event) -> None:
                self.copy_selection()

        if KEYMAPS_ENABLED and (binding := KEYMAPS["paste"]["binding"]):
            @kb.add(binding)  # type: ignore[arg-type]
            def _(event) -> None:
                self.paste_clipboard()

        if KEYMAPS_ENABLED and (binding := KEYMAPS["delete"]["binding"]):
            @kb.add(binding)  # type: ignore[arg-type]
            def _(event) -> None:
                self.delete_selection()

        @kb.add("backspace")
        def _(event) -> None:
            buffer = self.text_area.buffer
            if self._delete_active_selection():
                self._set_status("Deleted selection")
                self._ensure_unsaved_status()
                return
            before_text = buffer.text
            before_cursor = buffer.cursor_position
            try:
                buffer.delete_before_cursor(count=1)
            except Exception:
                self._set_status("Nothing to delete")
                return
            if buffer.text == before_text and buffer.cursor_position == before_cursor:
                self._set_status("Nothing to delete")
                return
            self._set_status("Deleted character")
            self._ensure_unsaved_status()

        @kb.add("escape")
        def _(event) -> None:
            event.app.layout.focus(self.text_area)
            self._set_status("Focus returned to editor")

        @kb.add("c-home")
        def _(event) -> None:
            self._toggle_scroll_top_fix()

        return kb

    def _create_application(self) -> Application:
        toolbar = self._create_toolbar()
        layout = HSplit(
            [
                toolbar,
                Window(height=1, char="─", style="class:divider", dont_extend_height=True),
                self.text_area,
                Window(height=1, char="─", style="class:divider", dont_extend_height=True),
                self.status_bar,
            ]
        )

        mouse_support_flag = True
        try:
            env_val = os.environ.get("QUDIX_MOUSE")
            if env_val is not None and env_val.strip().lower() in {"0", "false", "no", "off"}:
                mouse_support_flag = False
        except Exception:
            pass

        app = Application(
            layout=Layout(layout, focused_element=self.text_area),
            key_bindings=self._create_key_bindings(),
            full_screen=True,
            mouse_support=mouse_support_flag,
            style=APP_STYLE,
            clipboard=self.clipboard,
        )

        return app

    @property
    def application(self) -> Application:
        return self._application

    def run(self) -> None:
        self.application.run()

    def _set_status(self, message: str, *, error: bool = False, success: bool = False) -> None:
        self._status_text = f" {message}"
        if error:
            self._status_tag = "status.error"
        elif success:
            self._status_tag = "status.success"
        else:
            self._status_tag = "status"
        self.status_bar.style = f"class:{self._status_tag}"
        if hasattr(self, "_application"):
            self.application.invalidate()

    def _on_text_changed(self, _event=None) -> None:
        # Skip recording when we're programmatically restoring a state for undo/redo.
        if self._restoring_state:
            return
        self._dirty = True
        # Record previous snapshot for undo and clear redo on new edits.
        try:
            self._undo_stack.append((self._snapshot_text, self._snapshot_cursor))
        except Exception:
            # If snapshot was not initialized, skip silently.
            pass
        self._redo_stack.clear()
        # Update snapshot to current state.
        buffer = self.text_area.buffer
        self._snapshot_text = buffer.text
        self._snapshot_cursor = buffer.cursor_position
        self._set_status("Unsaved")
        # Cancel any pending exit confirmation once content changes.
        self._confirm_exit = False

    def _ensure_unsaved_status(self) -> None:
        if self._dirty:
            self._set_status("Unsaved")

    def _on_before_render(self, _app) -> None:
        """Keep cursor aligned with manual scrolling (mouse wheel, scrollbar)."""
        w = self.text_area.window
        ri = getattr(w, "render_info", None)
        if ri is None:
            return
        vscroll = ri.vertical_scroll
        win_h = ri.window_height
        buffer = self.text_area.buffer
        doc = buffer.document
        cursor_row = doc.cursor_position_row

        if self._last_vertical_scroll is None or self._last_cursor_row is None:
            self._last_vertical_scroll = vscroll
            self._last_cursor_row = cursor_row
            return

        if vscroll == self._last_vertical_scroll:
            self._last_cursor_row = cursor_row
            return

        cursor_moved = cursor_row != self._last_cursor_row
        is_windows = sys.platform.startswith("win")
        if is_windows and cursor_moved:
            # Windows PageUp/PageDown and keyboard navigation already move the cursor.
            # Skip our correction to avoid double-applying the movement.
            self._last_vertical_scroll = vscroll
            self._last_cursor_row = cursor_row
            return

        delta = vscroll - self._last_vertical_scroll
        lines = doc.lines
        max_row = len(lines) - 1
        col = doc.cursor_position_col
        cur_row = cursor_row
        if is_windows:
            # Windows mouse wheel events do not adjust the cursor automatically.
            # Force the cursor to the newly visible edge so the viewport keeps moving.
            if delta < 0:
                target_row = vscroll
            else:
                target_row = vscroll + max(0, win_h - 1)
        else:
            if delta < 0:
                target_row = max(vscroll, cur_row + delta)
            else:
                target_row = min(vscroll + max(0, win_h - 1), cur_row + delta)
        target_row = max(0, min(max_row, target_row))
        line_len = len(lines[target_row]) if 0 <= target_row <= max_row else 0
        target_col = col if col <= line_len else line_len
        try:
            new_index = doc.translate_row_col_to_index(target_row, target_col)
        except Exception:
            new_index = buffer.cursor_position
        buffer.cursor_position = new_index

        self._last_vertical_scroll = vscroll
        self._last_cursor_row = doc.cursor_position_row

    def _current_selection_range(self) -> Optional[tuple[int, int]]:
        document = self.text_area.buffer.document
        sel = document.selection_range()
        if not sel:
            return None
        start, end = sel
        if start == end:
            return None
        if start > end:
            start, end = end, start
        return start, end

    def _set_clipboard_text(self, text: str) -> None:
        data = ClipboardData(text=text)
        clipboards = []
        try:
            clipboards.append(get_app().clipboard)
        except Exception:
            pass
        app_clipboard = getattr(self.application, "clipboard", None)
        if app_clipboard:
            clipboards.append(app_clipboard)
        clipboards.append(self.clipboard)

        seen: set[int] = set()
        for clip in clipboards:
            if clip is None:
                continue
            clip_id = id(clip)
            if clip_id in seen:
                continue
            seen.add(clip_id)
            try:
                clip.set_data(data)
            except Exception:
                continue

    def _toggle_scroll_top_fix(self) -> None:
        buffer = self.text_area.buffer
        if self._scroll_fix_prev_cursor_pos is None:
            self._scroll_fix_prev_cursor_pos = buffer.cursor_position
            buffer.cursor_position = 0
            self._set_status("Cursor moved to top (Ctrl+Home again to restore)")
        else:
            buffer.cursor_position = self._scroll_fix_prev_cursor_pos
            self._scroll_fix_prev_cursor_pos = None
            self._set_status("Cursor position restored")

    def _on_mouse_scroll_up(self) -> None:
        buffer = self.text_area.buffer
        if self._scroll_fix_prev_cursor_pos is None:
            self._scroll_fix_prev_cursor_pos = buffer.cursor_position
            buffer.cursor_position = 0

    def _on_mouse_scroll_down(self) -> None:
        if self._scroll_fix_prev_cursor_pos is not None:
            self.text_area.buffer.cursor_position = self._scroll_fix_prev_cursor_pos
            self._scroll_fix_prev_cursor_pos = None

    def cut_selection(self) -> None:
        buffer = self.text_area.buffer
        selection_range = self._current_selection_range()
        has_user_selection = selection_range is not None
        if not has_user_selection:
            if not buffer.text:
                self._set_status("Nothing to cut")
                return
            self._select_current_line(include_line_break=True)
            selection_range = self._current_selection_range()
        if not selection_range:
            self._set_status("Nothing to cut")
            return
        start, end = selection_range
        text = buffer.text[start:end]
        self._set_clipboard_text(text)
        buffer.cursor_position = start
        buffer.delete(count=end - start)
        buffer.selection_state = None
        self._set_status("Cut selection" if has_user_selection else "Cut current line")
        self._ensure_unsaved_status()

    def copy_selection(self) -> None:
        buffer = self.text_area.buffer
        selection_range = self._current_selection_range()
        has_user_selection = selection_range is not None
        if not has_user_selection:
            if not buffer.text:
                self._set_status("Nothing to copy")
                return
            self._select_current_line(include_line_break=False)
            selection_range = self._current_selection_range()
        if not selection_range:
            self._set_status("Nothing to copy")
            return
        start, end = selection_range
        text = buffer.text[start:end]
        self._set_clipboard_text(text)
        if not has_user_selection:
            buffer.selection_state = None
        self._set_status("Copied selection" if has_user_selection else "Copied current line")

    def paste_clipboard(self) -> None:
        buffer = self.text_area.buffer
        before_text = buffer.text
        before_cursor = buffer.cursor_position
        try:
            buffer.paste_from_clipboard()
        except Exception:
            buffer = self.text_area.buffer
        if buffer.text == before_text and buffer.cursor_position == before_cursor:
            clip = None
            try:
                clip = get_app().clipboard
            except Exception:
                clip = None
            if not clip:
                clip = getattr(self.application, "clipboard", None)
            if not clip:
                clip = self.clipboard
            data = clip.get_data() if clip else self.clipboard.get_data()
            if not getattr(data, "text", ""):
                try:
                    from prompt_toolkit.clipboard.pyperclip import PyperclipClipboard
                    sys_clip = PyperclipClipboard()
                    sys_data = sys_clip.get_data()
                    if getattr(sys_data, "text", ""):
                        data = sys_data
                except Exception:
                    pass
            if not getattr(data, "text", ""):
                self._set_status("Clipboard empty", error=True)
                return
            if sys.platform.startswith("win"):
                try:
                    t = getattr(data, "text", "")
                    if t:
                        t = t.replace("\r\n", "\n").replace("\r", "\n")
                        data = ClipboardData(text=t)
                except Exception:
                    pass
            buffer.paste_clipboard_data(data)
        self._set_status("Pasted from clipboard")
        self._ensure_unsaved_status()

    def delete_selection(self) -> None:
        buffer = self.text_area.buffer
        if buffer.selection_state:
            if self._delete_active_selection():
                self._set_status("Deleted selection")
                self._ensure_unsaved_status()
            else:
                buffer.selection_state = None
                self._set_status("Nothing selected", error=True)
            return
        if not buffer.text:
            self._set_status("Nothing to delete")
            return
        self._select_current_line(include_line_break=True)
        if self._delete_active_selection():
            self._set_status("Deleted current line")
            self._ensure_unsaved_status()
        else:
            self._set_status("Nothing to delete")

    def _restore_state(self, text: str, cursor: int) -> None:
        """Restore the buffer to a specific state without recording it as a new edit."""
        self._restoring_state = True
        buffer = self.text_area.buffer
        buffer.text = text
        # Clamp cursor within bounds of the new text.
        cursor = max(0, min(len(buffer.text), cursor))
        buffer.cursor_position = cursor
        self._restoring_state = False

    def undo_action(self) -> None:
        if not self._undo_stack:
            self._set_status("Nothing to undo")
            return
        # Push current snapshot to redo, pop and restore the previous state.
        self._redo_stack.append((self._snapshot_text, self._snapshot_cursor))
        prev_text, prev_cursor = self._undo_stack.pop()
        self._restore_state(prev_text, prev_cursor)
        # Update snapshot to restored state.
        self._snapshot_text = prev_text
        self._snapshot_cursor = prev_cursor
        self._set_status("Undid change")
        self._ensure_unsaved_status()

    def redo_action(self) -> None:
        if not self._redo_stack:
            self._set_status("Nothing to redo")
            return
        # Push current snapshot to undo, pop and restore the next state.
        self._undo_stack.append((self._snapshot_text, self._snapshot_cursor))
        next_text, next_cursor = self._redo_stack.pop()
        self._restore_state(next_text, next_cursor)
        # Update snapshot to restored state.
        self._snapshot_text = next_text
        self._snapshot_cursor = next_cursor
        self._set_status("Redid change")
        self._ensure_unsaved_status()

    def save(self) -> None:
        if not self.path:
            self._set_status("No file path supplied; relaunch with a file path to save.", error=True)
            return
        try:
            self.path.write_text(self.text_area.text)
        except OSError as exc:
            self._set_status(f"Failed to save: {exc}", error=True)
            return
        self._dirty = False
        self._confirm_exit = False
        self._set_status(f"Saved to {self.path}", success=True)

    def _select_current_line(self, *, include_line_break: bool) -> None:
        buffer = self.text_area.buffer
        document = buffer.document
        row = document.cursor_position_row
        start = document.translate_row_col_to_index(row, 0)
        line_text = document.lines[row]
        end = document.translate_row_col_to_index(row, len(line_text))

        # Include the newline when asked and when it exists.
        if include_line_break and end < len(buffer.text) and buffer.text[end : end + 1] == "\n":
            end += 1

        buffer.cursor_position = start
        buffer.start_selection(selection_type=SelectionType.CHARACTERS)
        buffer.cursor_position = end

    def update_path(self, new_path: Path) -> None:
        self.path = new_path
        self._set_status(f"Target file set to {self.path}")

    def _delete_active_selection(self) -> bool:
        """Remove the currently selected text, returning True when a deletion occurred."""
        document = self.text_area.buffer.document
        selection_range = document.selection_range()
        if not selection_range:
            return False

        start, end = selection_range
        if start == end:
            return False
        if start > end:
            start, end = end, start

        buffer = self.text_area.buffer
        buffer.cursor_position = start
        buffer.delete(count=end - start)
        buffer.selection_state = None
        return True


def _load_file_contents(path: Path) -> tuple[str, Optional[str]]:
    if not path.exists():
        return "", None
    try:
        return path.read_text(), None
    except OSError as exc:
        return "", f"Unable to read {path}: {exc}"


def _prompt_for_filename() -> Optional[str]:
    """Show a dialog to ask the user for a filename.

    Returns the provided filename (str) when OK/Enter is pressed, or None when
    cancelled or Ctrl+X is pressed.
    """
    # Single-line input field that accepts with Enter.
    def _on_accept(_buff) -> None:
        do_ok()

    input_field = TextArea(
        height=1,
        multiline=False,
        focus_on_click=True,
        style="class:textarea",
        accept_handler=_on_accept,
    )

    def do_ok() -> None:
        # Return the stripped filename; empty becomes "" which the caller treats as cancel.
        get_app().exit(result=input_field.text.strip())

    def do_cancel() -> None:
        get_app().exit(result=None)

    ok_button = Button(text="OK", handler=do_ok)
    cancel_button = Button(text="Cancel", handler=do_cancel)

    body = HSplit(
        [
            Label(text="Create a file with name:"),
            input_field,
        ],
        padding=1,
    )

    dialog = Dialog(
        title="Create File",
        body=body,
        buttons=[ok_button, cancel_button],
        with_background=True,
    )

    # Key bindings for the dialog stage.
    kb = KeyBindings()

    @kb.add("c-x", eager=True)
    def _exit_program(event) -> None:  # Ctrl+X should immediately quit.
        event.app.exit(result=None)

    # Pressing Enter in the input field triggers OK (since multiline=False, Enter
    # is handled via accept, but we still ensure focus starts in the input field).

    app = Application(
        layout=Layout(dialog, focused_element=input_field),
        key_bindings=kb,
        full_screen=True,
        mouse_support=True,
        style=APP_STYLE,
    )

    return app.run()


def run(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Launch Qudix.")
    parser.add_argument("--version", action="store_true", help="Show Qudix version and exit.")
    parser.add_argument("path", nargs="?", help="Optional file path to open.")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    if args.version:
        print(f"qudix {__version__}")
        return

    file_path = Path(args.path).expanduser() if args.path else None
    initial_text = ""
    load_error: Optional[str] = None

    # When no path is provided, prompt for a filename in a dialog.
    if file_path is None:
        filename = _prompt_for_filename()
        if not filename:
            # User cancelled (or empty input) -> exit immediately.
            return
        # Expand and set the chosen path.
        file_path = Path(filename).expanduser()
        # Try to create (touch) the file now; report any error in the editor status.
        try:
            # Ensure parent directory exists before touching; if it doesn't, touching will fail.
            file_path.touch(exist_ok=True)
        except OSError as exc:
            load_error = f"Failed to create file '{file_path}': {exc}"
        # Continue with normal flow (loading contents if creation succeeded or file existed).
        initial_text, _ = _load_file_contents(file_path)
    else:
        initial_text, load_error = _load_file_contents(file_path)

    editor = QudixApplication(initial_text=initial_text, file_path=file_path)
    if load_error:
        editor._set_status(load_error, error=True)
    editor.run()


if __name__ == "__main__":
    run()
