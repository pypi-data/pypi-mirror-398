"""
Utility functions for PyIoneer.
"""

from typing import Tuple
import numpy as np


def calculate_statistics(time: np.ndarray, current: np.ndarray) -> dict:
    """Calculate basic statistics for a trace.
    
    Args:
        time: Time array
        current: Current array
        
    Returns:
        Dictionary with statistics
    """
    return {
        "mean": np.mean(current),
        "std": np.std(current),
        "median": np.median(current),
        "min": np.min(current),
        "max": np.max(current),
        "duration": time[-1] - time[0],
        "sample_rate": 1.0 / (time[1] - time[0]) if len(time) > 1 else 0,
        "n_samples": len(current),
    }


def filter_trace(
    current: np.ndarray,
    sample_rate: float,
    cutoff: float,
    filter_type: str = "lowpass",
) -> np.ndarray:
    """Apply digital filter to trace.
    
    Args:
        current: Current array
        sample_rate: Sampling rate in Hz
        cutoff: Cutoff frequency in Hz
        filter_type: Type of filter ('lowpass', 'highpass', 'bandpass')
        
    Returns:
        Filtered current array
    """
    from scipy import signal
    
    nyquist = sample_rate / 2
    normal_cutoff = cutoff / nyquist
    
    if filter_type == "lowpass":
        b, a = signal.butter(4, normal_cutoff, btype="low", analog=False)
    elif filter_type == "highpass":
        b, a = signal.butter(4, normal_cutoff, btype="high", analog=False)
    else:
        raise ValueError(f"Unknown filter type: {filter_type}")
    
    filtered = signal.filtfilt(b, a, current)
    return filtered

