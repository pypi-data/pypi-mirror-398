"""Unit tests for the validators module."""

import pytest
from braid.validators import (
    AtomicityValidator,
    ProceduralScaffoldingValidator,
    StructuralValidator,
    GRDValidator,
    ValidationResult,
    ValidationIssue,
    ValidationSeverity,
)
from braid.parser import GRDNode, GRDEdge, GRDStructure, NodeType


class TestAtomicityValidator:
    """Tests for AtomicityValidator class."""

    def test_count_tokens_simple(self):
        """Test basic token counting."""
        validator = AtomicityValidator()

        assert validator.count_tokens("Hello world") == 2
        assert validator.count_tokens("Calculate the speed") == 3
        assert validator.count_tokens("") == 0

    def test_count_tokens_with_punctuation(self):
        """Test token counting with punctuation."""
        validator = AtomicityValidator()

        # Punctuation counts as separate tokens
        count = validator.count_tokens("Hello, world!")
        assert count >= 2  # At least the words

    def test_validate_node_within_limit(self):
        """Test validating a node within token limit."""
        validator = AtomicityValidator(max_tokens_per_node=15)
        node = GRDNode(id="A", label="Calculate speed", node_type=NodeType.RECTANGLE)

        result = validator.validate_node(node)

        assert result.valid == True
        assert result.score == 1.0
        assert len(result.issues) == 0

    def test_validate_node_exceeds_limit(self):
        """Test validating a node exceeding token limit."""
        validator = AtomicityValidator(max_tokens_per_node=5, strict_mode=True)
        node = GRDNode(
            id="A",
            label="This is a very long node label that exceeds the token limit",
            node_type=NodeType.RECTANGLE,
        )

        result = validator.validate_node(node)

        assert len(result.issues) > 0
        assert result.issues[0].code == "ATOMICITY_VIOLATION"

    def test_validate_grd_all_valid(self):
        """Test validating a GRD where all nodes are valid."""
        validator = AtomicityValidator(max_tokens_per_node=15)
        grd = GRDStructure(
            nodes=[
                GRDNode(id="A", label="Start", node_type=NodeType.RECTANGLE),
                GRDNode(id="B", label="Calculate", node_type=NodeType.RECTANGLE),
                GRDNode(id="C", label="End", node_type=NodeType.RECTANGLE),
            ],
            edges=[
                GRDEdge(from_node="A", to_node="B"),
                GRDEdge(from_node="B", to_node="C"),
            ],
            start_nodes=["A"],
            end_nodes=["C"],
        )

        result = validator.validate_grd(grd)

        assert result.valid == True
        assert result.score == 1.0

    def test_validate_grd_with_violations(self):
        """Test validating a GRD with atomicity violations."""
        validator = AtomicityValidator(max_tokens_per_node=3, strict_mode=False)
        grd = GRDStructure(
            nodes=[
                GRDNode(id="A", label="Start", node_type=NodeType.RECTANGLE),
                GRDNode(
                    id="B", label="This label has way too many tokens", node_type=NodeType.RECTANGLE
                ),
            ],
            edges=[GRDEdge(from_node="A", to_node="B")],
            start_nodes=["A"],
            end_nodes=["B"],
        )

        result = validator.validate_grd(grd)

        assert len(result.issues) > 0
        assert result.score < 1.0


class TestProceduralScaffoldingValidator:
    """Tests for ProceduralScaffoldingValidator class."""

    def test_validate_node_with_leakage(self):
        """Test detecting answer leakage in a node."""
        validator = ProceduralScaffoldingValidator(strict_mode=True)
        node = GRDNode(id="A", label="Result = 42", node_type=NodeType.RECTANGLE)

        result = validator.validate_node(node)

        assert len(result.issues) > 0
        assert any(issue.code == "EQUALS_VALUE" for issue in result.issues)

    def test_validate_node_proper_scaffolding(self):
        """Test validating a properly scaffolded node."""
        validator = ProceduralScaffoldingValidator()
        node = GRDNode(id="A", label="Calculate the sum", node_type=NodeType.RECTANGLE)

        result = validator.validate_node(node)

        # Should have high score for action-oriented label
        assert result.score >= 0.5

    def test_validate_grd_mixed(self):
        """Test validating a GRD with mixed quality nodes."""
        validator = ProceduralScaffoldingValidator(strict_mode=False)
        grd = GRDStructure(
            nodes=[
                GRDNode(id="A", label="Calculate the value", node_type=NodeType.RECTANGLE),
                GRDNode(id="B", label="Answer = 100", node_type=NodeType.RECTANGLE),
            ],
            edges=[GRDEdge(from_node="A", to_node="B")],
            start_nodes=["A"],
            end_nodes=["B"],
        )

        result = validator.validate_grd(grd)

        # Should have some warnings about leakage
        assert len(result.issues) > 0


