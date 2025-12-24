"""
CogniHive CLI - Command Line Interface.

Provides commands for managing CogniHive instances.
"""

import argparse
import sys
from typing import Optional


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="cognihive",
        description="CogniHive: Transactive Memory System for Multi-Agent AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  cognihive init                    Initialize a new hive
  cognihive status                  Show hive status
  cognihive agents                  List registered agents
  cognihive who-knows python        Find experts on Python
  cognihive remember "content"      Store a memory
  cognihive recall "query"          Search memories
  
For more info, visit: https://github.com/vrush/cognihive
        """
    )
    
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="%(prog)s 0.1.0"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # init command
    init_parser = subparsers.add_parser("init", help="Initialize a new hive")
    init_parser.add_argument("--name", default="default", help="Hive name")
    init_parser.add_argument("--persist", help="Persistence directory")
    
    # status command
    status_parser = subparsers.add_parser("status", help="Show hive status")
    status_parser.add_argument("--name", default="default", help="Hive name")
    
    # agents command
    agents_parser = subparsers.add_parser("agents", help="List registered agents")
    agents_parser.add_argument("--name", default="default", help="Hive name")
    
    # register command
    register_parser = subparsers.add_parser("register", help="Register a new agent")
    register_parser.add_argument("agent_name", help="Name of the agent")
    register_parser.add_argument("--expertise", nargs="+", help="Expertise domains")
    register_parser.add_argument("--role", default="", help="Agent role")
    
    # who-knows command
    who_knows_parser = subparsers.add_parser("who-knows", help="Find experts on a topic")
    who_knows_parser.add_argument("topic", help="Topic to find experts for")
    who_knows_parser.add_argument("--name", default="default", help="Hive name")
    
    # remember command
    remember_parser = subparsers.add_parser("remember", help="Store a memory")
    remember_parser.add_argument("content", help="Memory content")
    remember_parser.add_argument("--agent", help="Agent creating the memory")
    remember_parser.add_argument("--topics", nargs="+", help="Topics")
    remember_parser.add_argument("--name", default="default", help="Hive name")
    
    # recall command
    recall_parser = subparsers.add_parser("recall", help="Search memories")
    recall_parser.add_argument("query", help="Search query")
    recall_parser.add_argument("--top-k", type=int, default=5, help="Number of results")
    recall_parser.add_argument("--name", default="default", help="Hive name")
    
    # demo command
    demo_parser = subparsers.add_parser("demo", help="Run interactive demo")
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 0
    
    # Import here to avoid slow startup
    from cognihive import Hive
    
    try:
        if args.command == "init":
            return cmd_init(args)
        elif args.command == "status":
            return cmd_status(args)
        elif args.command == "agents":
            return cmd_agents(args)
        elif args.command == "register":
            return cmd_register(args)
        elif args.command == "who-knows":
            return cmd_who_knows(args)
        elif args.command == "remember":
            return cmd_remember(args)
        elif args.command == "recall":
            return cmd_recall(args)
        elif args.command == "demo":
            return cmd_demo(args)
        else:
            parser.print_help()
            return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_init(args):
    """Initialize a new hive."""
    from cognihive import Hive
    
    persist = args.persist
    hive = Hive(name=args.name, persist_directory=persist)
    
    print(f"🐝 Initialized CogniHive: {args.name}")
    if persist:
        print(f"📁 Persistence: {persist}")
    else:
        print("⚡ Mode: In-memory (no persistence)")
    print("\nNext steps:")
    print("  cognihive register agent_name --expertise python sql")
    print("  cognihive remember 'Important information' --agent agent_name")
    return 0


def cmd_status(args):
    """Show hive status."""
    from cognihive import Hive
    
    hive = Hive(name=args.name)
    print(hive.summary())
    return 0


def cmd_agents(args):
    """List registered agents."""
    from cognihive import Hive
    
    hive = Hive(name=args.name)
    agents = hive.list_agents()
    
    if not agents:
        print("No agents registered yet.")
        print("Use: cognihive register <name> --expertise <domains>")
        return 0
    
    print(f"🐝 Agents in '{args.name}':\n")
    for agent in agents:
        expertise = list(agent.expertise_profile.expertise_domains.keys())[:3]
        expertise_str = ", ".join(expertise) if expertise else "none"
        print(f"  • {agent.name}")
        print(f"    Role: {agent.role or 'N/A'}")
        print(f"    Expertise: {expertise_str}")
        print(f"    Memories: {agent.memory_count}")
        print()
    
    return 0


def cmd_register(args):
    """Register a new agent."""
    from cognihive import Hive
    
    hive = Hive(name="default")
    
    try:
        agent = hive.register_agent(
            name=args.agent_name,
            expertise=args.expertise or [],
            role=args.role
        )
        print(f"✅ Registered agent: {agent.name}")
        if args.expertise:
            print(f"   Expertise: {', '.join(args.expertise)}")
    except ValueError as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


def cmd_who_knows(args):
    """Find experts on a topic."""
    from cognihive import Hive
    
    hive = Hive(name=args.name)
    experts = hive.who_knows(args.topic)
    
    if not experts:
        print(f"No experts found for: {args.topic}")
        return 0
    
    print(f"🔍 Experts on '{args.topic}':\n")
    for name, score in experts:
        bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
        print(f"  {name:20} [{bar}] {score:.2f}")
    
    return 0


def cmd_remember(args):
    """Store a memory."""
    from cognihive import Hive
    
    hive = Hive(name=args.name)
    
    memory = hive.remember(
        content=args.content,
        agent=args.agent,
        topics=args.topics or []
    )
    
    print(f"💾 Stored memory: {memory.id[:8]}...")
    if args.agent:
        print(f"   Agent: {args.agent}")
    if args.topics:
        print(f"   Topics: {', '.join(args.topics)}")
    
    return 0


def cmd_recall(args):
    """Search memories."""
    from cognihive import Hive
    
    hive = Hive(name=args.name)
    results = hive.recall(args.query, top_k=args.top_k)
    
    if not results:
        print(f"No memories found for: {args.query}")
        return 0
    
    print(f"📚 Memories matching '{args.query}':\n")
    for i, (memory, score) in enumerate(results, 1):
        print(f"  {i}. [{score:.2f}] {memory.content[:100]}...")
        if memory.owner_name:
            print(f"     From: {memory.owner_name}")
        print()
    
    return 0


def cmd_demo(args):
    """Run interactive demo."""
    from cognihive import Hive
    
    print("🐝 CogniHive Interactive Demo")
    print("=" * 40)
    print()
    
    # Create demo hive
    hive = Hive(name="demo")
    
    # Register demo agents
    hive.register_agent("coder", expertise=["python", "javascript", "api"])
    hive.register_agent("analyst", expertise=["sql", "data", "metrics"])
    hive.register_agent("writer", expertise=["docs", "tutorials", "examples"])
    
    print("📝 Registered 3 agents: coder, analyst, writer")
    print()
    
    # Add demo memories
    hive.remember(
        "Use list comprehensions for cleaner Python code",
        agent="coder",
        topics=["python", "best-practices"]
    )
    hive.remember(
        "Always use parameterized queries to prevent SQL injection",
        agent="analyst",
        topics=["sql", "security"]
    )
    hive.remember(
        "Include code examples in every API documentation page",
        agent="writer",
        topics=["docs", "api"]
    )
    
    print("💾 Added 3 demo memories")
    print()
    
    # Demo: Who knows what
    print("🔍 Demo: who_knows('database security')")
    experts = hive.who_knows("database security")
    for name, score in experts:
        print(f"   {name}: {score:.2f}")
    print()
    
    # Demo: Ask with routing
    print("🎯 Demo: ask('How should I write SQL queries?')")
    result = hive.ask("How should I write SQL queries?")
    print(f"   Routed to: {result['expert']} (confidence: {result['confidence']:.2f})")
    if result['memories']:
        print(f"   Found memory: {result['memories'][0].content[:60]}...")
    print()
    
    print("=" * 40)
    print("Try these commands:")
    print("  cognihive who-knows 'python'")
    print("  cognihive recall 'best practices'")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
