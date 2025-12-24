"""Numerical masking module for preventing answer leakage in GRDs.

This module implements the Numerical Masking Protocol from the BRAID paper,
which prevents the Architect model from leaking computed values into the
GRD structure. All numerical values are replaced with placeholders that
the Solver model must compute at runtime.
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class MaskingResult:
    """Result of masking operation."""

    original: str
    masked: str
    value_mapping: Dict[str, str]
    mask_count: int

    def has_masks(self) -> bool:
        """Check if any values were masked."""
        return self.mask_count > 0


@dataclass
class UnmaskingResult:
    """Result of unmasking operation."""

    original: str
    unmasked: str
    resolved_count: int
    unresolved_placeholders: List[str]


class NumericalMasker:
    """
    Masks numerical values in Mermaid diagrams to prevent answer leakage.

    The BRAID architecture requires that the Architect model creates a
    procedural scaffold without computing actual values. This class detects
    and replaces numerical values with placeholders like {{VALUE_1}}, {{VALUE_2}}, etc.

    Example:
        >>> masker = NumericalMasker()
        >>> result = masker.mask("Calculate[120 ÷ 2 = 60 km/h]")
        >>> print(result.masked)
        Calculate[{{VALUE_1}} ÷ {{VALUE_2}} = {{VALUE_3}} km/h]
    """

    # Placeholder template - must be easily distinguishable
    PLACEHOLDER_PREFIX = "{{VALUE_"
    PLACEHOLDER_SUFFIX = "}}"

    # Numerical patterns to detect (order matters - more specific first)
    NUMERICAL_PATTERNS = [
        # Currency with symbols (must be before plain numbers)
        (r"\$\s*[\d,]+\.?\d*", "currency_usd"),
        (r"€\s*[\d,]+\.?\d*", "currency_eur"),
        (r"£\s*[\d,]+\.?\d*", "currency_gbp"),
        (r"₺\s*[\d,]+\.?\d*", "currency_try"),
        # Percentages
        (r"[\d,]+\.?\d*\s*%", "percentage"),
        # Numbers with units (with space)
        (r"[\d,]+\.?\d*\s*(?:km/h|mph|m/s)", "speed"),
        (r"[\d,]+\.?\d*\s*(?:km|m|cm|mm|mi|ft|in)", "distance"),
        (r"[\d,]+\.?\d*\s*(?:kg|g|mg|lb|oz)", "weight"),
        (r"[\d,]+\.?\d*\s*(?:hours?|hrs?|minutes?|mins?|seconds?|secs?|days?)", "time"),
        (r"[\d,]+\.?\d*\s*(?:liters?|L|ml|gallons?|gal)", "volume"),
        # Scientific notation
        (r"[\d,]+\.?\d*\s*[eE][+-]?\d+", "scientific"),
        # Fractions
        (r"\d+\s*/\s*\d+", "fraction"),
        # Decimal numbers (must be before integers)
        (r"[\d,]+\.\d+", "decimal"),
        # Plain integers (last, most general)
        (r"\b\d{1,}(?:,\d{3})*\b", "integer"),
    ]

    # Patterns to exclude from masking (e.g., step numbers, node IDs)
    EXCLUDE_PATTERNS = [
        r"Step\s*\d+",  # Step 1, Step 2, etc.
        r"Node\s*\d+",  # Node 1, Node 2, etc.
        r"\bA\d+\b",  # Node IDs like A1, A2
        r"\bB\d+\b",
        r"\bC\d+\b",
        r"flowchart\s+\w+",  # flowchart TD, LR, etc.
        r"graph\s+\w+",  # graph TD, LR, etc.
    ]

    def __init__(
        self,
        preserve_step_numbers: bool = True,
        min_value_to_mask: Optional[float] = None,
        custom_patterns: Optional[List[Tuple[str, str]]] = None,
    ):
        """
        Initialize the NumericalMasker.

        Args:
            preserve_step_numbers: If True, don't mask step/node numbers
            min_value_to_mask: Minimum value to mask (smaller values preserved)
            custom_patterns: Additional patterns to detect (pattern, category)
        """
        self.preserve_step_numbers = preserve_step_numbers
        self.min_value_to_mask = min_value_to_mask
        self._counter = 0

        # Compile patterns for efficiency
        self._compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), category)
            for pattern, category in self.NUMERICAL_PATTERNS
        ]

        if custom_patterns:
            for pattern, category in custom_patterns:
                self._compiled_patterns.append((re.compile(pattern, re.IGNORECASE), category))

        self._exclude_compiled = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.EXCLUDE_PATTERNS
        ]

    def _generate_placeholder(self) -> str:
        """Generate a unique placeholder."""
        self._counter += 1
        return f"{self.PLACEHOLDER_PREFIX}{self._counter}{self.PLACEHOLDER_SUFFIX}"

    def _should_exclude(self, text: str, match_start: int, match_end: int) -> bool:
        """Check if a match should be excluded from masking."""
        # Get surrounding context
        context_start = max(0, match_start - 10)
        context_end = min(len(text), match_end + 10)
        context = text[context_start:context_end]

        for pattern in self._exclude_compiled:
            if pattern.search(context):
                # Check if the excluded pattern overlaps with our match
                for exc_match in pattern.finditer(context):
                    exc_start = context_start + exc_match.start()
                    exc_end = context_start + exc_match.end()
                    if not (exc_end <= match_start or exc_start >= match_end):
                        return True
        return False

    def _extract_numeric_value(self, matched_text: str) -> Optional[float]:
        """Extract the numeric value from a matched string."""
        # Remove currency symbols, units, and formatting
        cleaned = re.sub(r"[^\d.,\-eE+]", "", matched_text)
        cleaned = cleaned.replace(",", "")

        try:
            return float(cleaned)
        except ValueError:
            return None

    def mask(self, text: str) -> MaskingResult:
        """
        Mask all numerical values in the text.

        Args:
            text: Text containing numerical values to mask

        Returns:
            MaskingResult with masked text and value mapping
        """
        self._counter = 0
        value_mapping: Dict[str, str] = {}
        masked_text = text

        # Find all matches with their positions
        all_matches: List[Tuple[int, int, str, str]] = []  # (start, end, matched, category)

        for pattern, category in self._compiled_patterns:
            for match in pattern.finditer(text):
                start, end = match.start(), match.end()
                matched = match.group()

                # Check if this position is already covered by a previous match
                already_covered = any(s <= start < e or s < end <= e for s, e, _, _ in all_matches)

                if not already_covered:
                    # Check exclusions
                    if not self._should_exclude(text, start, end):
                        # Check minimum value threshold
                        if self.min_value_to_mask is not None:
                            value = self._extract_numeric_value(matched)
                            if value is not None and abs(value) < self.min_value_to_mask:
                                continue

                        all_matches.append((start, end, matched, category))

        # Sort by position (reverse order for replacement)
        all_matches.sort(key=lambda x: x[0], reverse=True)

        # Replace matches with placeholders
        for start, end, matched, category in all_matches:
            placeholder = self._generate_placeholder()
            value_mapping[placeholder] = matched
            masked_text = masked_text[:start] + placeholder + masked_text[end:]

        return MaskingResult(
            original=text,
            masked=masked_text,
            value_mapping=value_mapping,
            mask_count=len(value_mapping),
        )

    def unmask(
        self,
        text: str,
        value_mapping: Dict[str, str],
        computed_values: Optional[Dict[str, str]] = None,
    ) -> UnmaskingResult:
        """
        Restore masked values in the text.

        Args:
            text: Text with placeholders
            value_mapping: Original placeholder to value mapping
            computed_values: Optional computed values to use instead of originals

        Returns:
            UnmaskingResult with unmasked text
        """
        unmasked_text = text
        resolved_count = 0
        unresolved: List[str] = []

        # Use computed values if provided, otherwise use original mapping
        values_to_use = computed_values if computed_values else value_mapping

        # Find all placeholders in text
        placeholder_pattern = re.compile(
            re.escape(self.PLACEHOLDER_PREFIX) + r"\d+" + re.escape(self.PLACEHOLDER_SUFFIX)
        )

        for match in placeholder_pattern.finditer(text):
            placeholder = match.group()
            if placeholder in values_to_use:
                unmasked_text = unmasked_text.replace(placeholder, values_to_use[placeholder], 1)
                resolved_count += 1
            elif placeholder in value_mapping:
                # Fall back to original value if computed value not available
                unmasked_text = unmasked_text.replace(placeholder, value_mapping[placeholder], 1)
                resolved_count += 1
            else:
                unresolved.append(placeholder)

        return UnmaskingResult(
            original=text,
            unmasked=unmasked_text,
            resolved_count=resolved_count,
            unresolved_placeholders=unresolved,
        )

    def detect_leakage(self, grd: str) -> List[Dict[str, str]]:
        """
        Detect potential answer leakage in a GRD.

        This method finds numerical values that might be computed answers
        rather than problem inputs.

        Args:
            grd: Mermaid GRD code to analyze

        Returns:
            List of detected potential leaks with context
        """
        leaks: List[Dict[str, str]] = []

        # Patterns that suggest computed values (answer leakage)
        leakage_indicators = [
            (r"=\s*[\d,]+\.?\d*", "equals_result"),  # = 60
            (r"(?:answer|result|solution)\s*[:=]?\s*[\d,]+\.?\d*", "labeled_answer"),
            (r"[\d,]+\.?\d*\s*(?:is the|is our|gives us)", "conclusion_statement"),
        ]

        for pattern, leak_type in leakage_indicators:
            for match in re.finditer(pattern, grd, re.IGNORECASE):
                leaks.append(
                    {
                        "type": leak_type,
                        "matched": match.group(),
                        "position": match.start(),
                        "context": grd[
                            max(0, match.start() - 20) : min(len(grd), match.end() + 20)
                        ],
                    }
                )

        return leaks

    def mask_grd_nodes(
        self, mermaid_code: str, preserve_problem_values: bool = True
    ) -> MaskingResult:
        """
        Mask numerical values specifically in GRD node labels.

        This method is more targeted than mask(), focusing only on
        content within node brackets [text], (text), {text}, etc.

        Args:
            mermaid_code: Complete Mermaid GRD code
            preserve_problem_values: If True, try to preserve problem input values

        Returns:
            MaskingResult with masked GRD
        """
        # Pattern to match node content
        node_content_pattern = re.compile(r"(\w+)\s*(\[|\(|\{)(.*?)(\]|\)|\})", re.DOTALL)

        self._counter = 0
        value_mapping: Dict[str, str] = {}
        masked_code = mermaid_code

        # Find all node contents
        for match in node_content_pattern.finditer(mermaid_code):
            node_id = match.group(1)
            open_bracket = match.group(2)
            content = match.group(3)
            close_bracket = match.group(4)

            # Skip if this looks like a problem statement node
            if preserve_problem_values and any(
                kw in content.lower()
                for kw in ["problem", "given", "input", "question", "if", "when"]
            ):
                continue

            # Mask the content
            content_result = self.mask(content)

            if content_result.has_masks():
                # Update the value mapping
                value_mapping.update(content_result.value_mapping)

                # Replace in the code
                new_node = f"{node_id}{open_bracket}{content_result.masked}{close_bracket}"
                old_node = match.group(0)
                masked_code = masked_code.replace(old_node, new_node, 1)

        return MaskingResult(
            original=mermaid_code,
            masked=masked_code,
            value_mapping=value_mapping,
            mask_count=len(value_mapping),
        )
