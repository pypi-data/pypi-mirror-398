"""
CogniHive: The World's First Transactive Memory System for Multi-Agent AI

Mem0 gives one agent a brain. CogniHive gives your agent team a collective mind.
"""

from cognihive.core.hive import Hive
from cognihive.core.memory_types import (
    Memory,
    ExpertiseProfile,
    TopicExpertise,
    RoutingDecision,
    AccessPolicy,
    Conflict,
    Resolution,
)
from cognihive.core.agent_registry import AgentRegistry, Agent

__version__ = "0.1.0"
__author__ = "Vrushket"
__all__ = [
    "Hive",
    "Memory",
    "ExpertiseProfile",
    "TopicExpertise",
    "RoutingDecision",
    "AccessPolicy",
    "Agent",
    "AgentRegistry",
    "Conflict",
    "Resolution",
]
