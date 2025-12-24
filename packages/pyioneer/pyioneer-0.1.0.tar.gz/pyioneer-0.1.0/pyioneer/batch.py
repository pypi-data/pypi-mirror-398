"""
Batch processing for multiple ABF files.
"""

from pathlib import Path
from typing import List, Optional, Callable, Dict, Any
import json
from pyioneer.io import ABFReader
from pyioneer.idealization import IdealizationResult
from pyioneer.block_detection import Block, BlockDetector


class BatchProcessor:
    """Process multiple ABF files in batch."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize batch processor.
        
        Args:
            output_dir: Directory for output files (None = same as input)
        """
        self.output_dir = output_dir
        self.results = []
    
    def process_file(
        self,
        filepath: Path,
        idealization_func: Callable,
        idealization_kwargs: Optional[Dict[str, Any]] = None,
        detect_blocks: bool = False,
        block_kwargs: Optional[Dict[str, Any]] = None,
        current_channel: int = 0,
        voltage_channel: int = 1,
    ) -> Dict[str, Any]:
        """Process a single ABF file.
        
        Args:
            filepath: Path to ABF file
            idealization_func: Idealization function to use
            idealization_kwargs: Keyword arguments for idealization
            detect_blocks: Whether to detect blocks
            block_kwargs: Keyword arguments for block detection
            current_channel: Channel number for current data (default: 0)
            voltage_channel: Channel number for voltage data (default: 1)
            
        Returns:
            Dictionary with results
        """
        if idealization_kwargs is None:
            idealization_kwargs = {}
        if block_kwargs is None:
            block_kwargs = {}
        
        reader = ABFReader(str(filepath))
        metadata = reader.get_metadata()
        
        file_results = {
            "filepath": str(filepath),
            "metadata": metadata,
            "sweeps": [],
        }
        
        # Process each sweep
        for sweep_num in range(reader.n_sweeps):
            time, current = reader.get_sweep(sweep_num, channel=current_channel)
            
            # Load voltage channel if available
            voltage = None
            if voltage_channel < reader.n_channels:
                try:
                    _, voltage = reader.get_sweep(sweep_num, voltage_channel)
                except (IndexError, AttributeError):
                    pass  # Voltage channel not available
            
            # Idealize
            idealization_kwargs_with_voltage = idealization_kwargs.copy()
            if voltage is not None:
                idealization_kwargs_with_voltage["voltage"] = voltage
                # Add voltage_tolerance if not already specified
                if "voltage_tolerance" not in idealization_kwargs_with_voltage:
                    idealization_kwargs_with_voltage["voltage_tolerance"] = 1.0
            idealization_result = idealization_func(time, current, **idealization_kwargs_with_voltage)
            
            sweep_result = {
                "sweep_number": sweep_num,
                "idealization": {
                    "method": idealization_result.method,
                    "n_events": len(idealization_result.events),
                    "events": [
                        {
                            "start_time": e.start_time,
                            "end_time": e.end_time,
                            "dwell_time": e.dwell_time,
                            "amplitude": e.amplitude,
                            "state": e.state,
                            "voltage": e.voltage,
                            "voltage_segment_id": e.voltage_segment_id,
                        }
                        for e in idealization_result.events
                    ],
                },
            }
            
            # Block detection
            if detect_blocks:
                detector = BlockDetector(**block_kwargs)
                blocks = detector.detect(time, current, sweep_num, voltage=voltage)
                sweep_result["blocks"] = [
                    {
                        "block_number": b.block_number,
                        "start_time": b.start_time,
                        "end_time": b.end_time,
                        "duration": b.duration,
                        "average_amplitude": b.average_amplitude,
                        "baseline_amplitude": b.baseline_amplitude,
                        "block_depth": b.block_depth,
                        "voltage": b.voltage,
                    }
                    for b in blocks
                ]
            
            file_results["sweeps"].append(sweep_result)
        
        return file_results
    
    def process_directory(
        self,
        directory: Path,
        pattern: str = "*.abf",
        idealization_func: Callable = None,
        idealization_kwargs: Optional[Dict[str, Any]] = None,
        detect_blocks: bool = False,
        block_kwargs: Optional[Dict[str, Any]] = None,
        current_channel: int = 0,
        voltage_channel: int = 1,
    ) -> List[Dict[str, Any]]:
        """Process all ABF files in a directory.
        
        Args:
            directory: Directory containing ABF files
            pattern: File pattern to match
            idealization_func: Idealization function
            idealization_kwargs: Keyword arguments for idealization
            detect_blocks: Whether to detect blocks
            block_kwargs: Keyword arguments for block detection
            current_channel: Channel number for current data (default: 0)
            voltage_channel: Channel number for voltage data (default: 1)
            
        Returns:
            List of result dictionaries
        """
        directory = Path(directory)
        abf_files = list(directory.glob(pattern))
        
        results = []
        for abf_file in abf_files:
            result = self.process_file(
                abf_file,
                idealization_func,
                idealization_kwargs,
                detect_blocks,
                block_kwargs,
                current_channel,
                voltage_channel,
            )
            results.append(result)
        
        self.results = results
        return results
    
    def save_results(self, output_path: Path, format: str = "json"):
        """Save batch results to file.
        
        Args:
            output_path: Output file path
            format: Output format ('json', 'csv')
        """
        output_path = Path(output_path)
        
        if format == "json":
            with open(output_path, "w") as f:
                json.dump(self.results, f, indent=2)
        elif format == "csv":
            try:
                import pandas as pd
                # Flatten results for CSV
                rows = []
                for file_result in self.results:
                    for sweep in file_result["sweeps"]:
                        for event in sweep["idealization"]["events"]:
                            rows.append({
                                "file": Path(file_result["filepath"]).name,
                                "sweep": sweep["sweep_number"],
                                **event,
                            })
                df = pd.DataFrame(rows)
                df.to_csv(output_path, index=False)
            except ImportError:
                raise ImportError("pandas required for CSV export")


def batch_analyze(
    input_path: Path,
    idealization_func: Callable,
    idealization_kwargs: Optional[Dict[str, Any]] = None,
    detect_blocks: bool = False,
    block_kwargs: Optional[Dict[str, Any]] = None,
    output_path: Optional[Path] = None,
    current_channel: int = 0,
    voltage_channel: int = 1,
) -> List[Dict[str, Any]]:
    """Convenience function for batch analysis.
    
    Args:
        input_path: Path to file or directory
        idealization_func: Idealization function
        idealization_kwargs: Keyword arguments for idealization
        detect_blocks: Whether to detect blocks
        block_kwargs: Keyword arguments for block detection
        output_path: Optional output file path
        current_channel: Channel number for current data (default: 0)
        voltage_channel: Channel number for voltage data (default: 1)
        
    Returns:
        List of result dictionaries
    """
    processor = BatchProcessor()
    input_path = Path(input_path)
    
    if input_path.is_file():
        results = [processor.process_file(
            input_path,
            idealization_func,
            idealization_kwargs,
            detect_blocks,
            block_kwargs,
            current_channel,
            voltage_channel,
        )]
    else:
        results = processor.process_directory(
            input_path,
            idealization_func=idealization_func,
            idealization_kwargs=idealization_kwargs,
            detect_blocks=detect_blocks,
            block_kwargs=block_kwargs,
            current_channel=current_channel,
            voltage_channel=voltage_channel,
        )
    
    if output_path:
        processor.results = results
        processor.save_results(output_path)
    
    return results

