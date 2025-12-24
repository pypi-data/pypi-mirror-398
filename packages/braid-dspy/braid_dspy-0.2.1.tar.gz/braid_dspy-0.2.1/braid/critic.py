"""Critic module for self-verification and feedback loops in BRAID.

This module implements the Terminal Verification Loops pattern from the
BRAID paper, allowing the model to verify its own answers and retry
if verification fails.
"""

import re
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum

from braid.parser import GRDStructure, GRDNode, GRDEdge


class CriticType(Enum):
    """Types of critic nodes."""

    VERIFICATION = "verification"  # Check/Verify nodes
    VALIDATION = "validation"  # Validate nodes
    REVIEW = "review"  # Review nodes
    CONFIRMATION = "confirmation"  # Confirm nodes


@dataclass
class CriticNode:
    """Represents a critic node in the GRD."""

    node_id: str
    critic_type: CriticType
    target_nodes: List[str]  # Nodes this critic verifies
    fallback_node: Optional[str] = None  # Node to return to on failure


@dataclass
class CriticResult:
    """Result of critic evaluation."""

    passed: bool
    feedback: str
    confidence: float = 1.0
    suggested_action: Optional[str] = None
    retry_node: Optional[str] = None


@dataclass
class FeedbackLoopResult:
    """Result of a complete feedback loop."""

    final_passed: bool
    attempts: int
    critic_results: List[CriticResult]
    final_output: str


class CriticDetector:
    """
    Detects and classifies critic nodes in GRDs.

    Critic nodes are special nodes that verify previous computations
    and can trigger retries if verification fails.
    """

    # Patterns for detecting critic node types
    CRITIC_PATTERNS = {
        CriticType.VERIFICATION: [
            re.compile(r"^Check[:\s]", re.IGNORECASE),
            re.compile(r"^Verify[:\s]", re.IGNORECASE),
            re.compile(r"^Double[- ]?check", re.IGNORECASE),
        ],
        CriticType.VALIDATION: [
            re.compile(r"^Validate[:\s]", re.IGNORECASE),
            re.compile(r"^Ensure[:\s]", re.IGNORECASE),
            re.compile(r"^Assert[:\s]", re.IGNORECASE),
        ],
        CriticType.REVIEW: [
            re.compile(r"^Review[:\s]", re.IGNORECASE),
            re.compile(r"^Examine[:\s]", re.IGNORECASE),
            re.compile(r"^Inspect[:\s]", re.IGNORECASE),
        ],
        CriticType.CONFIRMATION: [
            re.compile(r"^Confirm[:\s]", re.IGNORECASE),
            re.compile(r"^Make sure[:\s]", re.IGNORECASE),
            re.compile(r"^Is this correct", re.IGNORECASE),
        ],
    }

    # Patterns indicating failure/retry edges
    FAILURE_EDGE_PATTERNS = [
        re.compile(r"fail", re.IGNORECASE),
        re.compile(r"error", re.IGNORECASE),
        re.compile(r"retry", re.IGNORECASE),
        re.compile(r"incorrect", re.IGNORECASE),
        re.compile(r"wrong", re.IGNORECASE),
        re.compile(r"no\s*$", re.IGNORECASE),
    ]

    def is_critic_node(self, node: GRDNode) -> bool:
        """Check if a node is a critic node."""
        for patterns in self.CRITIC_PATTERNS.values():
            for pattern in patterns:
                if pattern.search(node.label):
                    return True
        return False

    def get_critic_type(self, node: GRDNode) -> Optional[CriticType]:
        """Get the type of critic node."""
        for critic_type, patterns in self.CRITIC_PATTERNS.items():
            for pattern in patterns:
                if pattern.search(node.label):
                    return critic_type
        return None

    def detect_critics(self, grd: GRDStructure) -> List[CriticNode]:
        """
        Detect all critic nodes in a GRD.

        Args:
            grd: GRDStructure to analyze

        Returns:
            List of detected CriticNodes with their metadata
        """
        critics: List[CriticNode] = []

        for node in grd.nodes:
            critic_type = self.get_critic_type(node)
            if critic_type:
                # Find target nodes (nodes that lead to this critic)
                target_nodes = [edge.from_node for edge in grd.get_incoming_edges(node.id)]

                # Find fallback node (for retry on failure)
                fallback_node = self._find_fallback_node(grd, node.id)

                critics.append(
                    CriticNode(
                        node_id=node.id,
                        critic_type=critic_type,
                        target_nodes=target_nodes,
                        fallback_node=fallback_node,
                    )
                )

        return critics

    def _find_fallback_node(self, grd: GRDStructure, critic_node_id: str) -> Optional[str]:
        """Find the node to return to on critic failure."""
        outgoing_edges = grd.get_outgoing_edges(critic_node_id)

        for edge in outgoing_edges:
            # Check for failure/retry edge
            if edge.label:
                for pattern in self.FAILURE_EDGE_PATTERNS:
                    if pattern.search(edge.label):
                        return edge.to_node

        # If no explicit failure edge, check incoming nodes
        incoming_edges = grd.get_incoming_edges(critic_node_id)
        if incoming_edges:
            # Return to the first incoming node (most recent step)
            return incoming_edges[0].from_node

        return None

    def get_feedback_loops(self, grd: GRDStructure) -> List[Tuple[CriticNode, List[str]]]:
        """
        Identify feedback loops in the GRD.

        A feedback loop is a path from a critic node back to a previous node.

        Returns:
            List of (critic_node, loop_path) tuples
        """
        critics = self.detect_critics(grd)
        loops: List[Tuple[CriticNode, List[str]]] = []

        for critic in critics:
            if critic.fallback_node:
                # Find path from critic to fallback
                loop_path = self._find_path(grd, critic.node_id, critic.fallback_node)
                if loop_path:
                    loops.append((critic, loop_path))

        return loops

    def _find_path(self, grd: GRDStructure, from_node: str, to_node: str) -> Optional[List[str]]:
        """Find a path between two nodes (BFS)."""
        from collections import deque

        queue = deque([(from_node, [from_node])])
        visited = {from_node}

        while queue:
            current, path = queue.popleft()

            for edge in grd.get_outgoing_edges(current):
                if edge.to_node == to_node:
                    return path + [to_node]

                if edge.to_node not in visited:
                    visited.add(edge.to_node)
                    queue.append((edge.to_node, path + [edge.to_node]))

        return None


