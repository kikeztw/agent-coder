# agent/nodes.py
from typing import Literal
from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, ToolMessage
from langgraph.graph import END
from langgraph.types import interrupt
from agent.state import AgentState
from agent.tools import tools, tools_by_name

llm = init_chat_model("openai:gpt-4o-mini", temperature=0)
llm_with_tools = llm.bind_tools(tools)

DANGEROUS_TOOLS = {"write_file", "run_python"}


def agent_node(state: AgentState) -> dict:
    response = llm_with_tools.invoke(
        [SystemMessage(content="Eres un asistente útil de programación.")] + state["messages"]
    )
    return {"messages": [response]}


def human_review_node(state: AgentState) -> dict:
    last_message = state["messages"][-1]
    tool_call = last_message.tool_calls[0]
    tool_name = tool_call["name"]

    if tool_name not in DANGEROUS_TOOLS:
        return {}

    human_decision = interrupt({
        "tool_name": tool_name,
        "tool_args": tool_call["args"],
        "message": f"¿Confirmas ejecutar '{tool_name}' con args {tool_call['args']}?"
    })

    if human_decision != "s":
        return {
            "messages": [
                ToolMessage(
                    # ← Mensaje más explícito: le dice al LLM que NO reintente
                    content=(
                        f"El usuario rechazó ejecutar '{tool_name}'. "
                        f"No vuelvas a intentar esta acción. "
                        f"Informa al usuario que la acción fue cancelada y pregunta si desea hacer algo diferente."
                    ),
                    tool_call_id=tool_call["id"]
                )
            ]
        }

    return {}


def tool_node(state: AgentState) -> dict:
    results = []
    for tool_call in state["messages"][-1].tool_calls:
        selected_tool = tools_by_name[tool_call["name"]]
        observation = selected_tool.invoke(tool_call["args"])
        results.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    return {"messages": results}


def should_continue(state: AgentState) -> Literal["human_review_node", "tool_node", END]:
    last_message = state["messages"][-1]

    if not last_message.tool_calls:
        return END

    tool_name = last_message.tool_calls[0]["name"]

    if tool_name in DANGEROUS_TOOLS:
        return "human_review_node"

    return "tool_node"


def should_execute_after_review(state: AgentState) -> Literal["tool_node", "agent_node"]:
    last_message = state["messages"][-1]

    if hasattr(last_message, "content") and "rechazó" in last_message.content:
        return "agent_node"

    return "tool_node"
