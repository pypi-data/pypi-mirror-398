"""Tests for the statistical evaluator."""

import pytest
from datetime import datetime

from evalview.core.types import (
    VarianceConfig,
    StatisticalMetrics,
    TestCase,
    TestInput,
    ExpectedBehavior,
    Thresholds,
    EvaluationResult,
    Evaluations,
    ToolEvaluation,
    SequenceEvaluation,
    OutputEvaluation,
    ContainsChecks,
    CostEvaluation,
    LatencyEvaluation,
    ExecutionTrace,
    ExecutionMetrics,
)
from evalview.evaluators.statistical_evaluator import (
    compute_statistical_metrics,
    compute_flakiness_score,
    StatisticalEvaluator,
    is_statistical_mode,
)


class TestComputeStatisticalMetrics:
    """Tests for compute_statistical_metrics function."""

    def test_basic_metrics(self):
        """Test basic statistical metrics computation."""
        values = [70, 75, 80, 85, 90]
        stats = compute_statistical_metrics(values)

        assert stats.mean == 80.0
        assert stats.min_value == 70.0
        assert stats.max_value == 90.0
        assert stats.median == 80.0

    def test_confidence_interval(self):
        """Test confidence interval computation."""
        values = [75, 76, 77, 78, 79, 80, 81, 82, 83, 84]
        stats = compute_statistical_metrics(values, confidence_level=0.95)

        # Mean should be 79.5
        assert stats.mean == 79.5
        # CI should contain the mean
        assert stats.confidence_interval_lower < stats.mean
        assert stats.confidence_interval_upper > stats.mean

    def test_single_value(self):
        """Test with single value (std dev should be 0)."""
        values = [85.0]
        stats = compute_statistical_metrics(values)

        assert stats.mean == 85.0
        assert stats.std_dev == 0.0
        assert stats.variance == 0.0

    def test_empty_list_raises(self):
        """Test that empty list raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            compute_statistical_metrics([])

    def test_percentiles(self):
        """Test percentile calculations."""
        values = list(range(1, 101))  # 1 to 100
        stats = compute_statistical_metrics(values)

        assert stats.percentile_25 == 25.75
        assert stats.median == 50.5
        assert stats.percentile_75 == 75.25


class TestIsStatisticalMode:
    """Tests for is_statistical_mode function."""

    def test_with_variance_config(self):
        """Test detection when variance config is present."""
        test_case = TestCase(
            name="test",
            input=TestInput(query="test"),
            expected=ExpectedBehavior(),
            thresholds=Thresholds(min_score=70, variance=VarianceConfig(runs=5)),
        )
        assert is_statistical_mode(test_case) is True

    def test_without_variance_config(self):
        """Test detection when variance config is absent."""
        test_case = TestCase(
            name="test",
            input=TestInput(query="test"),
            expected=ExpectedBehavior(),
            thresholds=Thresholds(min_score=70),
        )
        assert is_statistical_mode(test_case) is False


class TestVarianceConfig:
    """Tests for VarianceConfig validation."""

    def test_default_values(self):
        """Test default configuration values."""
        config = VarianceConfig()
        assert config.runs == 10
        assert config.pass_rate == 0.8
        assert config.confidence_level == 0.95

    def test_custom_values(self):
        """Test custom configuration values."""
        config = VarianceConfig(
            runs=20,
            pass_rate=0.9,
            min_mean_score=75,
            max_std_dev=10,
        )
        assert config.runs == 20
        assert config.pass_rate == 0.9
        assert config.min_mean_score == 75
        assert config.max_std_dev == 10

    def test_runs_validation(self):
        """Test that runs must be between 2 and 100."""
        with pytest.raises(ValueError):
            VarianceConfig(runs=1)  # Too low

        with pytest.raises(ValueError):
            VarianceConfig(runs=101)  # Too high

    def test_pass_rate_validation(self):
        """Test that pass_rate must be between 0 and 1."""
        with pytest.raises(ValueError):
            VarianceConfig(pass_rate=-0.1)

        with pytest.raises(ValueError):
            VarianceConfig(pass_rate=1.1)


class TestComputeFlakinessScore:
    """Tests for compute_flakiness_score function."""

    def _make_result(self, passed: bool, score: float) -> EvaluationResult:
        """Helper to create a mock evaluation result."""
        return EvaluationResult(
            test_case="test",
            passed=passed,
            score=score,
            evaluations=Evaluations(
                tool_accuracy=ToolEvaluation(
                    accuracy=1.0, correct=["tool1"], missing=[], unexpected=[]
                ),
                sequence_correctness=SequenceEvaluation(
                    correct=True, expected_sequence=[], actual_sequence=[]
                ),
                output_quality=OutputEvaluation(
                    score=score,
                    rationale="test",
                    contains_checks=ContainsChecks(),
                    not_contains_checks=ContainsChecks(),
                ),
                cost=CostEvaluation(total_cost=0.01, threshold=1.0, passed=True),
                latency=LatencyEvaluation(total_latency=100, threshold=5000, passed=True),
            ),
            trace=ExecutionTrace(
                session_id="test",
                start_time=datetime.now(),
                end_time=datetime.now(),
                steps=[],
                final_output="test",
                metrics=ExecutionMetrics(total_cost=0.01, total_latency=100),
            ),
            timestamp=datetime.now(),
        )

    def test_stable_test(self):
        """Test flakiness score for stable test (all pass, low variance)."""
        results = [self._make_result(True, 85) for _ in range(10)]
        stats = compute_statistical_metrics([r.score for r in results])
        flakiness = compute_flakiness_score(results, stats)

        assert flakiness.score < 0.1
        assert flakiness.category == "stable"
        assert flakiness.pass_rate == 1.0

    def test_flaky_test(self):
        """Test flakiness score for flaky test (mixed pass/fail)."""
        results = [
            self._make_result(True, 85),
            self._make_result(False, 45),
            self._make_result(True, 90),
            self._make_result(False, 50),
            self._make_result(True, 80),
        ]
        stats = compute_statistical_metrics([r.score for r in results])
        flakiness = compute_flakiness_score(results, stats)

        assert flakiness.score > 0.3
        assert flakiness.pass_rate == 0.6
        assert len(flakiness.contributing_factors) > 0


class TestStatisticalEvaluator:
    """Tests for StatisticalEvaluator class."""

    def test_evaluate_from_results(self):
        """Test computing stats from pre-existing results."""
        evaluator = StatisticalEvaluator()

        # Create mock results
        results = []
        for i, (passed, score) in enumerate([
            (True, 85), (True, 82), (True, 88),
            (True, 79), (False, 65), (True, 84),
            (True, 86), (True, 81), (True, 83), (True, 87),
        ]):
            results.append(EvaluationResult(
                test_case="test",
                passed=passed,
                score=score,
                evaluations=Evaluations(
                    tool_accuracy=ToolEvaluation(
                        accuracy=1.0, correct=["tool1"], missing=[], unexpected=[]
                    ),
                    sequence_correctness=SequenceEvaluation(
                        correct=True, expected_sequence=[], actual_sequence=[]
                    ),
                    output_quality=OutputEvaluation(
                        score=score,
                        rationale="test",
                        contains_checks=ContainsChecks(),
                        not_contains_checks=ContainsChecks(),
                    ),
                    cost=CostEvaluation(total_cost=0.01, threshold=1.0, passed=True),
                    latency=LatencyEvaluation(total_latency=100, threshold=5000, passed=True),
                ),
                trace=ExecutionTrace(
                    session_id=f"test-{i}",
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    steps=[],
                    final_output="test",
                    metrics=ExecutionMetrics(total_cost=0.01, total_latency=100),
                ),
                timestamp=datetime.now(),
            ))

        test_case = TestCase(
            name="test",
            input=TestInput(query="test"),
            expected=ExpectedBehavior(),
            thresholds=Thresholds(min_score=70, variance=VarianceConfig(runs=10, pass_rate=0.8)),
        )

        stat_result = evaluator.evaluate_from_results(test_case, results)

        assert stat_result.total_runs == 10
        assert stat_result.successful_runs == 9
        assert stat_result.failed_runs == 1
        assert stat_result.pass_rate == 0.9
        assert stat_result.passed is True  # 90% > 80% required
        assert stat_result.score_stats.mean > 80
