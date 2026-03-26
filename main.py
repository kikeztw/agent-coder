# main.py
from dotenv import load_dotenv
load_dotenv()
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from agent.graph import build_graph


graph = build_graph()


def run_turn(user_input: str, thread_id: str, config: dict):
    """Ejecuta un turno de conversación y maneja interrupts."""

    print("─" * 40)

    _stream_until_interrupt(
        graph.stream(
            {"messages": [HumanMessage(content=user_input)]},
            config=config,
            stream_mode="values"
        )
    )

    # Loop de confirmaciones
    state = graph.get_state(config)
    while state.next:
        interrupt_data = state.tasks[0].interrupts[0].value
        print(f"\\n⚠️  Confirmación requerida:")
        print(f"   Tool: {interrupt_data['tool_name']}")
        print(f"   Args: {interrupt_data['tool_args']}")

        decision = input("   ¿Ejecutar? (s/n): ").strip().lower()

        _stream_until_interrupt(
            graph.stream(
                Command(resume=decision),
                config=config,
                stream_mode="values"
            )
        )

        state = graph.get_state(config)

    print("─" * 40)


def _stream_until_interrupt(stream):
    """Imprime eventos del stream evitando duplicados por ID."""
    seen_ids = set()

    for event in stream:
        last_msg = event["messages"][-1]
        msg_type = type(last_msg).__name__

        msg_id = getattr(last_msg, "id", None)
        if msg_id and msg_id in seen_ids:
            continue
        if msg_id:
            seen_ids.add(msg_id)

        if msg_type == "AIMessage":
            if last_msg.tool_calls:
                print(f"🤖 Agente quiere usar: {last_msg.tool_calls[0]['name']}")
                print(f"   Args: {last_msg.tool_calls[0]['args']}")
            elif last_msg.content:
                print(f"🤖 Agente: {last_msg.content}")

        elif msg_type == "ToolMessage":
            print(f"🔧 Tool result: {last_msg.content}")


def main():
    print("╔══════════════════════════════════════╗")
    print("║        ReAct Coding Agent  🤖         ║")
    print("║   escribe \\'exit\\' para salir          ║")
    print("╚══════════════════════════════════════╝")
    print()

    # thread_id fijo — mantiene memoria durante toda la sesión
    thread_id = "session-1"
    config = {"configurable": {"thread_id": thread_id}}

    while True:
        try:
            user_input = input("👤 Tú: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\\n👋 Hasta luego!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "salir"):
            print("👋 Hasta luego!")
            break

        run_turn(user_input, thread_id, config)


if __name__ == "__main__":
    main()