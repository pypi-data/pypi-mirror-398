"""
Basic usage example for CogniHive.

This example demonstrates the core features:
- Registering agents with expertise
- Storing memories
- "Who Knows What" queries
- Automatic query routing
"""

from cognihive import Hive


def main():
    print("🐝 CogniHive: Basic Usage Example")
    print("=" * 50)
    print()
    
    # Create a hive
    hive = Hive(name="demo")
    
    # Register agents with their expertise
    print("📝 Registering agents...")
    hive.register_agent(
        "coder",
        expertise=["python", "javascript", "api", "testing"],
        role="Software Engineer"
    )
    hive.register_agent(
        "analyst",
        expertise=["sql", "data", "metrics", "analytics"],
        role="Data Analyst"
    )
    hive.register_agent(
        "writer",
        expertise=["docs", "tutorials", "examples", "api"],
        role="Technical Writer"
    )
    
    print(f"   Registered {len(hive.agents)} agents: {', '.join(hive.agents)}")
    print()
    
    # Store memories from different agents
    print("💾 Storing team knowledge...")
    
    hive.remember(
        "Use list comprehensions for cleaner, more Pythonic code",
        agent="coder",
        topics=["python", "best-practices"]
    )
    
    hive.remember(
        "Always use parameterized queries to prevent SQL injection attacks",
        agent="analyst",
        topics=["sql", "security"]
    )
    
    hive.remember(
        "Include working code examples in every API documentation page",
        agent="writer",
        topics=["docs", "api", "examples"]
    )
    
    hive.remember(
        "The API rate limit is 1000 requests per minute per API key",
        agent="writer",
        topics=["api", "limits"]
    )
    
    hive.remember(
        "Use connection pooling for better database performance",
        agent="analyst",
        topics=["sql", "performance", "optimization"]
    )
    
    print("   Stored 5 memories from the team")
    print()
    
    # Demonstrate "Who Knows What" - the core innovation
    print("🔍 WHO KNOWS WHAT (Transactive Memory)")
    print("-" * 40)
    
    topics_to_query = [
        "python optimization",
        "database security",
        "API documentation"
    ]
    
    for topic in topics_to_query:
        experts = hive.who_knows(topic)
        print(f"\n   Q: Who knows about '{topic}'?")
        for name, score in experts[:2]:
            bar = "█" * int(score * 10)
            print(f"      • {name}: {bar} ({score:.2f})")
    
    print()
    
    # Demonstrate query routing
    print("🎯 AUTOMATIC QUERY ROUTING")
    print("-" * 40)
    
    queries = [
        "How do I write better Python code?",
        "What should I know about SQL security?",
        "How should I document our API?"
    ]
    
    for query in queries:
        result = hive.ask(query)
        print(f"\n   Q: {query}")
        print(f"   → Routed to: {result['expert']} (confidence: {result['confidence']:.2f})")
        if result['memories']:
            print(f"   → Found: \"{result['memories'][0].content[:50]}...\"")
    
    print()
    
    # Show expertise matrix
    print("📊 TEAM EXPERTISE MATRIX")
    print("-" * 40)
    matrix = hive.expertise_matrix()
    
    for agent_name, domains in matrix.items():
        top_domains = sorted(domains.items(), key=lambda x: x[1], reverse=True)[:3]
        domains_str = ", ".join([f"{d}({s:.1f})" for d, s in top_domains])
        print(f"   {agent_name}: {domains_str}")
    
    print()
    
    # Get hive summary
    print("📈 HIVE SUMMARY")
    print("-" * 40)
    print(hive.summary())
    print()
    
    print("✅ Example complete!")
    print()
    print("Try these in your code:")
    print("   hive.who_knows('your_topic')")
    print("   hive.ask('your question')")
    print("   hive.remember('knowledge', agent='agent_name')")


if __name__ == "__main__":
    main()
