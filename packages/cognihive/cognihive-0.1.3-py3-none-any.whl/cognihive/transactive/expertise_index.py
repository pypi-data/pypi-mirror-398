"""
Expertise Index - The Heart of Transactive Memory.

This module implements "Who Knows What" - tracking each agent's expertise
and enabling queries like "which agent is the expert on X?".
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

from cognihive.core.memory_types import ExpertiseProfile, TopicExpertise


@dataclass
class ExpertiseMatch:
    """Result of matching a query to expertise."""
    agent_id: str
    agent_name: str
    score: float
    matched_domains: List[str]
    matched_topics: List[str]
    evidence: List[str] = field(default_factory=list)


class ExpertiseIndex:
    """The Transactive Memory Index - tracks \"who knows what\".
    
    This is the core novel component of CogniHive. It maintains an index
    of each agent's expertise and enables efficient lookups.
    
    Key capabilities:
    - Index expertise from memories automatically
    - Query for experts on any topic
    - Learn and update expertise over time
    - Track expertise confidence and reliability
    """
    
    def __init__(self, embedding_model: Optional[Any] = None):
        """Initialize the expertise index.
        
        Args:
            embedding_model: Optional sentence transformer model for semantic matching
        """
        self._profiles: Dict[str, ExpertiseProfile] = {}
        self._domain_embeddings: Dict[str, List[float]] = {}
        self._embedding_model = embedding_model
        self._embedding_dim = 384  # Default for many models
        
        # Domain keyword mappings for fast matching
        self._domain_keywords: Dict[str, List[str]] = self._init_domain_keywords()
    
    def _init_domain_keywords(self) -> Dict[str, List[str]]:
        """Initialize domain to keyword mappings."""
        return {
            "python": ["python", "py", "pandas", "numpy", "django", "flask", "fastapi"],
            "javascript": ["javascript", "js", "node", "react", "vue", "angular", "typescript"],
            "sql": ["sql", "database", "mysql", "postgres", "sqlite", "query", "join"],
            "data": ["data", "analysis", "analytics", "statistics", "visualization", "etl"],
            "ml": ["machine learning", "ml", "model", "training", "neural", "deep learning"],
            "api": ["api", "rest", "graphql", "endpoint", "http", "request"],
            "devops": ["devops", "docker", "kubernetes", "ci/cd", "deployment", "aws"],
            "testing": ["test", "testing", "unittest", "pytest", "qa", "quality"],
            "docs": ["documentation", "docs", "readme", "tutorial", "guide"],
            "security": ["security", "auth", "authentication", "encryption", "jwt"],
        }
    
    def register_agent(
        self,
        agent_id: str,
        agent_name: str,
        initial_expertise: Optional[Dict[str, float]] = None
    ) -> ExpertiseProfile:
        """Register an agent in the expertise index.
        
        Args:
            agent_id: Unique agent identifier
            agent_name: Human-readable agent name
            initial_expertise: Optional dict of {domain: score} for initial expertise
            
        Returns:
            The created ExpertiseProfile
        """
        profile = ExpertiseProfile(
            agent_id=agent_id,
            agent_name=agent_name,
            expertise_domains=initial_expertise or {}
        )
        self._profiles[agent_id] = profile
        return profile
    
    def get_profile(self, agent_id: str) -> Optional[ExpertiseProfile]:
        """Get an agent's expertise profile."""
        return self._profiles.get(agent_id)
    
    def index_expertise(
        self,
        agent_id: str,
        memory_content: str,
        topics: List[str],
        confidence: float = 0.7
    ) -> Dict[str, float]:
        """Index expertise from a memory.
        
        Automatically extracts and updates expertise based on memory content.
        
        Args:
            agent_id: The agent who created the memory
            memory_content: The memory text content
            topics: Explicit topics from the memory
            confidence: Confidence to assign to expertise
            
        Returns:
            Dict of domains that were updated with their scores
        """
        profile = self._profiles.get(agent_id)
        if not profile:
            return {}
        
        updated_domains = {}
        content_lower = memory_content.lower()
        
        # Match against domain keywords
        for domain, keywords in self._domain_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    # Update expertise with diminishing returns
                    current = profile.expertise_domains.get(domain, 0.0)
                    boost = (confidence - current) * 0.1  # Gradual learning
                    new_score = min(1.0, current + max(0.05, boost))
                    profile.expertise_domains[domain] = new_score
                    updated_domains[domain] = new_score
                    break
        
        # Index explicit topics
        for topic in topics:
            topic_lower = topic.lower()
            profile.add_topic_expertise(topic_lower, confidence)
            
            # Also check if topic matches a domain
            for domain, keywords in self._domain_keywords.items():
                if topic_lower in keywords or domain in topic_lower:
                    current = profile.expertise_domains.get(domain, 0.0)
                    new_score = min(1.0, current + 0.1)
                    profile.expertise_domains[domain] = new_score
                    updated_domains[domain] = new_score
        
        # Update metrics
        profile.total_memories += 1
        profile.last_active = datetime.now()
        
        return updated_domains
    
    def query_experts(
        self,
        topic: str,
        min_score: float = 0.3,
        top_k: int = 5
    ) -> List[ExpertiseMatch]:
        """Find agents who are experts on a topic.
        
        This is the core "who knows what" query.
        
        Args:
            topic: The topic to find experts for
            min_score: Minimum expertise score to include
            top_k: Maximum number of experts to return
            
        Returns:
            List of ExpertiseMatch objects, sorted by score
        """
        matches = []
        topic_lower = topic.lower()
        topic_words = set(topic_lower.split())
        
        for agent_id, profile in self._profiles.items():
            score = 0.0
            matched_domains = []
            matched_topics = []
            
            # Check domain matches
            for domain, domain_score in profile.expertise_domains.items():
                # Direct domain match
                if domain in topic_lower or topic_lower in domain:
                    score = max(score, domain_score)
                    matched_domains.append(domain)
                
                # Keyword match within domain
                keywords = self._domain_keywords.get(domain, [])
                for keyword in keywords:
                    if keyword in topic_lower:
                        score = max(score, domain_score * 0.9)
                        if domain not in matched_domains:
                            matched_domains.append(domain)
            
            # Check topic matches
            for topic_name, topic_exp in profile.topics.items():
                if topic_name in topic_lower or topic_lower in topic_name:
                    topic_score = topic_exp.effective_confidence
                    score = max(score, topic_score)
                    matched_topics.append(topic_name)
                
                # Word overlap
                topic_words_set = set(topic_name.split())
                overlap = len(topic_words & topic_words_set)
                if overlap > 0:
                    overlap_score = topic_exp.effective_confidence * (overlap / max(len(topic_words), len(topic_words_set)))
                    score = max(score, overlap_score)
                    if topic_name not in matched_topics:
                        matched_topics.append(topic_name)
            
            if score >= min_score:
                matches.append(ExpertiseMatch(
                    agent_id=agent_id,
                    agent_name=profile.agent_name,
                    score=score,
                    matched_domains=matched_domains,
                    matched_topics=matched_topics
                ))
        
        # Sort by score and return top_k
        matches.sort(key=lambda x: x.score, reverse=True)
        return matches[:top_k]
    
    def who_knows(self, topic: str) -> List[Tuple[str, float]]:
        """Simple interface to find who knows about a topic.
        
        Args:
            topic: The topic to query
            
        Returns:
            List of (agent_name, score) tuples
        """
        matches = self.query_experts(topic)
        return [(m.agent_name, m.score) for m in matches]
    
    def get_agent_expertise_summary(self, agent_id: str) -> Dict[str, Any]:
        """Get a summary of an agent's expertise.
        
        Args:
            agent_id: The agent to summarize
            
        Returns:
            Dictionary with expertise summary
        """
        profile = self._profiles.get(agent_id)
        if not profile:
            return {}
        
        return {
            "agent_id": agent_id,
            "agent_name": profile.agent_name,
            "top_domains": profile.get_top_domains(5),
            "topic_count": len(profile.topics),
            "total_memories": profile.total_memories,
            "accuracy_score": profile.accuracy_score,
            "citation_count": profile.citation_count,
            "last_active": profile.last_active.isoformat()
        }
    
    def learn_from_outcome(
        self,
        agent_id: str,
        topic: str,
        success: bool,
        weight: float = 0.1
    ):
        """Update expertise based on query outcomes.
        
        When an agent successfully answers a query, boost their expertise.
        When they fail, reduce it slightly.
        
        Args:
            agent_id: The agent who answered
            topic: The topic of the query
            success: Whether the answer was successful
            weight: How much to adjust scores
        """
        profile = self._profiles.get(agent_id)
        if not profile:
            return
        
        delta = weight if success else -weight * 0.5
        
        # Update matching domains
        for domain in profile.expertise_domains:
            if domain in topic.lower():
                profile.update_expertise(domain, delta)
        
        # Update matching topics
        topic_lower = topic.lower()
        if topic_lower in profile.topics:
            exp = profile.topics[topic_lower]
            exp.validated_confidence = max(0, min(1, 
                exp.validated_confidence + delta
            ))
        
        # Update overall accuracy
        if success:
            profile.accuracy_score = min(1.0, profile.accuracy_score + 0.01)
        else:
            profile.accuracy_score = max(0.0, profile.accuracy_score - 0.02)
    
    def get_all_profiles(self) -> List[ExpertiseProfile]:
        """Get all expertise profiles."""
        return list(self._profiles.values())
    
    def export_expertise_matrix(self) -> Dict[str, Dict[str, float]]:
        """Export the full expertise matrix.
        
        Returns:
            Dict of {agent_id: {domain: score, ...}, ...}
        """
        matrix = {}
        for agent_id, profile in self._profiles.items():
            matrix[agent_id] = dict(profile.expertise_domains)
        return matrix
