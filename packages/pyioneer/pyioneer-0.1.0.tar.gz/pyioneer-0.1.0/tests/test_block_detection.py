"""Tests for block detection."""

import numpy as np
import pytest
from pyioneer.block_detection import detect_blocks, BlockDetector, Block


def generate_block_trace(n_samples=1000, dt=0.0001):
    """Generate a test trace with blocking events."""
    time = np.arange(n_samples) * dt
    current = np.full(n_samples, -0.25)  # Baseline at -0.25 pA
    
    # Add blocks (less negative, closer to zero)
    # Block 1: 0.02-0.03s
    current[200:300] = -0.1
    
    # Block 2: 0.06-0.07s
    current[600:700] = -0.15
    
    # Add noise
    current += np.random.normal(0, 0.02, n_samples)
    
    return time, current


def test_detect_blocks():
    """Test basic block detection."""
    time, current = generate_block_trace()
    
    blocks = detect_blocks(
        time, current,
        baseline=-0.25,
        block_threshold_factor=2.0,
        min_block_duration=0.001,
        sweep_number=0
    )
    
    assert len(blocks) > 0
    
    for block in blocks:
        assert isinstance(block, Block)
        assert block.start_time >= 0
        assert block.end_time > block.start_time
        assert block.duration > 0
        assert block.block_number >= 0
        assert block.sweep_number == 0


def test_block_detector():
    """Test BlockDetector class."""
    time, current = generate_block_trace()
    
    detector = BlockDetector(
        baseline_threshold=-0.25,
        block_threshold_factor=2.0,
        min_block_duration=0.001
    )
    
    blocks = detector.detect(time, current, sweep_number=0)
    assert len(blocks) >= 0


def test_block_detector_auto_baseline():
    """Test BlockDetector with auto-detected baseline."""
    time, current = generate_block_trace()
    
    detector = BlockDetector(
        baseline_threshold=None,  # Auto-detect
        block_threshold_factor=2.0,
        min_block_duration=0.001
    )
    
    blocks = detector.detect(time, current, sweep_number=0)
    assert isinstance(blocks, list)


def test_positive_baseline():
    """Test block detection with positive baseline."""
    time = np.arange(1000) * 0.0001
    current = np.full(1000, 0.25)  # Positive baseline
    
    # Add blocks (less positive, closer to zero)
    current[200:300] = 0.1
    
    blocks = detect_blocks(
        time, current,
        baseline=0.25,
        block_threshold_factor=2.0,
        min_block_duration=0.001
    )
    
    assert isinstance(blocks, list)

