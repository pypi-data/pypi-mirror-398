import sys
import json
from typing import Any, Dict

EVENT_PREFIX = "__CHARM_EVENT__"

class CharmEmitter:
    """負責發送符合 Charm SSE 協議的結構化事件"""
    
    @staticmethod
    def _write(event_type: str, payload: Dict[str, Any]):
        """將事件包裝成協議格式寫入 stdout"""
        data = {
            "type": event_type,
            **payload
        }
        # 確保只有單一行，且立即 Flush，避免 Docker buffer 卡住
        sys.__stdout__.write(f"{EVENT_PREFIX}{json.dumps(data, ensure_ascii=False)}\n")
        sys.__stdout__.flush()

    @staticmethod
    def emit_status(message: str):
        CharmEmitter._write("status", {"content": message})

    @staticmethod
    def emit_thinking(content: str):
        CharmEmitter._write("thinking", {"content": content})

    @staticmethod
    def emit_final(content: str, format: str = "markdown"):
        CharmEmitter._write("final", {"content": content, "format": format})

    @staticmethod
    def emit_error(message: str):
        CharmEmitter._write("error", {"content": message})
        
    @staticmethod
    def emit_artifact(name: str, url: str, mime: str):
        CharmEmitter._write("artifact", {"content": {"name": name, "url": url, "mime": mime}})

class StdoutInterceptor:
    """攔截標準輸出，將其轉換為 Thinking 事件"""
    def __init__(self):
        self.terminal = sys.__stdout__
        self.buffer = ""

    def write(self, message):
        if not message: return
        
        # 如果是我們自己發出的協議字串，直接放行
        if message.startswith(EVENT_PREFIX):
            self.terminal.write(message)
            self.terminal.flush()
            return
            
        # 將所有攔截到的普通 print (CrewAI/LangChain logs) 都視為 "thinking"
        self.buffer += message
        if "\n" in self.buffer:
            lines = self.buffer.split("\n")
            for line in lines[:-1]:
                if line.strip():
                     # 這裡將其包裝成 Event
                     self.terminal.write(f'{EVENT_PREFIX}{json.dumps({"type": "thinking", "content": line + "\\n"}, ensure_ascii=False)}\n')
            self.terminal.flush()
            self.buffer = lines[-1]

    def flush(self):
        if self.buffer.strip():
            self.terminal.write(f'{EVENT_PREFIX}{json.dumps({"type": "thinking", "content": self.buffer + "\\n"}, ensure_ascii=False)}\n')
            self.buffer = ""
        self.terminal.flush()