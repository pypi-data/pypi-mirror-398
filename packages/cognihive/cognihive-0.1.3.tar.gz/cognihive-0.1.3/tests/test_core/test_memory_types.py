"""Tests for CogniHive core memory types."""

import pytest
from datetime import datetime, timedelta

from cognihive.core.memory_types import (
    Memory,
    ExpertiseProfile,
    TopicExpertise,
    RoutingDecision,
    AccessPolicy,
    MemoryVisibility,
    Conflict,
    Resolution,
    ConflictType,
    ResolutionStrategy,
)


class TestMemory:
    """Tests for the Memory dataclass."""
    
    def test_memory_creation(self):
        """Test basic memory creation."""
        memory = Memory(
            content="Test content",
            owner_id="agent1",
            owner_name="TestAgent"
        )
        assert memory.content == "Test content"
        assert memory.owner_id == "agent1"
        assert memory.id is not None
        assert memory.is_active is True
    
    def test_memory_with_topics(self):
        """Test memory with topics."""
        memory = Memory(
            content="Python is great",
            topics=["python", "programming"]
        )
        assert "python" in memory.topics
        assert len(memory.topics) == 2
    
    def test_memory_to_dict(self):
        """Test memory serialization."""
        memory = Memory(
            content="Test",
            owner_id="agent1",
            owner_name="Agent",
            topics=["test"],
            confidence=0.9
        )
        d = memory.to_dict()
        assert d["content"] == "Test"
        assert d["owner_id"] == "agent1"
        assert d["confidence"] == 0.9
    
    def test_memory_from_dict(self):
        """Test memory deserialization."""
        data = {
            "id": "test-id",
            "content": "Test content",
            "owner_id": "agent1",
            "topics": ["topic1"],
            "confidence": 0.8
        }
        memory = Memory.from_dict(data)
        assert memory.id == "test-id"
        assert memory.content == "Test content"
        assert memory.confidence == 0.8


class TestAccessPolicy:
    """Tests for AccessPolicy."""
    
    def test_default_policy(self):
        """Test default access policy."""
        policy = AccessPolicy()
        assert policy.visibility == MemoryVisibility.TEAM
    
    def test_allows_read_public(self):
        """Test public visibility allows reads."""
        policy = AccessPolicy(visibility=MemoryVisibility.PUBLIC)
        assert policy.allows("any_agent", "read") is True
    
    def test_allows_team_read(self):
        """Test team visibility allows reads."""
        policy = AccessPolicy(visibility=MemoryVisibility.TEAM)
        assert policy.allows("team_member", "read") is True
    
    def test_denies_expired_access(self):
        """Test expired access is denied."""
        policy = AccessPolicy(
            visibility=MemoryVisibility.TEAM,
            expires_at=datetime.now() - timedelta(hours=1)
        )
        assert policy.allows("agent", "read") is False
    
    def test_specific_permissions(self):
        """Test specific permission lists."""
        policy = AccessPolicy(
            visibility=MemoryVisibility.SHARED,
            can_read=["agent1", "agent2"],
            can_write=["agent1"]
        )
        assert policy.allows("agent1", "read") is True
        assert policy.allows("agent1", "write") is True
        assert policy.allows("agent2", "write") is False


class TestExpertiseProfile:
    """Tests for ExpertiseProfile."""
    
    def test_profile_creation(self):
        """Test expertise profile creation."""
        profile = ExpertiseProfile(
            agent_id="agent1",
            agent_name="TestAgent"
        )
        assert profile.agent_id == "agent1"
        assert len(profile.expertise_domains) == 0
    
    def test_get_domain_score(self):
        """Test getting domain scores."""
        profile = ExpertiseProfile(
            agent_id="agent1",
            agent_name="Coder",
            expertise_domains={"python": 0.9, "javascript": 0.7}
        )
        assert profile.get_domain_score("python") == 0.9
        assert profile.get_domain_score("unknown") == 0.0
    
    def test_update_expertise(self):
        """Test updating expertise scores."""
        profile = ExpertiseProfile(
            agent_id="agent1",
            agent_name="Coder",
            expertise_domains={"python": 0.5}
        )
        profile.update_expertise("python", 0.2)
        assert profile.expertise_domains["python"] == 0.7
    
    def test_expertise_clamped(self):
        """Test expertise scores are clamped to 0-1."""
        profile = ExpertiseProfile(
            agent_id="agent1",
            agent_name="Coder",
            expertise_domains={"python": 0.9}
        )
        profile.update_expertise("python", 0.5)  # Would be 1.4
        assert profile.expertise_domains["python"] == 1.0
    
    def test_get_top_domains(self):
        """Test getting top domains."""
        profile = ExpertiseProfile(
            agent_id="agent1",
            agent_name="Coder",
            expertise_domains={
                "python": 0.9,
                "javascript": 0.7,
                "sql": 0.5,
                "rust": 0.3
            }
        )
        top = profile.get_top_domains(2)
        assert top[0] == ("python", 0.9)
        assert top[1] == ("javascript", 0.7)


class TestTopicExpertise:
    """Tests for TopicExpertise."""
    
    def test_effective_confidence_self_only(self):
        """Test effective confidence with only self-assessment."""
        exp = TopicExpertise(topic="python", confidence=0.8)
        assert exp.effective_confidence == 0.8
    
    def test_effective_confidence_with_validation(self):
        """Test effective confidence with external validation."""
        exp = TopicExpertise(
            topic="python",
            confidence=0.8,
            validated_confidence=0.9
        )
        # 0.3 * 0.8 + 0.7 * 0.9 = 0.24 + 0.63 = 0.87
        assert abs(exp.effective_confidence - 0.87) < 0.01


class TestRoutingDecision:
    """Tests for RoutingDecision."""
    
    def test_routing_decision_creation(self):
        """Test routing decision creation."""
        decision = RoutingDecision(
            primary_agent="agent1",
            primary_confidence=0.9,
            secondary_agents=["agent2"],
            reasoning="Best match for Python queries"
        )
        assert decision.primary_agent == "agent1"
        assert decision.primary_confidence == 0.9
        assert "agent2" in decision.secondary_agents
    
    def test_to_dict(self):
        """Test serialization."""
        decision = RoutingDecision(
            primary_agent="agent1",
            primary_confidence=0.85,
            query="How do I sort a list?"
        )
        d = decision.to_dict()
        assert d["primary_agent"] == "agent1"
        assert d["primary_confidence"] == 0.85


class TestConflict:
    """Tests for Conflict and Resolution."""
    
    def test_conflict_creation(self):
        """Test conflict creation."""
        conflict = Conflict(
            memory_a_id="mem1",
            memory_b_id="mem2",
            memory_a_content="The limit is 100",
            memory_b_content="The limit is 200",
            conflict_type=ConflictType.CONTRADICTION,
            severity=0.8
        )
        assert conflict.memory_a_id == "mem1"
        assert conflict.conflict_type == ConflictType.CONTRADICTION
    
    def test_resolution_creation(self):
        """Test resolution creation."""
        resolution = Resolution(
            conflict_id="conflict1",
            winning_memory_id="mem1",
            strategy=ResolutionStrategy.RECENCY,
            is_resolved=True,
            reasoning="Memory 1 is more recent"
        )
        assert resolution.is_resolved is True
        assert resolution.strategy == ResolutionStrategy.RECENCY


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
