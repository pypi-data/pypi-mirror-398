"""Training utilities for BRAID Architect models.

This module provides tools for:
- Generating synthetic training data for Architect models
- Preparing datasets for fine-tuning
- Creating DSPy examples for BootstrapFewShot optimization
"""

import json
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path

from braid.validators import AtomicityValidator, GRDValidator
from braid.masking import NumericalMasker


@dataclass
class TrainingSample:
    """A single training sample for Architect model training."""

    problem: str
    grd: str
    expected_answer: Optional[str] = None
    problem_type: str = "general"
    difficulty: str = "medium"  # easy, medium, hard
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrainingSample":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class DatasetStats:
    """Statistics for a training dataset."""

    total_samples: int
    problem_types: Dict[str, int]
    difficulty_distribution: Dict[str, int]
    avg_grd_nodes: float
    avg_tokens_per_node: float
    validation_passed: int
    validation_failed: int


class SyntheticDataGenerator:
    """
    Generates synthetic training data for Architect models.

    This generator creates problem-GRD pairs following BRAID protocol:
    - Procedural scaffolding (describe HOW, not WHAT)
    - Atomic nodes (≤15 tokens per node)
    - No answer leakage
    """

    # Problem templates by category
    MATH_TEMPLATES = [
        {
            "template": "If a {vehicle} travels {distance} km in {time} hours, what is its speed?",
            "grd_template": """flowchart TD
    Start[Read and analyze problem] --> Extract[Extract: distance and time values]
    Extract --> Identify[Identify: need to find speed]
    Identify --> Formula[Recall speed formula]
    Formula --> Apply[Apply: divide distance by time]
    Apply --> Units[Verify units are correct]
    Units --> Answer[State the final speed]""",
            "variables": {
                "vehicle": ["car", "train", "bus", "bicycle", "plane"],
                "distance": [60, 120, 180, 240, 300, 450, 600],
                "time": [1, 2, 3, 4, 5, 6],
            },
            "answer_fn": lambda v: f"{v['distance'] / v['time']} km/h",
        },
        {
            "template": "Solve: {a}x + {b} = {c}",
            "grd_template": """flowchart TD
    Start[Analyze the equation] --> Goal[Goal: isolate x]
    Goal --> Subtract[Subtract constant from both sides]
    Subtract --> Simplify1[Simplify right side]
    Simplify1 --> Divide[Divide by coefficient]
    Divide --> Simplify2[Calculate x value]
    Simplify2 --> Check[Verify by substitution]
    Check --> Answer[State solution]""",
            "variables": {
                "a": [2, 3, 4, 5, 6],
                "b": [1, 2, 3, 4, 5, 7, 8, 10],
                "c": [10, 12, 14, 15, 18, 20, 22, 25],
            },
            "answer_fn": lambda v: f"x = {(v['c'] - v['b']) / v['a']}",
        },
        {
            "template": "A store sells {item} at ${price} each. If {name} buys {quantity}, how much does {pronoun} pay?",
            "grd_template": """flowchart TD
    Start[Understand the scenario] --> Values[Identify: unit price and quantity]
    Values --> Operation[Determine operation needed]
    Operation --> Calculate[Multiply price by quantity]
    Calculate --> Format[Format as currency]
    Format --> Answer[State total cost]""",
            "variables": {
                "item": ["apples", "oranges", "books", "pens", "notebooks"],
                "price": [2, 3, 5, 8, 10, 15],
                "name": ["John", "Maria", "Alex", "Sarah"],
                "quantity": [3, 4, 5, 6, 7, 8, 10],
                "pronoun": ["he", "she", "they"],
            },
            "answer_fn": lambda v: f"${v['price'] * v['quantity']}",
        },
    ]

    LOGIC_TEMPLATES = [
        {
            "template": "If all {category_a} are {category_b}, and {item} is a {category_a}, what can we conclude?",
            "grd_template": """flowchart TD
    Start[Identify premises] --> P1[Premise 1: All A are B]
    P1 --> P2[Premise 2: X is A]
    P2 --> Apply[Apply syllogistic reasoning]
    Apply --> Deduce[Deduce: X must be B]
    Deduce --> Answer[State conclusion]""",
            "variables": {
                "category_a": ["dogs", "cats", "birds", "mammals"],
                "category_b": ["animals", "living things", "creatures"],
                "item": ["Rex", "Fluffy", "Tweety", "Max"],
            },
            "answer_fn": lambda v: f"{v['item']} is a {v['category_b'].rstrip('s')}",
        },
    ]

    REASONING_TEMPLATES = [
        {
            "template": "{person} has {count} {items}. {person2} gives {person} {more} more. How many does {person} have now?",
            "grd_template": """flowchart TD
    Start[Understand the situation] --> Initial[Identify initial count]
    Initial --> Change[Identify the change]
    Change --> Operation[Determine: addition needed]
    Operation --> Calculate[Add the quantities]
    Calculate --> Answer[State final count]""",
            "variables": {
                "person": ["Alice", "Bob", "Charlie", "Diana"],
                "person2": ["Bob", "Carol", "David", "Eve"],
                "count": [3, 5, 7, 10, 12],
                "items": ["apples", "books", "coins", "marbles"],
                "more": [2, 3, 4, 5],
            },
            "answer_fn": lambda v: f"{v['count'] + v['more']} {v['items']}",
        },
    ]

    def __init__(
        self,
        validate_output: bool = True,
        max_tokens_per_node: int = 15,
    ):
        """
        Initialize the synthetic data generator.

        Args:
            validate_output: Whether to validate generated samples
            max_tokens_per_node: Maximum tokens per node for validation
        """
        self.validate_output = validate_output
        self.validator = GRDValidator(max_tokens_per_node=max_tokens_per_node)
        self.masker = NumericalMasker()
        self.atomicity_validator = AtomicityValidator(max_tokens_per_node=max_tokens_per_node)

    def _fill_template(self, template: Dict[str, Any]) -> Tuple[str, str, str]:
        """Fill a template with random variables."""
        variables = {}
        for var_name, var_options in template["variables"].items():
            variables[var_name] = random.choice(var_options)

        problem = template["template"].format(**variables)
        grd = template["grd_template"]
        answer = template["answer_fn"](variables)

        return problem, grd, answer

    def generate_math_samples(self, count: int) -> List[TrainingSample]:
        """
        Generate math problem samples.

        Args:
            count: Number of samples to generate

        Returns:
            List of TrainingSample objects
        """
        samples = []
        for _ in range(count):
            template = random.choice(self.MATH_TEMPLATES)
            problem, grd, answer = self._fill_template(template)

            sample = TrainingSample(
                problem=problem,
                grd=f"```mermaid\n{grd}\n```",
                expected_answer=answer,
                problem_type="math",
                difficulty=random.choice(["easy", "medium"]),
            )
            samples.append(sample)

        return samples

    def generate_logic_samples(self, count: int) -> List[TrainingSample]:
        """
        Generate logic problem samples.

        Args:
            count: Number of samples to generate

        Returns:
            List of TrainingSample objects
        """
        samples = []
        for _ in range(count):
            template = random.choice(self.LOGIC_TEMPLATES)
            problem, grd, answer = self._fill_template(template)

            sample = TrainingSample(
                problem=problem,
                grd=f"```mermaid\n{grd}\n```",
                expected_answer=answer,
                problem_type="logic",
                difficulty=random.choice(["medium", "hard"]),
            )
            samples.append(sample)

        return samples

    def generate_reasoning_samples(self, count: int) -> List[TrainingSample]:
        """
        Generate general reasoning samples.

        Args:
            count: Number of samples to generate

        Returns:
            List of TrainingSample objects
        """
        samples = []
        for _ in range(count):
            template = random.choice(self.REASONING_TEMPLATES)
            problem, grd, answer = self._fill_template(template)

            sample = TrainingSample(
                problem=problem,
                grd=f"```mermaid\n{grd}\n```",
                expected_answer=answer,
                problem_type="reasoning",
                difficulty="easy",
            )
            samples.append(sample)

        return samples

    def generate_mixed_samples(
        self,
        count: int,
        math_ratio: float = 0.4,
        logic_ratio: float = 0.3,
        reasoning_ratio: float = 0.3,
    ) -> List[TrainingSample]:
        """
        Generate a mixed dataset of samples.

        Args:
            count: Total number of samples
            math_ratio: Proportion of math problems
            logic_ratio: Proportion of logic problems
            reasoning_ratio: Proportion of reasoning problems

        Returns:
            List of TrainingSample objects
        """
        math_count = int(count * math_ratio)
        logic_count = int(count * logic_ratio)
        reasoning_count = count - math_count - logic_count

        samples = []
        samples.extend(self.generate_math_samples(math_count))
        samples.extend(self.generate_logic_samples(logic_count))
        samples.extend(self.generate_reasoning_samples(reasoning_count))

        random.shuffle(samples)
        return samples

    def validate_samples(
        self, samples: List[TrainingSample]
    ) -> Tuple[List[TrainingSample], List[TrainingSample]]:
        """
        Validate samples against BRAID protocol rules.

        Args:
            samples: Samples to validate

        Returns:
            Tuple of (valid_samples, invalid_samples)
        """
        from braid.parser import MermaidParser
        from braid.utils import extract_mermaid_code

        parser = MermaidParser()
        valid = []
        invalid = []

        for sample in samples:
            try:
                mermaid_code = extract_mermaid_code(sample.grd)
                if mermaid_code:
                    parsed = parser.parse(mermaid_code)
                    result = self.validator.validate(parsed)

                    if result.valid:
                        valid.append(sample)
                    else:
                        sample.metadata["validation_issues"] = [
                            str(issue) for issue in result.issues
                        ]
                        invalid.append(sample)
                else:
                    sample.metadata["validation_issues"] = ["Could not extract Mermaid code"]
                    invalid.append(sample)
            except Exception as e:
                sample.metadata["validation_issues"] = [str(e)]
                invalid.append(sample)

        return valid, invalid


