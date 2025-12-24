"""
ABF file input/output handling using pyABF backend.
"""

from typing import Optional, Tuple
import numpy as np
import pyabf


class ABFReader:
    """Reader for ABF files with convenient data access."""
    
    def __init__(self, filepath: str):
        """Initialize ABF reader.
        
        Args:
            filepath: Path to ABF file
        """
        self.filepath = filepath
        self.abf = pyabf.ABF(filepath)
        self.n_channels = self.abf.channelCount
        self.n_sweeps = self.abf.sweepCount
        self.sample_rate = self.abf.dataRate
        
    def get_sweep(self, sweep_number: int = 0, channel: int = 0) -> Tuple[np.ndarray, np.ndarray]:
        """Get sweep data.
        
        Args:
            sweep_number: Sweep index (0-based)
            channel: Channel index (0-based)
            
        Returns:
            Tuple of (time, current) arrays
        """
        self.abf.setSweep(sweepNumber=sweep_number, channel=channel)
        return self.abf.sweepX, self.abf.sweepY
    
    def get_all_sweeps(self, channel: int = 0) -> list:
        """Get all sweeps for a channel.
        
        Args:
            channel: Channel index
            
        Returns:
            List of (time, current) tuples for each sweep
        """
        sweeps = []
        for i in range(self.n_sweeps):
            time, current = self.get_sweep(i, channel)
            sweeps.append((time, current))
        return sweeps
    
    def get_metadata(self) -> dict:
        """Get file metadata.
        
        Returns:
            Dictionary with metadata
        """
        return {
            "filepath": self.filepath,
            "n_channels": self.n_channels,
            "n_sweeps": self.n_sweeps,
            "sample_rate": self.sample_rate,
            "duration": self.abf.sweepLengthSec,
            "protocol": getattr(self.abf, "protocol", "Unknown"),
        }


def load_abf(filepath: str) -> ABFReader:
    """Convenience function to load ABF file.
    
    Args:
        filepath: Path to ABF file
        
    Returns:
        ABFReader instance
    """
    return ABFReader(filepath)