class TestStructuralValidator:
    """Tests for StructuralValidator class."""

    def test_validate_valid_structure(self):
        """Test validating a valid GRD structure."""
        validator = StructuralValidator()
        grd = GRDStructure(
            nodes=[
                GRDNode(id="A", label="Start", node_type=NodeType.RECTANGLE),
                GRDNode(id="B", label="Middle", node_type=NodeType.RECTANGLE),
                GRDNode(id="C", label="End", node_type=NodeType.RECTANGLE),
            ],
            edges=[
                GRDEdge(from_node="A", to_node="B"),
                GRDEdge(from_node="B", to_node="C"),
            ],
            start_nodes=["A"],
            end_nodes=["C"],
        )

        result = validator.validate(grd)

        assert result.valid == True

    def test_validate_too_few_nodes(self):
        """Test validating a GRD with too few nodes."""
        validator = StructuralValidator(min_nodes=3)
        grd = GRDStructure(
            nodes=[GRDNode(id="A", label="Only", node_type=NodeType.RECTANGLE)],
            edges=[],
            start_nodes=["A"],
            end_nodes=["A"],
        )

        result = validator.validate(grd)

        assert result.valid == False
        assert any(issue.code == "TOO_FEW_NODES" for issue in result.issues)

    def test_validate_orphan_nodes(self):
        """Test detecting orphan nodes."""
        validator = StructuralValidator()
        grd = GRDStructure(
            nodes=[
                GRDNode(id="A", label="Connected", node_type=NodeType.RECTANGLE),
                GRDNode(id="B", label="Connected", node_type=NodeType.RECTANGLE),
                GRDNode(id="C", label="Orphan", node_type=NodeType.RECTANGLE),
            ],
            edges=[GRDEdge(from_node="A", to_node="B")],
            start_nodes=["A"],
            end_nodes=["B"],
        )

        result = validator.validate(grd)

        assert any(issue.code == "ORPHAN_NODES" for issue in result.issues)


class TestGRDValidator:
    """Tests for the combined GRDValidator class."""

    def test_validate_valid_grd(self):
        """Test validating a fully valid GRD."""
        validator = GRDValidator(max_tokens_per_node=15)
        grd = GRDStructure(
            nodes=[
                GRDNode(id="A", label="Start analyzing", node_type=NodeType.RECTANGLE),
                GRDNode(id="B", label="Calculate result", node_type=NodeType.RECTANGLE),
                GRDNode(id="C", label="Verify answer", node_type=NodeType.RECTANGLE),
            ],
            edges=[
                GRDEdge(from_node="A", to_node="B"),
                GRDEdge(from_node="B", to_node="C"),
            ],
            start_nodes=["A"],
            end_nodes=["C"],
        )

        result = validator.validate(grd)

        assert result.valid == True
        assert result.score > 0.5

    def test_validate_and_report(self):
        """Test the report generation."""
        validator = GRDValidator()
        grd = GRDStructure(
            nodes=[
                GRDNode(id="A", label="Start", node_type=NodeType.RECTANGLE),
                GRDNode(id="B", label="End", node_type=NodeType.RECTANGLE),
            ],
            edges=[GRDEdge(from_node="A", to_node="B")],
            start_nodes=["A"],
            end_nodes=["B"],
        )

        report = validator.validate_and_report(grd)

        assert "GRD Validation Report" in report
        assert "Score:" in report


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_has_errors(self):
        """Test has_errors method."""
        result_with_error = ValidationResult(
            valid=False,
            issues=[
                ValidationIssue(
                    severity=ValidationSeverity.ERROR, code="TEST", message="Test error"
                )
            ],
        )
        result_without_error = ValidationResult(valid=True, issues=[])

        assert result_with_error.has_errors() == True
        assert result_without_error.has_errors() == False

    def test_get_errors(self):
        """Test get_errors method."""
        result = ValidationResult(
            valid=False,
            issues=[
                ValidationIssue(severity=ValidationSeverity.ERROR, code="E1", message="Error"),
                ValidationIssue(severity=ValidationSeverity.WARNING, code="W1", message="Warning"),
            ],
        )

        errors = result.get_errors()

        assert len(errors) == 1
        assert errors[0].code == "E1"

    def test_summary(self):
        """Test summary method."""
        result = ValidationResult(valid=True, issues=[], score=0.95)

        summary = result.summary()

        assert "Valid: True" in summary
        assert "0.95" in summary