class DatasetExporter:
    """Exports training datasets in various formats."""

    @staticmethod
    def to_jsonl(samples: List[TrainingSample], path: str) -> None:
        """
        Export samples to JSONL format.

        Args:
            samples: Samples to export
            path: Output file path
        """
        with open(path, "w", encoding="utf-8") as f:
            for sample in samples:
                f.write(json.dumps(sample.to_dict(), ensure_ascii=False) + "\n")

    @staticmethod
    def to_json(samples: List[TrainingSample], path: str) -> None:
        """
        Export samples to JSON format.

        Args:
            samples: Samples to export
            path: Output file path
        """
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                [sample.to_dict() for sample in samples],
                f,
                ensure_ascii=False,
                indent=2,
            )

    @staticmethod
    def from_jsonl(path: str) -> List[TrainingSample]:
        """
        Load samples from JSONL format.

        Args:
            path: Input file path

        Returns:
            List of TrainingSample objects
        """
        samples = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line.strip())
                samples.append(TrainingSample.from_dict(data))
        return samples

    @staticmethod
    def from_json(path: str) -> List[TrainingSample]:
        """
        Load samples from JSON format.

        Args:
            path: Input file path

        Returns:
            List of TrainingSample objects
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [TrainingSample.from_dict(item) for item in data]


class ArchitectTrainer:
    """
    Utilities for training/fine-tuning Architect models.

    Supports:
    - Creating DSPy examples for BootstrapFewShot
    - Preparing fine-tuning datasets
    - Calculating dataset statistics
    """

    def __init__(self):
        """Initialize the trainer."""
        self.generator = SyntheticDataGenerator()

    def create_dspy_examples(self, samples: List[TrainingSample]) -> List[Any]:
        """
        Create DSPy Example objects from training samples.

        Args:
            samples: Training samples to convert

        Returns:
            List of dspy.Example objects
        """
        try:
            import dspy

            examples = []
            for sample in samples:
                example = dspy.Example(
                    problem=sample.problem,
                    grd=sample.grd,
                ).with_inputs("problem")

                if sample.expected_answer:
                    example = example.with_inputs("problem")

                examples.append(example)

            return examples
        except ImportError:
            raise ImportError(
                "DSPy is required for creating examples. Install with: pip install dspy-ai"
            )

    def prepare_openai_finetune_dataset(
        self,
        samples: List[TrainingSample],
        system_prompt: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Prepare dataset in OpenAI fine-tuning format.

        Args:
            samples: Training samples
            system_prompt: Optional system prompt

        Returns:
            List of conversation dictionaries
        """
        if system_prompt is None:
            system_prompt = """You are an expert at creating Guided Reasoning Diagrams (GRDs) in Mermaid format.

BRAID Protocol Rules:
1. PROCEDURAL SCAFFOLDING: Describe HOW to solve, never WHAT the answer is
2. NO ANSWER LEAKAGE: Never include computed values in node labels
3. ATOMIC NODES: Keep each node under 15 tokens
4. ACTION-ORIENTED: Each node describes an executable action"""

        dataset = []
        for sample in samples:
            conversation = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Create a GRD for this problem: {sample.problem}"},
                    {"role": "assistant", "content": sample.grd},
                ]
            }
            dataset.append(conversation)

        return dataset

    def calculate_dataset_stats(self, samples: List[TrainingSample]) -> DatasetStats:
        """
        Calculate statistics for a dataset.

        Args:
            samples: Training samples

        Returns:
            DatasetStats object
        """
        from braid.parser import MermaidParser
        from braid.utils import extract_mermaid_code
        from braid.validators import AtomicityValidator

        parser = MermaidParser()
        validator = AtomicityValidator()

        problem_types: Dict[str, int] = {}
        difficulty_dist: Dict[str, int] = {}
        node_counts = []
        token_counts = []
        valid_count = 0
        invalid_count = 0

        for sample in samples:
            # Count problem types
            problem_types[sample.problem_type] = problem_types.get(sample.problem_type, 0) + 1

            # Count difficulties
            difficulty_dist[sample.difficulty] = difficulty_dist.get(sample.difficulty, 0) + 1

            # Parse and analyze GRD
            try:
                mermaid_code = extract_mermaid_code(sample.grd)
                if mermaid_code:
                    parsed = parser.parse(mermaid_code)
                    node_counts.append(len(parsed.nodes))

                    for node in parsed.nodes:
                        token_counts.append(validator.count_tokens(node.label))

                    valid_count += 1
                else:
                    invalid_count += 1
            except Exception:
                invalid_count += 1

        return DatasetStats(
            total_samples=len(samples),
            problem_types=problem_types,
            difficulty_distribution=difficulty_dist,
            avg_grd_nodes=sum(node_counts) / len(node_counts) if node_counts else 0,
            avg_tokens_per_node=sum(token_counts) / len(token_counts) if token_counts else 0,
            validation_passed=valid_count,
            validation_failed=invalid_count,
        )

    def generate_training_dataset(
        self,
        size: int = 100,
        output_path: Optional[str] = None,
        format: str = "jsonl",
    ) -> List[TrainingSample]:
        """
        Generate and optionally save a training dataset.

        Args:
            size: Number of samples to generate
            output_path: Optional path to save the dataset
            format: Output format ("jsonl" or "json")

        Returns:
            List of generated samples
        """
        samples = self.generator.generate_mixed_samples(size)
        valid_samples, _ = self.generator.validate_samples(samples)

        if output_path:
            if format == "jsonl":
                DatasetExporter.to_jsonl(valid_samples, output_path)
            else:
                DatasetExporter.to_json(valid_samples, output_path)

        return valid_samples
