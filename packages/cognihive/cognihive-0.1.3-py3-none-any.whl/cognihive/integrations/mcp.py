"""
Anthropic MCP (Model Context Protocol) integration for CogniHive.

Provides an MCP server that exposes CogniHive's transactive memory
capabilities to Claude and other MCP-compatible clients.

MCP allows Claude to:
- Query "who knows what" about topics
- Store and retrieve memories
- Route questions to experts
"""

from typing import Any, Dict, List, Optional
import json

try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    Server = None
    Tool = None
    TextContent = None

from cognihive.core.hive import Hive


# MCP Tool Definitions
MCP_TOOLS = [
    {
        "name": "cognihive_who_knows",
        "description": "Find which agent or team member is the expert on a specific topic. Returns a ranked list of experts with their expertise scores.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The topic to find experts for"
                }
            },
            "required": ["topic"]
        }
    },
    {
        "name": "cognihive_remember",
        "description": "Store a piece of knowledge or information in the team's collective memory.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The knowledge to store"
                },
                "agent": {
                    "type": "string",
                    "description": "Name of the agent storing this memory"
                },
                "topics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Related topics for this memory"
                }
            },
            "required": ["content"]
        }
    },
    {
        "name": "cognihive_recall",
        "description": "Search for relevant memories and knowledge based on a query.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results (default: 5)",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "cognihive_ask_expert",
        "description": "Route a question to the most appropriate expert and get relevant memories.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The question to route"
                }
            },
            "required": ["question"]
        }
    },
    {
        "name": "cognihive_list_agents",
        "description": "List all registered agents and their expertise areas.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]


class MCPHive:
    """CogniHive MCP Server integration.
    
    Exposes CogniHive capabilities through Anthropic's Model Context Protocol,
    allowing Claude to use transactive memory features.
    
    Example (as MCP server):
        ```python
        from cognihive.integrations import MCPHive
        
        hive = MCPHive()
        hive.register_agent("researcher", expertise=["research"])
        
        # Run as MCP server
        hive.run_server()
        ```
    
    Example (claude_desktop_config.json):
        ```json
        {
          "mcpServers": {
            "cognihive": {
              "command": "python",
              "args": ["-m", "cognihive.integrations.mcp"]
            }
          }
        }
        ```
    """
    
    def __init__(
        self,
        name: str = "mcp_hive",
        persist_directory: Optional[str] = None,
        default_agent: str = "claude",
        **kwargs
    ):
        """Initialize MCP-compatible Hive.
        
        Args:
            name: Name of the hive
            persist_directory: Path for persistent storage
            default_agent: Default agent for memory operations
        """
        self.hive = Hive(
            name=name,
            persist_directory=persist_directory,
            **kwargs
        )
        self.default_agent = default_agent
        
        # Register default agent
        self.hive.register_agent(
            name=default_agent,
            expertise=["general"],
            role="Claude Assistant"
        )
        
        self._server = None
    
    def register_agent(
        self,
        name: str,
        expertise: Optional[List[str]] = None,
        role: str = ""
    ):
        """Register an agent with the hive."""
        return self.hive.register_agent(name=name, expertise=expertise, role=role)
    
    def get_tools(self) -> List[Dict]:
        """Get MCP tool definitions."""
        return MCP_TOOLS
    
    def handle_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> str:
        """Handle an MCP tool call.
        
        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            
        Returns:
            JSON string result
        """
        handlers = {
            "cognihive_who_knows": self._handle_who_knows,
            "cognihive_remember": self._handle_remember,
            "cognihive_recall": self._handle_recall,
            "cognihive_ask_expert": self._handle_ask_expert,
            "cognihive_list_agents": self._handle_list_agents,
        }
        
        handler = handlers.get(tool_name)
        if not handler:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
        
        result = handler(arguments)
        return json.dumps(result, default=str)
    
    def _handle_who_knows(self, args: Dict) -> Dict:
        """Handle who_knows tool."""
        topic = args.get("topic", "")
        if not topic:
            return {"error": "Topic is required"}
        
        experts = self.hive.who_knows(topic)
        return {
            "topic": topic,
            "experts": [
                {"agent": name, "score": round(score, 2)}
                for name, score in experts
            ],
            "best_expert": experts[0][0] if experts else None
        }
    
    def _handle_remember(self, args: Dict) -> Dict:
        """Handle remember tool."""
        content = args.get("content", "")
        if not content:
            return {"error": "Content is required"}
        
        agent = args.get("agent", self.default_agent)
        topics = args.get("topics", [])
        
        memory = self.hive.remember(content, agent=agent, topics=topics)
        return {
            "success": True,
            "memory_id": memory.id,
            "agent": agent
        }
    
    def _handle_recall(self, args: Dict) -> Dict:
        """Handle recall tool."""
        query = args.get("query", "")
        if not query:
            return {"error": "Query is required"}
        
        top_k = args.get("top_k", 5)
        results = self.hive.recall(query, top_k=top_k)
        
        return {
            "query": query,
            "memories": [
                {
                    "content": m.content,
                    "agent": m.owner_name,
                    "topics": m.topics,
                    "score": round(s, 2)
                }
                for m, s in results
            ]
        }
    
    def _handle_ask_expert(self, args: Dict) -> Dict:
        """Handle ask_expert tool."""
        question = args.get("question", "")
        if not question:
            return {"error": "Question is required"}
        
        result = self.hive.ask(question)
        return {
            "question": question,
            "expert": result.get("expert"),
            "confidence": round(result.get("confidence", 0), 2),
            "reasoning": result.get("reasoning"),
            "memories": [
                {"content": m.content, "agent": m.owner_name}
                for m in result.get("memories", [])
            ]
        }
    
    def _handle_list_agents(self, args: Dict) -> Dict:
        """Handle list_agents tool."""
        agents = self.hive.list_agents()
        return {
            "agents": [
                {
                    "name": a.name,
                    "role": a.role,
                    "expertise": a.declared_expertise
                }
                for a in agents
            ],
            "count": len(agents)
        }
    
    def create_mcp_server(self) -> Any:
        """Create an MCP server instance.
        
        Returns:
            MCP Server instance (requires mcp package)
        """
        if not MCP_AVAILABLE:
            raise ImportError(
                "MCP package required. Install with: pip install mcp"
            )
        
        server = Server("cognihive")
        
        @server.list_tools()
        async def list_tools():
            tools = []
            for tool_def in MCP_TOOLS:
                tools.append(Tool(
                    name=tool_def["name"],
                    description=tool_def["description"],
                    inputSchema=tool_def["inputSchema"]
                ))
            return tools
        
        @server.call_tool()
        async def call_tool(name: str, arguments: dict):
            result = self.handle_tool_call(name, arguments)
            return [TextContent(type="text", text=result)]
        
        self._server = server
        return server
    
    def run_server(self):
        """Run the MCP server (blocking)."""
        if not MCP_AVAILABLE:
            raise ImportError(
                "MCP package required. Install with: pip install mcp"
            )
        
        import asyncio
        from mcp.server.stdio import stdio_server
        
        server = self.create_mcp_server()
        
        async def main():
            async with stdio_server() as (read, write):
                await server.run(read, write, server.create_initialization_options())
        
        asyncio.run(main())


# CLI entry point for running as MCP server
def main():
    """Run CogniHive as an MCP server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="CogniHive MCP Server")
    parser.add_argument("--persist", "-p", help="Persistence directory")
    parser.add_argument("--name", "-n", default="cognihive", help="Hive name")
    args = parser.parse_args()
    
    hive = MCPHive(
        name=args.name,
        persist_directory=args.persist
    )
    
    print("Starting CogniHive MCP Server...", file=__import__("sys").stderr)
    hive.run_server()


if __name__ == "__main__":
    main()
