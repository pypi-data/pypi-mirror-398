"""
LangChain Integration Example for CogniHive.

This example demonstrates how to use CogniHive with LangChain
for memory and retrieval in conversational AI applications.

Requirements:
    pip install cognihive[langchain]
    pip install langchain-openai  # or other LLM provider
"""

from cognihive.integrations import LangChainHive

# Note: LangChain and LLM imports would normally be:
# from langchain.chains import ConversationChain
# from langchain_openai import ChatOpenAI
# from langchain.chains import RetrievalQA


def main():
    """Demonstrate LangChain integration with CogniHive."""
    
    print("=" * 60)
    print("CogniHive + LangChain Integration Example")
    print("=" * 60)
    
    # =========================================================
    # 1. Initialize LangChainHive
    # =========================================================
    print("\n1. Creating LangChainHive...")
    
    hive = LangChainHive(name="langchain_example")
    
    # Register agents with their expertise
    hive.register_agent(
        "researcher",
        expertise=["research", "analysis", "data"],
        role="Research Specialist"
    )
    hive.register_agent(
        "writer",
        expertise=["writing", "documentation", "tutorials"],
        role="Technical Writer"
    )
    hive.register_agent(
        "developer",
        expertise=["python", "api", "coding"],
        role="Software Developer"
    )
    
    print("   Registered 3 agents: researcher, writer, developer")
    
    # =========================================================
    # 2. Store some knowledge
    # =========================================================
    print("\n2. Storing team knowledge...")
    
    # Researcher's knowledge
    hive.remember(
        "The latest AI research shows transformer models achieve 95% accuracy on NLP tasks",
        agent="researcher",
        topics=["ai", "research", "nlp"]
    )
    hive.remember(
        "Market analysis indicates 40% growth in AI adoption for enterprise",
        agent="researcher",
        topics=["market", "analysis", "enterprise"]
    )
    
    # Writer's knowledge
    hive.remember(
        "Documentation should always include code examples for better understanding",
        agent="writer",
        topics=["documentation", "best-practices"]
    )
    hive.remember(
        "Use clear headings and bullet points for technical tutorials",
        agent="writer",
        topics=["tutorials", "writing"]
    )
    
    # Developer's knowledge
    hive.remember(
        "Use async/await for non-blocking API calls in Python",
        agent="developer",
        topics=["python", "api", "async"]
    )
    hive.remember(
        "Always implement retry logic for external API integrations",
        agent="developer",
        topics=["api", "reliability", "best-practices"]
    )
    
    print("   Stored 6 memories across agents")
    
    # =========================================================
    # 3. Test "Who Knows What"
    # =========================================================
    print("\n3. Testing 'Who Knows What' queries...")
    
    topics_to_test = ["python api", "documentation", "ai research"]
    for topic in topics_to_test:
        experts = hive.who_knows(topic)
        if experts:
            top_expert = experts[0]
            print(f"   '{topic}' -> {top_expert[0]} (score: {top_expert[1]:.2f})")
        else:
            print(f"   '{topic}' -> No experts found")
    
    # =========================================================
    # 4. Get LangChain Memory
    # =========================================================
    print("\n4. Creating LangChain Memory...")
    
    # This creates a LangChain-compatible memory for a specific agent
    memory = hive.as_memory(
        agent_name="developer",
        memory_key="history"
    )
    
    print(f"   Memory type: {type(memory).__name__}")
    print(f"   Memory variables: {memory.memory_variables}")
    
    # =========================================================
    # 5. Get LangChain Retriever
    # =========================================================
    print("\n5. Creating LangChain Retriever...")
    
    # This creates a LangChain-compatible retriever for RAG
    retriever = hive.as_retriever(
        agent_name=None,  # Search all agents
        top_k=3
    )
    
    print(f"   Retriever type: {type(retriever).__name__}")
    
    # Test retrieval
    print("\n   Testing retrieval for 'API best practices':")
    try:
        docs = retriever._get_relevant_documents("API best practices")
        for i, doc in enumerate(docs[:3], 1):
            print(f"   [{i}] {doc.page_content[:60]}...")
            print(f"       Source: {doc.metadata.get('agent', 'unknown')}")
    except Exception as e:
        print(f"   Note: Full retrieval requires LangChain installed: {e}")
    
    # =========================================================
    # 6. Example: Using with ConversationChain (pseudo-code)
    # =========================================================
    print("\n6. Example usage with LangChain (pseudo-code):")
    print("""
    from langchain.chains import ConversationChain
    from langchain_openai import ChatOpenAI
    
    # Create LangChain memory backed by CogniHive
    memory = hive.as_memory("developer")
    
    # Create conversation chain
    chain = ConversationChain(
        llm=ChatOpenAI(model="gpt-4"),
        memory=memory
    )
    
    # Chat - memories are automatically saved to CogniHive
    response = chain.invoke({"input": "How do I build an API?"})
    """)
    
    # =========================================================
    # 7. Example: Using with RetrievalQA (pseudo-code)
    # =========================================================
    print("7. Example usage for RAG (pseudo-code):")
    print("""
    from langchain.chains import RetrievalQA
    
    # Create retriever that searches all agent memories
    retriever = hive.as_retriever(top_k=5)
    
    # Create RAG chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=ChatOpenAI(),
        retriever=retriever
    )
    
    # Query - retrieves relevant memories from all experts
    answer = qa_chain.invoke("What are API best practices?")
    """)
    
    # =========================================================
    # Summary
    # =========================================================
    print("=" * 60)
    print("LangChain Integration Features:")
    print("  - CogniHiveMemory: LangChain-compatible memory class")
    print("  - CogniHiveRetriever: For RAG pipelines")
    print("  - Transactive Memory: Find experts on any topic")
    print("  - Multi-Agent Knowledge: Shared team intelligence")
    print("=" * 60)


if __name__ == "__main__":
    main()
