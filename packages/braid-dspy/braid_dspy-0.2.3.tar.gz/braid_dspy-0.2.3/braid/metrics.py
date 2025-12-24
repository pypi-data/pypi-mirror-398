"""Performance metrics module for BRAID-DSPy.

This module implements the Performance-per-Dollar (PPD) metrics from the
BRAID paper, allowing users to measure and compare the cost-effectiveness
of different model configurations.
"""

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TokenUsage:
    """Token usage for a single operation."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int = 0

    def __post_init__(self):
        if self.total_tokens == 0:
            self.total_tokens = self.prompt_tokens + self.completion_tokens


@dataclass
class StepMetrics:
    """Metrics for a single reasoning step."""

    step_id: str
    phase: str  # "planning" or "execution"
    token_usage: TokenUsage
    cost_usd: float
    latency_ms: float


@dataclass
class CostAnalysis:
    """Complete cost analysis for an execution."""

    total_cost_usd: float
    planning_cost_usd: float
    execution_cost_usd: float
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    step_costs: List[StepMetrics] = field(default_factory=list)


@dataclass
class PPDReport:
    """Performance-per-Dollar report."""

    accuracy: float  # 0.0 to 1.0
    total_cost_usd: float
    ppd_score: float  # Performance per Dollar
    efficiency_multiplier: float  # vs baseline
    baseline_model: Optional[str] = None
    baseline_cost_usd: Optional[float] = None
    breakdown: Optional[Dict[str, Any]] = None


@dataclass
class ModelConfig:
    """Configuration for a model."""

    model_id: str
    input_cost_per_1m: float  # USD per 1M input tokens
    output_cost_per_1m: float  # USD per 1M output tokens
    provider: str = "openai"


class PPDAnalyzer:
    """
    Performance-per-Dollar analyzer for BRAID executions.

    This class tracks token usage and costs across the planning
    and execution phases, and provides metrics for comparing with
    baseline models.

    Example:
        >>> analyzer = PPDAnalyzer(
        ...     architect_model="gpt-4",
        ...     solver_model="gpt-3.5-turbo"
        ... )
        >>> analyzer.track_usage(TokenUsage(100, 50), "planning")
        >>> report = analyzer.generate_report(accuracy=0.95)
        >>> print(f"PPD Score: {report.ppd_score}")
    """

    # Model pricing (USD per 1M tokens) - Updated December 2025
    MODEL_CONFIGS: Dict[str, ModelConfig] = {
        # OpenAI Models
        "gpt-4": ModelConfig("gpt-4", 30.0, 60.0, "openai"),
        "gpt-4-turbo": ModelConfig("gpt-4-turbo", 10.0, 30.0, "openai"),
        "gpt-4-turbo-preview": ModelConfig("gpt-4-turbo-preview", 10.0, 30.0, "openai"),
        "gpt-4o": ModelConfig("gpt-4o", 2.50, 10.0, "openai"),
        "gpt-4o-mini": ModelConfig("gpt-4o-mini", 0.15, 0.60, "openai"),
        "gpt-3.5-turbo": ModelConfig("gpt-3.5-turbo", 0.50, 1.50, "openai"),
        "o1-preview": ModelConfig("o1-preview", 15.0, 60.0, "openai"),
        "o1-mini": ModelConfig("o1-mini", 0.15, 0.60, "openai"),
        "o1": ModelConfig("o1", 15.0, 60.0, "openai"),
        "o3": ModelConfig("o3", 2.0, 8.0, "openai"),
        "o3-mini": ModelConfig("o3-mini", 1.1, 4.4, "openai"),
        # Anthropic Models
        "claude-3-opus": ModelConfig("claude-3-opus", 15.0, 75.0, "anthropic"),
        "claude-3-sonnet": ModelConfig("claude-3-sonnet", 3.0, 15.0, "anthropic"),
        "claude-3-haiku": ModelConfig("claude-3-haiku", 0.25, 1.25, "anthropic"),
        "claude-3.5-sonnet": ModelConfig("claude-3.5-sonnet", 3.0, 15.0, "anthropic"),
        "claude-3.5-haiku": ModelConfig("claude-3.5-haiku", 0.80, 4.0, "anthropic"),
        "claude-3.7-sonnet": ModelConfig("claude-3.7-sonnet", 3.0, 15.0, "anthropic"),
        "claude-4.5-sonnet": ModelConfig("claude-4.5-sonnet", 3.0, 15.0, "anthropic"),
        "claude-4.5-opus": ModelConfig("claude-4.5-opus", 5.0, 25.0, "anthropic"),
        "claude-4.5-haiku": ModelConfig("claude-4.5-haiku", 1.0, 5.0, "anthropic"),
        # Google Models
        "gemini-1.5-pro": ModelConfig("gemini-1.5-pro", 1.25, 5.00, "google"),
        "gemini-1.5-flash": ModelConfig("gemini-1.5-flash", 0.075, 0.30, "google"),
        "gemini-2.0-flash": ModelConfig("gemini-2.0-flash", 0.10, 0.40, "google"),
        "gemini-2.0-flash-lite": ModelConfig("gemini-2.0-flash-lite", 0.075, 0.30, "google"),
        "gemini-2.5-pro": ModelConfig("gemini-2.5-pro", 1.25, 10.00, "google"),
        "gemini-2.5-flash": ModelConfig("gemini-2.5-flash", 0.30, 2.50, "google"),
        "gemini-3.0-pro": ModelConfig("gemini-3.0-pro", 2.00, 12.00, "google"),
        "gemini-3.0-flash": ModelConfig("gemini-3.0-flash", 0.50, 3.00, "google"),
        "gemini-2.0-pro-exp": ModelConfig("gemini-2.0-pro-exp", 0.00, 0.00, "google"),
        # Local/Open Models (estimated inference costs via providers like Together/Groq)
        "llama-3.3-70b": ModelConfig("llama-3.3-70b", 0.10, 0.40, "local"),
        "llama-4-scout": ModelConfig("llama-4-scout", 0.10, 0.34, "local"),
        "llama-4-maverick": ModelConfig("llama-4-maverick", 0.22, 0.85, "local"),
        "llama-4-behemoth": ModelConfig("llama-4-behemoth", 3.50, 3.50, "local"),
        "deepseek-v3": ModelConfig("deepseek-v3", 0.28, 0.42, "local"),
        "deepseek-r1": ModelConfig("deepseek-r1", 0.55, 2.19, "local"),
    }

    def __init__(
        self,
        architect_model: str = "gpt-4",
        solver_model: str = "gpt-3.5-turbo",
        custom_configs: Optional[Dict[str, ModelConfig]] = None,
    ):
        """
        Initialize the PPD Analyzer.

        Args:
            architect_model: Model used for GRD planning phase
            solver_model: Model used for GRD execution phase
            custom_configs: Optional custom model configurations
        """
        self.architect_model = architect_model
        self.solver_model = solver_model

        # Merge custom configs with defaults
        self.model_configs = dict(self.MODEL_CONFIGS)
        if custom_configs:
            self.model_configs.update(custom_configs)

        # Usage tracking
        self.usage_log: List[StepMetrics] = []
        self._session_start = datetime.now()

    def get_model_config(self, model_id: str) -> ModelConfig:
        """Get configuration for a model."""
        if model_id in self.model_configs:
            return self.model_configs[model_id]

        # Default config for unknown models
        return ModelConfig(model_id, 1.0, 2.0, "unknown")

    def calculate_cost(
        self,
        usage: TokenUsage,
        model_id: str,
    ) -> float:
        """
        Calculate cost for given token usage.

        Args:
            usage: Token usage to calculate cost for
            model_id: Model ID to use for pricing

        Returns:
            Cost in USD
        """
        config = self.get_model_config(model_id)

        input_cost = (usage.prompt_tokens / 1_000_000) * config.input_cost_per_1m
        output_cost = (usage.completion_tokens / 1_000_000) * config.output_cost_per_1m

        return input_cost + output_cost

    def track_usage(
        self,
        usage: TokenUsage,
        phase: str,
        step_id: Optional[str] = None,
        latency_ms: float = 0.0,
    ) -> StepMetrics:
        """
        Track token usage for a step.

        Args:
            usage: Token usage for this step
            phase: "planning" or "execution"
            step_id: Optional step identifier
            latency_ms: Latency in milliseconds

        Returns:
            StepMetrics for this step
        """
        model_id = self.architect_model if phase == "planning" else self.solver_model
        cost = self.calculate_cost(usage, model_id)

        metrics = StepMetrics(
            step_id=step_id or f"step_{len(self.usage_log) + 1}",
            phase=phase,
            token_usage=usage,
            cost_usd=cost,
            latency_ms=latency_ms,
        )

        self.usage_log.append(metrics)
        return metrics

    def get_cost_analysis(self) -> CostAnalysis:
        """
        Get complete cost analysis for all tracked usage.

        Returns:
            CostAnalysis with complete breakdown
        """
        total_cost = sum(m.cost_usd for m in self.usage_log)
        planning_cost = sum(m.cost_usd for m in self.usage_log if m.phase == "planning")
        execution_cost = sum(m.cost_usd for m in self.usage_log if m.phase == "execution")

        total_tokens = sum(m.token_usage.total_tokens for m in self.usage_log)
        prompt_tokens = sum(m.token_usage.prompt_tokens for m in self.usage_log)
        completion_tokens = sum(m.token_usage.completion_tokens for m in self.usage_log)

        return CostAnalysis(
            total_cost_usd=total_cost,
            planning_cost_usd=planning_cost,
            execution_cost_usd=execution_cost,
            total_tokens=total_tokens,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            step_costs=list(self.usage_log),
        )

    def estimate_baseline_cost(
        self,
        baseline_model: str,
        problem_complexity_tokens: int = 500,
        response_tokens: int = 200,
    ) -> float:
        """
        Estimate cost for solving with a single baseline model.

        This estimates what it would cost to solve the problem using
        a single model without BRAID's split architecture.

        Args:
            baseline_model: Model to use as baseline
            problem_complexity_tokens: Estimated input tokens
            response_tokens: Estimated response tokens

        Returns:
            Estimated cost in USD
        """
        usage = TokenUsage(
            prompt_tokens=problem_complexity_tokens,
            completion_tokens=response_tokens,
        )
        return self.calculate_cost(usage, baseline_model)

    def calculate_ppd_score(
        self,
        accuracy: float,
        total_cost: Optional[float] = None,
    ) -> float:
        """
        Calculate Performance-per-Dollar score.

        PPD = Accuracy / Cost

        Higher is better. A score of 100 means 100% accuracy at $0.01 cost.

        Args:
            accuracy: Accuracy between 0.0 and 1.0
            total_cost: Optional override for total cost

        Returns:
            PPD score
        """
        if total_cost is None:
            analysis = self.get_cost_analysis()
            total_cost = analysis.total_cost_usd

        if total_cost <= 0:
            return float("inf") if accuracy > 0 else 0.0

        # Scale PPD for readability (per $0.01)
        return (accuracy / total_cost) * 0.01

    def compare_with_baseline(
        self,
        accuracy: float,
        baseline_model: str,
        baseline_accuracy: Optional[float] = None,
    ) -> PPDReport:
        """
        Compare BRAID execution with a baseline model.

        Args:
            accuracy: BRAID accuracy
            baseline_model: Model to compare against
            baseline_accuracy: Baseline model accuracy (if known)

        Returns:
            PPDReport with comparison metrics
        """
        analysis = self.get_cost_analysis()
        braid_cost = analysis.total_cost_usd

        # Estimate baseline cost
        avg_tokens = analysis.total_tokens / max(len(self.usage_log), 1)
        baseline_cost = self.estimate_baseline_cost(
            baseline_model,
            problem_complexity_tokens=int(avg_tokens * 0.7),
            response_tokens=int(avg_tokens * 0.3),
        )

        # Calculate PPD scores
        braid_ppd = self.calculate_ppd_score(accuracy, braid_cost)

        if baseline_accuracy is not None and baseline_cost > 0:
            baseline_ppd = (baseline_accuracy / baseline_cost) * 0.01
            efficiency_multiplier = braid_ppd / baseline_ppd if baseline_ppd > 0 else float("inf")
        else:
            efficiency_multiplier = 1.0

        return PPDReport(
            accuracy=accuracy,
            total_cost_usd=braid_cost,
            ppd_score=braid_ppd,
            efficiency_multiplier=efficiency_multiplier,
            baseline_model=baseline_model,
            baseline_cost_usd=baseline_cost,
            breakdown={
                "architect_model": self.architect_model,
                "solver_model": self.solver_model,
                "planning_cost": analysis.planning_cost_usd,
                "execution_cost": analysis.execution_cost_usd,
                "total_tokens": analysis.total_tokens,
                "num_steps": len(self.usage_log),
            },
        )

    def generate_report(
        self,
        accuracy: float,
        baseline_model: Optional[str] = None,
        format: str = "markdown",
    ) -> str:
        """
        Generate a human-readable performance report.

        Args:
            accuracy: Achieved accuracy
            baseline_model: Optional model for comparison
            format: Output format ("markdown" or "text")

        Returns:
            Formatted report string
        """
        analysis = self.get_cost_analysis()

        if format == "markdown":
            return self._format_markdown_report(analysis, accuracy, baseline_model)
        else:
            return self._format_text_report(analysis, accuracy, baseline_model)

    def _format_markdown_report(
        self,
        analysis: CostAnalysis,
        accuracy: float,
        baseline_model: Optional[str],
    ) -> str:
        """Format report as Markdown."""
        lines = [
            "# BRAID Performance Report",
            "",
            "## Configuration",
            f"- **Architect Model:** {self.architect_model}",
            f"- **Solver Model:** {self.solver_model}",
            "",
            "## Cost Breakdown",
            f"| Phase | Cost (USD) | Tokens |",
            f"|-------|------------|--------|",
            f"| Planning | ${analysis.planning_cost_usd:.6f} | {sum(m.token_usage.total_tokens for m in self.usage_log if m.phase == 'planning')} |",
            f"| Execution | ${analysis.execution_cost_usd:.6f} | {sum(m.token_usage.total_tokens for m in self.usage_log if m.phase == 'execution')} |",
            f"| **Total** | **${analysis.total_cost_usd:.6f}** | **{analysis.total_tokens}** |",
            "",
            "## Performance Metrics",
            f"- **Accuracy:** {accuracy:.1%}",
            f"- **PPD Score:** {self.calculate_ppd_score(accuracy):.2f}",
        ]

        if baseline_model:
            report = self.compare_with_baseline(accuracy, baseline_model)
            lines.extend(
                [
                    "",
                    "## Baseline Comparison",
                    f"- **Baseline Model:** {baseline_model}",
                    f"- **Estimated Baseline Cost:** ${report.baseline_cost_usd:.6f}",
                    f"- **Efficiency Multiplier:** {report.efficiency_multiplier:.2f}x",
                ]
            )

        return "\n".join(lines)

    def _format_text_report(
        self,
        analysis: CostAnalysis,
        accuracy: float,
        baseline_model: Optional[str],
    ) -> str:
        """Format report as plain text."""
        lines = [
            "BRAID Performance Report",
            "=" * 40,
            f"Architect: {self.architect_model}",
            f"Solver: {self.solver_model}",
            "",
            "Cost Breakdown:",
            f"  Planning:  ${analysis.planning_cost_usd:.6f}",
            f"  Execution: ${analysis.execution_cost_usd:.6f}",
            f"  Total:     ${analysis.total_cost_usd:.6f}",
            "",
            f"Total Tokens: {analysis.total_tokens}",
            f"Accuracy: {accuracy:.1%}",
            f"PPD Score: {self.calculate_ppd_score(accuracy):.2f}",
        ]

        if baseline_model:
            report = self.compare_with_baseline(accuracy, baseline_model)
            lines.extend(
                [
                    "",
                    f"vs {baseline_model}:",
                    f"  Efficiency: {report.efficiency_multiplier:.2f}x",
                ]
            )

        return "\n".join(lines)

    def reset(self) -> None:
        """Reset all tracking data."""
        self.usage_log = []
        self._session_start = datetime.now()


class LatencyTracker:
    """Context manager for tracking operation latency."""

    def __init__(self):
        self.start_time: float = 0.0
        self.end_time: float = 0.0

    def __enter__(self) -> "LatencyTracker":
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args) -> None:
        self.end_time = time.perf_counter()

    @property
    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds."""
        return (self.end_time - self.start_time) * 1000
