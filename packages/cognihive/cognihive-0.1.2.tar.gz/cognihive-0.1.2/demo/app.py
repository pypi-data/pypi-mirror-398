"""
CogniHive Gradio Demo - HuggingFace Spaces

Interactive demo showcasing:
1. Agent Network Visualization
2. "Who Knows What" Queries
3. Live Query Routing
4. Memory Storage & Recall
"""

import os
import sys

# Add the src directory to Python path for HuggingFace Spaces
# This allows importing cognihive from the src folder
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "src")
if os.path.exists(src_path):
    sys.path.insert(0, src_path)

import gradio as gr
from typing import List, Tuple, Dict, Any
import json

# Import CogniHive
from cognihive import Hive


# ============================================================================
# Global Hive Instance (shared across demo)
# ============================================================================

def create_demo_hive() -> Hive:
    """Create a pre-populated demo hive."""
    hive = Hive(name="demo")
    
    # Register diverse agents
    hive.register_agent(
        "python_expert",
        expertise=["python", "fastapi", "django", "testing", "async"],
        role="Python Developer"
    )
    hive.register_agent(
        "data_scientist",
        expertise=["sql", "pandas", "machine-learning", "analytics", "statistics"],
        role="Data Scientist"
    )
    hive.register_agent(
        "frontend_dev",
        expertise=["react", "typescript", "css", "javascript", "ui-ux"],
        role="Frontend Developer"
    )
    hive.register_agent(
        "devops_engineer",
        expertise=["docker", "kubernetes", "aws", "ci-cd", "terraform"],
        role="DevOps Engineer"
    )
    hive.register_agent(
        "tech_writer",
        expertise=["documentation", "api-docs", "tutorials", "examples"],
        role="Technical Writer"
    )
    
    # Pre-populate with knowledge
    memories = [
        ("Use async/await with FastAPI for 10x better performance", "python_expert", ["python", "fastapi", "performance"]),
        ("pytest-asyncio is essential for testing async code", "python_expert", ["python", "testing", "async"]),
        ("Connection pooling with asyncpg gives 3x throughput", "data_scientist", ["sql", "performance", "postgres"]),
        ("Use EXPLAIN ANALYZE to debug slow queries", "data_scientist", ["sql", "debugging", "optimization"]),
        ("React 19 Server Components reduce bundle by 40%", "frontend_dev", ["react", "performance", "server-components"]),
        ("CSS container queries > media queries for components", "frontend_dev", ["css", "responsive", "modern"]),
        ("Use multi-stage Docker builds for smaller images", "devops_engineer", ["docker", "optimization", "best-practices"]),
        ("Terraform state should be stored in S3 with locking", "devops_engineer", ["terraform", "aws", "infrastructure"]),
        ("Always include code examples in API documentation", "tech_writer", ["documentation", "api-docs", "best-practices"]),
        ("Use OpenAPI specs to auto-generate client libraries", "tech_writer", ["api-docs", "openapi", "automation"]),
    ]
    
    for content, agent, topics in memories:
        hive.remember(content, agent=agent, topics=topics)
    
    return hive


# Global hive
HIVE = create_demo_hive()


# ============================================================================
# Gradio Interface Functions
# ============================================================================

def get_agents_display() -> str:
    """Get formatted display of all agents and their expertise."""
    lines = ["## Registered Agents\n"]
    
    matrix = HIVE.expertise_matrix()
    for agent_name, domains in matrix.items():
        agent = HIVE.get_agent(agent_name)
        role = agent.role if agent else ""
        
        top_domains = sorted(domains.items(), key=lambda x: x[1], reverse=True)[:5]
        domain_badges = " ".join([f"`{d}`" for d, _ in top_domains if _ > 0.3])
        
        lines.append(f"### {agent_name}")
        lines.append(f"**Role:** {role}")
        lines.append(f"**Expertise:** {domain_badges}")
        lines.append("")
    
    return "\n".join(lines)


def who_knows_query(topic: str) -> Tuple[str, str]:
    """Query who knows about a topic."""
    if not topic.strip():
        return "Please enter a topic to search.", ""
    
    experts = HIVE.who_knows(topic)
    
    if not experts:
        return f"No experts found for: **{topic}**", ""
    
    # Format results
    lines = [f"## Experts on '{topic}'\n"]
    
    chart_data = []
    for name, score in experts:
        agent = HIVE.get_agent(name)
        role = agent.role if agent else ""
        
        # Visual bar
        bar_width = int(score * 20)
        bar = "█" * bar_width + "░" * (20 - bar_width)
        
        lines.append(f"**{name}** ({role})")
        lines.append(f"`[{bar}]` {score:.2f}")
        lines.append("")
        
        chart_data.append({"agent": name, "score": score})
    
    return "\n".join(lines), json.dumps(chart_data, indent=2)


