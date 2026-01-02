"""
59CHAT - Zero-Trace Terminal Chat
Version: 0.3.7
Agent: ClaudeOpus

Changes in v0.3.7:
- Fixed: Window focus detection for read receipts
- Added: Real-time server deletion when messages expire
- Added: Desktop notifications (plyer)
- Added: /file command for file sharing
- Improved: Client-server sync for true zero-trace
"""

import asyncio
import os
import sys
import argparse
import random
import string
import base64
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Dict

import httpx
import pyperclip
from textual.app import App, ComposeResult
from textual.widgets import Input, Static, Footer, DirectoryTree
from textual.containers import Vertical, Horizontal
from textual.reactive import reactive
from textual.binding import Binding
from textual.screen import ModalScreen
from rich.text import Text

# Try to import notification library
try:
    from plyer import notification as desktop_notify
    HAS_NOTIFICATIONS = True
except ImportError:
    HAS_NOTIFICATIONS = False

# --- CONFIGURATION ---
VERSION = "0.3.7"
APP_NAME = "59chat"
INTERNAL_PKG = "chat59"
SUPABASE_URL = "https://xdqxebyyjxklzisddmwl.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhkcXhlYnl5anhrbHppc2RkbXdsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk4Mzc0NDAsImV4cCI6MjA3NTQxMzQ0MH0.37JtLjN6mGfdac-t-cqNADa8OQlYIgSkZEFSngwxlM0"
MAX_FILE_SIZE = 50 * 1024  # 50KB max for base64 encoded files

CSS = """
Screen { background: #000000; color: #FFFFFF; }
#header { dock: top; height: 3; background: #000000; padding: 0 2; }
#header-info { width: 1fr; content-align: left middle; }
#header-status { width: auto; content-align: right middle; color: #22C55E; text-style: bold; }
#chat-scroll { height: 1fr; padding: 1 2; }
#bottom-bar { dock: bottom; height: auto; background: #000000; }
#input-row { height: 1; background: #0A0A0A; padding: 0 2; }
#input-prefix { width: auto; color: #FFFFFF; text-style: bold; }
Input { background: transparent; border: none; width: 1fr; height: 1; color: #FFFFFF; padding: 0; }
Input:focus { border: none; }
.message-row { width: 100%; height: auto; margin-bottom: 1; }
.message-row.own { align-horizontal: right; }
.message-row.other { align-horizontal: left; }
.msg-box { width: auto; min-width: 30; max-width: 80%; height: auto; padding: 0 1; }
.msg-box.own { background: #0A0A0A; }
.msg-box.other { background: #111111; }
.file-msg { color: #22C55E; }

FilePickerScreen { align: center middle; }
#file-picker-container { width: 60; height: 20; background: #111111; border: solid #333333; padding: 1; }
#file-picker-title { text-align: center; text-style: bold; margin-bottom: 1; }
DirectoryTree { height: 1fr; }
"""


def parse_iso_dt(s: str) -> datetime:
    try:
        clean_s = s.replace('Z', '+00:00').split('+')[0]
        if '.' in clean_s:
            base, ms = clean_s.split('.')
            clean_s = f"{base}.{ms[:6]}"
        return datetime.fromisoformat(f"{clean_s}+00:00")
    except:
        return datetime.now(timezone.utc)


def send_notification(title: str, message: str):
    """Send desktop notification if available."""
    if not HAS_NOTIFICATIONS:
        return
    try:
        desktop_notify.notify(
            title=title,
            message=message,
            app_name="59CHAT",
            timeout=5
        )
    except:
        pass


