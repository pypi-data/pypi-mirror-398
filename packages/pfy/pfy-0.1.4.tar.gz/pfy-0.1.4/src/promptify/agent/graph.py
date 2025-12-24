from langgraph.graph import StateGraph, START, END
from .state import AgentState
from .node import triageAgent, criticAgent, expertAgent, promptSmith

def create_promptify_graph():
    """Builds and compiles the Promptify agent graph"""
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("triage", triageAgent)
    graph.add_node("critic", criticAgent)
    graph.add_node("expert", expertAgent)
    graph.add_node("smith", promptSmith)
    
    # Define flow
    graph.add_edge(START, "triage")
    graph.add_edge("triage", "critic")
    graph.add_edge("critic", "expert")
    graph.add_edge("expert", "smith")
    graph.add_edge("smith", END)
    
    return graph.compile()

# Export compiled graph
promptify = create_promptify_graph()