"""Unit tests for the training module."""

import pytest
import json
import tempfile
import os
from braid.training import (
    TrainingSample,
    SyntheticDataGenerator,
    ArchitectTrainer,
    DatasetExporter,
    DatasetStats,
)


class TestTrainingSample:
    """Tests for TrainingSample dataclass."""

    def test_creation(self):
        """Test creating a TrainingSample."""
        sample = TrainingSample(
            problem="What is 2 + 2?",
            grd="```mermaid\nflowchart TD\nA[Add] --> B[Result]\n```",
            expected_answer="4",
            problem_type="math",
            difficulty="easy",
        )

        assert sample.problem == "What is 2 + 2?"
        assert sample.expected_answer == "4"
        assert sample.problem_type == "math"
        assert sample.difficulty == "easy"

    def test_to_dict(self):
        """Test converting to dictionary."""
        sample = TrainingSample(
            problem="Test problem", grd="test grd", expected_answer="test answer"
        )

        d = sample.to_dict()

        assert isinstance(d, dict)
        assert d["problem"] == "Test problem"
        assert d["grd"] == "test grd"

    def test_from_dict(self):
        """Test creating from dictionary."""
        d = {
            "problem": "Test",
            "grd": "GRD",
            "expected_answer": "Answer",
            "problem_type": "logic",
            "difficulty": "hard",
            "metadata": {"key": "value"},
        }

        sample = TrainingSample.from_dict(d)

        assert sample.problem == "Test"
        assert sample.problem_type == "logic"
        assert sample.metadata["key"] == "value"


class TestSyntheticDataGenerator:
    """Tests for SyntheticDataGenerator class."""

    def test_initialization(self):
        """Test generator initialization."""
        generator = SyntheticDataGenerator()

        assert generator.validate_output == True
        assert generator.validator is not None

    def test_generate_math_samples(self):
        """Test generating math samples."""
        generator = SyntheticDataGenerator()
        samples = generator.generate_math_samples(5)

        assert len(samples) == 5
        for sample in samples:
            assert isinstance(sample, TrainingSample)
            assert sample.problem_type == "math"
            assert "```mermaid" in sample.grd

    def test_generate_logic_samples(self):
        """Test generating logic samples."""
        generator = SyntheticDataGenerator()
        samples = generator.generate_logic_samples(3)

        assert len(samples) == 3
        for sample in samples:
            assert sample.problem_type == "logic"

    def test_generate_reasoning_samples(self):
        """Test generating reasoning samples."""
        generator = SyntheticDataGenerator()
        samples = generator.generate_reasoning_samples(3)

        assert len(samples) == 3
        for sample in samples:
            assert sample.problem_type == "reasoning"

    def test_generate_mixed_samples(self):
        """Test generating mixed samples."""
        generator = SyntheticDataGenerator()
        samples = generator.generate_mixed_samples(
            count=10, math_ratio=0.5, logic_ratio=0.3, reasoning_ratio=0.2
        )

        assert len(samples) == 10

        # Check distribution (approximate due to rounding)
        types = [s.problem_type for s in samples]
        assert types.count("math") >= 3
        assert types.count("logic") >= 1

    def test_validate_samples(self):
        """Test sample validation."""
        generator = SyntheticDataGenerator()
        samples = generator.generate_math_samples(3)

        valid, invalid = generator.validate_samples(samples)

        # All generated samples should be valid
        assert len(valid) + len(invalid) == 3
        # Most should be valid since we generate from templates
        assert len(valid) >= len(invalid)


class TestDatasetExporter:
    """Tests for DatasetExporter class."""

    def test_to_jsonl(self):
        """Test exporting to JSONL format."""
        samples = [
            TrainingSample(problem="P1", grd="G1"),
            TrainingSample(problem="P2", grd="G2"),
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            path = f.name

        try:
            DatasetExporter.to_jsonl(samples, path)

            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            assert len(lines) == 2
            assert "P1" in lines[0]
            assert "P2" in lines[1]
        finally:
            os.unlink(path)

    def test_to_json(self):
        """Test exporting to JSON format."""
        samples = [
            TrainingSample(problem="P1", grd="G1"),
            TrainingSample(problem="P2", grd="G2"),
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name

        try:
            DatasetExporter.to_json(samples, path)

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            assert len(data) == 2
            assert data[0]["problem"] == "P1"
        finally:
            os.unlink(path)

    def test_from_jsonl(self):
        """Test loading from JSONL format."""
        samples = [
            TrainingSample(problem="P1", grd="G1"),
            TrainingSample(problem="P2", grd="G2"),
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            path = f.name

        try:
            DatasetExporter.to_jsonl(samples, path)
            loaded = DatasetExporter.from_jsonl(path)

            assert len(loaded) == 2
            assert loaded[0].problem == "P1"
            assert loaded[1].problem == "P2"
        finally:
            os.unlink(path)


class TestArchitectTrainer:
    """Tests for ArchitectTrainer class."""

    def test_initialization(self):
        """Test trainer initialization."""
        trainer = ArchitectTrainer()

        assert trainer.generator is not None

    def test_prepare_openai_finetune_dataset(self):
        """Test preparing OpenAI fine-tuning dataset."""
        trainer = ArchitectTrainer()
        samples = [
            TrainingSample(problem="P1", grd="G1"),
            TrainingSample(problem="P2", grd="G2"),
        ]

        dataset = trainer.prepare_openai_finetune_dataset(samples)

        assert len(dataset) == 2
        assert "messages" in dataset[0]
        assert len(dataset[0]["messages"]) == 3
        assert dataset[0]["messages"][0]["role"] == "system"
        assert dataset[0]["messages"][1]["role"] == "user"
        assert dataset[0]["messages"][2]["role"] == "assistant"

    def test_calculate_dataset_stats(self):
        """Test calculating dataset statistics."""
        trainer = ArchitectTrainer()
        samples = trainer.generator.generate_mixed_samples(10)

        stats = trainer.calculate_dataset_stats(samples)

        assert isinstance(stats, DatasetStats)
        assert stats.total_samples == 10
        assert len(stats.problem_types) > 0
        assert stats.validation_passed + stats.validation_failed == 10

    def test_generate_training_dataset(self):
        """Test generating a complete training dataset."""
        trainer = ArchitectTrainer()
        samples = trainer.generate_training_dataset(size=10)

        assert len(samples) > 0
        assert all(isinstance(s, TrainingSample) for s in samples)

    def test_generate_training_dataset_with_export(self):
        """Test generating and exporting training dataset."""
        trainer = ArchitectTrainer()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            path = f.name

        try:
            samples = trainer.generate_training_dataset(size=5, output_path=path, format="jsonl")

            assert len(samples) > 0
            assert os.path.exists(path)

            # Verify file content
            loaded = DatasetExporter.from_jsonl(path)
            assert len(loaded) == len(samples)
        finally:
            os.unlink(path)