class SupabaseClient:
    """Optimized Supabase client with connection reuse."""

    def __init__(self):
        self.base_url = f"{SUPABASE_URL}/rest/v1"
        self.headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=10.0)
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def get_messages(self, room_id: str) -> List[Dict]:
        client = await self._get_client()
        url = f"{self.base_url}/messages?room_id=eq.{room_id}&order=created_at.asc"
        res = await client.get(url, headers=self.headers)
        return res.json() if res.status_code == 200 else []

    async def send_message(self, room_id: str, nickname: str, content: str):
        client = await self._get_client()
        data = {"room_id": room_id, "nickname": nickname, "content": content}
        await client.post(f"{self.base_url}/messages", headers=self.headers, json=data)

    async def mark_read(self, msg_ids: List[str]):
        if not msg_ids:
            return
        client = await self._get_client()
        now = datetime.now(timezone.utc).isoformat()
        ids_str = ",".join(f'"{mid}"' for mid in msg_ids)
        url = f"{self.base_url}/messages?id=in.({ids_str})"
        await client.patch(url, headers=self.headers, json={"read_at": now})

    async def delete_message(self, msg_id: str):
        """Delete a single message from server (when it expires)."""
        client = await self._get_client()
        url = f"{self.base_url}/messages?id=eq.{msg_id}"
        headers = {**self.headers, "Prefer": "return=minimal"}
        await client.delete(url, headers=headers)

    async def delete_user_messages(self, room_id: str, nickname: str):
        """Delete all messages from a user when they exit (Exit Wipe)."""
        client = await self._get_client()
        url = f"{self.base_url}/messages?room_id=eq.{room_id}&nickname=eq.{nickname}"
        headers = {**self.headers, "Prefer": "return=minimal"}
        await client.delete(url, headers=headers)


class FilePickerScreen(ModalScreen):
    """Modal screen for file selection."""

    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def compose(self) -> ComposeResult:
        with Vertical(id="file-picker-container"):
            yield Static("SELECT FILE (ESC to cancel)", id="file-picker-title")
            yield DirectoryTree(".", id="file-tree")

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected):
        self.callback(str(event.path))
        self.dismiss()

    def action_cancel(self):
        self.callback(None)
        self.dismiss()


class MessageWidget(Static):
    """Lightweight message widget."""

    def __init__(self, msg: Dict, is_own: bool, is_file: bool = False):
        super().__init__()
        self.msg = msg
        self.is_own = is_own
        self.is_file = is_file
        self.classes = "msg-box own" if is_own else "msg-box other"
        if is_file:
            self.classes += " file-msg"

    def render(self) -> Text:
        now = datetime.now(timezone.utc)
        read_at = self.msg.get('read_at')

        # Status indicator
        if read_at:
            read_dt = parse_iso_dt(read_at)
            rem = 59 - (now - read_dt).total_seconds()
            if rem <= 0:
                return Text("")
            status = f"● {int(rem)}s"
            status_style = "bold green" if rem > 10 else "bold red"
        else:
            status = "○"
            status_style = "dim"

        # Time
        dt_utc = parse_iso_dt(self.msg['created_at'])
        dt_local = dt_utc.astimezone()
        time_str = dt_local.strftime("%H:%M")

        # Build text
        text = Text()
        nick_style = "bold white" if self.is_own else "bold #666666"
        text.append("› ", style="bold white")
        text.append(self.msg['nickname'], style=nick_style)
        text.append(f" {time_str} ", style="dim")
        text.append(status, style=status_style)
        text.append("\n")

        content = self.msg['content']
        if self.is_file or content.startswith("[FILE:"):
            text.append(content, style="bold #22C55E")
        else:
            text.append(content, style="white")

        return text

    def get_remaining_seconds(self) -> Optional[float]:
        """Get remaining seconds before expiry, or None if not read."""
        read_at = self.msg.get('read_at')
        if not read_at:
            return None
        read_dt = parse_iso_dt(read_at)
        return 59 - (datetime.now(timezone.utc) - read_dt).total_seconds()

    def should_remove(self) -> bool:
        rem = self.get_remaining_seconds()
        return rem is not None and rem <= 0


