"""Unit tests for the metrics module."""

import pytest
from braid.metrics import (
    PPDAnalyzer,
    TokenUsage,
    CostAnalysis,
    PPDReport,
    ModelConfig,
    LatencyTracker,
)


class TestTokenUsage:
    """Tests for TokenUsage dataclass."""

    def test_token_usage_creation(self):
        """Test creating a TokenUsage object."""
        usage = TokenUsage(prompt_tokens=100, completion_tokens=50)

        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.total_tokens == 150

    def test_token_usage_with_total(self):
        """Test creating TokenUsage with explicit total."""
        usage = TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=200)

        assert usage.total_tokens == 200  # Explicit value used


class TestPPDAnalyzer:
    """Tests for PPDAnalyzer class."""

    def test_initialization(self):
        """Test analyzer initialization."""
        analyzer = PPDAnalyzer(architect_model="gpt-4", solver_model="gpt-3.5-turbo")

        assert analyzer.architect_model == "gpt-4"
        assert analyzer.solver_model == "gpt-3.5-turbo"

    def test_get_model_config_known(self):
        """Test getting config for a known model."""
        analyzer = PPDAnalyzer()

        config = analyzer.get_model_config("gpt-4")

        assert config.model_id == "gpt-4"
        assert config.input_cost_per_1m > 0
        assert config.output_cost_per_1m > 0

    def test_get_model_config_unknown(self):
        """Test getting config for an unknown model."""
        analyzer = PPDAnalyzer()

        config = analyzer.get_model_config("unknown-model-xyz")

        assert config.model_id == "unknown-model-xyz"
        assert config.provider == "unknown"

    def test_calculate_cost(self):
        """Test cost calculation."""
        analyzer = PPDAnalyzer()
        usage = TokenUsage(prompt_tokens=1000, completion_tokens=500)

        cost = analyzer.calculate_cost(usage, "gpt-4")

        assert cost > 0
        # GPT-4: $30/1M input, $60/1M output
        # Expected: (1000/1M * 30) + (500/1M * 60) = 0.03 + 0.03 = 0.06
        assert 0.05 < cost < 0.07

    def test_track_usage(self):
        """Test tracking usage."""
        analyzer = PPDAnalyzer()

        metrics = analyzer.track_usage(TokenUsage(500, 200), phase="planning", step_id="step_1")

        assert metrics.step_id == "step_1"
        assert metrics.phase == "planning"
        assert metrics.cost_usd > 0

    def test_get_cost_analysis(self):
        """Test getting complete cost analysis."""
        analyzer = PPDAnalyzer(architect_model="gpt-4", solver_model="gpt-3.5-turbo")

        analyzer.track_usage(TokenUsage(500, 200), "planning")
        analyzer.track_usage(TokenUsage(100, 50), "execution")
        analyzer.track_usage(TokenUsage(100, 50), "execution")

        analysis = analyzer.get_cost_analysis()

        assert analysis.total_cost_usd > 0
        assert analysis.planning_cost_usd > 0
        assert analysis.execution_cost_usd > 0
        assert analysis.total_tokens == 1000

    def test_calculate_ppd_score(self):
        """Test PPD score calculation."""
        analyzer = PPDAnalyzer()
        analyzer.track_usage(TokenUsage(1000, 500), "planning")

        ppd = analyzer.calculate_ppd_score(accuracy=0.95)

        assert ppd > 0

    def test_calculate_ppd_score_zero_cost(self):
        """Test PPD score with zero cost."""
        analyzer = PPDAnalyzer()

        # No usage tracked, but using override
        ppd = analyzer.calculate_ppd_score(accuracy=0.95, total_cost=0)

        assert ppd == float("inf")

    def test_compare_with_baseline(self):
        """Test baseline comparison."""
        analyzer = PPDAnalyzer(architect_model="gpt-4", solver_model="gpt-3.5-turbo")

        analyzer.track_usage(TokenUsage(500, 200), "planning")
        analyzer.track_usage(TokenUsage(100, 50), "execution")

        report = analyzer.compare_with_baseline(accuracy=0.95, baseline_model="gpt-4")

        assert isinstance(report, PPDReport)
        assert report.accuracy == 0.95
        assert report.total_cost_usd > 0
        assert report.ppd_score > 0
        assert report.baseline_model == "gpt-4"

    def test_generate_report_markdown(self):
        """Test markdown report generation."""
        analyzer = PPDAnalyzer()
        analyzer.track_usage(TokenUsage(500, 200), "planning")

        report = analyzer.generate_report(accuracy=0.90, format="markdown")

        assert "# BRAID Performance Report" in report
        assert "Cost Breakdown" in report
        assert "Performance Metrics" in report

    def test_generate_report_text(self):
        """Test text report generation."""
        analyzer = PPDAnalyzer()
        analyzer.track_usage(TokenUsage(500, 200), "planning")

        report = analyzer.generate_report(accuracy=0.90, format="text")

        assert "BRAID Performance Report" in report
        assert "Total:" in report

    def test_reset(self):
        """Test resetting the analyzer."""
        analyzer = PPDAnalyzer()
        analyzer.track_usage(TokenUsage(500, 200), "planning")

        assert len(analyzer.usage_log) == 1

        analyzer.reset()

        assert len(analyzer.usage_log) == 0


class TestCostAnalysis:
    """Tests for CostAnalysis dataclass."""

    def test_cost_analysis_creation(self):
        """Test creating a CostAnalysis object."""
        analysis = CostAnalysis(
            total_cost_usd=0.05,
            planning_cost_usd=0.03,
            execution_cost_usd=0.02,
            total_tokens=1000,
            prompt_tokens=700,
            completion_tokens=300,
        )

        assert analysis.total_cost_usd == 0.05
        assert analysis.total_tokens == 1000


class TestPPDReport:
    """Tests for PPDReport dataclass."""

    def test_ppd_report_creation(self):
        """Test creating a PPDReport object."""
        report = PPDReport(
            accuracy=0.95,
            total_cost_usd=0.05,
            ppd_score=19.0,
            efficiency_multiplier=2.5,
            baseline_model="gpt-4",
        )

        assert report.accuracy == 0.95
        assert report.ppd_score == 19.0
        assert report.efficiency_multiplier == 2.5


class TestLatencyTracker:
    """Tests for LatencyTracker context manager."""

    def test_latency_tracking(self):
        """Test basic latency tracking."""
        import time

        with LatencyTracker() as tracker:
            time.sleep(0.01)  # 10ms

        assert tracker.elapsed_ms >= 10
        assert tracker.elapsed_ms < 100  # Shouldn't take more than 100ms

    def test_latency_no_work(self):
        """Test latency with minimal work."""
        with LatencyTracker() as tracker:
            pass

        assert tracker.elapsed_ms >= 0
        assert tracker.elapsed_ms < 10  # Should be very fast
