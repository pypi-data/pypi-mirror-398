import json
import uuid
import os
import time
from typing import Generator, List, Dict, Any, Optional

from lagent.core.llm import LLMClient
from lagent.core.prompt_engine import PromptEngine
from lagent.tools.sandbox import sandbox
from lagent.tools.registry import registry
from lagent.tools.builtin.shell import shell_execute 
from lagent.tools.demo_tools import get_weather 
from lagent.memory.manager import SessionManager
from lagent.memory.db import init_db_custom
from lagent.types import AgentState, MessageRole
from lagent.config import get_settings

class ContextAgent:
    def __init__(self, 
                 llm_client: LLMClient, 
                 session_manager: Optional[SessionManager] = None,
                 db_url: str = None,
                 session_id: str = None, 
                 user_id: str = "default_user", 
                 tools: List[str] = None,
                 debug: bool = None):
        
        # 1. Load Settings (Defaults)
        _settings = get_settings()
        self.max_steps = _settings.MAX_STEPS
        self.final_answer_marker = _settings.FINAL_ANSWER_MARKER
        self.min_tool_use = _settings.MIN_TOOL_USE
        self.max_tool_use = _settings.MAX_TOOL_USE
        self.debug = debug if debug is not None else _settings.DEBUG
        self.input_price = _settings.INPUT_PRICE_PER_1K
        self.output_price = _settings.OUTPUT_PRICE_PER_1K
        self.currency = _settings.CURRENCY_UNIT
        self.supports_fc = _settings.SUPPORTS_FUNCTION_CALLING

        # 2. Dependencies
        self.llm = llm_client
        self.allowed_tools = tools
        self.prompt_engine = PromptEngine()
        
        # 3. Session Management
        self.user_id = user_id
        self.session_id = session_id or str(uuid.uuid4())
        
        if session_manager:
            self.sm = session_manager
        else:
            # SDK/CLI Mode: Init internal DB
            effective_db_url = db_url or _settings.DATABASE_URL or "sqlite:///:memory:"
            # We need a way to get a session from a raw URL here without global app state
            # Assuming lagent.memory.db has a helper or we use the existing one
            # We'll need to adapt init_db or use a fresh engine
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            
            # Use init_db_custom helper if exists, otherwise do manual setup
            # For now, let's assume we can create a temporary SessionManager
            self.engine = create_engine(effective_db_url, connect_args={"check_same_thread": False})
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # Ensure tables exist
            from lagent.memory.models import Base
            Base.metadata.create_all(bind=self.engine)
            
            self.db_session = SessionLocal()
            self.sm = SessionManager(self.db_session)

        self.session_data = None
        self.history = []
        self.total_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        self.unique_tool_calls = set()
        
        # Load ID/Guidelines (Legacy support, maybe move to prompt engine eventually)
        self.agents_md = ""
        if os.path.exists("AGENTS.md"):
            with open("AGENTS.md", "r") as f:
                self.agents_md = f.read()
        
        # Load session
        self._hydrate()

    def _hydrate(self):
        self.session_data = self.sm.get_or_create_session(self.session_id, self.user_id)
        self.session_id = self.session_data.id
        self.current_version = self.session_data.version
        
        # Reconstruct history for LLM context
        self.history = []
        for m in self.session_data.messages:
             try:
                 content_obj = json.loads(m.content)
                 if isinstance(content_obj, dict) and "type" in content_obj:
                     if content_obj["type"] == "thought":
                         self.history.append({"role": m.role, "content": content_obj["content"]})
                     elif content_obj["type"] == "item.started":
                         item = content_obj.get("item", {})
                         action_repr = {
                             "action": {
                                 "name": item.get("tool"),
                                 "code": item.get("args")
                             }
                         }
                         self.history.append({"role": m.role, "content": json.dumps(action_repr)})
                     elif content_obj["type"] == "item.completed":
                         item = content_obj.get("item", {})
                         output = item.get("aggregated_output", "")
                         self.history.append({"role": m.role, "content": f"Observation: {output}"})
                     else:
                         self.history.append({"role": m.role, "content": m.content})
                 else:
                     self.history.append({"role": m.role, "content": m.content})
             except:
                 self.history.append({"role": m.role, "content": m.content})

    def _save_interaction(self, role: str, content: str | dict, tool_name: str = None, new_status: str =  AgentState.THINKING):
        content_str = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
        
        tool_call_id = None
        if isinstance(content, dict) and "item" in content:
             tool_call_id = content["item"].get("id")
             if tool_name is None:
                 tool_name = content["item"].get("tool")

        if isinstance(content, dict) and "type" in content:
             if content["type"] == "thought":
                 self.history.append({"role": role, "content": content["content"]})
             elif content["type"] == "item.started":
                 item = content["item"]
                 action_repr = {"action": {"name": item["tool"], "code": item["args"]}}
                 self.history.append({"role": role, "content": json.dumps(action_repr)})
             elif content["type"] == "item.completed":
                 item = content["item"]
                 self.history.append({"role": role, "content": f"Observation: {item['aggregated_output']}"})
        else:
             self.history.append({"role": role, "content": content_str})
        
        self.sm.save_step(
            session_id=self.session_id,
            new_messages=[{"role": role, "content": content_str, "tool_name": tool_name, "tool_call_id": tool_call_id}],
            new_status=new_status,
            old_version=self.current_version
        )
        self.current_version += 1

    def _build_system_prompt(self, use_compact_tools: bool = True) -> str:
        """Build system prompt. Use compact tools for non-FC mode, JSON for FC mode."""
        if use_compact_tools:
            tools_section = self._format_tools_compact()
        else:
            all_schemas = registry.get_schemas()
            if self.allowed_tools:
                target_schemas = [s for s in all_schemas if s["name"] in self.allowed_tools]
            else:
                target_schemas = all_schemas
            tools_section = json.dumps(target_schemas, indent=2)
        
        return self.prompt_engine.render(
            "system.j2",
            tools_section=tools_section,
            agents_md=self.agents_md,
            final_answer_marker=self.final_answer_marker
        )

    def _get_tools_for_fc(self) -> List[Dict]:
        """Convert registry schemas to OpenAI function calling format."""
        all_schemas = registry.get_schemas()
        if self.allowed_tools:
            target_schemas = [s for s in all_schemas if s["name"] in self.allowed_tools]
        else:
            target_schemas = all_schemas
        
        tools = []
        for schema in target_schemas:
            tools.append({
                "type": "function",
                "function": {
                    "name": schema["name"],
                    "description": schema.get("description", ""),
                    "parameters": schema.get("parameters", {"type": "object", "properties": {}})
                }
            })
        return tools

    def _format_tools_compact(self) -> str:
        """Generate compact tool descriptions for non-FC mode."""
        all_schemas = registry.get_schemas()
        if self.allowed_tools:
            target_schemas = [s for s in all_schemas if s["name"] in self.allowed_tools]
        else:
            target_schemas = all_schemas
        
        lines = []
        for schema in target_schemas:
            name = schema["name"]
            desc = schema.get("description", "").split("\n")[0]  # First line only
            params = schema.get("parameters", {}).get("properties", {})
            param_strs = []
            for p_name, p_info in params.items():
                p_type = p_info.get("type", "any")
                param_strs.append(f"{p_name}: {p_type}")
            params_str = ", ".join(param_strs)
            lines.append(f"- {name}({params_str}): {desc}")
        
        return "\n".join(lines)

    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        new_content = (content or "").strip()
        if new_content.startswith("{"):
            try:
                return json.loads(new_content)
            except Exception:
                pass

        decoder = json.JSONDecoder()
        last_obj = None
        i = 0
        n = len(new_content)

        while i < n:
            j = new_content.find("{", i)
            if j == -1:
                break
            try:
                obj, end = decoder.raw_decode(new_content[j:])
                if isinstance(obj, dict):
                    last_obj = obj
                i = j + end
            except Exception:
                i = j + 1

        if last_obj is not None:
            return last_obj

        return {"thought": content, "final_answer": new_content}

    def run(self, user_query: str) -> Generator[Dict, None, None]:
        self._save_interaction(MessageRole.USER, user_query)
        yield {"event": "input_received", "content": user_query}

        steps = 0
        while steps < self.max_steps:
            steps += 1
            step_start_time = time.time()
            
            yield {"event": "status", "content": f"Thinking (Step {steps})..."}
            
            # Route based on FC support
            if self.supports_fc:
                # Native Function Calling Mode (tools passed via API, not in prompt)
                messages = [{"role": "system", "content": self._build_system_prompt(use_compact_tools=False)}] + self.history
                tools = self._get_tools_for_fc()
                llm_result = self.llm.chat_with_tools(messages, tools)
                
                llm_response = llm_result.get("content") or ""
                tool_calls = llm_result.get("tool_calls")
                
                # Convert FC response to internal format
                if tool_calls:
                    # Model wants to call a tool
                    tc = tool_calls[0]  # Handle first tool call
                    parsed = {
                        "thought": f"Calling {tc['name']}",
                        "action": {
                            "name": tc["name"],
                            "code": tc["arguments"]  # JSON string from FC
                        }
                    }
                else:
                    # No tool call, treat as final answer
                    parsed = {"thought": f"{self.final_answer_marker} {llm_response}", "final_answer": llm_response}
            else:
                # Prompt-based Mode (fallback)
                messages = [{"role": "system", "content": self._build_system_prompt()}] + self.history
                llm_result = self.llm.chat(messages)
                llm_response = llm_result["content"]
                parsed = self._parse_llm_response(llm_response)
            
            step_duration = time.time() - step_start_time
            usage = llm_result.get("usage", {}) or {}
            
            self.total_usage["input_tokens"] += usage.get("input_tokens", 0)
            self.total_usage["output_tokens"] += usage.get("output_tokens", 0)
            self.total_usage["total_tokens"] += usage.get("total_tokens", 0)
            
            input_cost = (self.total_usage["input_tokens"] / 1000) * self.input_price
            output_cost = (self.total_usage["output_tokens"] / 1000) * self.output_price
            total_cost = input_cost + output_cost
            
            if self.debug:
                debug_data = {
                    "step": steps,
                    "history_len": len(self.history),
                    "current_usage": self.total_usage,
                    "input_cost": input_cost,
                    "output_cost": output_cost,
                    "total_cost": total_cost,
                    "currency": self.currency,
                    "llm_response_preview": llm_response[:100] + "..." if len(llm_response) > 100 else llm_response
                }
                
                yield {"event": "debug", "data": debug_data}
                
                self.sm.save_debug_log(
                    session_id=self.session_id,
                    step=steps,
                    data=debug_data,
                    duration=step_duration,
                    input_cost=input_cost,
                    output_cost=output_cost,
                    total_cost=total_cost,
                    model_provider_id=None, # Removed legacy provider logic for now or we can re-add if needed
                    input_tokens=self.total_usage["input_tokens"],
                    output_tokens=self.total_usage["output_tokens"],
                    total_tokens=self.total_usage["total_tokens"],
                    currency=self.currency
                )
            
            thought_content = parsed.get("thought", "")
            if self.final_answer_marker in thought_content:
                full_thought = thought_content
                _, answer = full_thought.split(self.final_answer_marker, 1)
                answer = answer.strip()

                thought_event = {"type": "thought", "step": steps, "content": full_thought}
                self._save_interaction(MessageRole.ASSISTANT, thought_event, new_status=AgentState.THINKING)
                yield {"event": "thought", "content": full_thought}

                if len(self.unique_tool_calls) < self.min_tool_use:
                    error_msg = f"Constraint Violation: You must use at least {self.min_tool_use} tools to verify information before answering. You have used {len(self.unique_tool_calls)} tools so far."
                    refusal_event = {"type": "thought", "step": steps, "content": error_msg}
                    self._save_interaction(MessageRole.SYSTEM, refusal_event, new_status=AgentState.THINKING)
                    yield {"event": "thought", "content": error_msg}
                    continue

                self._save_interaction(MessageRole.ASSISTANT, answer, new_status=AgentState.COMPLETED)
                yield {"event": "final_answer", "content": answer}
                break
            
            if "thought" in parsed and parsed.get("thought"):
                thought_content = parsed["thought"]
                thought_event = {"type": "thought", "step": steps, "content": thought_content}
                self._save_interaction(MessageRole.ASSISTANT, thought_event, new_status=AgentState.THINKING)
                yield {"event": "thought", "content": thought_content}
            
            if "final_answer" in parsed:
                if len(self.unique_tool_calls) < self.min_tool_use:
                    error_msg = f"Constraint Violation: You must use at least {self.min_tool_use} tools to verify information before answering. You have used {len(self.unique_tool_calls)} tools so far."
                    refusal_event = {"type": "thought", "step": steps, "content": error_msg}
                    self._save_interaction(MessageRole.SYSTEM, refusal_event, new_status=AgentState.THINKING)
                    yield {"event": "thought", "content": error_msg}
                    continue

                self._save_interaction(MessageRole.ASSISTANT, parsed["final_answer"], new_status=AgentState.COMPLETED)
                yield {"event": "final_answer", "content": parsed["final_answer"]}
                break
            
            if "action" in parsed:
                if len(self.unique_tool_calls) >= self.max_tool_use:
                     error_msg = f"Constraint Violation: Maximum tool usage ({self.max_tool_use}) reached. You cannot use more tools. Please provide the Final Answer now."
                     refusal_event = {"type": "thought", "step": steps, "content": error_msg}
                     self._save_interaction(MessageRole.SYSTEM, refusal_event, new_status=AgentState.THINKING)
                     yield {"event": "thought", "content": error_msg}
                     continue

                action = parsed["action"]
                tool_name = action.get("name")
                code = action.get("code") or action.get("arguments") or action.get("args") or action.get("parameters")
                action_id = f"call_{uuid.uuid4().hex[:8]}"
                self.unique_tool_calls.add(action_id)
                
                start_event = {
                    "type": "item.started",
                    "step": steps,
                    "item": {
                        "id": action_id,
                        "type": "tool_execution",
                        "tool": tool_name,
                        "args": code,
                        "status": "in_progress"
                    }
                }
                
                self._save_interaction(MessageRole.ASSISTANT, start_event, new_status=AgentState.EXECUTING)
                yield {"event": "item.started", "data": start_event}

                if tool_name == "python":
                    result = sandbox.execute(code)
                    output = result["output"] if result["success"] else f"Error: {result['error']}"
                    exit_code = 0 if result["success"] else 1
                elif registry.get_tool(tool_name):
                    try:
                        args = code
                        if isinstance(code, str):
                            stripped = code.strip()
                            if stripped.startswith("{") and stripped.endswith("}"):
                                try:
                                    args = json.loads(stripped)
                                except Exception:
                                    args = code
                        output = str(registry.execute(tool_name, args))
                        exit_code = 0
                    except Exception as e:
                        output = f"Tool Execution Error: {e}"
                        exit_code = 1
                else:
                    output = f"Unknown tool: {tool_name}"
                    exit_code = 1

                end_event = {
                    "type": "item.completed",
                    "step": steps,
                    "item": {
                        "id": action_id,
                        "type": "tool_execution",
                        "tool": tool_name,
                        "args": code,
                        "aggregated_output": output,
                        "exit_code": exit_code,
                        "status": "completed"
                    }
                }
                
                self._save_interaction(MessageRole.USER, end_event, tool_name=tool_name, new_status=AgentState.THINKING)
                yield {"event": "item.completed", "data": end_event}
                continue
            
            self._save_interaction(MessageRole.ASSISTANT, str(parsed), new_status=AgentState.THINKING)
            yield {"event": "final_answer", "content": str(parsed)}
            break
            
        if steps >= self.max_steps:
            yield {"event": "error", "content": "Max steps reached."}
            
        yield {
            "event": "usage_stats", 
            "content": {
                "usage": self.total_usage,
                "cost": {
                    "input_cost": input_cost, 
                    "output_cost": output_cost, 
                    "total_cost": total_cost,
                    "currency": self.currency
                }
            }
        }
