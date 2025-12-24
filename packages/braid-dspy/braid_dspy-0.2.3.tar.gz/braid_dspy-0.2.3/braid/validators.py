"""Validators for ensuring GRD quality and BRAID protocol compliance.

This module implements validation rules from the BRAID paper, including:
- Node atomicity (≤15 tokens per node)
- Structural validity
- Procedural scaffolding compliance
"""

import re
from typing import List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

from braid.parser import GRDNode, GRDStructure


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""

    ERROR = "error"  # Must be fixed
    WARNING = "warning"  # Should be fixed
    INFO = "info"  # Suggestion


@dataclass
class ValidationIssue:
    """A single validation issue."""

    severity: ValidationSeverity
    code: str
    message: str
    node_id: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of validation operation."""

    valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    score: float = 1.0  # 0.0 to 1.0

    def has_errors(self) -> bool:
        """Check if there are any error-level issues."""
        return any(issue.severity == ValidationSeverity.ERROR for issue in self.issues)

    def has_warnings(self) -> bool:
        """Check if there are any warning-level issues."""
        return any(issue.severity == ValidationSeverity.WARNING for issue in self.issues)

    def get_errors(self) -> List[ValidationIssue]:
        """Get all error-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]

    def get_warnings(self) -> List[ValidationIssue]:
        """Get all warning-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]

    def summary(self) -> str:
        """Get a summary of the validation result."""
        errors = len(self.get_errors())
        warnings = len(self.get_warnings())
        return (
            f"Valid: {self.valid}, Errors: {errors}, Warnings: {warnings}, Score: {self.score:.2f}"
        )


class AtomicityValidator:
    """
    Validates node atomicity in GRDs.

    According to BRAID research, nano-scale models achieve highest accuracy
    when node labels contain fewer than 15 tokens. This validator checks
    and enforces this constraint.

    Example:
        >>> validator = AtomicityValidator()
        >>> result = validator.validate_node(node)
        >>> if not result.valid:
        ...     print(result.issues[0].suggestion)
    """

    DEFAULT_MAX_TOKENS = 15

    def __init__(
        self,
        max_tokens_per_node: int = DEFAULT_MAX_TOKENS,
        strict_mode: bool = False,
    ):
        """
        Initialize the AtomicityValidator.

        Args:
            max_tokens_per_node: Maximum allowed tokens per node label
            strict_mode: If True, treat violations as errors; otherwise warnings
        """
        self.max_tokens_per_node = max_tokens_per_node
        self.strict_mode = strict_mode

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in a text string.

        Uses a simple whitespace + punctuation tokenization that approximates
        what most LLMs would produce. For more accurate counting, consider
        using the tiktoken library with a specific model's tokenizer.

        Args:
            text: Text to tokenize

        Returns:
            Number of tokens
        """
        if not text:
            return 0

        # Simple tokenization: split on whitespace and punctuation
        # This approximates GPT-style tokenization for English text
        tokens = re.findall(r"\b\w+\b|[^\w\s]", text)
        return len(tokens)

    def validate_node(self, node: GRDNode) -> ValidationResult:
        """
        Validate a single node's atomicity.

        Args:
            node: GRDNode to validate

        Returns:
            ValidationResult with any issues found
        """
        issues: List[ValidationIssue] = []
        token_count = self.count_tokens(node.label)

        if token_count > self.max_tokens_per_node:
            severity = ValidationSeverity.ERROR if self.strict_mode else ValidationSeverity.WARNING

            # Generate suggestion for fixing
            suggestion = self._generate_split_suggestion(node.label, token_count)

            issues.append(
                ValidationIssue(
                    severity=severity,
                    code="ATOMICITY_VIOLATION",
                    message=f"Node '{node.id}' has {token_count} tokens (max: {self.max_tokens_per_node})",
                    node_id=node.id,
                    suggestion=suggestion,
                )
            )

        # Calculate score (1.0 if within limit, decreasing as it exceeds)
        if token_count <= self.max_tokens_per_node:
            score = 1.0
        else:
            # Penalty increases with excess tokens
            excess_ratio = token_count / self.max_tokens_per_node
            score = max(0.0, 1.0 - (excess_ratio - 1.0) * 0.5)

        return ValidationResult(
            valid=len(issues) == 0 or not self.strict_mode,
            issues=issues,
            score=score,
        )

    def validate_grd(self, grd: GRDStructure) -> ValidationResult:
        """
        Validate all nodes in a GRD for atomicity.

        Args:
            grd: GRDStructure to validate

        Returns:
            ValidationResult with all issues found
        """
        all_issues: List[ValidationIssue] = []
        total_score = 0.0

        for node in grd.nodes:
            result = self.validate_node(node)
            all_issues.extend(result.issues)
            total_score += result.score

        # Average score across all nodes
        avg_score = total_score / len(grd.nodes) if grd.nodes else 1.0

        # Valid if no errors (in strict mode) or no issues at all
        has_errors = any(issue.severity == ValidationSeverity.ERROR for issue in all_issues)

        return ValidationResult(
            valid=not has_errors,
            issues=all_issues,
            score=avg_score,
        )

    def _generate_split_suggestion(self, label: str, token_count: int) -> str:
        """Generate a suggestion for splitting a long node."""
        if token_count <= self.max_tokens_per_node * 2:
            return f"Consider splitting into 2 nodes with ~{token_count // 2} tokens each"
        else:
            num_splits = (token_count // self.max_tokens_per_node) + 1
            return f"Consider splitting into {num_splits} sequential nodes"


class ProceduralScaffoldingValidator:
    """
    Validates that GRDs follow procedural scaffolding rules.

    The BRAID protocol requires that GRDs describe HOW to solve a problem,
    not WHAT the answer is. This validator detects answer leakage and
    ensures nodes describe actions rather than computed values.
    """

    # Patterns that indicate answer leakage
    LEAKAGE_PATTERNS = [
        (r"=\s*\d+", "EQUALS_VALUE", "Avoid computed values in node labels"),
        (
            r"(?:answer|result|solution)\s*[:=]?\s*\d+",
            "LABELED_ANSWER",
            "Don't include answers in scaffolding",
        ),
        (
            r"\d+\s*(?:km/h|mph|m/s|kg|lb)",
            "UNIT_VALUE",
            "Use placeholders instead of computed values with units",
        ),
        (
            r"(?:total|sum|difference|product)\s*[:=]?\s*\d+",
            "COMPUTED_AGGREGATE",
            "Describe the computation, not the result",
        ),
    ]

    # Patterns that indicate good procedural scaffolding
    SCAFFOLDING_PATTERNS = [
        r"(?:calculate|compute|find|determine|solve)\s+",
        r"(?:divide|multiply|add|subtract)\s+",
        r"(?:compare|check|verify|validate)\s+",
        r"(?:extract|identify|locate)\s+",
        r"(?:apply|use|utilize)\s+",
    ]

    def __init__(self, strict_mode: bool = False):
        """
        Initialize the ProceduralScaffoldingValidator.

        Args:
            strict_mode: If True, treat leakage as errors
        """
        self.strict_mode = strict_mode

        self._leakage_compiled = [
            (re.compile(pattern, re.IGNORECASE), code, msg)
            for pattern, code, msg in self.LEAKAGE_PATTERNS
        ]

        self._scaffolding_compiled = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.SCAFFOLDING_PATTERNS
        ]

    def validate_node(self, node: GRDNode) -> ValidationResult:
        """
        Validate a single node for procedural scaffolding compliance.

        Args:
            node: GRDNode to validate

        Returns:
            ValidationResult with any issues found
        """
        issues: List[ValidationIssue] = []
        label = node.label

        # Check for leakage patterns
        for pattern, code, message in self._leakage_compiled:
            if pattern.search(label):
                severity = (
                    ValidationSeverity.ERROR if self.strict_mode else ValidationSeverity.WARNING
                )
                issues.append(
                    ValidationIssue(
                        severity=severity,
                        code=code,
                        message=message,
                        node_id=node.id,
                        suggestion="Describe the action to take, not the computed value",
                    )
                )

        # Check for good scaffolding patterns (informational)
        has_scaffolding = any(pattern.search(label) for pattern in self._scaffolding_compiled)

        if not has_scaffolding and not issues:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    code="WEAK_SCAFFOLDING",
                    message="Node could be more action-oriented",
                    node_id=node.id,
                    suggestion="Start with action verbs like 'Calculate', 'Find', 'Determine'",
                )
            )

        # Calculate score
        if issues:
            error_count = sum(1 for i in issues if i.severity == ValidationSeverity.ERROR)
            warning_count = sum(1 for i in issues if i.severity == ValidationSeverity.WARNING)
            score = max(0.0, 1.0 - (error_count * 0.3) - (warning_count * 0.1))
        else:
            score = 1.0

        return ValidationResult(
            valid=not any(i.severity == ValidationSeverity.ERROR for i in issues),
            issues=issues,
            score=score,
        )

    def validate_grd(self, grd: GRDStructure) -> ValidationResult:
        """
        Validate all nodes in a GRD for procedural scaffolding.

        Args:
            grd: GRDStructure to validate

        Returns:
            ValidationResult with all issues found
        """
        all_issues: List[ValidationIssue] = []
        total_score = 0.0

        for node in grd.nodes:
            result = self.validate_node(node)
            # Only include errors and warnings, not info
            all_issues.extend(i for i in result.issues if i.severity != ValidationSeverity.INFO)
            total_score += result.score

        avg_score = total_score / len(grd.nodes) if grd.nodes else 1.0

        return ValidationResult(
            valid=not any(i.severity == ValidationSeverity.ERROR for i in all_issues),
            issues=all_issues,
            score=avg_score,
        )


