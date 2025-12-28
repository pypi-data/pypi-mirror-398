# freellama/core.py
import requests
import json
from datetime import datetime, timezone
from typing import List, Dict, Optional

URL = "https://cachegpt.app/api/v2/unified-chat-stream"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Accept": "*/*",
    "Content-Type": "application/json",
    "Origin": "https://cachegpt.app",
    "Referer": "https://cachegpt.app/chat",
}

class FreeLlama:
    """
    Simple client for free Llama-3.3-70B via public proxies.
    Supports fast/best mode, memory via history, limit, and streaming.
    """

    def __init__(
        self,
        mode: str = "fast",        # NEW: "fast" or "best"
        limit: Optional[int] = None,
        stream: bool = False
    ):
        self.mode = mode.lower()
        if self.mode not in ["fast", "best"]:
            self.mode = "fast"

        self.limit = limit
        self.stream = stream

        self.full_history: List[Dict] = []
        self.user_message_count = 0
        self.conversation_id = 1

    def _now(self):
        return datetime.now(timezone.utc).isoformat(timespec='milliseconds') + "Z"

    def _send(self, messages: List[Dict]) -> str:
        payload = {
            "messages": messages,
            "qualityMode": self.mode  # ← Sends "fast" or "best"
        }

        try:
            with requests.post(URL, headers=HEADERS, json=payload, stream=True, timeout=60) as r:
                if r.status_code != 200:
                    return f"[Error {r.status_code}]"

                full = ""
                for line in r.iter_lines():
                    if not line:
                        continue
                    line = line.decode().strip()
                    if not line.startswith("data: "):
                        continue
                    data = line[6:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        text = chunk.get("content", "")
                        if self.stream:
                            print(text[len(full):], end="", flush=True)
                        full = text
                        if chunk.get("done"):
                            break
                    except json.JSONDecodeError:
                        pass
                if self.stream:
                    print()
                return full.strip()
        except Exception as e:
            return f"[Error: {e}]"

    def ask(self, message: str) -> str:
        if not message.strip():
            return ""

        if self.limit and self.user_message_count >= self.limit:
            self.full_history.clear()
            self.user_message_count = 0
            self.conversation_id += 1

        user_msg = {
            "role": "user",
            "content": message,
            "created_at": self._now()
        }

        if self.limit:
            self.full_history.append(user_msg)
            self.user_message_count += 1
            response = self._send(self.full_history)
            if response and not response.startswith("[Error"):
                self.full_history.append({
                    "role": "assistant",
                    "content": response,
                    "created_at": self._now()
                })
        else:
            response = self._send([user_msg])

        return response

    def chat(self):
        print("=== FreeLlama (Free Llama-3.3-70B) ===")
        print(f"Mode: {self.mode.upper()} | "
              f"Memory: {'ON' if self.limit else 'OFF'} "
              f"{'(limit: ' + str(self.limit) + ')' if self.limit else ''}")
        print("Type 'exit' to quit\n")
        print(f"--- Conversation #{self.conversation_id} ---\n")

        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            if user_input.lower() in ["exit", "quit", "bye"]:
                print("Goodbye!")
                break

            response = self.ask(user_input)
            print("Bot:", response)
            print()

    def reset(self):
        self.full_history.clear()
        self.user_message_count = 0
        self.conversation_id += 1
