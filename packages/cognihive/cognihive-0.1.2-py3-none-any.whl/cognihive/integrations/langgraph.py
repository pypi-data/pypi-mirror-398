"""
LangGraph Integration for CogniHive.

Provides seamless integration with LangGraph workflows.
Enables transactive memory for LangGraph multi-agent graphs.
"""

from typing import Any, Dict, List, Optional, TypedDict

from cognihive.core.hive import Hive
from cognihive.core.memory_types import Memory

# Check if LangGraph is available
try:
    from langgraph.graph import StateGraph, END
    from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    StateGraph = None
    END = None


class HiveState(TypedDict, total=False):
    """State that includes CogniHive memory."""
    messages: List[Any]
    current_agent: str
    memory_context: str
    expert_recommendation: str
    hive_memories: List[Dict[str, Any]]


class LangGraphHive(Hive):
    """CogniHive with LangGraph-specific features.
    
    Extends the base Hive with LangGraph integration capabilities:
    - State management with memory context
    - Memory-aware node creation
    - Expert routing nodes
    
    Example:
        >>> from langgraph.graph import StateGraph
        >>> from cognihive.integrations import LangGraphHive
        >>> 
        >>> hive = LangGraphHive()
        >>> hive.register_agent("researcher", expertise=["research"])
        >>> hive.register_agent("writer", expertise=["writing"])
        >>> 
        >>> # Create a memory-aware graph
        >>> graph = hive.create_graph(HiveState)
        >>> graph.add_node("route", hive.expert_router_node())
        >>> graph.add_node("researcher", hive.memory_node("researcher", researcher_fn))
        >>> graph.add_node("writer", hive.memory_node("writer", writer_fn))
    """
    
    def __init__(
        self,
        name: str = "langgraph_hive",
        persist_directory: Optional[str] = None,
        **kwargs
    ):
        """Initialize a LangGraph-enabled Hive.
        
        Args:
            name: Hive name
            persist_directory: Path for persistent storage
            **kwargs: Additional Hive arguments
        """
        if not LANGGRAPH_AVAILABLE:
            raise ImportError(
                "LangGraph is required for LangGraphHive. "
                "Install with: pip install langgraph"
            )
        
        super().__init__(
            name=name,
            persist_directory=persist_directory,
            **kwargs
        )
    
    def create_graph(self, state_schema: type = None) -> "StateGraph":
        """Create a new LangGraph StateGraph with HiveState.
        
        Args:
            state_schema: Optional custom state schema (uses HiveState if None)
            
        Returns:
            A new StateGraph instance
        """
        schema = state_schema or HiveState
        return StateGraph(schema)
    
    def expert_router_node(self):
        """Create a node that routes to the best expert agent.
        
        Returns:
            A node function for expert routing
        """
        def router(state: HiveState) -> HiveState:
            # Get the last message
            messages = state.get("messages", [])
            if not messages:
                return state
            
            last_message = messages[-1]
            if hasattr(last_message, "content"):
                query = last_message.content
            else:
                query = str(last_message)
            
            # Get routing decision
            decision = self.route(query)
            agent_name = ""
            
            if decision.primary_agent:
                agent = self.get_agent(decision.primary_agent)
                agent_name = agent.name if agent else decision.primary_agent
            
            return {
                **state,
                "current_agent": agent_name,
                "expert_recommendation": decision.reasoning
            }
        
        return router
    
    def memory_injection_node(self):
        """Create a node that injects relevant memories into state.
        
        Returns:
            A node function for memory injection
        """
        def inject_memory(state: HiveState) -> HiveState:
            messages = state.get("messages", [])
            if not messages:
                return state
            
            last_message = messages[-1]
            if hasattr(last_message, "content"):
                query = last_message.content
            else:
                query = str(last_message)
            
            # Get relevant memories
            results = self.recall(query, top_k=3)
            
            memory_context = ""
            hive_memories = []
            
            if results:
                memory_parts = ["[Relevant team memories:]"]
                for mem, score in results:
                    if score > 0.3:
                        memory_parts.append(f"- {mem.owner_name}: {mem.content}")
                        hive_memories.append({
                            "content": mem.content,
                            "agent": mem.owner_name,
                            "score": score
                        })
                memory_context = "\n".join(memory_parts)
            
            return {
                **state,
                "memory_context": memory_context,
                "hive_memories": hive_memories
            }
        
        return inject_memory
    
    def memory_node(self, agent_name: str, node_fn):
        """Wrap a node function with memory capabilities.
        
        Args:
            agent_name: Name of the agent for this node
            node_fn: The original node function
            
        Returns:
            A wrapped node function with memory
        """
        def wrapped_node(state: HiveState) -> HiveState:
            # Call the original function
            result = node_fn(state)
            
            # Store any new messages as memories
            messages = result.get("messages", [])
            if messages:
                last_message = messages[-1]
                if hasattr(last_message, "content"):
                    content = last_message.content
                    if content and len(content) > 20:
                        self.remember(
                            content=content,
                            agent=agent_name,
                            metadata={"source": "langgraph"}
                        )
            
            return result
        
        return wrapped_node
    
    def who_knows_node(self):
        """Create a node that adds expert info to state.
        
        Returns:
            A node function for who-knows queries
        """
        def who_knows(state: HiveState) -> HiveState:
            messages = state.get("messages", [])
            if not messages:
                return state
            
            last_message = messages[-1]
            if hasattr(last_message, "content"):
                query = last_message.content
            else:
                query = str(last_message)
            
            experts = self.who_knows(query)
            
            if experts:
                expert_info = "Team experts for this topic: " + ", ".join(
                    [f"{name} ({score:.2f})" for name, score in experts[:3]]
                )
            else:
                expert_info = "No specific experts found for this topic."
            
            return {
                **state,
                "expert_recommendation": expert_info
            }
        
        return who_knows
    
    def conditional_router(self):
        """Create a conditional edge function for expert routing.
        
        Returns:
            A function suitable for add_conditional_edges
        """
        def route_by_expert(state: HiveState) -> str:
            current_agent = state.get("current_agent", "")
            if current_agent:
                return current_agent
            return "default"
        
        return route_by_expert


