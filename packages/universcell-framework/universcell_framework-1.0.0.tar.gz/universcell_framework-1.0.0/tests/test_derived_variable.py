"""
Unit tests for DerivedVariable primitive

Tests cover:
- Formula computation
- Timeseries aggregation (max, min, avg, percentile)
- ML model inference
- Historical baseline
- Caching with TTL
- Real-world scenarios (Finance VaR, Healthcare baseline, IoT anomaly)
"""

import pytest
import time
from universalengine.primitives.derived_variable import (
    DerivedVariable,
    ComputationType
)


class TestFormulaComputation:
    """Test mathematical formula evaluation"""
    
    def test_simple_formula(self):
        """Evaluate simple arithmetic expression"""
        dv = DerivedVariable(
            name="test",
            source="value",
            computation={
                "type": "formula",
                "formula": "value * 2"
            }
        )
        
        result = dv.compute(observations={"value": 42})
        assert result["value"] == 84
        assert result["status"] == "SUCCESS"
    
    def test_complex_formula(self):
        """Evaluate complex formula with multiple variables"""
        dv = DerivedVariable(
            name="normalized",
            source=["price"],
            computation={
                "type": "formula",
                "formula": "(price - min_price) / (max_price - min_price)"
            }
        )
        
        obs = {"price": 50, "min_price": 0, "max_price": 100}
        result = dv.compute(observations=obs)
        assert result["value"] == 0.5
    
    def test_formula_with_functions(self):
        """Formula can use built-in math functions"""
        dv = DerivedVariable(
            name="sqrt_test",
            source=["value"],
            computation={
                "type": "formula",
                "formula": "value ** 0.5"  # Square root
            }
        )
        
        result = dv.compute(observations={"value": 16})
        assert result["value"] == 4.0
    
    def test_formula_error(self):
        """Handle formula evaluation errors"""
        dv = DerivedVariable(
            name="bad_formula",
            source="value",
            computation={
                "type": "formula",
                "formula": "value / 0"  # Division by zero
            }
        )
        
        result = dv.compute(observations={"value": 10})
        assert result["status"] == "ERROR"


class TestTimeseriesAggregation:
    """Test timeseries aggregation functions"""
    
    def test_max_aggregation(self):
        """Find maximum value in history"""
        dv = DerivedVariable(
            name="max_price",
            source="price",
            computation={
                "type": "timeseries_aggregate",
                "function": "max"
            }
        )
        
        history = [
            {"price": 100},
            {"price": 105},
            {"price": 95},
            {"price": 110}
        ]
        
        result = dv.compute(observations={}, history=history)
        assert result["value"] == 110
    
    def test_min_aggregation(self):
        """Find minimum value in history"""
        dv = DerivedVariable(
            name="min_price",
            source="price",
            computation={
                "type": "timeseries_aggregate",
                "function": "min"
            }
        )
        
        history = [{"price": 100}, {"price": 95}, {"price": 110}]
        result = dv.compute(observations={}, history=history)
        assert result["value"] == 95
    
    def test_avg_aggregation(self):
        """Average of values"""
        dv = DerivedVariable(
            name="avg_price",
            source="price",
            computation={
                "type": "timeseries_aggregate",
                "function": "avg"
            }
        )
        
        history = [{"price": 100}, {"price": 110}, {"price": 90}]
        result = dv.compute(observations={}, history=history)
        assert result["value"] == 100.0
    
    def test_percentile_aggregation(self):
        """95th percentile of values"""
        dv = DerivedVariable(
            name="price_p95",
            source="price",
            computation={
                "type": "timeseries_aggregate",
                "function": "percentile",
                "parameters": {"percentile": 0.95}
            },
            cache=False
        )
        
        history = [{"price": float(i)} for i in range(100)]  # 0-99
        result = dv.compute(observations={}, history=history)
        
        # 95th percentile of 0-99 should be around 95
        assert result["status"] == "SUCCESS"
        assert result["value"] is not None
        assert 94 <= result["value"] <= 96
    
    def test_stddev_aggregation(self):
        """Standard deviation"""
        dv = DerivedVariable(
            name="price_stddev",
            source="price",
            computation={
                "type": "timeseries_aggregate",
                "function": "stddev"
            }
        )
        
        history = [{"price": 100}, {"price": 110}, {"price": 120}]
        result = dv.compute(observations={}, history=history)
        
        # Stddev of [100, 110, 120]
        mean = 110
        variance = ((100-110)**2 + (110-110)**2 + (120-110)**2) / 2
        expected_stddev = variance ** 0.5
        
        assert abs(result["value"] - expected_stddev) < 0.01
    
    def test_median_aggregation(self):
        """Median value"""
        dv = DerivedVariable(
            name="price_median",
            source="price",
            computation={
                "type": "timeseries_aggregate",
                "function": "median"
            }
        )
        
        history = [{"price": 100}, {"price": 110}, {"price": 105}]
        result = dv.compute(observations={}, history=history)
        assert result["value"] == 105


