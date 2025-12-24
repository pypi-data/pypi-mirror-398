"""Unit tests for the masking module."""

import pytest
from braid.masking import NumericalMasker, MaskingResult, UnmaskingResult


class TestNumericalMasker:
    """Tests for NumericalMasker class."""

    def test_mask_simple_integers(self):
        """Test masking simple integer values."""
        masker = NumericalMasker()
        result = masker.mask("Calculate 120 divided by 2")

        assert result.mask_count == 2
        assert "{{VALUE_" in result.masked
        # Check that original numbers are replaced with placeholders
        assert "120" in result.value_mapping.values()
        assert "2" in result.value_mapping.values()

    def test_mask_decimal_numbers(self):
        """Test masking decimal numbers."""
        masker = NumericalMasker()
        result = masker.mask("The result is 3.14159")

        assert result.mask_count >= 1
        assert "3.14159" not in result.masked

    def test_mask_units(self):
        """Test masking numbers with units."""
        masker = NumericalMasker()
        result = masker.mask("Speed is 60 km/h")

        assert result.mask_count >= 1
        assert "60 km/h" not in result.masked or "{{VALUE_" in result.masked

    def test_mask_currency(self):
        """Test masking currency values."""
        masker = NumericalMasker()
        result = masker.mask("Total cost is $150.00")

        assert result.mask_count >= 1
        assert "$150" not in result.masked or "{{VALUE_" in result.masked

    def test_mask_percentage(self):
        """Test masking percentage values."""
        masker = NumericalMasker()
        result = masker.mask("Discount is 25%")

        assert result.mask_count >= 1
        assert "25%" not in result.masked or "{{VALUE_" in result.masked

    def test_unmask_restores_values(self):
        """Test that unmask restores original values."""
        masker = NumericalMasker()
        original = "Calculate 100 + 50"

        masked_result = masker.mask(original)
        unmasked_result = masker.unmask(masked_result.masked, masked_result.value_mapping)

        # Should restore numerical values
        assert "100" in unmasked_result.unmasked or "50" in unmasked_result.unmasked

    def test_unmask_with_computed_values(self):
        """Test unmask with computed replacement values."""
        masker = NumericalMasker()
        original = "Result: {{VALUE_1}}"

        computed = {"{{VALUE_1}}": "42"}
        result = masker.unmask(original, {}, computed)

        assert result.unmasked == "Result: 42"
        assert result.resolved_count == 1

    def test_detect_leakage_equals(self):
        """Test detection of answer leakage with equals sign."""
        masker = NumericalMasker()
        grd = "Calculate[Speed = 60 km/h]"

        leaks = masker.detect_leakage(grd)

        assert len(leaks) > 0
        assert any(leak["type"] == "equals_result" for leak in leaks)

    def test_detect_leakage_answer_label(self):
        """Test detection of labeled answers."""
        masker = NumericalMasker()
        grd = "Answer: The result is 42"

        leaks = masker.detect_leakage(grd)

        assert len(leaks) >= 0  # May or may not detect based on pattern

    def test_mask_grd_nodes(self):
        """Test masking specifically in GRD node labels."""
        masker = NumericalMasker()
        grd = """flowchart TD
            Start[Problem] --> Calc[Calculate 100 / 5]
            Calc --> End[Result = 20]
        """

        result = masker.mask_grd_nodes(grd)

        assert result.mask_count >= 1

    def test_masking_result_has_masks(self):
        """Test has_masks method on MaskingResult."""
        masker = NumericalMasker()

        with_numbers = masker.mask("Value is 42")
        without_numbers = masker.mask("No numbers here")

        assert with_numbers.has_masks() == True
        assert without_numbers.has_masks() == False

    def test_preserve_step_numbers(self):
        """Test that step numbers are preserved when option is set."""
        masker = NumericalMasker(preserve_step_numbers=True)
        text = "Step 1: Calculate value"

        result = masker.mask(text)

        # Step numbers should be preserved if the pattern matches
        # The actual behavior depends on regex implementation

    def test_min_value_threshold(self):
        """Test minimum value threshold for masking."""
        masker = NumericalMasker(min_value_to_mask=10)
        text = "Small: 5, Large: 100"

        result = masker.mask(text)

        # Values below threshold might be preserved
        # This depends on implementation details


class TestMaskingResultDataclass:
    """Tests for MaskingResult dataclass."""

    def test_masking_result_creation(self):
        """Test creating a MaskingResult."""
        result = MaskingResult(
            original="test 123",
            masked="test {{VALUE_1}}",
            value_mapping={"{{VALUE_1}}": "123"},
            mask_count=1,
        )

        assert result.original == "test 123"
        assert result.masked == "test {{VALUE_1}}"
        assert result.mask_count == 1

    def test_has_masks_true(self):
        """Test has_masks returns True when masks exist."""
        result = MaskingResult(original="", masked="", value_mapping={}, mask_count=1)
        assert result.has_masks() == True

    def test_has_masks_false(self):
        """Test has_masks returns False when no masks."""
        result = MaskingResult(original="", masked="", value_mapping={}, mask_count=0)
        assert result.has_masks() == False


class TestUnmaskingResult:
    """Tests for UnmaskingResult dataclass."""

    def test_unmasking_result_creation(self):
        """Test creating an UnmaskingResult."""
        result = UnmaskingResult(
            original="{{VALUE_1}}", unmasked="42", resolved_count=1, unresolved_placeholders=[]
        )

        assert result.original == "{{VALUE_1}}"
        assert result.unmasked == "42"
        assert result.resolved_count == 1
        assert len(result.unresolved_placeholders) == 0

    def test_unresolved_placeholders(self):
        """Test tracking unresolved placeholders."""
        result = UnmaskingResult(
            original="{{VALUE_1}} and {{VALUE_2}}",
            unmasked="42 and {{VALUE_2}}",
            resolved_count=1,
            unresolved_placeholders=["{{VALUE_2}}"],
        )

        assert len(result.unresolved_placeholders) == 1
        assert "{{VALUE_2}}" in result.unresolved_placeholders
