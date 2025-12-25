import os
import openai
from typing import List, Dict, Any, Tuple, Optional
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from typing_extensions import TypedDict
from athenah_ai.logger import logger

from athenah_ai.client import AthenahClient
from athenah_ai.researcher.tools import get_research_tools

# --- State Definition ---


class AgentState(TypedDict):
    messages: List[Dict[str, Any]]


# --- Utility Functions ---


def safe_get_env(key: str, default: str = "") -> str:
    value = os.environ.get(key, default)
    if not value:
        logger.warning(f"Environment variable {key} not set, using default: {default}")
    return value


def safe_run(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Error in {func.__name__}: {e}")
        return None


def get_token_total(prompt: str, model: str = "gpt-4o-mini") -> int:
    import tiktoken

    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(prompt))
    except Exception as e:
        logger.error(f"Token count error: {e}")
        return 0


def get_max_tokens(model_name: str) -> int:
    MODEL_MAP = {
        "gpt-4o-mini": 16383,
        "gpt-4o": 4095,
        "gpt-4-turbo": 4095,
        "gpt-4": 8191,
        "gpt-4.1": 32768,
        "o4-mini": 100000,
    }
    return MODEL_MAP.get(model_name, 4096)


class ResearcherClient:
    def __init__(
        self,
        athenah_client: Optional[AthenahClient] = None,
        google_api_key: Optional[str] = None,
        google_cse_id: Optional[str] = None,
        bing_api_key: Optional[str] = None,
        enable_torrents: bool = True,
    ):
        self.athenah = athenah_client or AthenahClient()
        self.llm = self.athenah.llm
        self.vector_db = self.athenah.db
        self.google_api_key = google_api_key
        self.google_cse_id = google_cse_id
        self.bing_api_key = bing_api_key
        self.enable_torrents = enable_torrents

    def _find_query_info(self, query: str) -> str:
        system = "You are a world-class researcher. Find all relevant information about the given query."
        prompt = f"Research and summarize all important facts, people, and events related to: {query}"
        return self.athenah.base_prompt(system, prompt)

    def _extract_threads(self, info: str) -> List[str]:
        system = "Extract all unique names, organizations, or leads from the following text. Return as a list."
        prompt = info
        result = self.athenah.base_prompt(system, prompt)
        # Try to parse as list, fallback to splitting lines
        try:
            import ast

            leads = ast.literal_eval(result)
            if isinstance(leads, list):
                return [str(x) for x in leads]
        except Exception:
            return [line.strip() for line in result.splitlines() if line.strip()]
        return []

    def _research_thread(self, thread: str) -> str:
        system = "You are a research assistant. Deeply investigate the following lead and provide a detailed summary."
        prompt = thread
        return self.athenah.base_prompt(system, prompt)

    def research_query(self, query: str) -> Dict[str, Any]:
        info = safe_run(self._find_query_info, query)
        if not info:
            return {"error": "Failed to find query info."}
        threads = safe_run(self._extract_threads, info)
        if not threads:
            return {"info": info, "threads": [], "results": {}}
        results = {}
        for thread in threads:
            results[thread] = safe_run(self._research_thread, thread)
        return {"info": info, "threads": threads, "results": results}

    def agent_research(self, query: str) -> Dict[str, Any]:
        # Use langchain agent tools if needed, fallback to LLM
        info = self._find_query_info(query)
        threads = self._extract_threads(info)
        results = {}

        for thread in threads:
            # Get all research tools
            tools = get_research_tools(
                vector_db=self.vector_db,
                google_api_key=self.google_api_key,
                google_cse_id=self.google_cse_id,
                bing_api_key=self.bing_api_key,
                enable_torrents=self.enable_torrents,
            )
            llm_with_tools = self.llm.bind_tools(tools)

            # Define agent node
            def agent_node(state: AgentState) -> AgentState:
                messages = state["messages"]
                response = llm_with_tools.invoke(messages)
                return {"messages": messages + [response]}

            # Define conditional edge logic
            def should_continue(state: AgentState) -> str:
                messages = state["messages"]
                last_message = messages[-1]
                if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                    return "continue"
                return "end"

            # Build workflow
            workflow = StateGraph(AgentState)
            workflow.add_node("agent", agent_node)
            workflow.add_node("tools", ToolNode(tools))

            workflow.add_edge(START, "agent")
            workflow.add_conditional_edges(
                "agent", should_continue, {"continue": "tools", "end": END}
            )
            workflow.add_edge("tools", "agent")

            # Compile workflow
            compiled_workflow = workflow.compile(checkpointer=MemorySaver())

            try:
                result = compiled_workflow.invoke(
                    {"messages": [{"role": "user", "content": thread}]},
                    config={"configurable": {"thread_id": thread}},
                )
                results[thread] = result
            except Exception as e:
                logger.error(f"Agent error for thread '{thread}': {e}")
                results[thread] = f"Agent error: {e}"

        return {"info": info, "threads": threads, "results": results}