class TestMLModelInference:
    """Test ML model computation"""
    
    def test_ml_model_computation(self):
        """Placeholder ML model inference"""
        dv = DerivedVariable(
            name="anomaly_score",
            source=["sensor1", "sensor2"],
            computation={
                "type": "ml_model",
                "model_id": "isolation_forest_v2",
                "parameters": {"contamination": 0.1}
            }
        )
        
        obs = {"sensor1": 0.5, "sensor2": 0.3}
        result = dv.compute(observations=obs)
        
        assert result["status"] == "SUCCESS"
        assert 0 <= result["value"] <= 1  # Score between 0-1
    
    def test_ml_model_missing_id(self):
        """Error if model_id not specified"""
        dv = DerivedVariable(
            name="bad_ml",
            source="data",
            computation={"type": "ml_model"}
        )
        
        result = dv.compute(observations={"data": 42})
        assert result["status"] == "ERROR"


class TestHistoricalBaseline:
    """Test baseline computation"""
    
    def test_baseline_mean(self):
        """Compute mean as baseline"""
        dv = DerivedVariable(
            name="patient_baseline_hr",
            source="heart_rate",
            computation={
                "type": "historical_baseline",
                "parameters": {"method": "mean"}
            }
        )
        
        history = [
            {"heart_rate": 60},
            {"heart_rate": 62},
            {"heart_rate": 58}
        ]
        
        result = dv.compute(observations={}, history=history)
        assert result["value"] == 60.0
    
    def test_baseline_median(self):
        """Compute median as baseline"""
        dv = DerivedVariable(
            name="baseline",
            source="value",
            computation={
                "type": "historical_baseline",
                "parameters": {"method": "median"}
            }
        )
        
        history = [{"value": 10}, {"value": 20}, {"value": 30}]
        result = dv.compute(observations={}, history=history)
        assert result["value"] == 20


class TestCaching:
    """Test result caching"""
    
    def test_cache_hit(self):
        """Cache result on second call"""
        dv = DerivedVariable(
            name="cached",
            source="value",
            computation={
                "type": "formula",
                "formula": "value * 2"
            },
            cache=True,
            ttl=3600
        )
        
        # First call: cache miss
        result1 = dv.compute(observations={"value": 10})
        assert result1["cached"] == False
        assert dv.cache_miss_count == 1
        
        # Second call: cache hit
        result2 = dv.compute(observations={"value": 10})
        assert result2["cached"] == True
        assert dv.cache_hit_count == 1
        assert result2["value"] == result1["value"]
    
    def test_cache_ttl_expiry(self):
        """Cache expires after TTL"""
        dv = DerivedVariable(
            name="expiring_cache",
            source="value",
            computation={
                "type": "formula",
                "formula": "value * 2"
            },
            cache=True,
            ttl=1  # 1 second TTL
        )
        
        # First call
        result1 = dv.compute(observations={"value": 10})
        assert result1["cached"] == False
        
        # Immediate second call: should hit cache
        result2 = dv.compute(observations={"value": 10})
        assert result2["cached"] == True
        
        # Wait for TTL to expire
        time.sleep(1.1)
        
        # Third call: cache expired, recompute
        result3 = dv.compute(observations={"value": 10})
        assert result3["cached"] == False
    
    def test_force_recompute(self):
        """Force recompute even with valid cache"""
        dv = DerivedVariable(
            name="force_recompute",
            source="value",
            computation={
                "type": "formula",
                "formula": "value * 2"
            },
            cache=True
        )
        
        dv.compute(observations={"value": 10})
        
        # Force recompute despite cache
        result = dv.compute(observations={"value": 10}, force_recompute=True)
        assert result["cached"] == False


