"""
Idealization methods: HMM, threshold-crossing, and change-point detection.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
import numpy as np
from scipy import stats
try:
    from ruptures import Binseg, Window, Dynp
except ImportError:
    Binseg = None
    Window = None
    Dynp = None


@dataclass
class Event:
    """Represents a single idealized event."""
    start_time: float
    end_time: float
    dwell_time: float
    amplitude: float
    state: int  # State index (0=closed, 1=open, etc.)
    voltage: Optional[float] = None  # Average voltage during event (mV)
    voltage_segment_id: Optional[int] = None  # ID of voltage segment this event belongs to
    

@dataclass
class IdealizationResult:
    """Result of idealization process."""
    events: List[Event]
    idealized_trace: np.ndarray
    states: np.ndarray
    time: np.ndarray
    method: str
    
    def to_dataframe(self):
        """Convert to pandas DataFrame."""
        try:
            import pandas as pd
            data = {
                "start_time": [e.start_time for e in self.events],
                "end_time": [e.end_time for e in self.events],
                "dwell_time": [e.dwell_time for e in self.events],
                "amplitude": [e.amplitude for e in self.events],
                "state": [e.state for e in self.events],
                "voltage": [e.voltage for e in self.events],
                "voltage_segment_id": [e.voltage_segment_id for e in self.events],
            }
            return pd.DataFrame(data)
        except ImportError:
            raise ImportError("pandas required for DataFrame conversion")


def detect_voltage_segments(
    time: np.ndarray,
    voltage: np.ndarray,
    voltage_tolerance: float = 1.0,
    min_segment_duration: float = 0.001,
) -> List[Tuple[int, int, int, float]]:
    """Detect voltage segments (steps and ramps) in voltage trace.
    
    Args:
        time: Time array
        voltage: Voltage array (mV)
        voltage_tolerance: Tolerance for considering voltage constant (mV)
        min_segment_duration: Minimum duration for a segment (seconds)
        
    Returns:
        List of tuples: (segment_id, start_idx, end_idx, mean_voltage)
    """
    if len(voltage) < 2:
        return [(0, 0, len(voltage), np.mean(voltage) if len(voltage) > 0 else 0.0)]
    
    dt = time[1] - time[0] if len(time) > 1 else 1.0
    min_samples = max(1, int(min_segment_duration / dt)) if min_segment_duration > 0 else 1
    
    segments = []
    segment_id = 0
    start_idx = 0
    
    # Calculate voltage differences
    voltage_diff = np.abs(np.diff(voltage))
    
    i = 1
    while i < len(voltage):
        # Detect voltage steps (sudden large changes)
        if i > 0 and voltage_diff[i-1] > voltage_tolerance * 2:
            # Step detected - end current segment before step
            if i - start_idx >= min_samples:
                segments.append((segment_id, start_idx, i, np.mean(voltage[start_idx:i])))
                segment_id += 1
            start_idx = i
            i += 1
            continue
        
        # Detect ramps: check if voltage is changing consistently
        # Look for sustained changes in same direction
        if i < len(voltage) - 2:
            # Check next few points for consistent change
            change_1 = voltage[i] - voltage[i-1]
            change_2 = voltage[i+1] - voltage[i] if i+1 < len(voltage) else 0
            
            # If both changes are in same direction and significant
            if (abs(change_1) > voltage_tolerance * 0.2 and 
                abs(change_2) > voltage_tolerance * 0.2 and
                np.sign(change_1) == np.sign(change_2)):
                # Potential ramp - look ahead to find ramp end
                ramp_start = i - 1
                ramp_end = i + 1
                ramp_direction = np.sign(change_1)
                
                # Extend ramp forward
                while ramp_end < len(voltage) - 1:
                    next_change = voltage[ramp_end + 1] - voltage[ramp_end]
                    if (np.sign(next_change) == ramp_direction and 
                        abs(next_change) > voltage_tolerance * 0.1):
                        ramp_end += 1
                    else:
                        break
                
                # If ramp is significant (total change > tolerance)
                if abs(voltage[ramp_end] - voltage[ramp_start]) > voltage_tolerance:
                    # End segment before ramp
                    if ramp_start - start_idx >= min_samples:
                        segments.append((segment_id, start_idx, ramp_start, np.mean(voltage[start_idx:ramp_start])))
                        segment_id += 1
                    # Create segment for ramp
                    if ramp_end - ramp_start >= min_samples:
                        segments.append((segment_id, ramp_start, ramp_end + 1, np.mean(voltage[ramp_start:ramp_end+1])))
                        segment_id += 1
                    start_idx = ramp_end + 1
                    i = ramp_end + 1
                    continue
        
        # Check if voltage has drifted outside tolerance from segment mean
        segment_mean = np.mean(voltage[start_idx:i+1])
        if abs(voltage[i] - segment_mean) > voltage_tolerance:
            # Voltage drifted - end current segment
            if i - start_idx >= min_samples:
                segments.append((segment_id, start_idx, i, np.mean(voltage[start_idx:i])))
                segment_id += 1
            start_idx = i
        
        i += 1
    
    # Add final segment
    if len(voltage) - start_idx >= min_samples:
        segments.append((segment_id, start_idx, len(voltage), np.mean(voltage[start_idx:])))
    
    # If no segments found, create one for entire trace
    if not segments:
        segments = [(0, 0, len(voltage), np.mean(voltage))]
    
    return segments


def segment_threshold(
    time: np.ndarray,
    current: np.ndarray,
    threshold: float,
    min_dwell: float = 0.0,
    baseline: Optional[float] = None,
    voltage: Optional[np.ndarray] = None,
    voltage_tolerance: float = 1.0,
) -> IdealizationResult:
    """Idealize trace using threshold-crossing method.
    
    If voltage is provided, idealization is performed separately for each voltage segment
    (steps and ramps are detected automatically).
    
    Args:
        time: Time array
        current: Current array
        threshold: Threshold for state detection
        min_dwell: Minimum dwell time (seconds)
        baseline: Baseline current level (auto-detect if None)
        voltage: Optional voltage array (mV) for voltage-segmented idealization
        voltage_tolerance: Tolerance for voltage segment detection (mV, default: 1.0)
        
    Returns:
        IdealizationResult
    """
    all_events = []
    all_states = np.zeros_like(current)
    idealized = np.zeros_like(current)
    
    # If voltage is provided, detect voltage segments and idealize each separately
    if voltage is not None and len(voltage) == len(current):
        voltage_segments = detect_voltage_segments(time, voltage, voltage_tolerance)
        
        for segment_id, seg_start, seg_end, seg_voltage in voltage_segments:
            # Extract segment data
            seg_time = time[seg_start:seg_end]
            seg_current = current[seg_start:seg_end]
            
            # Idealize this segment
            seg_baseline = baseline if baseline is not None else np.median(seg_current)
            seg_dt = seg_time[1] - seg_time[0] if len(seg_time) > 1 else time[1] - time[0]
            seg_min_samples = int(min_dwell / seg_dt) if min_dwell > 0 else 1
            
            # Binary states for this segment
            seg_states = (seg_current > (seg_baseline + threshold)).astype(int)
            
            # Find transitions in this segment
            seg_transitions = np.diff(seg_states)
            seg_transition_indices = np.where(seg_transitions != 0)[0]
            
            # Handle all segments including first and last
            seg_segment_starts = [0] + (seg_transition_indices + 1).tolist()
            seg_segment_ends = (seg_transition_indices + 1).tolist() + [len(seg_current)]
            
            for seg_event_start, seg_event_end in zip(seg_segment_starts, seg_segment_ends):
                if seg_event_end - seg_event_start < seg_min_samples:
                    continue
                
                # Convert back to global indices
                global_start = seg_start + seg_event_start
                global_end = seg_start + seg_event_end
                time_end_idx = min(global_end, len(time) - 1)
                
                start_time = time[global_start]
                end_time = time[time_end_idx]
                dwell_time = end_time - start_time
                
                state = seg_states[seg_event_start]
                amplitude = np.mean(seg_current[seg_event_start:seg_event_end])
                
                all_events.append(Event(
                    start_time=start_time,
                    end_time=end_time,
                    dwell_time=dwell_time,
                    amplitude=amplitude,
                    state=state,
                    voltage=seg_voltage,
                    voltage_segment_id=segment_id
                ))
                
                # Update global arrays
                idealized[global_start:global_end] = amplitude
                all_states[global_start:global_end] = state
    else:
        # No voltage segmentation - idealize entire trace
        if baseline is None:
            baseline = np.median(current)
        
        dt = time[1] - time[0]
        min_samples = int(min_dwell / dt) if min_dwell > 0 else 1
        
        # Binary states: 0 = below threshold, 1 = above threshold
        states = (current > (baseline + threshold)).astype(int)
        
        # Find transitions
        transitions = np.diff(states)
        transition_indices = np.where(transitions != 0)[0]
        
        # Handle all segments including first and last
        segment_starts = [0] + (transition_indices + 1).tolist()
        segment_ends = (transition_indices + 1).tolist() + [len(current)]
        
        for start_idx, end_idx in zip(segment_starts, segment_ends):
            if end_idx - start_idx < min_samples:
                continue
            
            # Handle boundary: end_idx can be len(current) for slicing, but time array is 0-indexed
            time_end_idx = min(end_idx, len(time) - 1)
            start_time = time[start_idx]
            end_time = time[time_end_idx]
            dwell_time = end_time - start_time
            
            state = states[start_idx]
            amplitude = np.mean(current[start_idx:end_idx])
            
            # Calculate average voltage if voltage array is provided
            event_voltage = None
            if voltage is not None and len(voltage) >= end_idx and start_idx < len(voltage):
                event_voltage = np.mean(voltage[start_idx:end_idx])
            
            all_events.append(Event(
                start_time=start_time,
                end_time=end_time,
                dwell_time=dwell_time,
                amplitude=amplitude,
                state=state,
                voltage=event_voltage,
                voltage_segment_id=None
            ))
            
            idealized[start_idx:end_idx] = amplitude
            all_states[start_idx:end_idx] = state
    
    return IdealizationResult(
        events=all_events,
        idealized_trace=idealized,
        states=all_states,
        time=time,
        method="threshold"
    )


def segment_change_point(
    time: np.ndarray,
    current: np.ndarray,
    n_states: int = 2,
    method: str = "binseg",
    min_size: int = 2,
    voltage: Optional[np.ndarray] = None,
    voltage_tolerance: float = 1.0,
) -> IdealizationResult:
    """Idealize trace using change-point detection.
    
    If voltage is provided, idealization is performed separately for each voltage segment
    (steps and ramps are detected automatically).
    
    Args:
        time: Time array
        current: Current array
        n_states: Number of states to detect
        method: Detection method ('binseg', 'window', 'dynp')
        min_size: Minimum segment size
        voltage: Optional voltage array (mV) for voltage-segmented idealization
        voltage_tolerance: Tolerance for voltage segment detection (mV, default: 1.0)
        
    Returns:
        IdealizationResult
    """
    if Binseg is None:
        raise ImportError("ruptures library required for change-point detection")
    
    all_events = []
    all_states = np.zeros(len(current), dtype=int)
    idealized = np.zeros_like(current)
    
    # If voltage is provided, detect voltage segments and idealize each separately
    if voltage is not None and len(voltage) == len(current):
        voltage_segments = detect_voltage_segments(time, voltage, voltage_tolerance)
        
        for segment_id, seg_start, seg_end, seg_voltage in voltage_segments:
            # Extract segment data
            seg_time = time[seg_start:seg_end]
            seg_current = current[seg_start:seg_end]
            
            if len(seg_current) < min_size * 2:
                # Segment too short, skip
                continue
            
            # Reshape for ruptures (needs 2D array)
            seg_signal = seg_current.reshape(-1, 1)
            
            # Choose algorithm
            if method == "binseg":
                algo = Binseg(model="l2", min_size=min_size).fit(seg_signal)
            elif method == "window":
                algo = Window(width=min_size, model="l2").fit(seg_signal)
            elif method == "dynp":
                algo = Dynp(model="l2", min_size=min_size).fit(seg_signal)
            else:
                raise ValueError(f"Unknown method: {method}")
            
            # Detect change points in this segment
            seg_n_bkps = min(n_states - 1, len(seg_current) // (min_size * 2))
            if seg_n_bkps < 1:
                # Not enough points for change points, treat as single state
                global_start = seg_start
                global_end = seg_end
                time_end_idx = min(global_end, len(time) - 1)
                amplitude = np.mean(seg_current)
                
                all_events.append(Event(
                    start_time=time[global_start],
                    end_time=time[time_end_idx],
                    dwell_time=time[time_end_idx] - time[global_start],
                    amplitude=amplitude,
                    state=0,
                    voltage=seg_voltage,
                    voltage_segment_id=segment_id
                ))
                idealized[global_start:global_end] = amplitude
                all_states[global_start:global_end] = 0
            else:
                seg_change_points = algo.predict(n_bkps=seg_n_bkps)
                seg_change_points = [0] + seg_change_points + [len(seg_current)]
                
                for i in range(len(seg_change_points) - 1):
                    seg_event_start = seg_change_points[i]
                    seg_event_end = seg_change_points[i + 1]
                    
                    # Convert to global indices
                    global_start = seg_start + seg_event_start
                    global_end = seg_start + seg_event_end
                    time_end_idx = min(global_end, len(time) - 1)
                    
                    seg_event = seg_current[seg_event_start:seg_event_end]
                    amplitude = np.mean(seg_event)
                    state = i % n_states
                    
                    all_events.append(Event(
                        start_time=time[global_start],
                        end_time=time[time_end_idx],
                        dwell_time=time[time_end_idx] - time[global_start],
                        amplitude=amplitude,
                        state=state,
                        voltage=seg_voltage,
                        voltage_segment_id=segment_id
                    ))
                    
                    idealized[global_start:global_end] = amplitude
                    all_states[global_start:global_end] = state
    else:
        # No voltage segmentation - idealize entire trace
        signal = current.reshape(-1, 1)
        
        # Choose algorithm
        if method == "binseg":
            algo = Binseg(model="l2", min_size=min_size).fit(signal)
        elif method == "window":
            algo = Window(width=min_size, model="l2").fit(signal)
        elif method == "dynp":
            algo = Dynp(model="l2", min_size=min_size).fit(signal)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # Detect change points
        change_points = algo.predict(n_bkps=n_states - 1)
        change_points = [0] + change_points + [len(current)]
        
        for i in range(len(change_points) - 1):
            start_idx = change_points[i]
            end_idx = change_points[i + 1]
            
            segment = current[start_idx:end_idx]
            amplitude = np.mean(segment)
            state = i % n_states
            
            # Handle boundary: end_idx can be len(current) for slicing, but time array is 0-indexed
            time_end_idx = min(end_idx, len(time) - 1)
            start_time = time[start_idx]
            end_time = time[time_end_idx]
            dwell_time = end_time - start_time
            
            # Calculate average voltage if voltage array is provided
            event_voltage = None
            if voltage is not None and len(voltage) >= end_idx and start_idx < len(voltage):
                event_voltage = np.mean(voltage[start_idx:end_idx])
            
            all_events.append(Event(
                start_time=start_time,
                end_time=end_time,
                dwell_time=dwell_time,
                amplitude=amplitude,
                state=state,
                voltage=event_voltage,
                voltage_segment_id=None
            ))
            
            idealized[start_idx:end_idx] = amplitude
            all_states[start_idx:end_idx] = state
    
    return IdealizationResult(
        events=all_events,
        idealized_trace=idealized,
        states=all_states,
        time=time,
        method=f"change_point_{method}"
    )


def segment_hmm(
    time: np.ndarray,
    current: np.ndarray,
    n_states: int = 2,
    method: str = "gaussian",
    max_iter: int = 100,
    voltage: Optional[np.ndarray] = None,
    voltage_tolerance: float = 1.0,
) -> IdealizationResult:
    """Idealize trace using Hidden Markov Model.
    
    If voltage is provided, idealization is performed separately for each voltage segment
    (steps and ramps are detected automatically).
    
    Args:
        time: Time array
        current: Current array
        n_states: Number of hidden states
        method: Observation model ('gaussian', 'student')
        max_iter: Maximum EM iterations
        voltage: Optional voltage array (mV) for voltage-segmented idealization
        voltage_tolerance: Tolerance for voltage segment detection (mV, default: 1.0)
        
    Returns:
        IdealizationResult
    """
    try:
        from hmmlearn import hmm
    except ImportError:
        raise ImportError("hmmlearn required for HMM idealization")
    
    all_events = []
    all_states = np.zeros(len(current), dtype=int)
    idealized = np.zeros_like(current)
    
    # If voltage is provided, detect voltage segments and idealize each separately
    if voltage is not None and len(voltage) == len(current):
        voltage_segments = detect_voltage_segments(time, voltage, voltage_tolerance)
        
        for segment_id, seg_start, seg_end, seg_voltage in voltage_segments:
            # Extract segment data
            seg_time = time[seg_start:seg_end]
            seg_current = current[seg_start:seg_end]
            
            if len(seg_current) < n_states:
                # Segment too short, skip
                continue
            
            # Reshape for hmmlearn
            seg_X = seg_current.reshape(-1, 1)
            
            # Create HMM for this segment
            if method == "gaussian":
                seg_model = hmm.GaussianHMM(n_components=n_states, n_iter=max_iter)
            elif method == "student":
                seg_model = hmm.GaussianHMM(n_components=n_states, n_iter=max_iter)
            else:
                raise ValueError(f"Unknown method: {method}")
            
            # Fit model on this segment
            seg_model.fit(seg_X)
            
            # Predict states for this segment
            seg_states = seg_model.predict(seg_X)
            
            # Group consecutive states in this segment
            seg_state_changes = np.diff(seg_states)
            seg_change_indices = np.where(seg_state_changes != 0)[0] + 1
            seg_change_indices = [0] + seg_change_indices.tolist() + [len(seg_states)]
            
            for i in range(len(seg_change_indices) - 1):
                seg_event_start = seg_change_indices[i]
                seg_event_end = seg_change_indices[i + 1]
                
                # Convert to global indices
                global_start = seg_start + seg_event_start
                global_end = seg_start + seg_event_end
                time_end_idx = min(global_end, len(time) - 1)
                
                seg_event = seg_current[seg_event_start:seg_event_end]
                state = seg_states[seg_event_start]
                amplitude = seg_model.means_[state][0]
                
                all_events.append(Event(
                    start_time=time[global_start],
                    end_time=time[time_end_idx],
                    dwell_time=time[time_end_idx] - time[global_start],
                    amplitude=amplitude,
                    state=state,
                    voltage=seg_voltage,
                    voltage_segment_id=segment_id
                ))
                
                idealized[global_start:global_end] = amplitude
                all_states[global_start:global_end] = state
    else:
        # No voltage segmentation - idealize entire trace
        X = current.reshape(-1, 1)
        
        # Create HMM
        if method == "gaussian":
            model = hmm.GaussianHMM(n_components=n_states, n_iter=max_iter)
        elif method == "student":
            model = hmm.GaussianHMM(n_components=n_states, n_iter=max_iter)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # Fit model
        model.fit(X)
        
        # Predict states
        states = model.predict(X)
        
        # Group consecutive states
        state_changes = np.diff(states)
        change_indices = np.where(state_changes != 0)[0] + 1
        change_indices = [0] + change_indices.tolist() + [len(states)]
        
        for i in range(len(change_indices) - 1):
            start_idx = change_indices[i]
            end_idx = change_indices[i + 1]
            
            segment = current[start_idx:end_idx]
            state = states[start_idx]
            amplitude = model.means_[state][0]
            
            # Handle boundary: end_idx can be len(states) for slicing, but time array is 0-indexed
            time_end_idx = min(end_idx, len(time) - 1)
            start_time = time[start_idx]
            end_time = time[time_end_idx]
            dwell_time = end_time - start_time
            
            # Calculate average voltage if voltage array is provided
            event_voltage = None
            if voltage is not None and len(voltage) >= end_idx and start_idx < len(voltage):
                event_voltage = np.mean(voltage[start_idx:end_idx])
            
            all_events.append(Event(
                start_time=start_time,
                end_time=end_time,
                dwell_time=dwell_time,
                amplitude=amplitude,
                state=state,
                voltage=event_voltage,
                voltage_segment_id=None
            ))
            
            idealized[start_idx:end_idx] = amplitude
            all_states[start_idx:end_idx] = state
    
    return IdealizationResult(
        events=all_events,
        idealized_trace=idealized,
        states=all_states,
        time=time,
        method=f"hmm_{method}"
    )

# Backward-compatibility wrappers (deprecated)
def idealize_threshold(*args, **kwargs) -> IdealizationResult:  # type: ignore[override]
    import warnings
    warnings.warn("idealize_threshold is deprecated; use segment_threshold", DeprecationWarning)
    return segment_threshold(*args, **kwargs)


def idealize_change_point(*args, **kwargs) -> IdealizationResult:  # type: ignore[override]
    import warnings
    warnings.warn("idealize_change_point is deprecated; use segment_change_point", DeprecationWarning)
    return segment_change_point(*args, **kwargs)


def idealize_hmm(*args, **kwargs) -> IdealizationResult:  # type: ignore[override]
    import warnings
    warnings.warn("idealize_hmm is deprecated; use segment_hmm", DeprecationWarning)
    return segment_hmm(*args, **kwargs)

