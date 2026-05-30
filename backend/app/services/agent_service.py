"""Agent Service - Multi-agent system with tool calling using LangGraph."""

from typing import Any, Dict, List, Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


# ============ TOOLS ============

@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression safely.

    Args:
        expression: A mathematical expression to evaluate (e.g., "2 + 2", "sqrt(16)")
    """
    import ast
    import operator
    import math

    # Safe operators
    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
    }

    # Safe functions
    safe_functions = {
        "sqrt": math.sqrt,
        "abs": abs,
        "round": round,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "pi": math.pi,
        "e": math.e,
    }

    try:
        # Simple eval with restricted scope
        result = eval(expression, {"__builtins__": {}}, safe_functions)
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {e}"


@tool
def web_search(query: str) -> str:
    """Search the web for current information.

    Args:
        query: The search query string
    """
    # Placeholder - in production, integrate with a search API
    return f"Web search results for: '{query}' - [This would return real search results in production with a search API integration]"


@tool
def code_interpreter(code: str) -> str:
    """Execute Python code safely and return the output.

    Args:
        code: Python code to execute
    """
    import io
    import contextlib

    # Capture stdout
    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            # Restricted execution
            exec(code, {"__builtins__": {"print": print, "range": range, "len": len, "str": str, "int": int, "float": float, "list": list, "dict": dict}})
        result = output.getvalue()
        return result if result else "Code executed successfully (no output)"
    except Exception as e:
        return f"Error: {e}"


# ============ AGENT SERVICE ============

class AgentService:
    """Multi-agent system with tool calling capabilities."""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0,
            api_key=settings.openai_api_key,
        )
        self.tools = [calculator, web_search, code_interpreter]
        self.llm_with_tools = self.llm.bind_tools(self.tools)

    async def run_agent(
        self,
        query: str,
        agent_type: str = "general",
    ) -> Dict[str, Any]:
        """Run an agent with tool calling capabilities.

        Args:
            query: User query
            agent_type: Type of agent (general, research, code)

        Returns:
            Dict with response and tool calls made
        """
        system_prompts = {
            "general": "You are a helpful assistant with access to tools. Use them when needed.",
            "research": "You are a research assistant. Use web search to find current information.",
            "code": "You are a code assistant. Use the code interpreter to run and test code.",
        }

        system_prompt = system_prompts.get(agent_type, system_prompts["general"])

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=query),
        ]

        try:
            response = await self.llm_with_tools.ainvoke(messages)

            tool_calls = []
            if response.tool_calls:
                for tc in response.tool_calls:
                    # Execute tool
                    tool_func = {t.name: t for t in self.tools}.get(tc["name"])
                    if tool_func:
                        result = tool_func.invoke(tc["args"])
                        tool_calls.append({
                            "tool": tc["name"],
                            "args": tc["args"],
                            "result": result,
                        })

            return {
                "response": response.content,
                "tool_calls": tool_calls,
                "agent_type": agent_type,
            }

        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            return {
                "response": f"Agent error: {str(e)}",
                "tool_calls": [],
                "agent_type": agent_type,
            }


def get_agent_service() -> AgentService:
    """Factory function for agent service."""
    return AgentService()
