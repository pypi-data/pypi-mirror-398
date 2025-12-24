"""
Expertise Router - Automatic Query Routing to Experts.

Routes queries to the most appropriate agent based on expertise matching.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any

from cognihive.core.memory_types import RoutingDecision, ExpertiseProfile
from cognihive.transactive.expertise_index import ExpertiseIndex, ExpertiseMatch


class ExpertiseRouter:
    """Routes queries to the right agent based on expertise.
    
    The router analyzes incoming queries and determines which agent(s)
    should handle them based on the expertise index.
    
    Features:
    - Multi-factor scoring (domain match, topic match, recency, accuracy)
    - Primary + secondary expert selection
    - Confidence thresholds
    - Routing explanation generation
    - Learning from outcomes
    """
    
    def __init__(
        self,
        expertise_index: ExpertiseIndex,
        min_confidence: float = 0.3,
        require_explanation: bool = True
    ):
        """Initialize the router.
        
        Args:
            expertise_index: The expertise index to use for lookups
            min_confidence: Minimum confidence to make a routing decision
            require_explanation: Whether to generate routing explanations
        """
        self.expertise_index = expertise_index
        self.min_confidence = min_confidence
        self.require_explanation = require_explanation
        
        # Routing history for learning
        self._routing_history: List[Dict[str, Any]] = []
    
    def route(
        self,
        query: str,
        available_agents: Optional[List[str]] = None,
        exclude_agents: Optional[List[str]] = None
    ) -> RoutingDecision:
        """Route a query to the best expert(s).
        
        Args:
            query: The query text to route
            available_agents: Optional list of agent IDs to consider (None = all)
            exclude_agents: Optional list of agent IDs to exclude
            
        Returns:
            RoutingDecision with primary and secondary experts
        """
        # Get all expert matches
        matches = self.expertise_index.query_experts(
            topic=query,
            min_score=self.min_confidence,
            top_k=10
        )
        
        # Filter by available/excluded agents
        if available_agents:
            available_set = set(available_agents)
            matches = [m for m in matches if m.agent_id in available_set]
        
        if exclude_agents:
            exclude_set = set(exclude_agents)
            matches = [m for m in matches if m.agent_id not in exclude_set]
        
        # Build routing decision
        if not matches:
            return RoutingDecision(
                primary_agent="",
                primary_confidence=0.0,
                reasoning="No experts found for this query",
                query=query
            )
        
        primary = matches[0]
        secondary = matches[1:3] if len(matches) > 1 else []
        
        # Generate explanation
        reasoning = self._generate_explanation(query, primary, secondary)
        
        # Collect matched domains and topics
        all_domains = []
        all_topics = []
        for m in matches[:3]:
            all_domains.extend(m.matched_domains)
            all_topics.extend(m.matched_topics)
        
        decision = RoutingDecision(
            primary_agent=primary.agent_id,
            primary_confidence=primary.score,
            secondary_agents=[m.agent_id for m in secondary],
            secondary_confidences=[m.score for m in secondary],
            reasoning=reasoning,
            matched_domains=list(set(all_domains)),
            matched_topics=list(set(all_topics)),
            query=query
        )
        
        # Record in history
        self._routing_history.append({
            "query": query,
            "decision": decision.to_dict(),
            "timestamp": datetime.now().isoformat()
        })
        
        return decision
    
    def _generate_explanation(
        self,
        query: str,
        primary: ExpertiseMatch,
        secondary: List[ExpertiseMatch]
    ) -> str:
        """Generate a human-readable routing explanation."""
        if not self.require_explanation:
            return ""
        
        parts = []
        
        # Primary expert explanation
        parts.append(f"Primary Expert: {primary.agent_name} (confidence: {primary.score:.2f})")
        
        if primary.matched_domains:
            parts.append(f"  • Matched domains: {', '.join(primary.matched_domains)}")
        if primary.matched_topics:
            parts.append(f"  • Matched topics: {', '.join(primary.matched_topics)}")
        
        # Secondary experts
        if secondary:
            parts.append("\nSecondary Experts:")
            for s in secondary:
                parts.append(f"  • {s.agent_name} (confidence: {s.score:.2f})")
        
        return "\n".join(parts)
    
    def route_with_fallback(
        self,
        query: str,
        fallback_agent: str,
        min_primary_confidence: float = 0.5
    ) -> RoutingDecision:
        """Route with fallback to a default agent if confidence is low.
        
        Args:
            query: The query to route
            fallback_agent: Agent ID to use if no confident match
            min_primary_confidence: Minimum confidence to use primary expert
            
        Returns:
            RoutingDecision (may be to fallback agent)
        """
        decision = self.route(query)
        
        if decision.primary_confidence < min_primary_confidence:
            return RoutingDecision(
                primary_agent=fallback_agent,
                primary_confidence=0.5,
                secondary_agents=[decision.primary_agent] if decision.primary_agent else [],
                secondary_confidences=[decision.primary_confidence] if decision.primary_agent else [],
                reasoning=f"Low confidence ({decision.primary_confidence:.2f}), using fallback agent",
                query=query
            )
        
        return decision
    
    def batch_route(
        self,
        queries: List[str],
        available_agents: Optional[List[str]] = None
    ) -> List[RoutingDecision]:
        """Route multiple queries at once.
        
        Args:
            queries: List of queries to route
            available_agents: Optional list of agent IDs to consider
            
        Returns:
            List of RoutingDecisions
        """
        return [
            self.route(query, available_agents)
            for query in queries
        ]
    
    def learn_from_feedback(
        self,
        query: str,
        agent_id: str,
        success: bool
    ):
        """Learn from query outcome to improve future routing.
        
        Args:
            query: The original query
            agent_id: The agent who handled it
            success: Whether the handling was successful
        """
        self.expertise_index.learn_from_outcome(
            agent_id=agent_id,
            topic=query,
            success=success
        )
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get statistics about routing decisions."""
        if not self._routing_history:
            return {"total_routes": 0}
        
        total = len(self._routing_history)
        
        # Agent usage frequency
        agent_counts: Dict[str, int] = {}
        confidence_sum = 0.0
        
        for entry in self._routing_history:
            decision = entry["decision"]
            agent_id = decision.get("primary_agent", "")
            if agent_id:
                agent_counts[agent_id] = agent_counts.get(agent_id, 0) + 1
            confidence_sum += decision.get("primary_confidence", 0)
        
        return {
            "total_routes": total,
            "average_confidence": confidence_sum / total if total > 0 else 0,
            "agent_usage": agent_counts,
            "most_routed_agent": max(agent_counts.items(), key=lambda x: x[1])[0] if agent_counts else None
        }
    
    def explain_last_decision(self) -> str:
        """Get a detailed explanation of the last routing decision."""
        if not self._routing_history:
            return "No routing decisions have been made yet."
        
        last = self._routing_history[-1]
        return f"""
Last Routing Decision:
━━━━━━━━━━━━━━━━━━━━
Query: {last['query']}
Timestamp: {last['timestamp']}

{last['decision'].get('reasoning', 'No reasoning available')}
"""
