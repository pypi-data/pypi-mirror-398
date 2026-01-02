import asyncio
import os
import sys
import argparse
import subprocess
import json
import urllib.request
from datetime import datetime, timezone
from typing import Optional, Set, List, Dict
from textual.app import App, ComposeResult
from textual.widgets import Input, Static, Footer
from textual.containers import Vertical, Horizontal, Container, VerticalScroll
from textual.reactive import reactive
from textual.binding import Binding
from rich.markdown import Markdown
from supabase import create_client, Client
import random
import string
import pyperclip

# --- CONFIGURATION ---
VERSION = "0.1.9"
APP_NAME = "59chat"
CMD_NAME = "59chat"
SUPABASE_URL = "https://xdqxebyyjxklzisddmwl.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhkcXhlYnl5anhrbHppc2RkbXdsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk4Mzc0NDAsImV4cCI6MjA3NTQxMzQ0MH0.37JtLjN6mGfdac-t-cqNADa8OQlYIgSkZEFSngwxlM0"

CSS = """
Screen {
    background: #000000;
    color: #FFFFFF;
}

#header {
    dock: top;
    height: 4;
    background: #000000;
    padding: 1 2;
}

#header-info {
    width: 1fr;
    content-align: left middle;
}

#header-status {
    width: auto;
    content-align: right middle;
    color: #22C55E;
    text-style: bold;
}

#chat-scroll {
    height: 1fr;
    padding: 1 2;
}

#bottom-bar {
    dock: bottom;
    height: auto;
    background: #000000;
}

#input-row {
    height: 1;
    background: #0A0A0A;
    padding: 0 2;
}

#input-prefix {
    width: auto;
    color: #FFFFFF;
    text-style: bold;
}

Input {
    background: transparent;
    border: none;
    width: 1fr;
    height: 1;
    color: #FFFFFF;
    padding: 0;
}

Input:focus {
    border: none;
}

.message-item {
    width: 100%;
    height: auto;
    margin-bottom: 2;
}

.message-item.own {
    align-horizontal: right;
}

.message-item.other {
    align-horizontal: left;
}

.msg-container {
    width: auto;
    min-width: 40%;
    max-width: 80%;
    height: auto;
}

.msg-header {
    height: 1;
    color: #FFFFFF;
}

.msg-content {
    height: auto;
    padding: 0 1;
}

.msg-line {
    height: 1;
    color: #525252;
}
"""

class MessageItem(Vertical):
    def __init__(self, m, is_own):
        super().__init__(classes=f"message-item {'own' if is_own else 'other'}")
        self.m = m
        self.is_own = is_own
        self.rendered_markdown = False

    def compose(self) -> ComposeResult:
        with Vertical(classes="msg-container"):
            yield Static(id="msg-header", classes="msg-header", markup=True)
            yield Static(id="msg-content", classes="msg-content")
            yield Static(id="msg-line", classes="msg-line", markup=True)

    def on_mount(self):
        self.set_interval(0.5, self.refresh_msg)
        self.refresh_msg()

    def refresh_msg(self):
        now = datetime.now(timezone.utc)
        read_at = self.m.get('read_at')
        
        status = " [dim]○[/]"
        if read_at:
            read_dt = datetime.fromisoformat(read_at.replace('Z', '+00:00'))
            rem = 59 - (now - read_dt).total_seconds()
            if rem <= 0:
                self.remove()
                return
            status = f" [bold #22C55E]●[/] [bold #EF4444]{int(rem)}s[/]"

        user_style = "bold #FFFFFF" if self.is_own else "bold #525252"
        prefix = "› "
        time_part = self.m['created_at'].split('T')[1][:5]
        
        header_text = f"[{user_style}]{prefix}{self.m['nickname']}[/] [dim]{time_part}[/]{status}"
        self.query_one("#msg-header").update(header_text)
        
        if not self.rendered_markdown:
            self.query_one("#msg-content").update(Markdown(self.m['content']))
            self.rendered_markdown = True
        
        # Responsive Çizgi Mantığı (Önce Yatayda Genişle)
        edge_padding = 4
        screen_w = (self.app.size.width or 80) - edge_padding
        w_min = int(screen_w * 0.4)
        w_max = int(screen_w * 0.8)
        
        # İçerik uzunluğu tahmini
        lines = self.m['content'].split('\n')
        max_line = max(len(l) for l in lines) if lines else 0
        target_w = max(w_min, min(max_line + 10, w_max))
        
        container = self.query_one(".msg-container")
        container.styles.width = target_w
        self.query_one("#msg-line").update(f"[dim]{'─' * target_w}[/]")