class CriticEvaluator:
    """
    Evaluates critic node outputs to determine pass/fail.

    Interprets the output of critic nodes and decides whether
    verification passed and what action to take.
    """

    # Patterns indicating success
    SUCCESS_PATTERNS = [
        re.compile(
            r"\b(?:correct|right|valid|verified|confirmed|passed|yes|true)\b", re.IGNORECASE
        ),
        re.compile(r"\b(?:looks good|seems correct|is accurate)\b", re.IGNORECASE),
        re.compile(r"✓|✅|👍", re.IGNORECASE),
    ]

    # Patterns indicating failure
    FAILURE_PATTERNS = [
        re.compile(r"\b(?:incorrect|wrong|invalid|failed|no|false|error)\b", re.IGNORECASE),
        re.compile(r"\b(?:doesn't match|doesn't look right|is not accurate)\b", re.IGNORECASE),
        re.compile(r"\b(?:try again|redo|recalculate)\b", re.IGNORECASE),
        re.compile(r"✗|❌|👎", re.IGNORECASE),
    ]

    def evaluate(self, critic_output: str, context: Dict[str, Any]) -> CriticResult:
        """
        Evaluate the output from a critic node.

        Args:
            critic_output: The text output from executing the critic node
            context: Current execution context

        Returns:
            CriticResult indicating pass/fail and next action
        """
        output_lower = critic_output.lower()

        # Count success and failure indicators
        success_count = sum(
            len(pattern.findall(critic_output)) for pattern in self.SUCCESS_PATTERNS
        )
        failure_count = sum(
            len(pattern.findall(critic_output)) for pattern in self.FAILURE_PATTERNS
        )

        # Determine if passed
        if failure_count > 0 and failure_count >= success_count:
            passed = False
            # Try to extract suggested action
            action = self._extract_action(critic_output)
        else:
            passed = True
            action = None

        # Calculate confidence based on clarity of indicators
        total_indicators = success_count + failure_count
        if total_indicators > 0:
            confidence = max(success_count, failure_count) / total_indicators
        else:
            # No clear indicators - moderate confidence
            confidence = 0.5

        return CriticResult(
            passed=passed,
            feedback=critic_output,
            confidence=confidence,
            suggested_action=action,
        )

    def _extract_action(self, output: str) -> Optional[str]:
        """Extract suggested corrective action from critic output."""
        # Look for action patterns
        action_patterns = [
            re.compile(r"(?:should|need to|must)\s+(.+?)(?:\.|$)", re.IGNORECASE),
            re.compile(r"(?:try|redo|recalculate)\s+(.+?)(?:\.|$)", re.IGNORECASE),
            re.compile(r"(?:fix|correct)\s+(.+?)(?:\.|$)", re.IGNORECASE),
        ]

        for pattern in action_patterns:
            match = pattern.search(output)
            if match:
                return match.group(1).strip()

        return None


