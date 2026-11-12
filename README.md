# Gemini Assistant Plugin for Fenn

A personal AI desktop companion for the **Fenn** floating notch on Windows 10 and 11.

---

## Highlights

- **Bring Your Own Key (BYOK):** Connect your free Google Gemini API key. All keys stay private on your PC.
- **Notch Quick Actions:** Summarize, proofread, or explain copied text straight from the floating notch.
- **Zero Extra Dependencies:** Pure Python standard library implementation (`urllib`, `ctypes`, `json`).
- **Interactive Expanded Panel:** Features prompt presets for writing polish, code explanations, and Windows command lookups.

---

## Directory Structure

```text
fenn-gemini-assistant/
├── plugin.toml         # Fenn extension manifest
├── main.py             # Event loop & JSON protocol handler
├── gemini_client.py    # Direct Google Gemini REST API client
├── config_manager.py   # Local persistent settings manager
├── clipboard.py        # Windows clipboard integration
├── test_simulator.py   # CLI testing harness
└── README.md           # Documentation & setup instructions
```

---

## Setup & Local Testing

1. **Verify Python:** Ensure Python 3.8+ is installed on your Windows machine.
2. **Install into Fenn:**
   Copy the `fenn-gemini-assistant` folder into:
   ```text
   %APPDATA%\Fenn\plugins\gemini-assistant
   ```
3. **Turn on Developer Mode:**
   Open Fenn Settings and enable **Plugin dev mode** to reload on save.
4. **Local CLI Testing:**
   You can also test the plugin protocol without Fenn running:
   ```powershell
   python test_simulator.py
   ```

---

## Privacy & Network

- Requests are transmitted over HTTPS directly to Google's official Gemini endpoint (`generativelanguage.googleapis.com`).
- No telemetry, intermediate proxies, or third-party servers are used.