class FiftyNineChat(App):
    CSS = CSS
    status_text = reactive("")

    BINDINGS = [
        Binding("ctrl+c", "quit", "QUIT"),
        Binding("ctrl+r", "new_room", "NEW ROOM"),
        Binding("ctrl+l", "copy_invite", "INVITE"),
        Binding("ctrl+f", "file_picker", "FILE"),
    ]

    def __init__(self, room_id: Optional[str] = None, is_new: bool = False):
        super().__init__()
        self.api = SupabaseClient()
        self.room_id = room_id or ""
        self.nickname = ""
        self.running = True
        self.active_users = 1
        self.is_new_session = is_new
        self.displayed_messages: Dict[str, MessageWidget] = {}
        self.window_focused = True
        self.known_nicknames: set = set()
        self.pending_deletions: set = set()  # Track messages to delete from server

    def compose(self) -> ComposeResult:
        with Horizontal(id="header"):
            yield Static(id="header-info")
            yield Static(id="header-status")
        from textual.containers import VerticalScroll
        yield VerticalScroll(id="chat-scroll")
        with Vertical(id="bottom-bar"):
            with Horizontal(id="input-row"):
                yield Static("› ", id="input-prefix")
                yield Input(placeholder="Type message... (/file to send file)", id="message-input")
            yield Footer()

    def on_mount(self) -> None:
        try:
            self.nickname = self._generate_nickname()
            if not self.room_id:
                self.room_id = self._generate_room_id()
                self.is_new_session = True

            self._update_header()
            self._add_system_message("**59CHAT** — Messages vanish 59s after read. Ctrl+F to send file.")

            # Global timer for UI refresh and expiry checks
            self.set_interval(1.0, self._global_tick)

            # Background sync
            asyncio.create_task(self._sync_loop())

            if self.is_new_session:
                asyncio.create_task(self.action_copy_invite())

            self.query_one("#message-input").focus()
        except Exception as e:
            self.notify(f"Init failed: {e}", severity="error")

    def on_app_blur(self) -> None:
        """App lost focus."""
        self.window_focused = False

    def on_app_focus(self) -> None:
        """App gained focus."""
        self.window_focused = True

    def _global_tick(self) -> None:
        """Refresh UI and handle expired messages."""
        to_remove = []

        for mid, widget in self.displayed_messages.items():
            if widget.should_remove():
                to_remove.append(mid)
                # Queue for server deletion
                if not mid.startswith('sys-'):
                    self.pending_deletions.add(mid)
            else:
                widget.refresh()

        for mid in to_remove:
            widget = self.displayed_messages.pop(mid, None)
            if widget and widget.parent:
                widget.parent.remove()

    def watch_status_text(self, text: str):
        try:
            self.query_one("#header-status").update(text)
        except:
            pass

    async def on_input_submitted(self, event: Input.Submitted):
        content = event.value.strip()
        if not content:
            return

        # Handle /file command
        if content.lower() == "/file":
            event.input.value = ""
            self.action_file_picker()
            return

        # Character limit
        if len(content) > 900:
            self.notify("Message too long (max 900 chars)", severity="warning")
            return

        try:
            await self.api.send_message(self.room_id, self.nickname, content)
            event.input.value = ""
        except Exception as e:
            self.notify(f"Send failed: {e}", severity="error")

    def action_file_picker(self):
        """Open file picker modal."""
        def on_file_selected(path: Optional[str]):
            if path:
                asyncio.create_task(self._send_file(path))

        self.push_screen(FilePickerScreen(on_file_selected))

    async def _send_file(self, file_path: str):
        """Send file as base64 encoded message."""
        try:
            path = Path(file_path)
            if not path.exists():
                self.notify("File not found", severity="error")
                return

            size = path.stat().st_size
            if size > MAX_FILE_SIZE:
                self.notify(f"File too large (max {MAX_FILE_SIZE // 1024}KB)", severity="error")
                return

            with open(path, "rb") as f:
                data = base64.b64encode(f.read()).decode()

            # Format: [FILE:filename.ext]base64data
            content = f"[FILE:{path.name}]{data}"
            await self.api.send_message(self.room_id, self.nickname, content)
            self.notify(f"File sent: {path.name}", severity="information")
        except Exception as e:
            self.notify(f"File send failed: {e}", severity="error")

    def _generate_nickname(self) -> str:
        adj = ["Cold", "Swift", "Pure", "Thin", "Hard", "Dark", "Sharp", "Calm"]
        noun = ["Grid", "Line", "Type", "Form", "Node", "Void", "Pulse", "Edge"]
        return f"{random.choice(adj)}{random.choice(noun)}"

    def _generate_room_id(self) -> str:
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    def _update_header(self):
        focus_indicator = "●" if self.window_focused else "○"
        info = f"ROOM [bold]{self.room_id}[/]  │  YOU [bold]{self.nickname}[/]  │  ONLINE [bold green]{self.active_users}[/]  {focus_indicator}"
        self.query_one("#header-info").update(info)

    def _add_system_message(self, content: str):
        msg = {
            'id': f'sys-{random.randint(1000,9999)}',
            'nickname': 'SYSTEM',
            'content': content,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'read_at': datetime.now(timezone.utc).isoformat()
        }
        self._add_message_widget(msg)

    def _add_message_widget(self, msg: Dict):
        mid = str(msg['id'])
        if mid in self.displayed_messages:
            # Update existing message data
            self.displayed_messages[mid].msg = msg
            return

        scroll = self.query_one("#chat-scroll")
        is_own = msg['nickname'] == self.nickname
        is_file = msg['content'].startswith("[FILE:")

        row = Horizontal(classes=f"message-row {'own' if is_own else 'other'}")
        widget = MessageWidget(msg, is_own, is_file)

        self.displayed_messages[mid] = widget
        scroll.mount(row)
        row.mount(widget)
        scroll.scroll_end(animate=False)

    async def _sync_loop(self):
        """Main sync loop with proper focus handling."""
        while self.running:
            try:
                # Delete expired messages from server
                if self.pending_deletions:
                    for mid in list(self.pending_deletions):
                        try:
                            await self.api.delete_message(mid)
                            self.pending_deletions.discard(mid)
                        except:
                            pass

                data = await self.api.get_messages(self.room_id)

                if isinstance(data, list):
                    current_nicknames = {m['nickname'] for m in data}

                    # Check for user exits
                    left_users = self.known_nicknames - current_nicknames - {self.nickname, 'SYSTEM'}
                    for user in left_users:
                        to_remove = [mid for mid, w in self.displayed_messages.items()
                                     if w.msg.get('nickname') == user]
                        for mid in to_remove:
                            widget = self.displayed_messages.pop(mid, None)
                            if widget and widget.parent:
                                widget.parent.remove()

                    # Check for new users (for notification)
                    new_users = current_nicknames - self.known_nicknames - {self.nickname, 'SYSTEM'}
                    if new_users and not self.window_focused:
                        send_notification("59CHAT", f"{', '.join(new_users)} joined the room")

                    self.known_nicknames = current_nicknames
                    self.active_users = len(current_nicknames)
                    self._update_header()

                    # Track new messages for notification
                    new_message_count = 0

                    for m in data:
                        mid = str(m['id'])
                        is_new = mid not in self.displayed_messages

                        # Add/update message in UI
                        self._add_message_widget(m)

                        # Count new messages from others
                        if is_new and m['nickname'] != self.nickname and m['nickname'] != 'SYSTEM':
                            new_message_count += 1

                    # Send notification for new messages if window not focused
                    if new_message_count > 0 and not self.window_focused:
                        send_notification("59CHAT", f"{new_message_count} new message(s)")

                    # CRITICAL: Only mark as read if window IS FOCUSED
                    if self.window_focused:
                        unread = [
                            str(m['id']) for m in data
                            if m['nickname'] != self.nickname and m.get('read_at') is None
                        ]
                        if unread:
                            await self.api.mark_read(unread)

                await asyncio.sleep(1.5)
            except Exception:
                await asyncio.sleep(3)

    async def action_copy_invite(self):
        sep = " ; " if sys.platform == "win32" else " && "
        py = "python" if sys.platform == "win32" else "python3"
        cmd = f"{py} -m pip install -U {APP_NAME}{sep}{py} -m {INTERNAL_PKG} --join {self.room_id}"
        try:
            pyperclip.copy(cmd)
            self.status_text = "INVITE COPIED!"
            await asyncio.sleep(2)
            self.status_text = ""
        except:
            pass

    def action_new_room(self):
        self.room_id = self._generate_room_id()
        scroll = self.query_one("#chat-scroll")
        for child in list(scroll.children):
            child.remove()
        self.displayed_messages.clear()
        self.known_nicknames.clear()
        self._update_header()
        self._add_system_message(f"New room: **{self.room_id}**")
        asyncio.create_task(self.action_copy_invite())

    async def action_quit(self) -> None:
        """Exit Wipe: Delete all user's messages before quitting."""
        self.running = False
        try:
            await self.api.delete_user_messages(self.room_id, self.nickname)
        except:
            pass
        finally:
            await self.api.close()
        self.exit()

    def on_unmount(self) -> None:
        self.running = False


def main_func():
    parser = argparse.ArgumentParser(description="59CHAT - Zero-trace terminal chat")
    parser.add_argument("--join", "-j", help="Room ID to join")
    parser.add_argument("--new", "-n", action="store_true", help="Create new room")
    parser.add_argument("--version", "-v", action="version", version=f"59chat {VERSION}")
    args = parser.parse_args()

    app = FiftyNineChat(room_id=None if args.new else args.join, is_new=args.new)
    app.run()


if __name__ == "__main__":
    main_func()
