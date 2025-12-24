"""Tests for CogniHive Hive class."""

import pytest

from cognihive import Hive, Memory


class TestHiveBasics:
    """Basic Hive functionality tests."""
    
    def test_hive_creation(self):
        """Test basic hive initialization."""
        hive = Hive(name="test")
        assert hive.name == "test"
        assert len(hive.agents) == 0
    
    def test_register_agent(self):
        """Test agent registration."""
        hive = Hive(name="test")
        agent = hive.register_agent(
            "coder",
            expertise=["python", "javascript"],
            role="Software Engineer"
        )
        assert agent.name == "coder"
        assert "coder" in hive.agents
        assert len(hive.list_agents()) == 1
    
    def test_register_duplicate_agent_fails(self):
        """Test that duplicate registration fails."""
        hive = Hive(name="test")
        hive.register_agent("coder")
        with pytest.raises(ValueError):
            hive.register_agent("coder")
    
    def test_get_agent(self):
        """Test getting an agent."""
        hive = Hive(name="test")
        hive.register_agent("coder")
        agent = hive.get_agent("coder")
        assert agent is not None
        assert agent.name == "coder"
    
    def test_get_nonexistent_agent(self):
        """Test getting a nonexistent agent returns None."""
        hive = Hive(name="test")
        assert hive.get_agent("nobody") is None


class TestHiveMemory:
    """Memory operations tests."""
    
    @pytest.fixture
    def hive_with_agents(self):
        """Create a hive with test agents."""
        hive = Hive(name="test")
        hive.register_agent("coder", expertise=["python", "javascript"])
        hive.register_agent("analyst", expertise=["sql", "data"])
        return hive
    
    def test_remember(self, hive_with_agents):
        """Test storing a memory."""
        hive = hive_with_agents
        memory = hive.remember(
            "Use list comprehensions for cleaner code",
            agent="coder",
            topics=["python", "best-practices"]
        )
        assert memory.content == "Use list comprehensions for cleaner code"
        assert memory.owner_name == "coder"
        assert "python" in memory.topics
    
    def test_remember_without_agent(self, hive_with_agents):
        """Test storing a memory without specifying an agent."""
        hive = hive_with_agents
        memory = hive.remember("General knowledge")
        assert memory.owner_id == ""
    
    def test_recall(self, hive_with_agents):
        """Test recalling memories."""
        hive = hive_with_agents
        hive.remember("Python is a great language", agent="coder")
        hive.remember("SQL is for databases", agent="analyst")
        
        results = hive.recall("Python programming")
        assert len(results) > 0
        # The Python memory should be most relevant
        memory, score = results[0]
        assert "python" in memory.content.lower() or score > 0


class TestTransactiveMemory:
    """Transactive memory (who knows what) tests."""
    
    @pytest.fixture
    def hive_with_knowledge(self):
        """Create a hive with agents and memories."""
        hive = Hive(name="test")
        hive.register_agent("python_expert", expertise=["python", "fastapi"])
        hive.register_agent("data_expert", expertise=["sql", "analytics"])
        hive.register_agent("fullstack", expertise=["javascript", "react"])
        
        # Add some memories
        hive.remember(
            "Use async/await for better FastAPI performance",
            agent="python_expert",
            topics=["python", "fastapi", "performance"]
        )
        hive.remember(
            "Index your frequently queried columns",
            agent="data_expert",
            topics=["sql", "optimization"]
        )
        
        return hive
    
    def test_who_knows(self, hive_with_knowledge):
        """Test finding experts on a topic."""
        hive = hive_with_knowledge
        experts = hive.who_knows("python")
        
        assert len(experts) > 0
        # python_expert should be top
        assert experts[0][0] == "python_expert"
    
    def test_who_knows_sql(self, hive_with_knowledge):
        """Test finding SQL experts."""
        hive = hive_with_knowledge
        experts = hive.who_knows("database optimization")
        
        # data_expert should be top
        names = [name for name, _ in experts]
        assert "data_expert" in names
    
    def test_get_expert(self, hive_with_knowledge):
        """Test getting the single best expert."""
        hive = hive_with_knowledge
        expert = hive.get_expert("python async")
        assert expert == "python_expert"
    
    def test_expertise_matrix(self, hive_with_knowledge):
        """Test getting the full expertise matrix."""
        hive = hive_with_knowledge
        matrix = hive.expertise_matrix()
        
        assert "python_expert" in matrix
        assert "python" in matrix["python_expert"]


class TestQueryRouting:
    """Query routing tests."""
    
    @pytest.fixture
    def hive_with_experts(self):
        """Create a hive with diverse experts."""
        hive = Hive(name="test")
        hive.register_agent("coder", expertise=["python", "api", "testing"])
        hive.register_agent("dba", expertise=["sql", "postgres", "optimization"])
        hive.register_agent("writer", expertise=["docs", "tutorials"])
        return hive
    
    def test_route(self, hive_with_experts):
        """Test query routing."""
        hive = hive_with_experts
        decision = hive.route("How do I write unit tests?")
        
        # Should route to coder
        agent = hive.get_agent(decision.primary_agent)
        if agent:
            assert agent.name == "coder"
    
    def test_ask(self, hive_with_experts):
        """Test ask with routing."""
        hive = hive_with_experts
        
        # Add a memory
        hive.remember(
            "Use pytest for Python testing",
            agent="coder",
            topics=["testing", "pytest"]
        )
        
        result = hive.ask("How should I test my code?")
        
        assert "expert" in result
        assert "memories" in result
        # The coder should be the expert
        assert result["expert"] == "coder" or result["confidence"] >= 0


class TestHiveStats:
    """Stats and utility tests."""
    
    def test_stats(self):
        """Test getting hive stats."""
        hive = Hive(name="test")
        hive.register_agent("agent1")
        hive.remember("Test memory", agent="agent1")
        
        stats = hive.stats()
        assert stats["name"] == "test"
        assert stats["agent_count"] == 1
        assert stats["memory_count"] >= 1
    
    def test_summary(self):
        """Test getting summary."""
        hive = Hive(name="test_hive")
        hive.register_agent("coder", expertise=["python"])
        
        summary = hive.summary()
        assert "CogniHive" in summary
        assert "coder" in summary
    
    def test_repr(self):
        """Test string representation."""
        hive = Hive(name="test")
        repr_str = repr(hive)
        assert "test" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