class CriticExecutor:
    """
    Executes GRDs with critic feedback loops.

    This executor handles the complete cycle of:
    1. Executing normal nodes
    2. Executing critic nodes
    3. Processing critic feedback
    4. Retrying on failure (up to max retries)
    """

    DEFAULT_MAX_RETRIES = 2

    def __init__(
        self,
        grd: GRDStructure,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        """
        Initialize the CriticExecutor.

        Args:
            grd: The GRD structure to execute
            max_retries: Maximum number of retries per critic failure
        """
        self.grd = grd
        self.max_retries = max_retries
        self.detector = CriticDetector()
        self.evaluator = CriticEvaluator()
        self.critics = self.detector.detect_critics(grd)

    def is_critic_node(self, node_id: str) -> bool:
        """Check if a node ID is a critic node."""
        return any(c.node_id == node_id for c in self.critics)

    def get_critic(self, node_id: str) -> Optional[CriticNode]:
        """Get critic node by ID."""
        for critic in self.critics:
            if critic.node_id == node_id:
                return critic
        return None

    def process_critic_output(
        self,
        critic: CriticNode,
        output: str,
        context: Dict[str, Any],
        retry_count: int,
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Process the output from a critic node.

        Args:
            critic: The critic node that was executed
            output: Output from critic execution
            context: Current execution context
            retry_count: Number of retries already attempted

        Returns:
            Tuple of (should_continue, next_node_id, updated_context)
        """
        result = self.evaluator.evaluate(output, context)

        if result.passed:
            # Critic passed - continue normally
            outgoing = self.grd.get_outgoing_edges(critic.node_id)

            # Find success edge
            for edge in outgoing:
                if not edge.label or edge.label.lower() in ("yes", "success", "pass", "continue"):
                    return (True, edge.to_node, context)

            # Default to first edge if no labeled edge
            if outgoing:
                return (True, outgoing[0].to_node, context)

            return (True, None, context)

        else:
            # Critic failed
            if retry_count >= self.max_retries:
                # Max retries reached - continue anyway or fail
                context["critic_exceeded_retries"] = True
                return (True, None, context)

            if critic.fallback_node:
                # Update context with feedback
                context["critic_feedback"] = result.feedback
                if result.suggested_action:
                    context["suggested_correction"] = result.suggested_action
                context["retry_count"] = retry_count + 1

                return (True, critic.fallback_node, context)

            # No fallback - continue anyway
            return (True, None, context)

    def execute_with_feedback(
        self,
        problem: str,
        executor: Callable[[GRDNode, Dict[str, Any]], str],
        initial_context: Optional[Dict[str, Any]] = None,
    ) -> FeedbackLoopResult:
        """
        Execute the GRD with critic feedback loops.

        Args:
            problem: The problem being solved
            executor: Function to execute a single node
            initial_context: Optional initial context

        Returns:
            FeedbackLoopResult with complete execution details
        """
        context = initial_context or {}
        context["problem"] = problem

        critic_results: List[CriticResult] = []
        attempts = 0
        max_total_steps = 100  # Safety limit

        # Simple execution tracking
        completed: set = set()
        results: Dict[str, str] = {}
        current_node = self.grd.start_nodes[0] if self.grd.start_nodes else None

        while current_node and attempts < max_total_steps:
            attempts += 1
            node = self.grd.get_node_by_id(current_node)

            if not node:
                break

            # Execute the node
            exec_context = dict(context)
            exec_context["previous_results"] = results
            exec_context["completed_nodes"] = list(completed)

            try:
                output = executor(node, exec_context)
                results[current_node] = output
                completed.add(current_node)

                # Check if this is a critic node
                if self.is_critic_node(current_node):
                    critic = self.get_critic(current_node)
                    crit_result = self.evaluator.evaluate(output, context)
                    critic_results.append(crit_result)

                    if critic:
                        retry_count = context.get("retry_count", 0)
                        should_continue, next_node, context = self.process_critic_output(
                            critic, output, context, retry_count
                        )

                        if should_continue:
                            current_node = next_node
                        else:
                            break
                    else:
                        current_node = self._get_next_node(current_node)
                else:
                    # Normal node - get next
                    current_node = self._get_next_node(current_node)

            except Exception as e:
                results[current_node] = f"Error: {str(e)}"
                current_node = self._get_next_node(current_node)

        # Determine final output
        final_output = ""
        for end_node in self.grd.end_nodes:
            if end_node in results:
                final_output = results[end_node]
                break

        if not final_output and results:
            # Use last result
            final_output = list(results.values())[-1]

        # Determine if all critics passed
        final_passed = all(r.passed for r in critic_results) if critic_results else True

        return FeedbackLoopResult(
            final_passed=final_passed,
            attempts=attempts,
            critic_results=critic_results,
            final_output=final_output,
        )

    def _get_next_node(self, current: str) -> Optional[str]:
        """Get the next node in sequence."""
        outgoing = self.grd.get_outgoing_edges(current)
        return outgoing[0].to_node if outgoing else None
