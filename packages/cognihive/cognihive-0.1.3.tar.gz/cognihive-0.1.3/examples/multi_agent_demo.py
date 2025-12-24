"""
Multi-Agent Demo for CogniHive.

This demo simulates a realistic multi-agent scenario:
A team of AI agents working on a software project,
with CogniHive providing collective intelligence.
"""

from cognihive import Hive


def run_demo():
    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║   🐝 CogniHive: Transactive Memory System                            ║
║   ────────────────────────────────────────                            ║
║   "Mem0 gives one agent a brain.                                      ║
║    CogniHive gives your agent team a collective mind."               ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
""")
    
    # === Setup: Create the development team ===
    print("📋 SCENARIO: A development team with specialized agents")
    print("━" * 60)
    print()
    
    hive = Hive(name="dev_team")
    
    # Register specialized agents
    agents_config = [
        {
            "name": "backend_dev",
            "expertise": ["python", "fastapi", "postgres", "api"],
            "role": "Backend Developer",
            "description": "Expert in Python, FastAPI, and database design"
        },
        {
            "name": "frontend_dev",
            "expertise": ["react", "typescript", "css", "ui"],
            "role": "Frontend Developer", 
            "description": "Expert in React, TypeScript, and modern CSS"
        },
        {
            "name": "devops_eng",
            "expertise": ["docker", "kubernetes", "aws", "ci-cd"],
            "role": "DevOps Engineer",
            "description": "Expert in cloud infrastructure and deployment"
        },
        {
            "name": "qa_lead",
            "expertise": ["testing", "pytest", "selenium", "quality"],
            "role": "QA Lead",
            "description": "Expert in testing strategies and automation"
        },
        {
            "name": "tech_writer",
            "expertise": ["docs", "api-docs", "tutorials", "examples"],
            "role": "Technical Writer",
            "description": "Expert in documentation and developer experience"
        }
    ]
    
    for config in agents_config:
        agent = hive.register_agent(
            name=config["name"],
            expertise=config["expertise"],
            role=config["role"],
            description=config["description"]
        )
        print(f"   ✓ {config['role']}: {agent.name}")
    
    print()
    
    # === Simulate: Agents learn and share knowledge ===
    print("💡 SIMULATION: Agents discover and share knowledge")
    print("━" * 60)
    print()
    
    # Backend dev learns something
    hive.remember(
        "Use Pydantic v2's model_validate() instead of parse_obj() for better performance",
        agent="backend_dev",
        topics=["python", "pydantic", "performance"]
    )
    print("   backend_dev: Learned about Pydantic v2 migration")
    
    hive.remember(
        "Connection pooling with asyncpg gives 3x throughput for Postgres",
        agent="backend_dev",
        topics=["postgres", "performance", "async"]
    )
    print("   backend_dev: Learned about asyncpg connection pooling")
    
    # Frontend dev learns something
    hive.remember(
        "React 19 Server Components reduce bundle size by 40% for our use case",
        agent="frontend_dev",
        topics=["react", "performance", "server-components"]
    )
    print("   frontend_dev: Learned about React 19 benefits")
    
    hive.remember(
        "Use CSS container queries for responsive components instead of media queries",
        agent="frontend_dev",
        topics=["css", "responsive", "modern"]
    )
    print("   frontend_dev: Learned about CSS container queries")
    
    # DevOps learns something
    hive.remember(
        "The staging environment uses m5.large instances with 4GB memory limit",
        agent="devops_eng",
        topics=["aws", "staging", "infrastructure"]
    )
    print("   devops_eng: Documented staging environment specs")
    
    hive.remember(
        "Deploy to production using GitHub Actions with the deploy-prod.yml workflow",
        agent="devops_eng",
        topics=["ci-cd", "deployment", "github-actions"]
    )
    print("   devops_eng: Documented deployment workflow")
    
    # QA learns something
    hive.remember(
        "Use pytest-asyncio for testing async FastAPI endpoints with @pytest.mark.asyncio",
        agent="qa_lead",
        topics=["testing", "pytest", "async", "fastapi"]
    )
    print("   qa_lead: Learned about async testing patterns")
    
    # Tech writer documents
    hive.remember(
        "API documentation is at /docs (Swagger) and /redoc (ReDoc) endpoints",
        agent="tech_writer",
        topics=["api-docs", "swagger", "documentation"]
    )
    print("   tech_writer: Documented API documentation locations")
    
    print()
    
    # === Demo: "Who Knows What" queries ===
    print("🔍 DEMO: 'Who Knows What' - Transactive Memory in Action")
    print("━" * 60)
    print()
    
    queries = [
        "Python performance optimization",
        "React best practices",
        "How to deploy to production",
        "Testing async code"
    ]
    
    for query in queries:
        print(f"   Q: Who knows about '{query}'?")
        experts = hive.who_knows(query)
        
        if experts:
            for name, score in experts[:2]:
                bars = "█" * int(score * 10) + "░" * (10 - int(score * 10))
                print(f"      {name:15} [{bars}] {score:.2f}")
        else:
            print("      No experts found")
        print()
    
    # === Demo: Automatic Query Routing ===
    print("🎯 DEMO: Automatic Query Routing")
    print("━" * 60)
    print()
    
    questions = [
        "How do I improve our API response time?",
        "What's the best way to test our endpoints?",
        "How do I deploy a new feature to production?",
        "Where can I find the API documentation?"
    ]
    
    for question in questions:
        result = hive.ask(question)
        print(f"   Q: {question}")
        print(f"   → Routed to: {result['expert']} (confidence: {result['confidence']:.2f})")
        
        if result['memories']:
            answer = result['memories'][0].content
            if len(answer) > 60:
                answer = answer[:60] + "..."
            print(f"   → Answer: \"{answer}\"")
        print()
    
    # === Show: Expertise Matrix ===
    print("📊 TEAM EXPERTISE MATRIX")
    print("━" * 60)
    print()
    
    matrix = hive.expertise_matrix()
    for agent_name, domains in matrix.items():
        top = sorted(domains.items(), key=lambda x: x[1], reverse=True)[:4]
        domain_str = ", ".join([f"{d}({s:.1f})" for d, s in top if s > 0.3])
        print(f"   {agent_name:15} │ {domain_str}")
    
    print()
    
    # === Stats ===
    stats = hive.stats()
    print("📈 HIVE STATISTICS")
    print("━" * 60)
    print(f"   Agents:    {stats['agent_count']}")
    print(f"   Memories:  {stats['memory_count']}")
    print(f"   Queries:   {stats['metrics']['queries_processed']}")
    print(f"   Routes:    {stats['metrics']['routing_decisions']}")
    print()
    
    # === Why this matters ===
    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                         WHY THIS MATTERS                              ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║   Without CogniHive:                                                  ║
║   • Agents don't know what each other knows                          ║
║   • Questions go to the wrong expert (or all experts)                ║
║   • Duplicated research and wasted tokens                            ║
║   • No coordination = chaos at scale                                  ║
║                                                                       ║
║   With CogniHive:                                                     ║
║   ✓ "Who knows what" queries work instantly                          ║
║   ✓ Questions auto-route to the right expert                         ║
║   ✓ 15x fewer tokens (Anthropic's research)                          ║
║   ✓ Transactive Memory = team intelligence                           ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    run_demo()
