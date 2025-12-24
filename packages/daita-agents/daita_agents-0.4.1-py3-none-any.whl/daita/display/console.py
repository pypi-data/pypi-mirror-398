"""
Console Decision Display for Daita Framework

Provides simple, clean console display of agent decision-making during development.
Always uses minimal styling to encourage users to upgrade to dashboard for detailed 
reasoning insights and comprehensive observability.
"""

import sys
from typing import Optional

from ..core.decision_tracing import DecisionEvent, DecisionEventType


class ConsoleDecisionDisplay:
    """
    Console decision display for local development.
    
    Shows just enough information to understand what the agent is doing,
    encouraging users to use the dashboard for detailed reasoning analysis.
    """
    
    def __init__(self, agent_name: str, agent_id: str):
        self.agent_name = agent_name
        self.agent_id = agent_id
        self.decision_count = 0
        self.is_active = False
        self.current_decisions = {}  # Track ongoing decisions
        
    def start(self):
        """Start the console decision display."""
        self.is_active = True
        print(f"🤔 Agent: {self.agent_name}")
    
    def stop(self):
        """Stop the decision display."""
        if self.is_active and self.decision_count > 0:
            print(f"✨ Complete: {self.decision_count} decisions made")
        self.is_active = False
    
    def handle_event(self, event: DecisionEvent):
        """Handle decision events with minimal output."""
        if not self.is_active:
            return
        
        span_id = event.span_id or "unknown"
        
        if event.event_type == DecisionEventType.DECISION_STARTED:
            self._handle_decision_started(event, span_id)
            
        elif event.event_type == DecisionEventType.DECISION_COMPLETED:
            self._handle_decision_completed(event, span_id)
        
        # We ignore intermediate events (reasoning, confidence, alternatives)
        # to keep output minimal and drive users to dashboard for details
        
        sys.stdout.flush()
    
    def _handle_decision_started(self, event: DecisionEvent, span_id: str):
        """Handle decision started - track but don't display yet."""
        self.current_decisions[span_id] = {
            "decision_point": event.decision_point,
            "started": True
        }
    
    def _handle_decision_completed(self, event: DecisionEvent, span_id: str):
        """Handle decision completed - show final result."""
        if span_id not in self.current_decisions:
            # Decision started before display was active, show it anyway
            decision_point = event.decision_point
        else:
            decision_point = self.current_decisions[span_id]["decision_point"]
            del self.current_decisions[span_id]
        
        self.decision_count += 1
        
        final_conf = event.data.get('final_confidence', 0)
        success = event.data.get('success', False)
        
        # Determine the decision outcome for display
        outcome = self._determine_outcome(decision_point, final_conf, success)
        
        status_icon = "" if success else ""
        
        # Simple one-line format: Decision → Outcome (confidence)
        print(f" Decision: {decision_point} → {outcome} ({final_conf:.2f})")
    
    def _determine_outcome(self, decision_point: str, confidence: float, success: bool) -> str:
        """
        Determine a simple outcome description for the decision.
        
        This is intentionally basic - detailed reasoning is available in dashboard.
        """
        if not success:
            return "FAILED"
        
        # Try to infer outcome from decision point name and confidence
        if "urgency" in decision_point.lower():
            if confidence >= 0.8:
                return "HIGH urgency"
            elif confidence >= 0.5:
                return "MEDIUM urgency" 
            else:
                return "LOW urgency"
                
        elif "classification" in decision_point.lower() or "classify" in decision_point.lower():
            if confidence >= 0.8:
                return "CLASSIFIED"
            else:
                return "UNCERTAIN"
                
        elif "analysis" in decision_point.lower() or "analyze" in decision_point.lower():
            if confidence >= 0.8:
                return "ANALYZED"
            else:
                return "PARTIAL"
                
        elif "recommendation" in decision_point.lower() or "recommend" in decision_point.lower():
            if confidence >= 0.8:
                return "RECOMMENDED"
            else:
                return "SUGGESTED"
                
        elif "validation" in decision_point.lower() or "validate" in decision_point.lower():
            if confidence >= 0.8:
                return "VALID"
            else:
                return "QUESTIONABLE"
                
        else:
            # Generic outcomes based on confidence
            if confidence >= 0.9:
                return "HIGH confidence"
            elif confidence >= 0.7:
                return "CONFIDENT"
            elif confidence >= 0.5:
                return "MODERATE"
            else:
                return "LOW confidence"


def create_console_decision_display(agent_name: str, agent_id: str) -> ConsoleDecisionDisplay:
    """
    Create a console decision display for local development.
    
    This is the primary display mode for local development and testing.
    For detailed reasoning analysis, users should use the Daita dashboard.
    
    Args:
        agent_name: Name of the agent for display
        agent_id: Agent ID for tracking
    
    Returns:
        ConsoleDecisionDisplay instance
    """
    return ConsoleDecisionDisplay(agent_name, agent_id)

# Legacy alias for backwards compatibility during migration
MinimalDecisionDisplay = ConsoleDecisionDisplay
create_minimal_decision_display = create_console_decision_display