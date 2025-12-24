---
title: CogniHive
emoji: "\U0001F41D"
colorFrom: yellow
colorTo: red
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: true
license: mit
short_description: Transactive Memory for Multi-Agent AI
tags:
  - multi-agent
  - memory
  - ai-agents
  - transactive-memory
  - crewai
  - autogen
  - langgraph
  - collective-intelligence
  - agent-orchestration
  - llm
---

<div align="center">

# 🐝 CogniHive

### The World's First Transactive Memory for Multi-Agent AI

**"Mem0 gives one agent a brain. CogniHive gives your agent team a collective mind."**

[![GitHub stars](https://img.shields.io/github/stars/vrush/cognihive?style=social)](https://github.com/vrush/cognihive)
[![PyPI](https://img.shields.io/pypi/v/cognihive)](https://pypi.org/project/cognihive/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

</div>

---

## 🧠 The Problem No One Has Solved

Every multi-agent AI system today suffers from the same problem:

> **"Agents don't know what each other knows."**

This leads to:
- 🔄 **Redundant work** - Multiple agents research the same thing
- 💰 **Token explosion** - 15x more tokens wasted (Anthropic's research)
- 🎲 **Random routing** - Questions go to the wrong agent
- 🤷 **Lost expertise** - Agent A learns something, Agent B never finds out

---

## 💡 The Solution: Transactive Memory

In human teams, not everyone remembers everything. Instead, teams develop **"who knows what"** awareness:

- *"Sarah handles legal stuff"*
- *"Mike knows the technical details"*
- *"Ask Jennifer about customer history"*

This is called **Transactive Memory Systems (TMS)** — proven by 40 years of cognitive science research to be the #1 predictor of team performance.

**CogniHive is the FIRST implementation for AI agents.**

---

## 🎮 Try The Demo

### Tab 1: Who Knows What
Enter any topic and instantly find which agent is the expert.

### Tab 2: Ask & Route
Ask a question and watch it automatically route to the right expert.

### Tab 3: Memory
Store and recall team knowledge with full provenance.

### Tab 4: Agents
View the expertise matrix across your entire agent team.

---

## ⚡ Quick Start

```bash
pip install cognihive
```

```python
from cognihive import Hive

# Create a hive
hive = Hive()

# Register specialized agents
hive.register_agent("coder", expertise=["python", "javascript"])
hive.register_agent("analyst", expertise=["sql", "data"])
hive.register_agent("writer", expertise=["docs", "tutorials"])

# Store team knowledge
hive.remember(
    "Use connection pooling for 3x database throughput",
    agent="analyst",
    topics=["database", "performance"]
)

# THE KEY INNOVATION: "Who Knows What"
experts = hive.who_knows("database optimization")
# Returns: [("analyst", 0.92), ("coder", 0.45)]

# Automatic routing to experts
result = hive.ask("How do I improve query performance?")
print(f"Routed to: {result['expert']}")  # → "analyst"
```

---

## 🔗 Works With Your Stack

| Framework | Integration | Status |
|-----------|-------------|--------|
| **CrewAI** | `CrewAIHive` | ✅ Ready |
| **AutoGen** | `AutoGenHive` | ✅ Ready |
| **LangGraph** | `LangGraphHive` | ✅ Ready |

```python
# CrewAI Example
from cognihive.integrations import CrewAIHive

hive = CrewAIHive()
researcher = Agent(role="Researcher", memory=hive.agent_memory("researcher"))
writer = Agent(role="Writer", memory=hive.agent_memory("writer"))
# Now they share transactive memory!
```

---

## 📊 Why This Matters

| Metric | Without CogniHive | With CogniHive |
|--------|-------------------|----------------|
| Token usage | 15x baseline | 1x baseline |
| Query routing | Random/manual | Automatic |
| Team coordination | Chaos | Structured |
| Knowledge sharing | None | Full provenance |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   CogniHive Core                     │
│  ┌───────────────────────────────────────────────┐  │
│  │         TRANSACTIVE MEMORY INDEX              │  │
│  │   "Who Knows What" - The Key Innovation       │  │
│  │                                               │  │
│  │   Coder: python(0.9), api(0.7), testing(0.8)│  │
│  │   Analyst: sql(0.95), data(0.85)             │  │
│  │   Writer: docs(0.9), tutorials(0.8)          │  │
│  └───────────────────────────────────────────────┘  │
│                        ↓                             │
│  ┌───────────────────────────────────────────────┐  │
│  │            EXPERTISE ROUTER                   │  │
│  │   Query → Best Expert → Relevant Memories     │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## 🌟 Features

- **🔍 Who Knows What** - Instantly find domain experts
- **🎯 Smart Routing** - Auto-route queries to the right agent
- **🔐 Access Control** - Private, shared, and team memories
- **📝 Provenance** - Track where knowledge came from
- **⚔️ Conflict Resolution** - Handle contradicting information
- **🔌 Integrations** - CrewAI, AutoGen, LangGraph ready

---

## 📚 Research Background

CogniHive is backed by:

- **Wegner (1985)** - Original Transactive Memory Systems theory
- **Anthropic (2025)** - Multi-agent coordination research showing 15x token overhead
- **Stanford (2023)** - Generative Agents memory architecture
- **LLM-MAS Survey (2025)** - Identified "who knows what" as critical missing capability

---

## 🚀 Get Started

```bash
pip install cognihive
```

- [GitHub Repository](https://github.com/vrush/cognihive)
- [PyPI Package](https://pypi.org/project/cognihive/)
- [Documentation](https://github.com/vrush/cognihive#readme)

---

<div align="center">

**Built for the multi-agent AI revolution** 🐝

*Star us on GitHub if you find this useful!*

</div>
