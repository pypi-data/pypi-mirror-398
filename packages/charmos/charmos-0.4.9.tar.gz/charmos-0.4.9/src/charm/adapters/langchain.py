from typing import Any, Dict, List
import inspect
import asyncio
from .base import BaseAdapter
from ..core.logger import logger

# [New] 引入 LangChain 訊息物件
try:
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
except ImportError:
    from langchain.schema import HumanMessage, AIMessage, SystemMessage # type: ignore

class CharmLangChainAdapter(BaseAdapter):
    """Adapter for standard LangChain Chains/Agents."""

    def _ensure_instantiated(self):
        self._smart_instantiate()
        if not hasattr(self.agent, "invoke"):
            for attr in ["chain", "agent", "runnable", "pipeline"]:
                if hasattr(self.agent, attr):
                    candidate = getattr(self.agent, attr)
                    if hasattr(candidate, "invoke"):
                        print(f"[Charm] Detected LangChain Wrapper. Switching to inner '.{attr}' attribute.")
                        self.agent = candidate
                        break

    # [New] 統一的歷史轉換邏輯
    def _convert_history_to_messages(self, history: List[Dict[str, str]]) -> List[Any]:
        lc_messages = []
        for msg in history:
            role = msg.get("role")
            content = msg.get("content") or ""
            if role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
            elif role == "system":
                lc_messages.append(SystemMessage(content=content))
        return lc_messages

    # [Update] 支援 callbacks 和 history
    def invoke(self, inputs: Dict[str, Any], callbacks: List[Any] = None) -> Dict[str, Any]:
        self._pending_inputs = inputs
        self._ensure_instantiated()
        
        native_input = inputs.copy()
        
        # 1. 處理歷史紀錄
        history_data = native_input.pop("__charm_history__", None)
        lc_history = []
        if history_data:
            lc_history = self._convert_history_to_messages(history_data)

        # 2. 注入歷史紀錄
        # 策略 A: 許多 Chain 預期 "chat_history" 這個 key
        if "chat_history" not in native_input:
            native_input["chat_history"] = lc_history
        
        # 策略 B: 如果是 Runnable (LCEL)，可能直接接收 List[Message]
        # 這裡我們做一個判斷：如果 input 裡已經有 messages 列表，我們合併
        if "messages" in native_input and isinstance(native_input["messages"], list):
            native_input["messages"] = lc_history + native_input["messages"]

        # [Proactive Logic] 對於傳統 LangChain Agent，通常需要一個 input key
        # 如果 native_input 是空的 (代表空啟動)，我們可能需要塞一個預設值，或是信任 Agent 能處理
        # 這裡保持原樣，因為 AgentExecutor 通常會自己檢查 input key

        config = {}
        if callbacks:
            config["callbacks"] = callbacks

        result = None
        try:
            result = self.agent.invoke(native_input, config=config)
        except TypeError:
            result = self.agent.invoke(native_input)
        except Exception as e:
            if hasattr(self.agent, "ainvoke"):
                logger.info("[Charm] Sync invoke failed, attempting Async ainvoke...")
                try:
                    result = self._execute_async_safely(self.agent.ainvoke(native_input, config=config))
                except Exception as async_e:
                    return {"status": "error", "message": f"Async execution also failed: {async_e}"}
            else:
                return {"status": "error", "message": str(e)}

        try:
            output_str = str(result)
            if isinstance(result, dict):
                for key in ["output", "text", "result", "generation"]:
                    if key in result:
                        val = result[key]
                        if hasattr(val, "text"): output_str = val.text
                        else: output_str = str(val)
                        break
            elif isinstance(result, str):
                output_str = result
            elif hasattr(result, "content"):
                output_str = str(result.content)
                
            return {"status": "success", "output": output_str}
        except Exception as e:
            return {"status": "error", "message": f"Output parsing error: {str(e)}"}