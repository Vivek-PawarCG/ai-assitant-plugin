import json
import urllib.request
import urllib.error
import ssl

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

class GeminiClient:
    def __init__(self, api_key="", model="gemini-1.5-flash"):
        self.api_key = api_key.strip()
        self.model = model.strip() or "gemini-1.5-flash"
        self._ctx = ssl.create_default_context()

    def set_api_key(self, api_key):
        self.api_key = api_key.strip()

    def set_model(self, model):
        self.model = model.strip() or "gemini-1.5-flash"

    def generate(self, prompt, system_instruction=None, temperature=0.7, max_tokens=1024):
        if not self.api_key:
            return {
                "success": False,
                "error": "No API key configured. Please add your Gemini API key in Settings."
            }

        url = f"{GEMINI_API_BASE}/{self.model}:generateContent?key={self.api_key}"

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }

        if system_instruction:
            payload["system_instruction"] = {
                "parts": [
                    {"text": system_instruction}
                ]
            }

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Fenn-Gemini-Plugin/1.0"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, context=self._ctx, timeout=30) as response:
                body = response.read().decode("utf-8")
                res_json = json.loads(body)
                candidates = res_json.get("candidates", [])
                if not candidates:
                    return {
                        "success": False,
                        "error": "Empty response from Gemini."
                    }
                first_part = candidates[0].get("content", {}).get("parts", [{}])[0]
                text = first_part.get("text", "").strip()
                return {
                    "success": True,
                    "text": text
                }
        except urllib.error.HTTPError as e:
            try:
                err_body = e.read().decode("utf-8")
                err_json = json.loads(err_body)
                msg = err_json.get("error", {}).get("message", str(e))
            except Exception:
                msg = str(e)

            if e.code == 400 or e.code == 403:
                return {
                    "success": False,
                    "error": f"Authentication Error ({e.code}): Invalid API key or permission denied.\n{msg}"
                }
            elif e.code == 429:
                return {
                    "success": False,
                    "error": "Rate limit exceeded (429). Please wait a moment and try again."
                }
            else:
                return {
                    "success": False,
                    "error": f"API Error ({e.code}): {msg}"
                }
        except urllib.error.URLError as e:
            return {
                "success": False,
                "error": f"Network Error: Unable to connect to Gemini API. Check your internet connection. ({e.reason})"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }

    def validate_key(self, api_key):
        old_key = self.api_key
        try:
            self.api_key = api_key.strip()
            res = self.generate("Say OK", max_tokens=10)
            return res.get("success", False), res.get("error", "")
        finally:
            self.api_key = old_key
