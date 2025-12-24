"""Stateful execution engine for dynamic GRD traversal.

This module implements the execution logic for GRDs, supporting:
- Dynamic state management
- Conditional branching based on edge labels
- Cycle support for critic feedback loops
- Runtime condition evaluation
"""

import re
from typing import Dict, List, Optional, Any, Callable, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

from braid.parser import GRDStructure, GRDNode, GRDEdge


class ExecutionStatus(Enum):
    """Status of execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class NodeExecutionResult:
    """Result of executing a single node."""

    node_id: str
    status: ExecutionStatus
    output: str
    execution_time_ms: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionState:
    """Maintains the state of GRD execution."""

    current_node: Optional[str] = None
    completed_nodes: Set[str] = field(default_factory=set)
    skipped_nodes: Set[str] = field(default_factory=set)
    step_results: Dict[str, str] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    iteration_count: Dict[str, int] = field(default_factory=dict)
    execution_path: List[str] = field(default_factory=list)

    def mark_completed(self, node_id: str, result: str) -> None:
        """Mark a node as completed with its result."""
        self.completed_nodes.add(node_id)
        self.step_results[node_id] = result
        self.execution_path.append(node_id)
        self.iteration_count[node_id] = self.iteration_count.get(node_id, 0) + 1

    def get_iteration_count(self, node_id: str) -> int:
        """Get how many times a node has been executed."""
        return self.iteration_count.get(node_id, 0)

    def reset_for_retry(self, from_node: str) -> None:
        """Reset state for retrying from a specific node."""
        # Remove nodes executed after from_node from completed set
        # Keep results for potential reference
        if from_node in self.execution_path:
            idx = self.execution_path.index(from_node)
            nodes_to_reset = self.execution_path[idx:]
            for node in nodes_to_reset:
                self.completed_nodes.discard(node)
            self.execution_path = self.execution_path[:idx]


@dataclass
class ExecutionResult:
    """Complete result of GRD execution."""

    success: bool
    final_answer: str
    state: ExecutionState
    node_results: List[NodeExecutionResult]
    total_iterations: int
    error: Optional[str] = None

    def get_execution_trace(self) -> List[Dict[str, Any]]:
        """Get a detailed execution trace."""
        return [
            {
                "step": i + 1,
                "node_id": result.node_id,
                "status": result.status.value,
                "output": result.output,
                "error": result.error,
            }
            for i, result in enumerate(self.node_results)
        ]


class ConditionEvaluator:
    """
    Evaluates conditions on edge labels for branching decisions.

    Supports conditions like:
    - "success" / "failure" / "error"
    - "yes" / "no"
    - "value > 100" / "value < 50"
    - "contains X" / "not contains X"
    """

    # Pattern for comparison conditions
    COMPARISON_PATTERN = re.compile(r"(?:value|result)?\s*([<>=!]+)\s*(\d+\.?\d*)", re.IGNORECASE)

    # Keywords for boolean conditions
    SUCCESS_KEYWORDS = {"success", "yes", "true", "valid", "correct", "pass", "ok"}
    FAILURE_KEYWORDS = {"failure", "no", "false", "invalid", "incorrect", "fail", "error"}

    def evaluate(self, condition: str, context: Dict[str, Any], last_result: str) -> bool:
        """
        Evaluate a condition against the current context.

        Args:
            condition: Condition string from edge label
            context: Current execution context
            last_result: Result from the previous node

        Returns:
            True if condition is satisfied, False otherwise
        """
        condition_lower = condition.lower().strip()

        # Check for success keywords
        if condition_lower in self.SUCCESS_KEYWORDS:
            return self._is_success_result(last_result)

        # Check for failure keywords
        if condition_lower in self.FAILURE_KEYWORDS:
            return not self._is_success_result(last_result)

        # Check for comparison conditions
        match = self.COMPARISON_PATTERN.search(condition)
        if match:
            operator = match.group(1)
            threshold = float(match.group(2))
            return self._evaluate_comparison(last_result, operator, threshold)

        # Check for contains conditions
        if "contains" in condition_lower:
            search_term = condition_lower.replace("contains", "").strip()
            negate = "not" in condition_lower
            result = search_term.lower() in last_result.lower()
            return not result if negate else result

        # Default: assume condition matches if it's mentioned in result
        return condition_lower in last_result.lower()

    def _is_success_result(self, result: str) -> bool:
        """Check if a result indicates success."""
        result_lower = result.lower()

        # Check for explicit failure indicators
        failure_indicators = ["error", "failed", "invalid", "incorrect", "exception"]
        for indicator in failure_indicators:
            if indicator in result_lower:
                return False

        return True

    def _evaluate_comparison(self, result: str, operator: str, threshold: float) -> bool:
        """Evaluate a numeric comparison."""
        # Extract numeric value from result
        numbers = re.findall(r"-?\d+\.?\d*", result)
        if not numbers:
            return False

        try:
            value = float(numbers[-1])  # Use last number found
        except ValueError:
            return False

        # Evaluate comparison
        if operator == ">":
            return value > threshold
        elif operator == ">=":
            return value >= threshold
        elif operator == "<":
            return value < threshold
        elif operator == "<=":
            return value <= threshold
        elif operator in ("==", "="):
            return value == threshold
        elif operator in ("!=", "<>"):
            return value != threshold

        return False


class StatefulExecutionEngine:
    """
    Stateful execution engine for GRDs.

    Unlike simple topological sorting, this engine:
    - Maintains execution state across steps
    - Supports conditional branching
    - Handles cycles for critic/verification loops
    - Provides runtime condition evaluation
    """

    DEFAULT_MAX_ITERATIONS = 3  # Per node, to prevent infinite loops
    DEFAULT_MAX_TOTAL_STEPS = 50

    def __init__(
        self,
        grd: GRDStructure,
        max_iterations_per_node: int = DEFAULT_MAX_ITERATIONS,
        max_total_steps: int = DEFAULT_MAX_TOTAL_STEPS,
    ):
        """
        Initialize the execution engine.

        Args:
            grd: The GRD structure to execute
            max_iterations_per_node: Max times a single node can be executed
            max_total_steps: Maximum total execution steps
        """
        self.grd = grd
        self.max_iterations_per_node = max_iterations_per_node
        self.max_total_steps = max_total_steps
        self.condition_evaluator = ConditionEvaluator()
        self.state = ExecutionState()

    def reset(self) -> None:
        """Reset the execution state."""
        self.state = ExecutionState()

    def execute(
        self,
        problem: str,
        executor: Callable[[GRDNode, Dict[str, Any]], str],
        initial_context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """
        Execute the GRD step by step.

        Args:
            problem: The problem being solved
            executor: Function that executes a single node
            initial_context: Optional initial context

        Returns:
            ExecutionResult with complete execution details
        """
        self.reset()

        # Initialize context
        self.state.context = initial_context or {}
        self.state.context["problem"] = problem

        node_results: List[NodeExecutionResult] = []
        total_iterations = 0

        # Find start node(s)
        current_nodes = list(self.grd.start_nodes)
        if not current_nodes:
            # Fallback: find nodes with no incoming edges
            current_nodes = self._find_start_nodes()

        if not current_nodes:
            return ExecutionResult(
                success=False,
                final_answer="",
                state=self.state,
                node_results=[],
                total_iterations=0,
                error="No start nodes found in GRD",
            )

        # Execute starting from first start node
        self.state.current_node = current_nodes[0]

        while self.state.current_node and total_iterations < self.max_total_steps:
            current_id = self.state.current_node
            node = self.grd.get_node_by_id(current_id)

            if not node:
                break

            # Check iteration limit
            if self.state.get_iteration_count(current_id) >= self.max_iterations_per_node:
                node_results.append(
                    NodeExecutionResult(
                        node_id=current_id,
                        status=ExecutionStatus.SKIPPED,
                        output="",
                        error=f"Max iterations ({self.max_iterations_per_node}) reached",
                    )
                )
                break

            # Execute the node
            total_iterations += 1

            try:
                # Build execution context
                exec_context = self._build_execution_context(node)
                output = executor(node, exec_context)

                self.state.mark_completed(current_id, output)

                node_results.append(
                    NodeExecutionResult(
                        node_id=current_id,
                        status=ExecutionStatus.COMPLETED,
                        output=output,
                    )
                )

                # Determine next node
                self.state.current_node = self._get_next_node(current_id, output)

            except Exception as e:
                node_results.append(
                    NodeExecutionResult(
                        node_id=current_id,
                        status=ExecutionStatus.FAILED,
                        output="",
                        error=str(e),
                    )
                )

                # Try to continue on error
                self.state.current_node = self._get_next_node_on_error(current_id)

        # Determine final answer
        final_answer = self._extract_final_answer()

        return ExecutionResult(
            success=len(node_results) > 0 and node_results[-1].status == ExecutionStatus.COMPLETED,
            final_answer=final_answer,
            state=self.state,
            node_results=node_results,
            total_iterations=total_iterations,
        )

    def _find_start_nodes(self) -> List[str]:
        """Find nodes with no incoming edges."""
        has_incoming = {edge.to_node for edge in self.grd.edges}
        return [node.id for node in self.grd.nodes if node.id not in has_incoming]

    def _build_execution_context(self, node: GRDNode) -> Dict[str, Any]:
        """Build context for node execution."""
        context = dict(self.state.context)
        context["current_node"] = node.id
        context["current_label"] = node.label
        context["previous_results"] = dict(self.state.step_results)
        context["execution_path"] = list(self.state.execution_path)

        # Build formatted previous steps
        previous_steps = []
        for prev_id in self.state.execution_path:
            prev_node = self.grd.get_node_by_id(prev_id)
            if prev_node and prev_id in self.state.step_results:
                previous_steps.append(f"{prev_node.label}: {self.state.step_results[prev_id]}")
        context["previous_steps_formatted"] = "\n".join(previous_steps)

        return context

    def _get_next_node(self, current_id: str, output: str) -> Optional[str]:
        """
        Determine the next node based on output and edge conditions.

        Args:
            current_id: Current node ID
            output: Output from current node execution

        Returns:
            ID of next node, or None if execution should end
        """
        outgoing_edges = self.grd.get_outgoing_edges(current_id)

        if not outgoing_edges:
            return None  # End of execution

        # If only one edge, follow it
        if len(outgoing_edges) == 1:
            return outgoing_edges[0].to_node

        # Multiple edges - evaluate conditions
        for edge in outgoing_edges:
            if edge.label:
                # Check if this edge's condition is satisfied
                if self.condition_evaluator.evaluate(edge.label, self.state.context, output):
                    return edge.to_node
            elif edge.condition:
                # Use explicit condition field
                if self.condition_evaluator.evaluate(edge.condition, self.state.context, output):
                    return edge.to_node

        # Default: follow first edge without condition
        for edge in outgoing_edges:
            if not edge.label and not edge.condition:
                return edge.to_node

        # Fallback: first edge
        return outgoing_edges[0].to_node

    def _get_next_node_on_error(self, current_id: str) -> Optional[str]:
        """Get next node when current node execution failed."""
        outgoing_edges = self.grd.get_outgoing_edges(current_id)

        # Look for error/failure edges
        for edge in outgoing_edges:
            if edge.label and edge.label.lower() in ("error", "failure", "fail"):
                return edge.to_node

        # Continue with default path if no error edge
        if outgoing_edges:
            return outgoing_edges[0].to_node

        return None

    def _extract_final_answer(self) -> str:
        """Extract the final answer from execution results."""
        # Try end nodes first
        for end_node_id in self.grd.end_nodes:
            if end_node_id in self.state.step_results:
                return self.state.step_results[end_node_id]

        # Use last executed node's result
        if self.state.execution_path:
            last_node = self.state.execution_path[-1]
            if last_node in self.state.step_results:
                return self.state.step_results[last_node]

        return ""

    def can_reach(self, from_node: str, to_node: str) -> bool:
        """Check if to_node is reachable from from_node."""
        visited: Set[str] = set()
        queue = [from_node]

        while queue:
            current = queue.pop(0)
            if current == to_node:
                return True
            if current in visited:
                continue
            visited.add(current)

            for edge in self.grd.get_outgoing_edges(current):
                if edge.to_node not in visited:
                    queue.append(edge.to_node)

        return False

    def has_cycles(self) -> bool:
        """Check if the GRD contains cycles."""
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            for edge in self.grd.get_outgoing_edges(node_id):
                if edge.to_node not in visited:
                    if dfs(edge.to_node):
                        return True
                elif edge.to_node in rec_stack:
                    return True

            rec_stack.discard(node_id)
            return False

        for node in self.grd.nodes:
            if node.id not in visited:
                if dfs(node.id):
                    return True

        return False

    def detect_cycles(self) -> List[List[str]]:
        """Detect all cycles in the GRD."""
        cycles: List[List[str]] = []

        def find_cycles_from(start: str, path: List[str], visited: Set[str]) -> None:
            if start in path:
                # Found a cycle
                cycle_start = path.index(start)
                cycles.append(path[cycle_start:] + [start])
                return

            if start in visited:
                return

            visited.add(start)
            path = path + [start]

            for edge in self.grd.get_outgoing_edges(start):
                find_cycles_from(edge.to_node, path, visited.copy())

        for node in self.grd.nodes:
            find_cycles_from(node.id, [], set())

        return cycles
