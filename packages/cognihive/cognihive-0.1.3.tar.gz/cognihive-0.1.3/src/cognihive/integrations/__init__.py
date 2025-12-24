"""Framework integrations."""

from cognihive.integrations.crewai import CrewAIHive, CrewAIMemory
from cognihive.integrations.autogen import AutoGenHive, AutoGenMemoryAdapter
from cognihive.integrations.langgraph import LangGraphHive

# Optional imports for LangChain
try:
    from cognihive.integrations.langchain import (
        LangChainHive,
        CogniHiveMemory,
        CogniHiveRetriever
    )
except ImportError:
    LangChainHive = None
    CogniHiveMemory = None
    CogniHiveRetriever = None

# Optional imports for OpenAI
try:
    from cognihive.integrations.openai import (
        OpenAIHive,
        COGNIHIVE_TOOLS,
        create_tool_outputs
    )
except ImportError:
    OpenAIHive = None
    COGNIHIVE_TOOLS = None
    create_tool_outputs = None

# Optional imports for MCP
try:
    from cognihive.integrations.mcp import (
        MCPHive,
        MCP_TOOLS
    )
except ImportError:
    MCPHive = None
    MCP_TOOLS = None

__all__ = [
    # CrewAI
    "CrewAIHive",
    "CrewAIMemory",
    # AutoGen
    "AutoGenHive",
    "AutoGenMemoryAdapter",
    # LangGraph
    "LangGraphHive",
    # LangChain
    "LangChainHive",
    "CogniHiveMemory",
    "CogniHiveRetriever",
    # OpenAI
    "OpenAIHive",
    "COGNIHIVE_TOOLS",
    "create_tool_outputs",
    # MCP
    "MCPHive",
    "MCP_TOOLS",
]