class FiftyNineChat(App):
    CSS = CSS
    status_text = reactive("")
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "QUIT"),
        Binding("ctrl+r", "new_room", "NEW ROOM"),
        Binding("ctrl+l", "copy_invite", "INVITE"),
    ]
    
    def __init__(self, room_id: Optional[str] = None, is_new: bool = False):
        super().__init__()
        self.supabase: Optional[Client] = None
        self.room_id = room_id or ""
        self.nickname = ""
        self.running = True
        self.active_users = 1
        self.is_new_session = is_new
        self.displayed_ids = set()

    def compose(self) -> ComposeResult:
        with Horizontal(id="header"):
            yield Static(id="header-info")
            yield Static(id="header-status")
        yield VerticalScroll(id="chat-scroll")
        with Vertical(id="bottom-bar"):
            with Horizontal(id="input-row"):
                yield Static("› ", id="input-prefix")
                yield Input(placeholder="Type message...", id="message-input")
            yield Footer()

    def on_mount(self) -> None:
        try:
            self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            self.nickname = self._generate_nickname()
            if not self.room_id:
                self.room_id = self._generate_room_id()
                self.is_new_session = True
            
            self._update_header()
            
            welcome_msg = {
                'id': 'welcome-msg',
                'nickname': 'SYSTEM',
                'content': '**WELCOME TO 59CHAT**\nMessages vanish in 59s. Type and press Enter.',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'read_at': datetime.now(timezone.utc).isoformat()
            }
            self._add_message_to_scroll(welcome_msg)

            asyncio.create_task(self._watch_messages())
            asyncio.create_task(self._mark_as_read())
            asyncio.create_task(self._presence_heartbeat())
            
            if self.is_new_session:
                asyncio.create_task(self.action_copy_invite())
                
            self.query_one("#message-input").focus()
        except Exception as e:
            self.notify(f"Init failed: {e}", severity="error")

    def watch_status_text(self, text: str):
        try:
            self.query_one("#header-status").update(text)
        except: pass

    async def on_input_submitted(self, event: Input.Submitted):
        content = event.value.strip()
        if not content or not self.supabase: return
        try:
            self.supabase.table('messages').insert({
                'room_id': self.room_id,
                'nickname': self.nickname,
                'content': content
            }).execute()
            event.input.value = ""
        except: pass

    def _generate_nickname(self) -> str:
        adj = ["Cold", "Swift", "Pure", "Thin", "Hard", "Dark"]
        noun = ["Grid", "Line", "Type", "Form", "Node", "Void"]
        return f"{random.choice(adj)}{random.choice(noun)}"

    def _generate_room_id(self) -> str:
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    def _update_header(self):
        info = f"ROOM [bold #FFFFFF]{self.room_id}[/]  │  USER [bold #FFFFFF]{self.nickname}[/]  │  ONLINE [bold #22C55E]{self.active_users}[/]"
        self.query_one("#header-info").update(info)

    def _add_message_to_scroll(self, m):
        mid = m['id']
        if mid not in self.displayed_ids:
            self.displayed_ids.add(mid)
            scroll = self.query_one("#chat-scroll")
            is_own = m['nickname'] == self.nickname
            msg_widget = MessageItem(m, is_own)
            scroll.mount(msg_widget)
            scroll.scroll_end(animate=False)

    async def _presence_heartbeat(self):
        while self.running and self.supabase:
            try:
                res = self.supabase.table('messages').select('nickname').eq('room_id', self.room_id).execute()
                self.active_users = max(1, len({m['nickname'] for m in res.data}))
                self._update_header()
                await asyncio.sleep(10)
            except: await asyncio.sleep(10)

    async def _watch_messages(self):
        while self.running and self.supabase:
            try:
                res = self.supabase.table('messages').select('*').eq('room_id', self.room_id).order('created_at').execute()
                for m in res.data:
                    self._add_message_to_scroll(m)
                await asyncio.sleep(1)
            except: await asyncio.sleep(2)

    async def _mark_as_read(self):
        while self.running and self.supabase:
            try:
                res = self.supabase.table('messages').select('id, nickname').eq('room_id', self.room_id).is_('read_at', 'null').execute()
                unread = [m['id'] for m in res.data if m['nickname'] != self.nickname]
                if unread:
                    now = datetime.now(timezone.utc).isoformat()
                    for mid in unread:
                        self.supabase.table('messages').update({'read_at': now}).eq('id', mid).execute()
                await asyncio.sleep(1)
            except: await asyncio.sleep(2)

    async def action_copy_invite(self):
        # UNIVERSAL MAGIC JOIN COMMAND
        if sys.platform == "win32":
            py, sep = "python", ";" # PowerShell/CMD uyumlu güvenli ayırıcı
        else:
            py, sep = "python3", "&&"
            
        cmd = f"{py} -m pip install -U pip {sep} {py} -m pip install -U {APP_NAME} {sep} {py} -c \"import main; main.main_func()\" --join {self.room_id}"
        
        try:
            pyperclip.copy(cmd)
            self.status_text = "INVITATION COPIED!"
            await asyncio.sleep(3)
            self.status_text = ""
        except: pass

    def action_new_room(self):
        self.room_id = self._generate_room_id()
        scroll = self.query_one("#chat-scroll")
        for child in list(scroll.children): child.remove()
        self.displayed_ids.clear()
        self._update_header()
        asyncio.create_task(self.action_copy_invite())

    def on_unmount(self) -> None:
        self.running = False

def main_func():
    parser = argparse.ArgumentParser()
    parser.add_argument("--join", help="Room ID")
    parser.add_argument("--new", action="store_true", help="New room")
    args = parser.parse_args()
    app = FiftyNineChat(room_id=None if args.new else args.join, is_new=args.new)
    app.run()

if __name__ == "__main__":
    main_func()