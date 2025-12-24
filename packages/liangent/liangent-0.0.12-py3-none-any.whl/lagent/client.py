from typing import List, Generator, Union, Dict, Any
from lagent.core.llm import LLMClient
from lagent.core.agent import ContextAgent
from lagent.config import get_settings

class Lagent:
    """
    High-level client for Lagent.
    Provides a simple interface to initialize and interact with the agent.
    """
    def __init__(
        self, 
        api_key: str = None, 
        base_url: str = None, 
        model_name: str = None, 
        db_url: str = None, 
        tools: List[str] = None,
        verbose: bool = False
    ):
        """
        Initialize the Lagent client.
        
        Args:
            api_key: OpenAI API Key.
            base_url: OpenAI Base URL.
            model_name: Model name (e.g., gpt-3.5-turbo).
            db_url: Database URL. Defaults to in-memory SQLite if not provided and not in env.
            tools: List of tool names to enable.
            verbose: If True, prints thinking process and tool execution details to console.
        """
        self.verbose = verbose
        # 1. Initialize LLM
        self.llm = LLMClient(api_key=api_key, base_url=base_url, model_name=model_name)
        
        # 2. Determine DB URL
        # If explicitly passed, use it.
        # If not, try settings/env. 
        # If still none, agent will default to :memory: internally, so passing None is fine.
        
        # 3. Initialize Agent
        # Single-user, single-session mode for SDK usage typically
        self.agent = ContextAgent(
            llm_client=self.llm,
            db_url=db_url,
            tools=tools,
            user_id="sdk_user",
            debug=verbose # Pass verbose as debug flag
        )
        
    def chat(self, query: str) -> str:
        """
        Send a query to the agent and get the final response synchronously.
        If verbose=True, prints logs to stdout.
        """
        import json
        final_answer = ""
        
        # Re-use the loop structure for both verbose and non-verbose to capture final answer
        for event in self.agent.run(query):
            evt_type = event.get("event")
            
            if self.verbose:
                if evt_type == "thought":
                    content = event.get("content", "")
                    # Check if thought contains the marker to avoid duplicate printing (Agent will emit final_answer next)
                    if content and self.agent.final_answer_marker not in content:
                         print(f"\n[Thinking] {content}", end="", flush=True)
                
                elif evt_type == "item.started":
                    item = event.get("data", {}).get("item", {})
                    print(f"\n[Tool Call] {item.get('tool')}({item.get('args')})", end="", flush=True)
                
                elif evt_type == "item.completed":
                    item = event.get("data", {}).get("item", {})
                    output = item.get("aggregated_output", "")
                    if len(output) > 100:
                         output = output[:100] + "..."
                    print(f"\n[Tool Output] {output}", end="", flush=True)
                
                elif evt_type == "debug":
                    data = event.get("data", {})
                    print(f"\n[Debug] Step {data.get('step')} | Cost: {data.get('total_cost'):.4f} {data.get('currency')}", end="", flush=True)
                
                elif evt_type == "usage_stats":
                    content = event.get("content", {})
                    cost = content.get("cost", {})
                    print(f"\n\n[Stats] Total Cost: {cost.get('total_cost'):.4f} {cost.get('currency')}", end="", flush=True)
                
                elif evt_type == "error":
                    print(f"\nError: {event.get('content')}")
            
            if evt_type == "final_answer":
                final_answer = event.get("content")
                if self.verbose:
                    print_content = final_answer
                    # Try to parse if it looks like JSON to show cleaner output
                    if isinstance(final_answer, str) and final_answer.strip().startswith("{"):
                        try:
                            parsed = json.loads(final_answer)
                            if isinstance(parsed, dict):
                                if "final_answer" in parsed:
                                    print_content = parsed["final_answer"]
                                elif "thought" in parsed:
                                    # Fallback if thought contains data
                                    print_content = parsed["thought"]
                        except:
                            pass
                    print(f"\n\n[Final Answer] {print_content}\n")
            elif evt_type == "error":
                if not self.verbose: # If verbose, we already printed it
                    pass
                raise RuntimeError(f"Agent Error: {event.get('content')}")
                
        return final_answer
        
    def stream(self, query: str) -> Generator[Dict[str, Any], None, None]:
        """
        Stream events from the agent.
        """
        yield from self.agent.run(query)
