"""
BRAID-DSPy Integration Library

This library integrates BRAID (Bounded Reasoning for Autonomous Inference and Decisions)
architecture into the DSPy framework, enabling structured reasoning through
Guided Reasoning Diagrams (GRD).

Features:
- Numerical Masking: Prevents answer leakage in GRDs
- Atomicity Validation: Ensures optimal node token density
- Stateful Execution: Dynamic GRD traversal with branching
- Critic Feedback: Self-verification loops
- PPD Metrics: Performance-per-Dollar analysis
"""

from braid.module import BraidReasoning, BraidResult
from braid.signatures import (
    BraidPlanSignature,
    BraidExecuteSignature,
    BraidReasoningSignature,
    BraidStepSignature,
)
from braid.optimizer import BraidOptimizer, GRDMetrics
from braid.parser import MermaidParser, GRDStructure, GRDNode, GRDEdge
from braid.generator import GRDGenerator

# New BRAID Protocol modules
from braid.masking import NumericalMasker, MaskingResult
from braid.validators import (
    AtomicityValidator,
    ProceduralScaffoldingValidator,
    GRDValidator,
    ValidationResult,
)
from braid.engine import StatefulExecutionEngine, ExecutionState, ExecutionResult
from braid.critic import CriticDetector, CriticExecutor, CriticNode
from braid.metrics import PPDAnalyzer, TokenUsage, CostAnalysis, PPDReport
from braid.training import (
    SyntheticDataGenerator,
    ArchitectTrainer,
    TrainingSample,
    DatasetExporter,
)

__version__ = "0.2.3"

__all__ = [
    # Core modules
    "BraidReasoning",
    "BraidResult",
    # Signatures
    "BraidPlanSignature",
    "BraidExecuteSignature",
    "BraidReasoningSignature",
    "BraidStepSignature",
    # Optimization
    "BraidOptimizer",
    "GRDMetrics",
    # Parsing
    "MermaidParser",
    "GRDStructure",
    "GRDNode",
    "GRDEdge",
    "GRDGenerator",
    # Masking (BRAID Protocol)
    "NumericalMasker",
    "MaskingResult",
    # Validation (BRAID Protocol)
    "AtomicityValidator",
    "ProceduralScaffoldingValidator",
    "GRDValidator",
    "ValidationResult",
    # Execution Engine (BRAID Protocol)
    "StatefulExecutionEngine",
    "ExecutionState",
    "ExecutionResult",
    # Critic (BRAID Protocol)
    "CriticDetector",
    "CriticExecutor",
    "CriticNode",
    # Metrics (BRAID Protocol)
    "PPDAnalyzer",
    "TokenUsage",
    "CostAnalysis",
    "PPDReport",
    # Training (BRAID Protocol)
    "SyntheticDataGenerator",
    "ArchitectTrainer",
    "TrainingSample",
    "DatasetExporter",
]
