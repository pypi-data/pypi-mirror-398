<div align="center">

# 🐝 CogniHive

### The World's First Transactive Memory System for Multi-Agent AI

**Mem0 gives one agent a brain. CogniHive gives your agent team a collective mind.**

[![PyPI version](https://img.shields.io/pypi/v/cognihive)](https://pypi.org/project/cognihive/)
[![Python](https://img.shields.io/pypi/pyversions/cognihive)](https://pypi.org/project/cognihive/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![HuggingFace](https://img.shields.io/badge/🤗-Demo-yellow)](https://huggingface.co/spaces/vrush/cognihive)

[Installation](#-installation) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Integrations](#-integrations)

</div>

---

## 🧠 What is Transactive Memory?

In human teams, not everyone remembers everything. Instead, teams develop a **shared awareness of who knows what**:

- *"Sarah handles the legal stuff"*
- *"Mike knows all the technical details"*  
- *"Ask Jennifer about customer history"*

This is called a **Transactive Memory System (TMS)** — a concept from cognitive science that has **never been implemented for AI agents**... until now.

## 💡 Why CogniHive?

Current multi-agent systems fail because:

| Problem | Without CogniHive | With CogniHive |
|---------|-------------------|----------------|
| "Which agent knows X?" | Manual orchestration | `hive.who_knows("topic")` |
| Redundant work | Multiple agents research same thing | Expertise routing prevents duplication |
| Conflicting info | Silent failures | Conflict detection + resolution |
| Token explosion | 15x more tokens (Anthropic's research) | Smart routing = massive savings |

## 🚀 Installation

```bash
pip install cognihive
```

With framework integrations:
```bash
pip install cognihive[crewai]      # For CrewAI
pip install cognihive[autogen]     # For AutoGen
pip install cognihive[all]         # Everything
```

## ⚡ Quick Start

```python
from cognihive import Hive

# Create a hive (multi-agent memory system)
hive = Hive()

# Register agents with their specializations
hive.register_agent("coder", expertise=["python", "javascript", "testing"])
hive.register_agent("analyst", expertise=["sql", "data", "metrics"])
hive.register_agent("writer", expertise=["docs", "tutorials", "api"])

# Agents store knowledge
hive.remember(
    "Use connection pooling for better DB performance",
    agent="analyst",
    topics=["database", "performance"]
)

# 🔍 THE KEY INNOVATION: "Who Knows What" queries
experts = hive.who_knows("database optimization")
# Returns: [("analyst", 0.92), ("coder", 0.45)]

# 🎯 Automatic query routing to the right expert
result = hive.ask("How do I optimize my queries?")
# Automatically routes to "analyst" and returns relevant memories

print(f"Expert: {result['expert']}")  # "analyst"
print(f"Answer: {result['memories'][0].content}")
```

## 🔗 Integrations

### CrewAI

```python
from crewai import Agent, Crew
from cognihive.integrations import CrewAIHive

hive = CrewAIHive()

researcher = Agent(
    role="Researcher",
    goal="Find information",
    memory=hive.agent_memory("researcher")  # CogniHive memory!
)

writer = Agent(
    role="Writer",
    goal="Write content",
    memory=hive.agent_memory("writer")  # CogniHive memory!
)

# Now agents automatically:
# ✓ Know what each other knows
# ✓ Route questions to the right expert
# ✓ Share learnings across the team
```

### AutoGen

```python
from autogen import AssistantAgent
from cognihive.integrations import AutoGenHive

hive = AutoGenHive()

# Create agents with shared transactive memory
coder = hive.create_memory_enhanced_agent(
    name="coder",
    system_message="You are an expert coder.",
    expertise=["python", "coding"]
)

reviewer = hive.create_memory_enhanced_agent(
    name="reviewer",
    system_message="You review code for quality.",
    expertise=["review", "testing"]
)

# Agents now have collective intelligence!
```

### LangGraph

```python
from cognihive.integrations import LangGraphHive, create_expert_routing_graph

hive = LangGraphHive()
hive.register_agent("researcher", expertise=["research"])
hive.register_agent("writer", expertise=["writing"])

# Create a graph with automatic expert routing
graph = create_expert_routing_graph(
    hive=hive,
    agent_nodes={
        "researcher": researcher_node,
        "writer": writer_node
    }
)
```

## 🛠️ CLI

```bash
# Initialize a hive
cognihive init --name my_project

# Register agents
cognihive register coder --expertise python javascript

# Store knowledge
cognihive remember "Important info" --agent coder

# Query "who knows what"
cognihive who-knows "python optimization"

# Search memories
cognihive recall "best practices"

# Run interactive demo
cognihive demo
```

## 📚 Documentation

### Core Concepts

| Concept | Description |
|---------|-------------|
| **Hive** | The central coordinator for multi-agent memory |
| **Agent** | An entity with expertise that stores/retrieves memories |
| **Memory** | A piece of knowledge with provenance and access control |
| **ExpertiseProfile** | Tracks "who knows what" for each agent |
| **ExpertiseRouter** | Routes queries to the best expert |

### Key Methods

```python
# Agent management
hive.register_agent(name, expertise, role)
hive.get_agent(name)
hive.list_agents()

# Memory operations
hive.remember(content, agent, topics, visibility)
hive.recall(query, top_k=5)

# Transactive memory (THE INNOVATION)
hive.who_knows(topic)          # Find experts
hive.get_expert(topic)         # Get best expert
hive.expertise_matrix()        # Get full expertise map

# Query routing
hive.ask(query)                # Auto-route + retrieve
hive.route(query)              # Get routing decision
```

### Memory Visibility

```python
# Private - only the owner sees it
hive.remember("Secret notes", agent="coder", visibility="private")

# Shared - specific agents can see
hive.remember("For the team lead", agent="coder", visibility="shared")

# Team - all agents in the hive can see
hive.remember("Team announcement", agent="coder", visibility="team")
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      CogniHive Core                                  │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │               TRANSACTIVE MEMORY INDEX                       │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │    │
│  │  │ Agent: Coder│  │ Agent: Docs │  │Agent: Data  │          │    │
│  │  │ Knows:      │  │ Knows:      │  │ Knows:      │          │    │
│  │  │ - Python    │  │ - API specs │  │ - SQL       │          │    │
│  │  │ - FastAPI   │  │ - Tutorials │  │ - Analytics │          │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘          │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    EXPERTISE ROUTER                          │    │
│  │  Query: "How do I optimize the database queries?"            │    │
│  │  Routing: Data Agent (0.92) > Coder Agent (0.67)            │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

## 🎯 Use Cases

- **Multi-Agent Software Teams** - Coder, reviewer, tester, writer working together
- **Research Workflows** - Researcher, analyst, writer with shared findings
- **Customer Support** - Specialists routing questions to the right expert
- **Enterprise Knowledge** - Departments sharing institutional knowledge

## 📊 Comparison

| Feature | Mem0 | Zep | Letta | CogniHive |
|---------|------|-----|-------|-----------|
| Single-agent memory | ✅ | ✅ | ✅ | ✅ |
| "Who Knows What" | ❌ | ❌ | ❌ | ✅ |
| Expert routing | ❌ | ❌ | ❌ | ✅ |
| Conflict resolution | ❌ | ❌ | ❌ | ✅ |
| Access control | ❌ | ❌ | ❌ | ✅ |
| CrewAI integration | ❌ | ❌ | ❌ | ✅ |
| AutoGen integration | ❌ | ❌ | ❌ | ✅ |

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **Daniel Wegner** - Transactive Memory Systems theory (1985)
- **Anthropic** - Multi-agent coordination research
- **Stanford** - Generative Agents memory architecture

---

<div align="center">

**Built with ❤️ for the multi-agent AI community**

[⭐ Star on GitHub](https://github.com/vrush/cognihive) • [📦 PyPI](https://pypi.org/project/cognihive/) • [🤗 HuggingFace Demo](https://huggingface.co/spaces/vrush/cognihive)

</div>
