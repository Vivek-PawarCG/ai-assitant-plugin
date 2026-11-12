import sys
import json
import os
import threading
import time

from config_manager import ConfigManager
from gemini_client import GeminiClient
from clipboard import get_clipboard_text, set_clipboard_text

PRESETS = {
    "summarize": {
        "title": "Summarize Clipboard",
        "instruction": "Summarize the following text clearly in 3-5 concise bullet points. Focus on key takeaways and action items:",
    },
    "polish": {
        "title": "Fix & Polish Grammar",
        "instruction": "Proofread and polish the following text. Correct grammar, spelling, punctuation, and flow while keeping the exact same tone and meaning:",
    },
    "professional": {
        "title": "Make Professional",
        "instruction": "Rewrite the following text into clear, polite, and professional business communication for email or workplace chat:",
    },
    "code": {
        "title": "Explain & Fix Code",
        "instruction": "Analyze this code snippet. Explain what it does concisely, identify any bugs, performance issues, or edge cases, and provide the clean corrected version:",
    },
    "cmd": {
        "title": "Windows CMD / PowerShell",
        "instruction": "Translate the user request into the exact Windows PowerShell or CMD command. Output the command line followed by a 1-sentence explanation of what it does:",
    },
    "reply": {
        "title": "Draft Reply",
        "instruction": "Draft a concise, courteous, and constructive reply to the following message or email:",
    }
}

