"""
OpenAI Assistants Integration Example for CogniHive.

This example demonstrates how to use CogniHive with OpenAI's
Assistants API for transactive memory capabilities.

Requirements:
    pip install cognihive[openai]
    export OPENAI_API_KEY="your-api-key"
"""

from cognihive.integrations import OpenAIHive, COGNIHIVE_TOOLS

# Note: OpenAI imports would normally be:
# from openai import OpenAI


def main():
    """Demonstrate OpenAI Assistants integration with CogniHive."""
    
    print("=" * 60)
    print("CogniHive + OpenAI Assistants Integration Example")
    print("=" * 60)
    
    # =========================================================
    # 1. Initialize OpenAIHive
    # =========================================================
    print("\n1. Creating OpenAIHive...")
    
    hive = OpenAIHive(name="openai_example", default_agent="assistant")
    
    # Register additional agents
    hive.hive.register_agent(
        "data_analyst",
        expertise=["sql", "analytics", "data"],
        role="Data Analyst"
    )
    hive.hive.register_agent(
        "frontend_dev",
        expertise=["react", "typescript", "ui"],
        role="Frontend Developer"
    )
    hive.hive.register_agent(
        "devops",
        expertise=["docker", "kubernetes", "aws"],
        role="DevOps Engineer"
    )
    
    print("   Created hive with 4 agents")
    
    # =========================================================
    # 2. Store team knowledge
    # =========================================================
    print("\n2. Storing team knowledge...")
    
    hive.hive.remember(
        "Use CTEs for complex SQL queries - improves readability",
        agent="data_analyst",
        topics=["sql", "best-practices"]
    )
    hive.hive.remember(
        "React Server Components reduce client bundle by 40%",
        agent="frontend_dev",
        topics=["react", "performance"]
    )
    hive.hive.remember(
        "Use multi-stage Docker builds for smaller images",
        agent="devops",
        topics=["docker", "optimization"]
    )
    
    print("   Stored 3 memories")
    
    # =========================================================
    # 3. View available tools
    # =========================================================
    print("\n3. CogniHive function tools for OpenAI:")
    
    tools = hive.get_tools()
    for tool in tools:
        func = tool["function"]
        print(f"\n   {func['name']}:")
        print(f"   {func['description'][:60]}...")
    
    # =========================================================
    # 4. Simulate tool call processing
    # =========================================================
    print("\n\n4. Simulating tool call processing...")
    
    # Simulate a "who_knows" tool call
    class MockToolCall:
        class Function:
            def __init__(self, name, arguments):
                self.name = name
                self.arguments = arguments
        
        def __init__(self, name, arguments):
            self.id = "call_123"
            self.function = self.Function(name, arguments)
    
    # Test who_knows
    print("\n   Simulating: who_knows({\"topic\": \"docker\"})")
    mock_call = MockToolCall("who_knows", '{"topic": "docker"}')
    result = hive.process_tool_call(mock_call)
    print(f"   Result: {result}")
    
    # Test remember
    print("\n   Simulating: remember({\"content\": \"New best practice\", \"topics\": [\"general\"]})")
    mock_call = MockToolCall("remember", '{"content": "Always use environment variables for secrets", "topics": ["security"]}')
    result = hive.process_tool_call(mock_call)
    print(f"   Result: {result}")
    
    # Test recall
    print("\n   Simulating: recall({\"query\": \"docker best practices\"})")
    mock_call = MockToolCall("recall", '{"query": "docker best practices"}')
    result = hive.process_tool_call(mock_call)
    print(f"   Result: {result}")
    
    # Test ask_expert
    print("\n   Simulating: ask_expert({\"question\": \"How do I optimize React?\"})")
    mock_call = MockToolCall("ask_expert", '{"question": "How do I optimize React?"}')
    result = hive.process_tool_call(mock_call)
    print(f"   Result: {result}")
    
    # =========================================================
    # 5. Full OpenAI Assistants example (pseudo-code)
    # =========================================================
    print("\n\n5. Full OpenAI Assistants usage (pseudo-code):")
    print("""
    from openai import OpenAI
    from cognihive.integrations import OpenAIHive, create_tool_outputs
    
    client = OpenAI()
    hive = OpenAIHive()
    
    # Create assistant with CogniHive tools
    assistant = client.beta.assistants.create(
        name="Team Coordinator",
        instructions="You coordinate a software team. Use tools to find experts and access team knowledge.",
        tools=hive.get_tools(),
        model="gpt-4-turbo"
    )
    
    # Create thread and run
    thread = client.beta.threads.create()
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content="Who on our team knows about Docker optimization?"
    )
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )
    
    # Poll for completion
    while run.status in ["queued", "in_progress"]:
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        
        # Handle tool calls
        if run.status == "requires_action":
            tool_calls = run.required_action.submit_tool_outputs.tool_calls
            outputs = create_tool_outputs(hive, tool_calls)
            
            run = client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=outputs
            )
    
    # Get response
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    print(messages.data[0].content[0].text.value)
    """)
    
    # =========================================================
    # Summary
    # =========================================================
    print("=" * 60)
    print("OpenAI Integration Features:")
    print("  - who_knows: Find team experts on any topic")
    print("  - remember: Store knowledge for future reference")
    print("  - recall: Search team memories semantically")
    print("  - ask_expert: Route questions to the right expert")
    print("=" * 60)


if __name__ == "__main__":
    main()