class TestRealWorldScenarios:
    """Test realistic domain scenarios"""
    
    def test_day2_finance_var_95(self):
        """Day 2: Value at Risk (95th percentile loss)"""
        dv = DerivedVariable(
            name="var_95_confidence",
            source="daily_returns",
            computation={
                "type": "timeseries_aggregate",
                "function": "percentile",
                "parameters": {"percentile": 0.05}  # 5th percentile = 95% VaR
            }
        )
        
        # Simulate 30 days of returns (mostly positive with some losses)
        history = [
            {"daily_returns": -0.03},  # Worst case
            {"daily_returns": -0.02},
            {"daily_returns": -0.01},
            {"daily_returns": 0.0},
        ] + [
            {"daily_returns": 0.01} for _ in range(10)  # Moderate gains
        ] + [
            {"daily_returns": 0.02} for _ in range(15)  # Better days
        ]
        
        result = dv.compute(observations={}, history=history)
        
        # VaR should be worst 5th percentile loss
        assert result["status"] == "SUCCESS"
        assert result["value"] is not None
        assert result["value"] < 0  # Losses are negative
    
    def test_day3_healthcare_baseline_hr(self):
        """Day 3: Patient baseline heart rate from 7 days"""
        dv = DerivedVariable(
            name="patient_baseline_hr",
            source="heart_rate",
            computation={
                "type": "historical_baseline",
                "parameters": {"method": "mean"}
            },
            description="7-day average heart rate baseline"
        )
        
        # Simulate 7 days of readings
        history = [{"heart_rate": 60 + i} for i in range(7)]  # 60-66
        
        result = dv.compute(observations={}, history=history)
        
        # Baseline should be ~63
        assert 62 <= result["value"] <= 64
    
    def test_day4_iot_anomaly_score(self):
        """Day 4: Anomaly detection score for sensor readings"""
        dv = DerivedVariable(
            name="sensor_anomaly_score",
            source=["temp", "humidity", "co2"],
            computation={
                "type": "ml_model",
                "model_id": "isolation_forest_sensor_v1",
                "parameters": {"contamination": 0.05}
            }
        )
        
        # Normal sensor readings
        obs = {"temp": 22.5, "humidity": 45, "co2": 600}
        result = dv.compute(observations=obs)
        
        assert result["status"] == "SUCCESS"
        assert 0 <= result["value"] <= 1


class TestHistory:
    """Test history tracking"""
    
    def test_history_tracking(self):
        """Values added to history on each computation"""
        dv = DerivedVariable(
            name="test",
            source="value",
            computation={
                "type": "formula",
                "formula": "value * 2"
            },
            cache=False
        )
        
        dv.compute(observations={"value": 10})
        dv.compute(observations={"value": 20})
        dv.compute(observations={"value": 30})
        
        # History should contain all 3 computed values
        assert len(dv.value_history) == 3
        assert dv.value_history[0][1] == 20
        assert dv.value_history[1][1] == 40
        assert dv.value_history[2][1] == 60
    
    def test_manual_history_addition(self):
        """Add historical data points manually"""
        dv = DerivedVariable(
            name="test",
            source="value",
            computation={"type": "formula", "formula": "value"}
        )
        
        dv.add_history_point(timestamp=1000, value=42)
        dv.add_history_point(timestamp=2000, value=84)
        
        assert len(dv.value_history) == 2


class TestMetrics:
    """Test internal metrics"""
    
    def test_cache_metrics(self):
        """Track cache hit/miss rates"""
        dv = DerivedVariable(
            name="test",
            source="value",
            computation={
                "type": "formula",
                "formula": "value * 2"
            },
            cache=True
        )
        
        dv.compute(observations={"value": 10})  # miss
        dv.compute(observations={"value": 10})  # hit
        dv.compute(observations={"value": 10})  # hit
        
        metrics = dv.get_metrics()
        assert metrics["cache_miss_count"] == 1
        assert metrics["cache_hit_count"] == 2
        assert metrics["cache_hit_rate"] == pytest.approx(0.667, abs=0.01)


class TestReset:
    """Test reset functionality"""
    
    def test_reset_clears_cache_and_history(self):
        """Reset clears all cached data"""
        dv = DerivedVariable(
            name="test",
            source="value",
            computation={
                "type": "formula",
                "formula": "value * 2"
            },
            cache=True
        )
        
        dv.compute(observations={"value": 10})
        dv.compute(observations={"value": 20})
        
        assert len(dv.value_history) > 0
        assert dv.cached_value is not None
        
        dv.reset()
        
        assert len(dv.value_history) == 0
        assert dv.cached_value is None
        assert dv.cache_hit_count == 0


class TestEdgeCases:
    """Test edge cases"""
    
    def test_empty_history(self):
        """Aggregation with empty history"""
        dv = DerivedVariable(
            name="test",
            source="value",
            computation={
                "type": "timeseries_aggregate",
                "function": "max"
            }
        )
        
        result = dv.compute(observations={}, history=[])
        assert result["value"] is None
    
    def test_missing_source_in_history(self):
        """Source variable not in history entries"""
        dv = DerivedVariable(
            name="test",
            source="missing_var",
            computation={
                "type": "timeseries_aggregate",
                "function": "max"
            }
        )
        
        history = [{"other_var": 100}]
        result = dv.compute(observations={}, history=history)
        assert result["value"] is None
    
    def test_single_value_stddev(self):
        """Standard deviation of single value"""
        dv = DerivedVariable(
            name="test",
            source="value",
            computation={
                "type": "timeseries_aggregate",
                "function": "stddev"
            }
        )
        
        history = [{"value": 42}]
        result = dv.compute(observations={}, history=history)
        assert result["value"] == 0.0
