import asyncio
import os
import sys
import argparse
from datetime import datetime, timezone
from typing import Optional, Set, List, Dict
from textual.app import App, ComposeResult
from textual.widgets import Input, Static, Button, Footer, RichLog
from textual.containers import Vertical, Horizontal
from supabase import create_client, Client
import random
import string
import pyperclip

# EMBEDDED CONFIGURATION
SUPABASE_URL = "https://xdqxebyyjxklzisddmwl.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhkcXhlYnl5anhrbHppc2RkbXdsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk4Mzc0NDAsImV4cCI6MjA3NTQxMzQ0MH0.37JtLjN6mGfdac-t-cqNADa8OQlYIgSkZEFSngwxlM0"

# Design System
COLOR_BG = "#000000"
COLOR_SURFACE = "#0A0A0A"
COLOR_BORDER = "#1A1A1A"
COLOR_ACCENT = "#FFFFFF"
COLOR_TEXT_SECONDARY = "#525252"
COLOR_SUCCESS = "#22C55E"
COLOR_ERROR = "#EF4444"

CSS = f""
Screen {{
    background: {COLOR_BG};
    color: {COLOR_ACCENT};
}}

#header {{
    dock: top;
    height: 3;
    background: {COLOR_SURFACE};
    border-bottom: solid {COLOR_BORDER};
    content-align: center middle;
    text-style: bold;
}}

#chat-log {{
    height: 1fr;
    background: {COLOR_BG};
    border: none;
    padding: 1 1;
    scrollbar-gutter: stable;
}}

#input-area {{
    dock: bottom;
    height: 3;
    background: {COLOR_SURFACE};
    border-top: solid {COLOR_BORDER};
}}

Input {{
    background: {COLOR_SURFACE};
    border: none;
    width: 1fr;
    padding: 0 2;
    color: {COLOR_ACCENT};
}}

Input:focus {{
    border: none;
}}

#send-btn {{
    width: 10;
    background: {COLOR_ACCENT};
    color: {COLOR_BG};
    border: none;
    text-style: bold;
    height: 1;
    margin: 1 1 0 0;
}}
""

