# freellm/core.py
import requests
import uuid
from typing import List, Dict, Optional


URL = "https://talkai.info/chat/send/"

HEADERS = {
    "Host": "talkai.info",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Accept": "application/json, text/event-stream",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Referer": "https://talkai.info/chat/",
    "Content-Type": "application/json",
    "Origin": "https://talkai.info",
    "Connection": "close",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Priority": "u=0",
}

MODELS = {
    "deepseek": "deepseek-chat",
    "google": "gemini-2.0-flash-lite",
    "claude": "claude-3-haiku-20240307",
    "gpt": "gpt-4.1-nano"
}


class FreeLLM:
    """
    Simple client for free access to multiple top-tier AI models via public endpoint.
    Supports DeepSeek, Gemini Flash, Claude Haiku, and GPT-4.1 Nano — all completely free.
    """

    def __init__(
        self,
        model: str = "gpt",
        limit: Optional[int] = None,
        stream: bool = False
    ):
        if model not in MODELS:
            model = "gpt"
        self.model_name = MODELS[model]
        self.model_key = model
        self.limit = limit
        self.stream = stream
        self.history: List[Dict] = []
        self.user_message_count = 0
        self.conversation_id = 1

    def _generate_id(self) -> str:
        return str(uuid.uuid4())

    def _get_limited_history(self) -> List[Dict]:
        if self.limit is None or self.limit <= 0:
            return self.history
        max_messages = self.limit * 2
        return self.history[-max_messages:] if len(self.history) > max_messages else self.history

    def _send(self, user_message: str) -> str:
        self.history.append({
            "id": self._generate_id(),
            "from": "you",
            "content": user_message,
            "model": ""
        })

        payload = {
            "type": "chat",
            "messagesHistory": self._get_limited_history(),
            "settings": {
                "model": self.model_name,
                "temperature": 0.7
            }
        }

        try:
            response = requests.post(URL, headers=HEADERS, json=payload, stream=True, timeout=60)
            response.raise_for_status()

            full_response = ""
            first_chunk = True
            last_char = ""

            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                line = line.strip()
                if not line.startswith("data: "):
                    continue
                data = line[6:].strip()
                if not data:
                    continue

                # Skip model name prefix in first chunk
                if first_chunk:
                    if any(prefix in data for prefix in ["GPT", "DeepSeek", "Gemini", "Claude"]):
                        parts = data.split(None, 3)
                        data = parts[3] if len(parts) > 3 else ""
                    first_chunk = False

                if data.isdigit():
                    continue

                data = data.replace("\\n", "\n")

                # Streaming with smart spacing
                if self.stream:
                    if data:
                        if full_response and last_char not in " \n\t.!?,:;，。！？；：”)]}" and \
                           data[0] not in " \n\t.!?,:;，。！？；：“([{":
                            print(" ", end="", flush=True)
                        print(data, end="", flush=True)
                        last_char = data[-1] if data else last_char
                    full_response += data
                else:
                    # Batch mode: smart spacing
                    if full_response and full_response[-1] not in " \n\t.!?,:;，。！？；：”)]}" and \
                       data[0] not in " \n\t.!?,:;，。！？；：“([{":
                        full_response += " " + data
                    else:
                        full_response += data

            final_text = full_response.strip()
            if self.stream:
                print()  # newline after streaming

            if final_text:
                self.history.append({
                    "id": self._generate_id(),
                    "from": "chatGPT",
                    "content": final_text,
                    "model": self.model_name
                })
            else:
                self.history.pop()  # remove user message on failure
                final_text = "[No response received]"

            return final_text

        except requests.exceptions.RequestException as e:
            self.history.pop()
            return f"[Network Error: {e}]"
        except Exception as e:
            self.history.pop()
            return f"[Error: {e}]"

    def ask(self, message: str) -> str:
        if not message.strip():
            return ""
        if self.limit is not None and self.user_message_count >= self.limit:
            self.history.clear()
            self.user_message_count = 0
            self.conversation_id += 1
        self.user_message_count += 1
        return self._send(message.strip())

    def chat(self):
        print("=== FreeLLM - Free Access to Top AI Models ===")
        print(f"Model: {self.model_key.upper()} | "
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
            if not user_input:
                continue
            response = self.ask(user_input)
            if not self.stream:
                print(f"Bot:\n{response}\n")

    def reset(self):
        self.history.clear()
        self.user_message_count = 0
        self.conversation_id += 1
