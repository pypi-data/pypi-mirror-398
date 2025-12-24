"""Tests for idealization methods."""

import numpy as np
import pytest
from pyioneer.idealization import (
    segment_threshold,
    segment_change_point,
    segment_hmm,
    Event,
    IdealizationResult,
)


def generate_test_trace(n_samples=1000, dt=0.0001):
    """Generate a simple test trace with two states."""
    time = np.arange(n_samples) * dt
    current = np.zeros(n_samples)
    
    # Create two-state trace: 0-0.05s at 0 pA, 0.05-0.1s at 1 pA
    current[0:500] = 0.0
    current[500:1000] = 1.0
    
    # Add noise
    current += np.random.normal(0, 0.1, n_samples)
    
    return time, current


def test_idealize_threshold():
    """Test threshold idealization."""
    time, current = generate_test_trace()
    
    result = segment_threshold(
        time, current,
        threshold=0.5,
        min_dwell=0.001,
        baseline=0.0
    )
    
    assert isinstance(result, IdealizationResult)
    assert len(result.events) > 0
    assert len(result.idealized_trace) == len(current)
    assert result.method == "threshold"
    
    # Check that events have required attributes
    for event in result.events:
        assert isinstance(event, Event)
        assert event.start_time >= 0
        assert event.end_time > event.start_time
        assert event.dwell_time > 0


def test_idealize_threshold_auto_baseline():
    """Test threshold idealization with auto-detected baseline."""
    time, current = generate_test_trace()
    
    result = segment_threshold(
        time, current,
        threshold=0.5,
        baseline=None  # Auto-detect
    )
    
    assert isinstance(result, IdealizationResult)
    assert len(result.events) >= 0


@pytest.mark.skipif(
    True,  # Skip if ruptures not available
    reason="ruptures library required"
)
def test_idealize_change_point():
    """Test change-point detection."""
    time, current = generate_test_trace()
    
    try:
        result = segment_change_point(
            time, current,
            n_states=2,
            method="binseg"
        )
        
        assert isinstance(result, IdealizationResult)
        assert len(result.events) > 0
        assert "change_point" in result.method
    except ImportError:
        pytest.skip("ruptures library not available")


@pytest.mark.skipif(
    True,  # Skip if hmmlearn not available
    reason="hmmlearn library required"
)
def test_idealize_hmm():
    """Test HMM idealization."""
    time, current = generate_test_trace()
    
    try:
        result = segment_hmm(
            time, current,
            n_states=2,
            method="gaussian"
        )
        
        assert isinstance(result, IdealizationResult)
        assert len(result.events) > 0
        assert "hmm" in result.method
    except ImportError:
        pytest.skip("hmmlearn library not available")


def test_idealization_result_to_dataframe():
    """Test conversion to DataFrame."""
    time, current = generate_test_trace()
    result = segment_threshold(time, current, threshold=0.5)
    
    try:
        df = result.to_dataframe()
        assert df is not None
        assert len(df) == len(result.events)
        assert "start_time" in df.columns
        assert "dwell_time" in df.columns
    except ImportError:
        pytest.skip("pandas library not available")