def create_expert_routing_graph(
    hive: LangGraphHive,
    agent_nodes: Dict[str, Any],
    default_node: str = None
) -> "StateGraph":
    """Create a complete expert-routing graph.
    
    Args:
        hive: The LangGraphHive instance
        agent_nodes: Dict of {agent_name: node_function}
        default_node: Name of default node if no expert found
        
    Returns:
        A configured StateGraph
        
    Example:
        >>> hive = LangGraphHive()
        >>> hive.register_agent("coder", expertise=["python"])
        >>> hive.register_agent("writer", expertise=["docs"])
        >>> 
        >>> graph = create_expert_routing_graph(
        ...     hive=hive,
        ...     agent_nodes={
        ...         "coder": coder_function,
        ...         "writer": writer_function
        ...     },
        ...     default_node="coder"
        ... )
    """
    if not LANGGRAPH_AVAILABLE:
        raise ImportError("LangGraph is required. Install with: pip install langgraph")
    
    graph = hive.create_graph(HiveState)
    
    # Add memory injection node
    graph.add_node("inject_memory", hive.memory_injection_node())
    
    # Add routing node
    graph.add_node("route", hive.expert_router_node())
    
    # Add agent nodes with memory wrapping
    for agent_name, node_fn in agent_nodes.items():
        wrapped = hive.memory_node(agent_name, node_fn)
        graph.add_node(agent_name, wrapped)
    
    # Set entry point
    graph.set_entry_point("inject_memory")
    
    # Add edge from memory injection to routing
    graph.add_edge("inject_memory", "route")
    
    # Add conditional routing
    route_map = {name: name for name in agent_nodes}
    if default_node:
        route_map["default"] = default_node
    
    graph.add_conditional_edges(
        "route",
        hive.conditional_router(),
        route_map
    )
    
    # Add edges from agents to END
    for agent_name in agent_nodes:
        graph.add_edge(agent_name, END)
    
    return graph
