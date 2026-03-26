from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver 
from agent.state import AgentState
from agent.nodes import agent_node, human_review_node, tool_node, should_continue, should_execute_after_review

def build_graph():
    graph = StateGraph(AgentState)

    # Nodos
    graph.add_node("agent_node", agent_node)
    graph.add_node("human_review_node", human_review_node)
    graph.add_node("tool_node", tool_node)

    # Edges
    graph.add_edge(START, "agent_node")

    graph.add_conditional_edges(
        "agent_node",
        should_continue,
        ["human_review_node", "tool_node", END]
    )

    graph.add_conditional_edges(
        "human_review_node",
        should_execute_after_review,
        ["tool_node", "agent_node"]
    )

    graph.add_edge("tool_node", "agent_node")

    # MemorySaver es el checkpointer — guarda el estado del grafo
    # cuando interrupt() lo pausa, para poder reanudarlo después
    checkpointer = MemorySaver()

    return graph.compile(checkpointer=checkpointer)