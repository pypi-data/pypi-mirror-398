"""
PyIoneer: A Python library for idealizing single-channel current recordings.

An open-source, clean, modern idealization tool for electrophysiology data.
"""

__version__ = "0.1.0"

from pyioneer.io import load_abf, ABFReader
from pyioneer.idealization import (
    segment_hmm,
    segment_threshold,
    segment_change_point,
    IdealizationResult,
    Event,
)
from pyioneer.block_detection import detect_blocks, BlockDetector, Block
from pyioneer.batch import batch_analyze, BatchProcessor

__all__ = [
    "load_abf",
    "ABFReader",
    "segment_hmm",
    "segment_threshold",
    "segment_change_point",
    "IdealizationResult",
    "Event",
    "detect_blocks",
    "BlockDetector",
    "Block",
    "batch_analyze",
    "BatchProcessor",
]

