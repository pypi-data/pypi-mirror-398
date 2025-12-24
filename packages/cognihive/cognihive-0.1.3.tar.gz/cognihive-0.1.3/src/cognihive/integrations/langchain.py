"""
LangChain integration for CogniHive.

Provides LangChain-compatible memory and retriever classes for
seamless integration with LangChain chains and agents.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

try:
    from langchain_core.memory import BaseMemory
    from langchain_core.retrievers import BaseRetriever
    from langchain_core.documents import Document
    from langchain_core.callbacks import CallbackManagerForRetrieverRun
    LANGCHAIN_AVAILABLE = True
except ImportError:
    try:
        # Fallback to older langchain imports
        from langchain.memory import BaseMemory
        from langchain.schema import BaseRetriever, Document
        LANGCHAIN_AVAILABLE = True
    except ImportError:
        LANGCHAIN_AVAILABLE = False
        BaseMemory = object
        BaseRetriever = object
        Document = None

from cognihive.core.hive import Hive
from cognihive.core.agent_registry import Agent


class LangChainHive:
    """CogniHive wrapper for LangChain integration.
    
    Provides methods to convert CogniHive components into
    LangChain-compatible memory and retriever objects.
    
    Example:
        ```python
        from cognihive.integrations import LangChainHive
        from langchain.chains import ConversationChain
        from langchain_openai import ChatOpenAI
        
        hive = LangChainHive()
        hive.register_agent("assistant", expertise=["general"])
        
        chain = ConversationChain(
            llm=ChatOpenAI(),
            memory=hive.as_memory("assistant")
        )
        ```
    """
    
    def __init__(
        self,
        name: str = "langchain_hive",
        persist_directory: Optional[str] = None,
        **kwargs
    ):
        """Initialize LangChain-compatible Hive.
        
        Args:
            name: Name of the hive
            persist_directory: Path for persistent storage
            **kwargs: Additional arguments passed to Hive
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "LangChain is required for LangChainHive. "
                "Install with: pip install langchain langchain-core"
            )
        
        self.hive = Hive(
            name=name,
            persist_directory=persist_directory,
            **kwargs
        )
    
    def register_agent(
        self,
        name: str,
        expertise: Optional[List[str]] = None,
        role: str = "",
        **kwargs
    ) -> Agent:
        """Register an agent with the hive.
        
        Args:
            name: Unique agent name
            expertise: List of expertise areas
            role: Agent's role description
            
        Returns:
            Registered Agent object
        """
        return self.hive.register_agent(
            name=name,
            expertise=expertise,
            role=role,
            **kwargs
        )
    
    def as_memory(
        self,
        agent_name: str,
        memory_key: str = "history",
        input_key: str = "input",
        output_key: str = "output",
        return_messages: bool = False
    ) -> "CogniHiveMemory":
        """Get a LangChain-compatible memory for an agent.
        
        Args:
            agent_name: Name of the agent this memory belongs to
            memory_key: Key to use in the chain's memory dict
            input_key: Key for input in save_context
            output_key: Key for output in save_context
            return_messages: Whether to return as message objects
            
        Returns:
            CogniHiveMemory instance
        """
        return CogniHiveMemory(
            hive=self.hive,
            agent_name=agent_name,
            memory_key=memory_key,
            input_key=input_key,
            output_key=output_key,
            return_messages=return_messages
        )
    
    def as_retriever(
        self,
        agent_name: Optional[str] = None,
        top_k: int = 5,
        min_similarity: float = 0.0
    ) -> "CogniHiveRetriever":
        """Get a LangChain-compatible retriever.
        
        Args:
            agent_name: Filter to specific agent's memories (None = all)
            top_k: Number of documents to retrieve
            min_similarity: Minimum similarity threshold
            
        Returns:
            CogniHiveRetriever instance
        """
        return CogniHiveRetriever(
            hive=self.hive,
            agent_name=agent_name,
            top_k=top_k,
            min_similarity=min_similarity
        )
    
    def who_knows(self, topic: str) -> List[tuple]:
        """Find experts on a topic.
        
        Args:
            topic: Topic to search for experts
            
        Returns:
            List of (agent_name, score) tuples
        """
        return self.hive.who_knows(topic)
    
    def remember(
        self,
        content: str,
        agent: str,
        topics: Optional[List[str]] = None,
        **kwargs
    ):
        """Store a memory.
        
        Args:
            content: Memory content
            agent: Agent storing the memory
            topics: Related topics
            
        Returns:
            Stored Memory object
        """
        return self.hive.remember(content, agent=agent, topics=topics, **kwargs)
    
    def recall(self, query: str, agent: Optional[str] = None, top_k: int = 5):
        """Recall relevant memories.
        
        Args:
            query: Search query
            agent: Filter to specific agent
            top_k: Number of results
            
        Returns:
            List of (Memory, score) tuples
        """
        return self.hive.recall(query, agent=agent, top_k=top_k)


