"""
Fenn Plugin Local CLI Simulator
Allows testing the Gemini Assistant plugin protocol directly from PowerShell or Command Prompt.
"""

import subprocess
import json
import threading
import sys
import os
import time

def main():
    plugin_dir = os.path.dirname(os.path.abspath(__file__))
    main_py = os.path.join(plugin_dir, "main.py")

    print("=" * 65)
    print(" 🌟 Fenn Plugin Local Protocol Simulator (Gemini Assistant)")
    print("=" * 65)
    print(f"Spawning: python {main_py}")

    proc = subprocess.Popen(
        [sys.executable, "-u", main_py],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        cwd=plugin_dir
    )

    def reader():
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            try:
                data = json.loads(line.strip())
                msg_type = data.get("type", "unknown")
                if msg_type == "tile":
                    print(f"\n[Fenn Notch <- Plugin] TILE VIEW:\n{json.dumps(data.get('view'), indent=2)}")
                elif msg_type == "page":
                    print(f"\n[Fenn Notch <- Plugin] PAGE VIEW UPDATED (actions: {len(data.get('actions', []))})")
                elif msg_type == "badge":
                    print(f"[Fenn Notch <- Plugin] BADGE: {data.get('badge')}")
                elif msg_type == "copy":
                    print(f"📋 [Clipboard Copy] \"{data.get('text')[:80]}...\"")
                elif msg_type == "log":
                    print(f"📝 [Log] [{data.get('level')}] {data.get('message')}")
                else:
                    print(f"[Fenn Notch <- Plugin] {line.strip()}")
            except Exception:
                print(f"[Raw Output] {line.strip()}")

    t = threading.Thread(target=reader, daemon=True)
    t.start()

    time.sleep(0.5)

    # Send hello handshake
    hello_msg = {
        "type": "hello",
        "protocol": 1,
        "fenn_version": "1.0.0",
        "plugin_id": "gemini-assistant",
        "data_dir": plugin_dir,
        "theme": {"dark": True, "accent": "#4f46e5"}
    }
    print("\n[Simulator -> Plugin] Sending 'hello' handshake...")
    proc.stdin.write(json.dumps(hello_msg) + "\n")
    proc.stdin.flush()

    time.sleep(1)

    print("\n" + "-" * 65)
    print("Commands:")
    print("  1 - Trigger 'btn_tile_open' (Open page)")
    print("  2 - Trigger 'preset_summarize' (Summarize clipboard)")
    print("  3 - Trigger 'preset_polish' (Fix grammar in clipboard)")
    print("  4 - Set API key (e.g., input_api_key)")
    print("  5 - Send custom prompt (e.g., 'What is 15 * 4?')")
    print("  q - Quit simulator")
    print("-" * 65)

    while True:
        try:
            cmd = input("\nEnter choice (1/2/3/4/5/q): ").strip()
            if cmd == "q":
                proc.stdin.write(json.dumps({"type": "shutdown"}) + "\n")
                proc.stdin.flush()
                break
            elif cmd == "1":
                event = {"type": "event", "id": "btn_tile_open", "kind": "click"}
                proc.stdin.write(json.dumps(event) + "\n")
                proc.stdin.flush()
            elif cmd == "2":
                event = {"type": "event", "id": "preset_summarize", "kind": "click"}
                proc.stdin.write(json.dumps(event) + "\n")
                proc.stdin.flush()
            elif cmd == "3":
                event = {"type": "event", "id": "preset_polish", "kind": "click"}
                proc.stdin.write(json.dumps(event) + "\n")
                proc.stdin.flush()
            elif cmd == "4":
                key = input("Paste Gemini API Key: ").strip()
                event = {"type": "event", "id": "input_api_key", "kind": "commit", "value": key}
                proc.stdin.write(json.dumps(event) + "\n")
                proc.stdin.flush()
            elif cmd == "5":
                p = input("Enter prompt: ").strip()
                event = {"type": "event", "id": "prompt_input", "kind": "commit", "value": p}
                proc.stdin.write(json.dumps(event) + "\n")
                proc.stdin.flush()
            time.sleep(0.5)
        except (KeyboardInterrupt, EOFError):
            break

    proc.terminate()
    print("\nSimulator stopped.")

if __name__ == "__main__":
    main()