def ask_query(question: str) -> Tuple[str, str, str]:
    """Ask a question and get routed to an expert."""
    if not question.strip():
        return "Please enter a question.", "", ""
    
    result = HIVE.ask(question)
    
    # Format routing decision
    routing_lines = ["## Routing Decision\n"]
    routing_lines.append(f"**Question:** {question}")
    routing_lines.append("")
    routing_lines.append(f"**Routed to:** {result['expert'] or 'No expert found'}")
    routing_lines.append(f"**Confidence:** {result['confidence']:.2f}")
    
    if result['secondary_experts']:
        routing_lines.append(f"**Secondary experts:** {', '.join(result['secondary_experts'])}")
    
    routing_lines.append("")
    routing_lines.append("### Reasoning")
    routing_lines.append(result['reasoning'] or "No specific reasoning available.")
    
    # Format memories
    memory_lines = ["## Relevant Memories\n"]
    if result['memories']:
        for i, (mem, score) in enumerate(zip(result['memories'], result['scores']), 1):
            memory_lines.append(f"**{i}. From {mem.owner_name}** (relevance: {score:.2f})")
            memory_lines.append(f"> {mem.content}")
            memory_lines.append("")
    else:
        memory_lines.append("No relevant memories found.")
    
    return "\n".join(routing_lines), "\n".join(memory_lines), result['expert']


def add_memory(content: str, agent: str, topics: str) -> str:
    """Add a new memory to the hive."""
    if not content.strip():
        return "Please enter memory content."
    
    if not agent.strip():
        return "Please select an agent."
    
    topic_list = [t.strip() for t in topics.split(",") if t.strip()]
    
    try:
        memory = HIVE.remember(content, agent=agent, topics=topic_list)
        return f"Memory stored successfully!\n\n**ID:** `{memory.id[:8]}...`\n**Agent:** {agent}\n**Topics:** {', '.join(topic_list) or 'None'}"
    except Exception as e:
        return f"Error storing memory: {str(e)}"


def recall_memories(query: str) -> str:
    """Search for memories."""
    if not query.strip():
        return "Please enter a search query."
    
    results = HIVE.recall(query, top_k=5)
    
    if not results:
        return f"No memories found for: **{query}**"
    
    lines = [f"## Memories matching '{query}'\n"]
    
    for i, (memory, score) in enumerate(results, 1):
        lines.append(f"### {i}. {memory.owner_name} (score: {score:.2f})")
        lines.append(f"> {memory.content}")
        if memory.topics:
            lines.append(f"**Topics:** {', '.join(memory.topics)}")
        lines.append("")
    
    return "\n".join(lines)


def get_hive_stats() -> str:
    """Get hive statistics."""
    stats = HIVE.stats()
    
    lines = [
        "## Hive Statistics\n",
        f"**Name:** {stats['name']}",
        f"**Agents:** {stats['agent_count']}",
        f"**Memories:** {stats['memory_count']}",
        f"**Queries Processed:** {stats['metrics']['queries_processed']}",
        f"**Routing Decisions:** {stats['metrics']['routing_decisions']}",
    ]
    
    return "\n".join(lines)


def reset_hive() -> str:
    """Reset the hive to initial state."""
    global HIVE
    HIVE = create_demo_hive()
    return "Hive reset to initial state with demo data."


# ============================================================================
# Build Gradio Interface
# ============================================================================