class CogniHiveMemory(BaseMemory):
    """LangChain-compatible memory backed by CogniHive.
    
    Stores conversation history in CogniHive with transactive memory
    capabilities. Memories are associated with a specific agent and
    can be searched across the entire hive.
    """
    
    hive: Any = None
    agent_name: str = ""
    memory_key: str = "history"
    input_key: str = "input"
    output_key: str = "output"
    return_messages: bool = False
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(
        self,
        hive: Hive,
        agent_name: str,
        memory_key: str = "history",
        input_key: str = "input",
        output_key: str = "output",
        return_messages: bool = False,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.hive = hive
        self.agent_name = agent_name
        self.memory_key = memory_key
        self.input_key = input_key
        self.output_key = output_key
        self.return_messages = return_messages
    
    @property
    def memory_variables(self) -> List[str]:
        """Return memory variables."""
        return [self.memory_key]
    
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load memory variables for the chain.
        
        Retrieves recent memories from the agent and formats them
        for use in the chain prompt.
        """
        # Get recent memories for this agent
        query = inputs.get(self.input_key, "")
        if not query:
            query = str(inputs) if inputs else "recent conversation"
        
        memories = self.hive.recall(query, agent=self.agent_name, top_k=5)
        
        if self.return_messages:
            # Return as message-like format
            messages = []
            for memory, score in memories:
                messages.append({
                    "type": "memory",
                    "content": memory.content,
                    "score": score
                })
            return {self.memory_key: messages}
        else:
            # Return as string
            history_parts = []
            for memory, score in memories:
                history_parts.append(memory.content)
            
            history = "\n".join(history_parts) if history_parts else ""
            return {self.memory_key: history}
    
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """Save conversation context to CogniHive.
        
        Stores both the input and output as separate memories
        with appropriate metadata.
        """
        input_str = inputs.get(self.input_key, "")
        output_str = outputs.get(self.output_key, "")
        
        # Store the exchange as a memory
        if input_str and output_str:
            content = f"User: {input_str}\nAssistant: {output_str}"
            self.hive.remember(
                content=content,
                agent=self.agent_name,
                topics=["conversation"],
                metadata={
                    "type": "conversation",
                    "input": input_str,
                    "output": output_str,
                    "timestamp": datetime.now().isoformat()
                }
            )
    
    def clear(self) -> None:
        """Clear memory (not fully implemented - would need agent-specific clear)."""
        # Note: Full implementation would clear only this agent's memories
        pass


class CogniHiveRetriever(BaseRetriever):
    """LangChain-compatible retriever backed by CogniHive.
    
    Retrieves relevant documents from CogniHive memories for
    use in RAG (Retrieval Augmented Generation) pipelines.
    
    Example:
        ```python
        from langchain.chains import RetrievalQA
        
        retriever = hive.as_retriever()
        qa_chain = RetrievalQA.from_chain_type(
            llm=ChatOpenAI(),
            retriever=retriever
        )
        ```
    """
    
    hive: Any = None
    agent_name: Optional[str] = None
    top_k: int = 5
    min_similarity: float = 0.0
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(
        self,
        hive: Hive,
        agent_name: Optional[str] = None,
        top_k: int = 5,
        min_similarity: float = 0.0,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.hive = hive
        self.agent_name = agent_name
        self.top_k = top_k
        self.min_similarity = min_similarity
    
    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: Optional[Any] = None
    ) -> List[Document]:
        """Get relevant documents for a query.
        
        Args:
            query: Search query
            run_manager: Callback manager (optional)
            
        Returns:
            List of LangChain Document objects
        """
        if Document is None:
            raise ImportError("LangChain Document class not available")
        
        # Query CogniHive
        results = self.hive.recall(
            query=query,
            agent=self.agent_name,
            top_k=self.top_k,
            min_similarity=self.min_similarity
        )
        
        # Also check who knows about the query topics
        experts = self.hive.who_knows(query)
        expert_info = ""
        if experts:
            top_experts = [f"{name} (score: {score:.2f})" for name, score in experts[:3]]
            expert_info = f"Experts on this topic: {', '.join(top_experts)}"
        
        # Convert to LangChain Documents
        documents = []
        for memory, score in results:
            metadata = {
                "source": "cognihive",
                "agent": memory.owner_name,
                "score": score,
                "memory_id": memory.id,
                "topics": memory.topics,
                "created_at": memory.created_at.isoformat() if memory.created_at else None
            }
            
            doc = Document(
                page_content=memory.content,
                metadata=metadata
            )
            documents.append(doc)
        
        # Add expert info as a document if available
        if expert_info:
            documents.insert(0, Document(
                page_content=expert_info,
                metadata={"source": "cognihive_experts", "type": "expert_routing"}
            ))
        
        return documents
    
    async def _aget_relevant_documents(
        self,
        query: str,
        *,
        run_manager: Optional[Any] = None
    ) -> List[Document]:
        """Async version of get_relevant_documents."""
        return self._get_relevant_documents(query, run_manager=run_manager)
