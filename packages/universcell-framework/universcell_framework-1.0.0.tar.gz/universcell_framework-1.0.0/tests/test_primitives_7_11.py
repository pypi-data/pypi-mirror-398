"""
Consolidated test suite for Primitives 7-11 (TimeWindow, DistributedVariable, 
ParameterizedTemplate, DerivedVariable, ReactiveConstraint)

This file aggregates all tests for the core primitives 7-11 from:
- test_timewindow.py (Primitive 7)
- test_distributed_variable.py (Primitive 8)
- test_parameterized_template.py (Primitive 9)
- test_derived_variable.py (Primitive 10)
- test_day4_iot_retest.py (Integration tests)
- test_day2_finance_retest.py (Integration tests)

Total: 129 tests covering all primitives 7-10 functionality
"""

# Import all test classes from individual test files
from test_timewindow import (
    TestDurationParsing,
    TestAggregationCount,
    TestAggregationNumeric,
    TestAggregationPercentile,
    TestWindowPruning,
    TestConstraintEvaluation as TimeWindowConstraintEvaluation,
    TestRealWorldScenarios as TimeWindowRealWorldScenarios,
    TestMetrics as TimeWindowMetrics,
    TestReset as TimeWindowReset,
    TestEdgeCases as TimeWindowEdgeCases,
)

from test_distributed_variable import (
    TestConsensusThreshold,
    TestMajority,
    TestUnanimous,
    TestQuorum,
    TestEventual,
    TestObservationTracking,
    TestRealWorldScenarios as DistributedVariableRealWorldScenarios,
    TestMetrics as DistributedVariableMetrics,
    TestInstanceHealth,
    TestReset as DistributedVariableReset,
    TestEdgeCases as DistributedVariableEdgeCases,
)

from test_parameterized_template import (
    TestBasicSubstitution,
    TestInstanceIDGeneration,
    TestCartesianProduct,
    TestInstanceGeneration,
    TestConstraintEvaluation as ParameterizedTemplateConstraintEvaluation,
    TestRealWorldScenarios as ParameterizedTemplateRealWorldScenarios,
    TestTemplateFactory,
    TestMetrics as ParameterizedTemplateMetrics,
    TestReset as ParameterizedTemplateReset,
    TestEdgeCases as ParameterizedTemplateEdgeCases,
)

from test_derived_variable import (
    TestFormulaComputation,
    TestTimeseriesAggregation,
    TestMLModelInference,
    TestHistoricalBaseline,
    TestCaching,
    TestRealWorldScenarios as DerivedVariableRealWorldScenarios,
    TestHistory,
    TestMetrics as DerivedVariableMetrics,
    TestReset as DerivedVariableReset,
    TestEdgeCases as DerivedVariableEdgeCases,
)

from test_day4_iot_retest import (
    TestDay4IoTRegressionComplete,
    TestDay4ConfidenceProjection,
    TestDay4VsOriginal,
)

from test_day2_finance_retest import (
    TestDay2FinanceRegressionComplete,
    TestDay2ConfidenceProjection,
    TestDay2VsOriginal,
)

from test_reactive_constraint import (
    TestValueChangeTrigger,
    TestThresholdBreach,
    TestPatternMatching,
    TestStateTransition,
    TestSuppressionCooldown,
    TestSuppressionExponentialBackoff,
    TestConstraintEvaluation as ReactiveConstraintEvaluation,
    TestRealWorldScenarios as ReactiveConstraintRealWorldScenarios,
    TestMetrics as ReactiveConstraintMetrics,
    TestReset as ReactiveConstraintReset,
)


__all__ = [
    # TimeWindow tests (Primitive 7)
    "TestDurationParsing",
    "TestAggregationCount",
    "TestAggregationNumeric",
    "TestAggregationPercentile",
    "TestWindowPruning",
    "TimeWindowConstraintEvaluation",
    "TimeWindowRealWorldScenarios",
    "TimeWindowMetrics",
    "TimeWindowReset",
    "TimeWindowEdgeCases",
    
    # DistributedVariable tests (Primitive 8)
    "TestConsensusThreshold",
    "TestMajority",
    "TestUnanimous",
    "TestQuorum",
    "TestEventual",
    "TestObservationTracking",
    "DistributedVariableRealWorldScenarios",
    "DistributedVariableMetrics",
    "TestInstanceHealth",
    "DistributedVariableReset",
    "DistributedVariableEdgeCases",
    
    # ParameterizedTemplate tests (Primitive 9)
    "TestBasicSubstitution",
    "TestInstanceIDGeneration",
    "TestCartesianProduct",
    "TestInstanceGeneration",
    "ParameterizedTemplateConstraintEvaluation",
    "ParameterizedTemplateRealWorldScenarios",
    "TestTemplateFactory",
    "ParameterizedTemplateMetrics",
    "ParameterizedTemplateReset",
    "ParameterizedTemplateEdgeCases",
    
    # DerivedVariable tests (Primitive 10)
    "TestFormulaComputation",
    "TestTimeseriesAggregation",
    "TestMLModelInference",
    "TestHistoricalBaseline",
    "TestCaching",
    "DerivedVariableRealWorldScenarios",
    "TestHistory",
    "DerivedVariableMetrics",
    "DerivedVariableReset",
    "DerivedVariableEdgeCases",
    
    # ReactiveConstraint tests (Primitive 11)
    "TestValueChangeTrigger",
    "TestThresholdBreach",
    "TestPatternMatching",
    "TestStateTransition",
    "TestSuppressionCooldown",
    "TestSuppressionExponentialBackoff",
    "ReactiveConstraintEvaluation",
    "ReactiveConstraintRealWorldScenarios",
    "ReactiveConstraintMetrics",
    "ReactiveConstraintReset",
    
    # Integration tests
    "TestDay4IoTRegressionComplete",
    "TestDay4ConfidenceProjection",
    "TestDay4VsOriginal",
    "TestDay2FinanceRegressionComplete",
    "TestDay2ConfidenceProjection",
    "TestDay2VsOriginal",
]