def create_demo():
    """Create the Gradio demo interface."""
    
    with gr.Blocks(
        title="CogniHive - Transactive Memory for AI Agents",
        theme=gr.themes.Soft(
            primary_hue="amber",
            secondary_hue="orange",
        ),
        css="""
        .gradio-container { max-width: 1200px !important; }
        .main-header { text-align: center; margin-bottom: 20px; }
        .feature-box { border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; margin: 10px 0; }
        """
    ) as demo:
        
        # Header
        gr.Markdown("""
        # CogniHive
        ### The World's First Transactive Memory System for Multi-Agent AI
        
        **"Mem0 gives one agent a brain. CogniHive gives your agent team a collective mind."**
        
        ---
        """)
        
        with gr.Tabs():
            
            # Tab 1: Who Knows What
            with gr.TabItem("Who Knows What"):
                gr.Markdown("""
                ## Find Experts on Any Topic
                
                This is the core innovation of CogniHive: **Transactive Memory**.
                Ask "who knows about X" and find the right expert instantly.
                """)
                
                with gr.Row():
                    with gr.Column(scale=1):
                        topic_input = gr.Textbox(
                            label="Topic to search",
                            placeholder="e.g., python optimization, database security, react components",
                            lines=1
                        )
                        who_knows_btn = gr.Button("Find Experts", variant="primary")
                        
                        gr.Examples(
                            examples=[
                                ["python async programming"],
                                ["database optimization"],
                                ["react performance"],
                                ["docker best practices"],
                                ["API documentation"],
                            ],
                            inputs=topic_input,
                            label="Try these topics:"
                        )
                    
                    with gr.Column(scale=2):
                        who_knows_output = gr.Markdown(label="Expert Results")
                        who_knows_data = gr.Code(label="Raw Data (JSON)", language="json", visible=False)
                
                who_knows_btn.click(
                    who_knows_query,
                    inputs=[topic_input],
                    outputs=[who_knows_output, who_knows_data]
                )
            
            # Tab 2: Ask a Question
            with gr.TabItem("Ask & Route"):
                gr.Markdown("""
                ## Automatic Query Routing
                
                Ask any question and CogniHive will automatically route it to the best expert
                and retrieve relevant memories.
                """)
                
                with gr.Row():
                    with gr.Column(scale=1):
                        question_input = gr.Textbox(
                            label="Your Question",
                            placeholder="e.g., How do I improve my Python code performance?",
                            lines=2
                        )
                        ask_btn = gr.Button("Ask the Hive", variant="primary")
                        
                        routed_to = gr.Textbox(label="Routed to Expert", interactive=False)
                        
                        gr.Examples(
                            examples=[
                                ["How do I write better async Python code?"],
                                ["What's the best way to optimize SQL queries?"],
                                ["How should I structure my React components?"],
                                ["What are Docker best practices?"],
                                ["How do I document my API effectively?"],
                            ],
                            inputs=question_input,
                            label="Try these questions:"
                        )
                    
                    with gr.Column(scale=2):
                        routing_output = gr.Markdown(label="Routing Decision")
                        memories_output = gr.Markdown(label="Relevant Memories")
                
                ask_btn.click(
                    ask_query,
                    inputs=[question_input],
                    outputs=[routing_output, memories_output, routed_to]
                )
            
            # Tab 3: Memory Operations
            with gr.TabItem("Memory"):
                gr.Markdown("""
                ## Store & Recall Team Knowledge
                
                Add new memories to the hive or search existing knowledge.
                """)
                
                with gr.Row():
                    # Add memory
                    with gr.Column():
                        gr.Markdown("### Add New Memory")
                        memory_content = gr.Textbox(
                            label="Memory Content",
                            placeholder="Enter knowledge to store...",
                            lines=3
                        )
                        memory_agent = gr.Dropdown(
                            label="Agent",
                            choices=["python_expert", "data_scientist", "frontend_dev", "devops_engineer", "tech_writer"],
                            value="python_expert"
                        )
                        memory_topics = gr.Textbox(
                            label="Topics (comma-separated)",
                            placeholder="e.g., python, performance, tips"
                        )
                        add_memory_btn = gr.Button("Store Memory", variant="primary")
                        add_result = gr.Markdown()
                    
                    # Search memories
                    with gr.Column():
                        gr.Markdown("### Search Memories")
                        search_query = gr.Textbox(
                            label="Search Query",
                            placeholder="Search for relevant memories...",
                            lines=1
                        )
                        search_btn = gr.Button("Search", variant="secondary")
                        search_results = gr.Markdown()
                
                add_memory_btn.click(
                    add_memory,
                    inputs=[memory_content, memory_agent, memory_topics],
                    outputs=[add_result]
                )
                
                search_btn.click(
                    recall_memories,
                    inputs=[search_query],
                    outputs=[search_results]
                )
            
            # Tab 4: Agent Network
            with gr.TabItem("Agents"):
                gr.Markdown("""
                ## Agent Network & Expertise
                
                View all registered agents and their areas of expertise.
                """)
                
                with gr.Row():
                    with gr.Column():
                        refresh_btn = gr.Button("Refresh Agent List")
                        agents_display = gr.Markdown(value=get_agents_display())
                    
                    with gr.Column():
                        stats_display = gr.Markdown(value=get_hive_stats(), label="Hive Stats")
                        reset_btn = gr.Button("Reset Hive", variant="secondary")
                        reset_result = gr.Markdown()
                
                refresh_btn.click(get_agents_display, outputs=[agents_display])
                refresh_btn.click(get_hive_stats, outputs=[stats_display])
                reset_btn.click(reset_hive, outputs=[reset_result])
        
        # Footer
        gr.Markdown("""
        ---
        
        ### About CogniHive
        
        CogniHive implements **Transactive Memory Systems (TMS)** for AI agents - 
        a concept from cognitive science that enables teams to know "who knows what."
        
        **Key Features:**
        - "Who Knows What" queries
        - Automatic expert routing
        - Memory with access control
        - Framework integrations (CrewAI, AutoGen, LangGraph)
        
        [GitHub](https://github.com/vrush/cognihive) | [PyPI](https://pypi.org/project/cognihive/)
        
        ---
        *Built with Gradio | Powered by ChromaDB*
        """)
    
    return demo


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    demo = create_demo()
    demo.launch(
        share=False,
        server_name="0.0.0.0",
        server_port=7860
    )