class StructuralValidator:
    """
    Validates the structural integrity of GRDs.

    Checks for:
    - Connectivity (no orphan nodes)
    - Proper start/end nodes
    - Reasonable topology
    """

    def __init__(
        self,
        min_nodes: int = 2,
        max_nodes: int = 20,
        require_single_start: bool = True,
        require_single_end: bool = False,
    ):
        """
        Initialize the StructuralValidator.

        Args:
            min_nodes: Minimum required nodes
            max_nodes: Maximum allowed nodes
            require_single_start: Require exactly one start node
            require_single_end: Require exactly one end node
        """
        self.min_nodes = min_nodes
        self.max_nodes = max_nodes
        self.require_single_start = require_single_start
        self.require_single_end = require_single_end

    def validate(self, grd: GRDStructure) -> ValidationResult:
        """
        Validate the structural integrity of a GRD.

        Args:
            grd: GRDStructure to validate

        Returns:
            ValidationResult with any issues found
        """
        issues: List[ValidationIssue] = []

        # Check node count
        node_count = len(grd.nodes)
        if node_count < self.min_nodes:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="TOO_FEW_NODES",
                    message=f"GRD has {node_count} nodes (min: {self.min_nodes})",
                    suggestion="Add more reasoning steps",
                )
            )
        elif node_count > self.max_nodes:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code="TOO_MANY_NODES",
                    message=f"GRD has {node_count} nodes (max recommended: {self.max_nodes})",
                    suggestion="Consider simplifying or combining steps",
                )
            )

        # Check start nodes
        if self.require_single_start and len(grd.start_nodes) != 1:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code="INVALID_START_NODES",
                    message=f"GRD has {len(grd.start_nodes)} start nodes (expected: 1)",
                    suggestion="Ensure there is a single entry point",
                )
            )

        # Check end nodes
        if self.require_single_end and len(grd.end_nodes) != 1:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code="INVALID_END_NODES",
                    message=f"GRD has {len(grd.end_nodes)} end nodes (expected: 1)",
                    suggestion="Ensure there is a single conclusion node",
                )
            )

        # Check for orphan nodes (nodes with no connections)
        connected_nodes: Set[str] = set()
        for edge in grd.edges:
            connected_nodes.add(edge.from_node)
            connected_nodes.add(edge.to_node)

        orphans = [n.id for n in grd.nodes if n.id not in connected_nodes]
        if orphans and len(grd.nodes) > 1:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="ORPHAN_NODES",
                    message=f"Disconnected nodes found: {', '.join(orphans)}",
                    suggestion="Connect all nodes in the reasoning flow",
                )
            )

        # Check for edges referencing non-existent nodes
        node_ids = {n.id for n in grd.nodes}
        invalid_edges = [
            (e.from_node, e.to_node)
            for e in grd.edges
            if e.from_node not in node_ids or e.to_node not in node_ids
        ]
        if invalid_edges:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="INVALID_EDGES",
                    message=f"Edges reference non-existent nodes: {invalid_edges}",
                    suggestion="Ensure all edge endpoints are valid nodes",
                )
            )

        # Calculate score
        error_count = sum(1 for i in issues if i.severity == ValidationSeverity.ERROR)
        warning_count = sum(1 for i in issues if i.severity == ValidationSeverity.WARNING)
        score = max(0.0, 1.0 - (error_count * 0.25) - (warning_count * 0.1))

        return ValidationResult(
            valid=error_count == 0,
            issues=issues,
            score=score,
        )


