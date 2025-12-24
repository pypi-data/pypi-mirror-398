"""
CrewAI Integration Example for CogniHive.

This example shows how to integrate CogniHive with CrewAI
for transactive memory in multi-agent workflows.

NOTE: Requires CrewAI to be installed:
  pip install cognihive[crewai]
"""

# Check if CrewAI is available
try:
    from crewai import Agent, Crew, Task
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    print("⚠️  CrewAI not installed. Install with: pip install crewai")
    print("   This example shows the integration pattern.")


def example_with_crewai():
    """Example using CogniHive with CrewAI."""
    from cognihive.integrations import CrewAIHive
    
    print("🐝 CogniHive + CrewAI Integration Example")
    print("=" * 50)
    print()
    
    # Create a CrewAI-enabled hive
    hive = CrewAIHive(name="crewai_demo")
    
    # Create CrewAI agents with CogniHive memory
    researcher = Agent(
        role="Researcher",
        goal="Find comprehensive information on topics",
        backstory="You are an expert researcher with years of experience.",
        verbose=True,
        memory=hive.agent_memory("researcher")  # CogniHive memory!
    )
    
    writer = Agent(
        role="Writer",
        goal="Write clear and engaging content",
        backstory="You are a skilled technical writer.",
        verbose=True,
        memory=hive.agent_memory("writer")  # CogniHive memory!
    )
    
    analyst = Agent(
        role="Analyst",
        goal="Analyze data and provide insights",
        backstory="You are a data-driven analyst.",
        verbose=True,
        memory=hive.agent_memory("analyst")  # CogniHive memory!
    )
    
    # Register agents in hive (extracts expertise from roles)
    hive.from_crew_agent(researcher, extract_expertise=True)
    hive.from_crew_agent(writer, extract_expertise=True)
    hive.from_crew_agent(analyst, extract_expertise=True)
    
    print("📝 Registered agents with transactive memory:")
    for agent_name in hive.agents:
        print(f"   • {agent_name}")
    print()
    
    # Agents can store memories
    hive.remember(
        "The market research shows 40% growth in AI adoption",
        agent="researcher",
        topics=["research", "market", "ai"]
    )
    
    hive.remember(
        "Technical documentation should use active voice",
        agent="writer",
        topics=["writing", "documentation"]
    )
    
    # Who Knows What works across the crew!
    print("🔍 Who knows about 'AI market trends'?")
    experts = hive.who_knows("AI market trends")
    for name, score in experts:
        print(f"   {name}: {score:.2f}")
    print()
    
    # Queries are automatically routed to the right expert
    print("🎯 Routing: 'What does the research say about AI?'")
    result = hive.ask("What does the research say about AI?")
    print(f"   → Expert: {result['expert']}")
    print(f"   → Confidence: {result['confidence']:.2f}")
    print()
    
    print("✅ CrewAI integration complete!")
    print()
    print("Now agents automatically:")
    print("   1. Know what each other knows")
    print("   2. Route questions to the right expert")
    print("   3. Share learnings with access control")


def example_without_crewai():
    """Show the pattern without requiring CrewAI."""
    from cognihive import Hive
    
    print("🐝 CogniHive CrewAI Pattern (without CrewAI)")
    print("=" * 50)
    print()
    print("This shows the integration pattern. Install CrewAI to run the full example.")
    print()
    
    # The pattern is simple:
    hive = Hive(name="demo")
    
    # 1. Register agents (CrewAI roles become expertise)
    hive.register_agent("researcher", expertise=["research", "analysis"])
    hive.register_agent("writer", expertise=["writing", "documentation"])
    
    # 2. Store memories as agents work
    hive.remember("Key finding from research", agent="researcher")
    
    # 3. Other agents can query "who knows what"
    experts = hive.who_knows("research")
    print(f"Who knows about research: {experts}")
    
    # 4. Queries route to the right expert
    result = hive.ask("What did the research find?")
    print(f"Query routed to: {result['expert']}")
    
    print()
    print("Install CrewAI for the full integration:")
    print("   pip install cognihive[crewai]")


if __name__ == "__main__":
    if CREWAI_AVAILABLE:
        example_with_crewai()
    else:
        example_without_crewai()
