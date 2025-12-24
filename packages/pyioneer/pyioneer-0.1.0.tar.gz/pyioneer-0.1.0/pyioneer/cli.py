"""
Command-line interface for PyIoneer.
"""

import click
from pathlib import Path
import json
from pyioneer.io import load_abf
from pyioneer.idealization import (
    segment_hmm,
    segment_threshold,
    segment_change_point,
)
from pyioneer.block_detection import detect_blocks
from pyioneer.batch import batch_analyze


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """PyIoneer: Idealization tool for single-channel recordings."""
    pass


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--method", "-m", 
              type=click.Choice(["hmm", "threshold", "changepoint"]),
              default="threshold",
              help="Idealization method")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--sweep", "-s", type=int, default=0, help="Sweep number")
@click.option("--current-channel", type=int, default=0, help="Current channel number (default: 0)")
@click.option("--voltage-channel", type=int, default=1, help="Voltage channel number (default: 1)")
@click.option("--n-states", type=int, default=2, help="Number of states (HMM/changepoint)")
@click.option("--threshold", type=float, help="Threshold value (threshold method)")
@click.option("--min-dwell", type=float, default=0.0, help="Minimum dwell time (seconds)")
@click.option("--voltage-tolerance", type=float, default=1.0, help="Voltage tolerance for segment detection (mV, default: 1.0)")
def idealize(input_file, method, output, sweep, current_channel, voltage_channel, n_states, threshold, min_dwell, voltage_tolerance):
    """Idealize a single ABF file."""
    reader = load_abf(input_file)
    time, current = reader.get_sweep(sweep, current_channel)
    
    # Load voltage channel if available
    voltage = None
    if voltage_channel < reader.n_channels:
        try:
            _, voltage = reader.get_sweep(sweep, voltage_channel)
        except (IndexError, AttributeError):
            pass  # Voltage channel not available
    
    # Choose method
    if method == "hmm":
        result = segment_hmm(time, current, n_states=n_states, voltage=voltage, voltage_tolerance=voltage_tolerance)
    elif method == "threshold":
        if threshold is None:
            click.echo("Error: --threshold required for threshold method", err=True)
            return
        result = segment_threshold(time, current, threshold=threshold, min_dwell=min_dwell, voltage=voltage, voltage_tolerance=voltage_tolerance)
    elif method == "changepoint":
        result = segment_change_point(time, current, n_states=n_states, voltage=voltage, voltage_tolerance=voltage_tolerance)
    
    # Output results
    if output:
        df = result.to_dataframe()
        df.to_csv(output, index=False)
        click.echo(f"Results saved to {output}")
    else:
        click.echo(f"Found {len(result.events)} events")
        click.echo(result.to_dataframe().to_string())


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--sweep", "-s", type=int, default=0, help="Sweep number")
@click.option("--current-channel", type=int, default=0, help="Current channel number (default: 0)")
@click.option("--voltage-channel", type=int, default=1, help="Voltage channel number (default: 1)")
@click.option("--baseline", type=float, help="Baseline current (auto-detect if not provided)")
@click.option("--threshold-factor", type=float, default=2.0, help="Block threshold factor")
@click.option("--min-duration", type=float, default=0.001, help="Minimum block duration (seconds)")
def blocks(input_file, output, sweep, current_channel, voltage_channel, baseline, threshold_factor, min_duration):
    """Detect blocks in an ABF file."""
    reader = load_abf(input_file)
    time, current = reader.get_sweep(sweep, current_channel)
    
    # Load voltage channel if available
    voltage = None
    if voltage_channel < reader.n_channels:
        try:
            _, voltage = reader.get_sweep(sweep, voltage_channel)
        except (IndexError, AttributeError):
            pass  # Voltage channel not available
    
    blocks = detect_blocks(
        time,
        current,
        baseline=baseline,
        block_threshold_factor=threshold_factor,
        min_block_duration=min_duration,
        sweep_number=sweep,
        voltage=voltage,
    )
    
    if output:
        data = [
            {
                "block_number": b.block_number,
                "sweep_number": b.sweep_number,
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
        with open(output, "w") as f:
            json.dump(data, f, indent=2)
        click.echo(f"Found {len(blocks)} blocks, saved to {output}")
    else:
        click.echo(f"Found {len(blocks)} blocks")
        for b in blocks:
            click.echo(f"Block {b.block_number}: {b.duration:.4f}s, amplitude={b.average_amplitude:.4f}")


@cli.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.option("--method", "-m",
              type=click.Choice(["hmm", "threshold", "changepoint"]),
              default="threshold",
              help="Idealization method")
@click.option("--output", "-o", type=click.Path(), required=True, help="Output file path")
@click.option("--detect-blocks", is_flag=True, help="Also detect blocks")
@click.option("--n-states", type=int, default=2, help="Number of states")
@click.option("--threshold", type=float, help="Threshold value")
def batch(input_path, method, output, detect_blocks, n_states, threshold):
    """Batch analyze multiple ABF files."""
    input_path = Path(input_path)
    
    # Choose idealization function
    idealization_kwargs = {}
    if method == "hmm":
        idealization_func = segment_hmm
        idealization_kwargs["n_states"] = n_states
    elif method == "threshold":
        idealization_func = segment_threshold
        if threshold is None:
            click.echo("Error: --threshold required for threshold method", err=True)
            return
        idealization_kwargs["threshold"] = threshold
    elif method == "changepoint":
        idealization_func = segment_change_point
        idealization_kwargs["n_states"] = n_states
    
    results = batch_analyze(
        input_path,
        idealization_func,
        idealization_kwargs,
        detect_blocks=detect_blocks,
        output_path=Path(output),
    )
    
    click.echo(f"Processed {len(results)} files, results saved to {output}")


if __name__ == "__main__":
    cli()