class GRDValidator:
    """
    Comprehensive GRD validator combining all validation rules.

    This is the main entry point for validating GRDs according to
    BRAID protocol requirements.
    """

    def __init__(
        self,
        max_tokens_per_node: int = 15,
        strict_atomicity: bool = False,
        strict_scaffolding: bool = False,
    ):
        """
        Initialize the GRDValidator.

        Args:
            max_tokens_per_node: Maximum tokens allowed per node
            strict_atomicity: Treat atomicity violations as errors
            strict_scaffolding: Treat scaffolding violations as errors
        """
        self.atomicity_validator = AtomicityValidator(
            max_tokens_per_node=max_tokens_per_node,
            strict_mode=strict_atomicity,
        )
        self.scaffolding_validator = ProceduralScaffoldingValidator(
            strict_mode=strict_scaffolding,
        )
        self.structural_validator = StructuralValidator()

    def validate(self, grd: GRDStructure) -> ValidationResult:
        """
        Perform comprehensive validation on a GRD.

        Args:
            grd: GRDStructure to validate

        Returns:
            Combined ValidationResult from all validators
        """
        results = [
            self.atomicity_validator.validate_grd(grd),
            self.scaffolding_validator.validate_grd(grd),
            self.structural_validator.validate(grd),
        ]

        # Combine all issues
        all_issues: List[ValidationIssue] = []
        for result in results:
            all_issues.extend(result.issues)

        # Calculate combined score (weighted average)
        weights = [0.4, 0.4, 0.2]  # atomicity, scaffolding, structural
        combined_score = sum(r.score * w for r, w in zip(results, weights))

        # Valid only if all validations pass
        valid = all(r.valid for r in results)

        return ValidationResult(
            valid=valid,
            issues=all_issues,
            score=combined_score,
        )

    def validate_and_report(self, grd: GRDStructure) -> str:
        """
        Validate a GRD and return a formatted report.

        Args:
            grd: GRDStructure to validate

        Returns:
            Markdown-formatted validation report
        """
        result = self.validate(grd)

        lines = ["# GRD Validation Report\n"]
        lines.append(f"**Status:** {'✅ Valid' if result.valid else '❌ Invalid'}")
        lines.append(f"**Score:** {result.score:.2f}/1.00\n")

        if result.issues:
            lines.append("## Issues\n")

            errors = result.get_errors()
            if errors:
                lines.append("### Errors\n")
                for issue in errors:
                    lines.append(f"- **{issue.code}**: {issue.message}")
                    if issue.node_id:
                        lines.append(f"  - Node: `{issue.node_id}`")
                    if issue.suggestion:
                        lines.append(f"  - Suggestion: {issue.suggestion}")
                lines.append("")

            warnings = result.get_warnings()
            if warnings:
                lines.append("### Warnings\n")
                for issue in warnings:
                    lines.append(f"- **{issue.code}**: {issue.message}")
                    if issue.node_id:
                        lines.append(f"  - Node: `{issue.node_id}`")
                    if issue.suggestion:
                        lines.append(f"  - Suggestion: {issue.suggestion}")
        else:
            lines.append("No issues found! ✨")

        return "\n".join(lines)