class GeminiPlugin:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.gemini = GeminiClient(
            api_key=self.config_manager.get("api_key", ""),
            model=self.config_manager.get("model", "gemini-3.8-flash-lite")
        )

        self.current_view = "chat" if self.config_manager.has_api_key() else "settings"
        self.status_message = "Ready"
        self.last_prompt = ""
        self.last_response = ""
        self.is_busy = False
        self.pending_input = ""
        self.pending_key_input = ""
        self.lock = threading.Lock()

    def send(self, payload):
        """Sends a JSON message line to Fenn via standard output."""
        try:
            line = json.dumps(payload, ensure_ascii=False)
            sys.stdout.write(line + "\n")
            sys.stdout.flush()
        except Exception as e:
            self.log("error", f"Failed to send JSON to Fenn: {str(e)}")

    def log(self, level, message):
        """Emits a log line to Fenn."""
        self.send({
            "type": "log",
            "level": level,
            "message": f"[GeminiAssistant] {message}"
        })

    def update_badge(self, kind=None, icon="sparkle"):
        if kind == "pulse":
            self.send({"type": "badge", "badge": {"kind": "pulse"}})
        elif kind == "glyph":
            self.send({"type": "badge", "badge": {"kind": "glyph", "icon": icon}})
        elif kind is None:
            if self.config_manager.has_api_key():
                self.send({"type": "badge", "badge": {"kind": "glyph", "icon": "sparkle"}})
            else:
                self.send({"type": "badge", "badge": {"kind": "glyph", "icon": "key"}})

    def render_tile(self):
        """Renders the collapsed tile in Fenn's notch grid."""
        has_key = self.config_manager.has_api_key()

        if self.is_busy:
            view = {
                "type": "row",
                "align": "center",
                "children": [
                    {"type": "text", "text": "Gemini: Thinking...", "size": "body"},
                    {"type": "spacer"},
                    {"type": "button", "id": "btn_tile_open", "icon": "sparkle"}
                ]
            }
        elif not has_key:
            view = {
                "type": "row",
                "align": "center",
                "children": [
                    {"type": "text", "text": "Gemini AI", "size": "body"},
                    {"type": "spacer"},
                    {"type": "button", "id": "btn_tile_setup", "icon": "key"}
                ]
            }
        else:
            view = {
                "type": "row",
                "align": "center",
                "children": [
                    {"type": "text", "text": "Gemini AI", "size": "title"},
                    {"type": "spacer"},
                    {"type": "button", "id": "btn_tile_summarize", "icon": "clipboard-text"},
                    {"type": "button", "id": "btn_tile_polish", "icon": "magic-wand"},
                    {"type": "button", "id": "btn_tile_open", "icon": "sparkle"}
                ]
            }

        self.send({"type": "tile", "view": view})

    def render_page(self):
        """Renders the expanded page when the user clicks the tile."""
        has_key = self.config_manager.has_api_key()

        actions = [
            {"id": "action_new_chat", "icon": "arrows-clockwise", "tooltip": "Clear / New Prompt"},
            {"id": "action_settings", "icon": "gear", "tooltip": "API Key & Model Settings"},
            {"id": "action_get_key", "icon": "arrow-square-out", "tooltip": "Get Gemini Key (AI Studio)"}
        ]

        if self.current_view == "settings" or not has_key:
            view = self._build_settings_view()
        else:
            view = self._build_chat_view()

        self.send({
            "type": "page",
            "view": view,
            "actions": actions
        })

    def _build_settings_view(self):
        has_key = self.config_manager.has_api_key()
        key = self.config_manager.get("api_key", "")
        masked_key = (key[:6] + "..." + key[-4:]) if len(key) > 10 else "No key saved"
        current_model = self.config_manager.get("model", "gemini-3.8-flash-lite")

        children = [
            {"type": "text", "text": "Google Gemini Settings", "size": "title"},
            {"type": "text", "text": "Bring Your Own Key (BYOK) - free from Google AI Studio. Your key is stored locally.", "size": "body"},
            {"type": "spacer"},
            {
                "type": "row",
                "align": "center",
                "children": [
                    {"type": "button", "id": "btn_open_ai_studio", "icon": "arrow-square-out", "text": "Get Free Key"},
                    {"type": "spacer"},
                    {"type": "button", "id": "btn_paste_key", "icon": "clipboard", "text": "Paste Key from Clipboard"},
                    {"type": "spacer"},
                    {"type": "button", "id": "btn_open_config", "icon": "note-pencil", "text": "Open in Notepad"}
                ]
            },
            {"type": "spacer"},
            {"type": "text", "text": f"Current Key: {masked_key}", "size": "body"},
            {
                "type": "input",
                "id": "input_api_key",
                "placeholder": "Or type / paste AIzaSy... here",
                "value": self.pending_key_input
            },
            {"type": "spacer"},
            {
                "type": "row",
                "align": "center",
                "children": [
                    {"type": "button", "id": "btn_model_flash_15", "icon": "lightning", "text": "1.5 Flash"},
                    {"type": "button", "id": "btn_model_flash_20", "icon": "sparkle", "text": "2.0 Flash"},
                    {"type": "spacer"},
                    {"type": "button", "id": "btn_save_key", "icon": "check", "text": "Save Key"}
                ]
            },
            {"type": "spacer"},
            {"type": "text", "text": f"Active Model: {current_model} | Status: {self.status_message}", "size": "small"}
        ]

        if has_key:
            children.append({
                "type": "row",
                "align": "center",
                "children": [
                    {"type": "spacer"},
                    {"type": "button", "id": "btn_back_to_chat", "icon": "chat-centered-text", "text": "Back to Assistant"}
                ]
            })

        return {
            "type": "column",
            "children": children
        }

    def _build_chat_view(self):
        children = []

        # Presets Bar
        children.append({
            "type": "row",
            "align": "center",
            "children": [
                {"type": "button", "id": "preset_summarize", "icon": "clipboard-text", "text": "Summarize"},
                {"type": "button", "id": "preset_polish", "icon": "magic-wand", "text": "Fix Grammar"},
                {"type": "button", "id": "preset_code", "icon": "code", "text": "Explain Code"},
                {"type": "button", "id": "preset_cmd", "icon": "terminal-window", "text": "Win CMD"}
            ]
        })

        # Input Row
        children.append({"type": "spacer"})
        children.append({
            "type": "row",
            "align": "center",
            "children": [
                {
                    "type": "input",
                    "id": "prompt_input",
                    "placeholder": "Ask Gemini anything, or click a quick action above...",
                    "value": self.pending_input
                },
                {"type": "button", "id": "btn_send", "icon": "paper-plane-right"},
                {"type": "button", "id": "btn_from_clipboard", "icon": "clipboard"}
            ]
        })

        children.append({"type": "spacer"})

        # Response or Status Area
        if self.is_busy:
            children.append({"type": "text", "text": "Gemini is thinking...", "size": "body"})
            children.append({"type": "text", "text": f"Prompt: {self.last_prompt[:90]}...", "size": "small"})
        elif self.last_response:
            # Action row for response
            children.append({
                "type": "row",
                "align": "center",
                "children": [
                    {"type": "text", "text": "Gemini Response:", "size": "title"},
                    {"type": "spacer"},
                    {"type": "button", "id": "btn_copy_response", "icon": "copy", "text": "Copy"},
                    {"type": "button", "id": "btn_clear_response", "icon": "trash"}
                ]
            })
            children.append({"type": "spacer"})
            # Display response (wrapped or sliced for presentation)
            display_text = self.last_response
            if len(display_text) > 800:
                display_text = display_text[:800] + "\n\n[...click Copy to view full response in clipboard]"
            children.append({"type": "text", "text": display_text, "size": "body"})
        else:
            children.append({"type": "text", "text": "💡 Tip: Copy text to your clipboard and hit 'Summarize' or 'Fix Grammar' for instant desktop assistance.", "size": "body"})
            children.append({"type": "text", "text": f"Status: {self.status_message}", "size": "small"})

        return {
            "type": "column",
            "children": children
        }

    def execute_async_prompt(self, prompt, system_instruction=None, auto_copy=True):
        """Runs the Gemini request in a background thread to prevent UI freezing."""
        if self.is_busy:
            return

        with self.lock:
            self.is_busy = True
            self.last_prompt = prompt
            self.last_response = ""
            self.status_message = "Generating..."

        self.update_badge(kind="pulse")
        self.render_tile()
        self.render_page()

        def worker():
            res = self.gemini.generate(
                prompt=prompt,
                system_instruction=system_instruction,
                temperature=self.config_manager.get("temperature", 0.7)
            )

            with self.lock:
                self.is_busy = False
                if res.get("success"):
                    text = res.get("text", "")
                    self.last_response = text
                    self.status_message = "Completed"
                    if auto_copy and text:
                        # Copy to clipboard via Fenn command and ctypes fallback
                        self.send({"type": "copy", "text": text})
                        set_clipboard_text(text)
                else:
                    err = res.get("error", "Unknown error")
                    self.last_response = f"⚠️ Error: {err}"
                    self.status_message = "Error"

            self.update_badge(kind="glyph", icon="sparkle")
            self.render_tile()
            self.render_page()

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def handle_preset(self, preset_key):
        preset = PRESETS.get(preset_key)
        if not preset:
            return

        clip = get_clipboard_text().strip()
        if not clip:
            self.last_response = f"⚠️ Clipboard is empty! Copy some text first, then click '{preset['title']}'."
            self.render_page()
            return

        full_prompt = f"{preset['instruction']}\n\n---\n{clip}\n---"
        self.execute_async_prompt(full_prompt, auto_copy=True)

    def handle_event(self, event_id, kind, value=None):
        """Processes interaction events sent by Fenn."""
        # Text input changes / commits
        if event_id == "input_api_key":
            if value is not None:
                self.pending_key_input = value.strip()
            if kind in ("submit", "commit") and self.pending_key_input:
                self.save_api_key(self.pending_key_input)
            return

        if event_id == "prompt_input":
            if value is not None:
                self.pending_input = value
            if kind in ("submit", "commit") and self.pending_input.strip():
                p = self.pending_input.strip()
                self.pending_input = ""
                self.execute_async_prompt(p, auto_copy=False)
            return

        # Tile buttons
        if event_id == "btn_tile_open":
            self.send({"type": "open_page"})
            return

        if event_id == "btn_tile_setup":
            self.current_view = "settings"
            self.render_page()
            self.send({"type": "open_page"})
            return

        if event_id == "btn_tile_summarize":
            self.handle_preset("summarize")
            return

        if event_id == "btn_tile_polish":
            self.handle_preset("polish")
            return

        # Action bar buttons
        if event_id == "action_new_chat":
            self.last_response = ""
            self.last_prompt = ""
            self.pending_input = ""
            self.status_message = "Cleared"
            self.render_page()
            return

        if event_id == "action_settings":
            self.current_view = "settings" if self.current_view != "settings" else "chat"
            self.render_page()
            return

        if event_id == "action_get_key" or event_id == "btn_open_ai_studio":
            self.send({"type": "open", "target": "https://aistudio.google.com/app/apikey"})
            return

        # Page buttons
        if event_id == "btn_back_to_chat":
            self.current_view = "chat"
            self.render_page()
            return

        if event_id == "btn_open_config":
            try:
                import subprocess
                os.makedirs(os.path.dirname(self.config_manager.config_path), exist_ok=True)
                if not os.path.exists(self.config_manager.config_path):
                    self.config_manager.save()
                subprocess.Popen(["notepad.exe", self.config_manager.config_path])
                self.status_message = "Opened config.json in Notepad"
            except Exception as e:
                self.status_message = f"Failed to open Notepad: {e}"
            self.render_page()
            return

        if event_id == "btn_paste_key":
            clip = get_clipboard_text().strip()
            if clip.startswith("AIzaSy") or len(clip) > 20:
                self.save_api_key(clip)
            else:
                self.status_message = "Clipboard does not appear to contain a valid Gemini API key."
                self.render_page()
            return

        if event_id == "btn_save_key":
            if self.pending_key_input:
                self.save_api_key(self.pending_key_input)
            else:
                self.status_message = "Please enter an API key."
                self.render_page()
            return

        if event_id == "btn_model_flash_15":
            self.config_manager.set("model", "gemini-3.8-flash-lite")
            self.gemini.set_model("gemini-3.8-flash-lite")
            self.status_message = "Switched to Gemini 1.5 Flash"
            self.render_page()
            return

        if event_id == "btn_model_flash_20":
            self.config_manager.set("model", "gemini-2.0-flash")
            self.gemini.set_model("gemini-2.0-flash")
            self.status_message = "Switched to Gemini 2.0 Flash"
            self.render_page()
            return

        # Quick action presets
        if event_id == "preset_summarize":
            self.handle_preset("summarize")
            return

        if event_id == "preset_polish":
            self.handle_preset("polish")
            return

        if event_id == "preset_code":
            self.handle_preset("code")
            return

        if event_id == "preset_cmd":
            clip = get_clipboard_text().strip()
            if clip:
                full_prompt = f"{PRESETS['cmd']['instruction']}\n\nTask: {clip}"
                self.execute_async_prompt(full_prompt, auto_copy=True)
            elif self.pending_input.strip():
                full_prompt = f"{PRESETS['cmd']['instruction']}\n\nTask: {self.pending_input.strip()}"
                self.pending_input = ""
                self.execute_async_prompt(full_prompt, auto_copy=True)
            else:
                self.last_response = "⚠️ Please type what command you need or copy it to your clipboard first!"
                self.render_page()
            return

        if event_id == "btn_send":
            if self.pending_input.strip():
                p = self.pending_input.strip()
                self.pending_input = ""
                self.execute_async_prompt(p, auto_copy=False)
            return

        if event_id == "btn_from_clipboard":
            clip = get_clipboard_text().strip()
            if clip:
                self.pending_input = clip
                self.render_page()
            return

        if event_id == "btn_copy_response":
            if self.last_response:
                self.send({"type": "copy", "text": self.last_response})
                set_clipboard_text(self.last_response)
                self.status_message = "Copied to clipboard!"
                self.render_page()
            return

        if event_id == "btn_clear_response":
            self.last_response = ""
            self.render_page()
            return

    def save_api_key(self, key):
        key = key.strip()
        self.status_message = "Validating key with Google Gemini..."
        self.render_page()

        def test_worker():
            valid, err = self.gemini.validate_key(key)
            if valid:
                self.config_manager.set("api_key", key)
                self.gemini.set_api_key(key)
                self.current_view = "chat"
                self.status_message = "Key verified successfully!"
                self.pending_key_input = ""
            else:
                self.status_message = f"Invalid Key: {err}"

            self.update_badge()
            self.render_tile()
            self.render_page()

        t = threading.Thread(target=test_worker, daemon=True)
        t.start()

    def run(self):
        """Main event loop listening to Fenn's standard input."""
        # Initial render
        self.update_badge()
        self.render_tile()
        self.render_page()

        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue

            try:
                msg = json.loads(line)
            except Exception:
                continue

            msg_type = msg.get("type")

            if msg_type == "hello":
                data_dir = msg.get("data_dir")
                if data_dir:
                    self.config_manager.set_data_dir(data_dir)
                    self.gemini.set_api_key(self.config_manager.get("api_key", ""))
                self.update_badge()
                self.render_tile()
                self.render_page()

            elif msg_type == "event":
                event_id = msg.get("id")
                kind = msg.get("kind", "click")
                value = msg.get("value")
                self.handle_event(event_id, kind, value)

            elif msg_type == "tile_click":
                self.config_manager.config = self.config_manager.load()
                self.gemini.set_api_key(self.config_manager.get("api_key", ""))
                self.render_page()
                self.send({"type": "open_page"})

            elif msg_type == "page_open":
                self.config_manager.config = self.config_manager.load()
                self.gemini.set_api_key(self.config_manager.get("api_key", ""))
                self.render_page()

            elif msg_type == "page_close":
                pass

            elif msg_type == "shutdown":
                break

if __name__ == "__main__":
    plugin = GeminiPlugin()
    plugin.run()