class EphemeralChat(App):
    CSS = CSS
    
    BINDINGS = [
        ("ctrl+c", "quit", "Exit"),
        ("ctrl+r", "new_room", "New Room"),
        ("ctrl+l", "copy_invite", "Copy Invite Link"),
    ]
    
    def __init__(self, room_id: Optional[str] = None, is_new: bool = False):
        super().__init__()
        self.supabase: Optional[Client] = None
        self.room_id: str = room_id or ""
        self.nickname: str = ""
        self.running = True
        self.active_users: int = 1
        self.is_new_session = is_new

    def compose(self) -> ComposeResult:
        yield Static(id="header")
        yield RichLog(id="chat-log", markup=True, wrap=False)
        with Horizontal(id="input-area"):
            yield Input(placeholder="Type message...", id="message-input")
            yield Button("SEND", id="send-btn")
        yield Footer()

    def on_mount(self) -> None:
        try:
            self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            self.nickname = self._generate_nickname()
            if not self.room_id:
                self.room_id = self._generate_room_id()
                self.is_new_session = True
            
            self._update_header()
            asyncio.create_task(self._watch_and_refresh())
            asyncio.create_task(self._mark_as_read())
            asyncio.create_task(self._presence_heartbeat())
            
            if self.is_new_session:
                self.action_copy_invite()
                
        except Exception as e:
            self.notify(f"Init failed: {e}", severity="error")

    def _generate_nickname(self) -> str:
        return f"{random.choice(['Cold','Swift','Pure','Thin'])}{random.choice(['Grid','Line','Type','Form'])}"

    def _generate_room_id(self) -> str:
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    def _update_header(self):
        presence_info = f"  [dim]│[/]  [bold {COLOR_SUCCESS}]●[/] {self.active_users} ONLINE"
        self.query_one("#header").update(f"ROOM: [bold]{self.room_id}[/]  [dim]│[/]  USER: [bold]{self.nickname}[/]{presence_info}")

    async def _presence_heartbeat(self):
        while self.running and self.supabase:
            try:
                res = self.supabase.table('messages').select('nickname').eq('room_id', self.room_id).execute()
                nicknames = {m['nickname'] for m in res.data}
                self.active_users = max(1, len(nicknames))
                self._update_header()
                await asyncio.sleep(10)
            except:
                await asyncio.sleep(10)

    async def _watch_and_refresh(self):
        while self.running and self.supabase:
            try:
                res = self.supabase.table('messages').select('*').eq('room_id', self.room_id).order('created_at').execute()
                chat_log = self.query_one("#chat-log")
                
                now = datetime.now(timezone.utc)
                visible_messages = []
                for m in res.data:
                    if m.get('read_at'):
                        read_dt = datetime.fromisoformat(m['read_at'].replace('Z', '+00:00'))
                        if (now - read_dt).total_seconds() < 59:
                            visible_messages.append(m)
                    else:
                        visible_messages.append(m)

                chat_log.clear()
                
                # Show Invitation Command at Top if it's a new room
                invite_cmd = f"pip install -U ephemeral-terminal-chat && ephemeral --join {self.room_id}"
                chat_log.write(f"[bold {COLOR_TEXT_SECONDARY}]MAGIC JOIN COMMAND (SHARE THIS):[/]")
                chat_log.write(f"[reverse] {invite_cmd} [/]")
                chat_log.write(f"[dim]Press Ctrl+L to copy this command again.[/]")
                chat_log.write(f"[dim]{'─' * 40}[/]\n")

                width = chat_log.content_size.width or 80
                max_msg_width = int(width * 0.8)
                
                for m in visible_messages:
                    is_own = m['nickname'] == self.nickname
                    time_part = m['created_at'].split('T')[1][:5]
                    
                    status = " [dim]○[/]"
                    if m.get('read_at'):
                        read_dt = datetime.fromisoformat(m['read_at'].replace('Z', '+00:00'))
                        rem = max(0, int(59 - (now - read_dt).total_seconds()))
                        status = f" [bold {COLOR_SUCCESS}]●[/] [bold {COLOR_ERROR}]{rem}s[/]"

                    user_style = f"bold {COLOR_ACCENT}" if is_own else f"bold {COLOR_TEXT_SECONDARY}"
                    
                    indent_size = (width - max_msg_width - 4) if is_own else 0
                    indent = " " * indent_size
                    prefix = "> " if is_own else ""
                    
                    header = f"{indent}[{user_style}]{prefix}{m['nickname']}[/] [dim]{time_part}[/]{status}"
                    content = f"{indent}  {m['content']}"
                    underline = f"{indent}[dim]{'━' * max_msg_width}[/]]"
                    
                    chat_log.write(header)
                    chat_log.write(content)
                    chat_log.write(underline)
                    chat_log.write("")
                
                chat_log.scroll_end(animate=False)
                await asyncio.sleep(0.5)
            except:
                await asyncio.sleep(1)

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
            except:
                await asyncio.sleep(2)

    def _send(self):
        inp = self.query_one(Input)
        content = inp.value.strip()
        if not content or not self.supabase: return
        try:
            self.supabase.table('messages').insert({
                'room_id': self.room_id,
                'nickname': self.nickname,
                'content': content
            }).execute()
            inp.value = ""
        except:
            self.notify("Send failed")

    def on_input_submitted(self): self._send()
    def on_button_pressed(self): self._send()

    def action_copy_invite(self):
        invite_cmd = f"pip install -U ephemeral-terminal-chat && ephemeral --join {self.room_id}"
        try:
            pyperclip.copy(invite_cmd)
            self.notify("Invite command copied to clipboard!", severity="information")
        except:
            self.notify("Failed to copy. Please select it manually.", severity="warning")

    def action_new_room(self):
        self.room_id = self._generate_room_id()
        self.query_one("#chat-log").clear()
        self._update_header()
        self.action_copy_invite()

    def on_unmount(self) -> None:
        self.running = False

def main_func():
    parser = argparse.ArgumentParser()
    parser.add_argument("--join", help="Room ID")
    parser.add_argument("--new", action="store_true", help="Start a new room")
    args = parser.parse_args()
    
    room = None if args.new else args.join
    app = EphemeralChat(room_id=room, is_new=args.new)
    app.run()

if __name__ == "__main__":
    main_func()