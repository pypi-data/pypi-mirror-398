"""
Block detection for single-channel recordings (adapted from synapse-abf).
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
import numpy as np
from scipy import stats


@dataclass
class Block:
    """Represents a detected block event."""
    block_number: int
    sweep_number: int
    start_time: float
    end_time: float
    duration: float
    average_amplitude: float
    baseline_amplitude: float
    block_depth: float
    voltage: Optional[float] = None  # Average voltage during block (mV)


class BlockDetector:
    """Detector for blocking events in single-channel recordings."""
    
    def __init__(
        self,
        baseline_threshold: Optional[float] = None,
        block_threshold_factor: float = 2.0,
        min_block_duration: float = 0.001,
    ):
        """Initialize block detector.
        
        Args:
            baseline_threshold: Baseline current level (None for auto-detect)
            block_threshold_factor: Sensitivity factor (higher = more conservative)
            min_block_duration: Minimum block duration in seconds
        """
        self.baseline_threshold = baseline_threshold
        self.block_threshold_factor = block_threshold_factor
        self.min_block_duration = min_block_duration
    
    def estimate_baseline(self, current: np.ndarray) -> float:
        """Estimate baseline from data distribution.
        
        Args:
            current: Current array
            
        Returns:
            Estimated baseline level
        """
        # Use mode or median of distribution
        hist, bins = np.histogram(current, bins=100)
        mode_idx = np.argmax(hist)
        baseline = (bins[mode_idx] + bins[mode_idx + 1]) / 2
        return baseline
    
    def detect(
        self,
        time: np.ndarray,
        current: np.ndarray,
        sweep_number: int = 0,
        baseline: Optional[float] = None,
        voltage: Optional[np.ndarray] = None,
    ) -> List[Block]:
        """Detect blocks in trace.
        
        Args:
            time: Time array
            current: Current array
            sweep_number: Sweep number for labeling
            baseline: Baseline level (uses detector's baseline if None)
            voltage: Optional voltage array (mV) for calculating average voltage per block
            
        Returns:
            List of Block objects
        """
        if baseline is None:
            baseline = self.baseline_threshold
            if baseline is None:
                baseline = self.estimate_baseline(current)
        
        # Determine block direction (toward zero)
        if baseline < 0:
            # Negative baseline: blocks are less negative (closer to zero)
            block_direction = 1  # positive direction
            threshold = baseline + abs(baseline) / self.block_threshold_factor
        else:
            # Positive baseline: blocks are less positive (closer to zero)
            block_direction = -1  # negative direction
            threshold = baseline - abs(baseline) / self.block_threshold_factor
        
        dt = time[1] - time[0]
        min_samples = int(self.min_block_duration / dt)
        
        # Detect blocks
        if block_direction > 0:
            # Blocks are above threshold (less negative)
            block_mask = current > threshold
        else:
            # Blocks are below threshold (less positive)
            block_mask = current < threshold
        
        # Find contiguous block regions
        blocks = []
        in_block = False
        block_start_idx = 0
        block_number = 0
        
        for i in range(len(block_mask)):
            if block_mask[i] and not in_block:
                # Start of block
                in_block = True
                block_start_idx = i
            elif not block_mask[i] and in_block:
                # End of block
                block_end_idx = i
                block_duration = (block_end_idx - block_start_idx) * dt
                
                if block_duration >= self.min_block_duration:
                    block_segment = current[block_start_idx:block_end_idx]
                    avg_amplitude = np.mean(block_segment)
                    block_depth = abs(baseline - avg_amplitude)
                    
                    # Calculate average voltage if voltage array is provided
                    block_voltage = None
                    if voltage is not None and len(voltage) >= block_end_idx and block_start_idx < len(voltage):
                        block_voltage = np.mean(voltage[block_start_idx:block_end_idx])
                    
                    blocks.append(Block(
                        block_number=block_number,
                        sweep_number=sweep_number,
                        start_time=time[block_start_idx],
                        end_time=time[block_end_idx],
                        duration=block_duration,
                        average_amplitude=avg_amplitude,
                        baseline_amplitude=baseline,
                        block_depth=block_depth,
                        voltage=block_voltage,
                    ))
                    block_number += 1
                
                in_block = False
        
        # Handle block that extends to end
        if in_block:
            block_end_idx = len(block_mask)
            block_duration = (block_end_idx - block_start_idx) * dt
            
            if block_duration >= self.min_block_duration:
                block_segment = current[block_start_idx:block_end_idx]
                avg_amplitude = np.mean(block_segment)
                block_depth = abs(baseline - avg_amplitude)
                
                # Calculate average voltage if voltage array is provided
                block_voltage = None
                if voltage is not None and len(voltage) >= block_end_idx:
                    block_voltage = np.mean(voltage[block_start_idx:block_end_idx])
                
                blocks.append(Block(
                    block_number=block_number,
                    sweep_number=sweep_number,
                    start_time=time[block_start_idx],
                    end_time=time[min(block_end_idx, len(time) - 1)],
                    duration=block_duration,
                    average_amplitude=avg_amplitude,
                    baseline_amplitude=baseline,
                    block_depth=block_depth,
                    voltage=block_voltage,
                ))
        
        return blocks


def detect_blocks(
    time: np.ndarray,
    current: np.ndarray,
    baseline: Optional[float] = None,
    block_threshold_factor: float = 2.0,
    min_block_duration: float = 0.001,
    sweep_number: int = 0,
    voltage: Optional[np.ndarray] = None,
) -> List[Block]:
    """Convenience function for block detection.
    
    Args:
        time: Time array
        current: Current array
        baseline: Baseline level (None for auto-detect)
        block_threshold_factor: Sensitivity factor
        min_block_duration: Minimum block duration
        sweep_number: Sweep number for labeling
        voltage: Optional voltage array (mV) for calculating average voltage per block
        
    Returns:
        List of Block objects
    """
    detector = BlockDetector(
        baseline_threshold=baseline,
        block_threshold_factor=block_threshold_factor,
        min_block_duration=min_block_duration,
    )
    return detector.detect(time, current, sweep_number, baseline, voltage)

