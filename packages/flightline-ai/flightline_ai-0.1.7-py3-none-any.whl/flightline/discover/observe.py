"""Build observations from detected calls.

Combines detection and tracing into complete AiCallObservation objects.
"""

from pathlib import Path

from flightline.discover.detect import DetectedCall, detect_ai_calls
from flightline.discover.heuristics import detect_heuristic_calls
from flightline.discover.ingest import FileIndex
from flightline.discover.schema import AiCallObservation, DetectionMethod
from flightline.discover.trace import trace_inputs, trace_outputs


def build_observation(
    file_path: Path, call: DetectedCall, method: DetectionMethod = DetectionMethod.SDK_VERIFIED, confidence: float = 1.0
) -> AiCallObservation:
    """
    Build a complete observation for a detected AI call.

    Args:
        file_path: Path to source file
        call: Detected AI call
        method: How the call was detected
        confidence: Detection confidence

    Returns:
        Complete AiCallObservation
    """
    # Trace inputs
    inputs = trace_inputs(file_path, call)

    # Trace outputs
    outputs, usage = trace_outputs(file_path, call)

    return AiCallObservation(
        id=call.make_id(file_path),
        location=call.location,
        provider=call.provider,
        call_type=call.call_type,
        detection_method=method,
        confidence=confidence,
        inputs=inputs,
        outputs=outputs,
        usage=usage,
    )


def observe_file(file_path: Path) -> list[AiCallObservation]:
    """
    Detect and observe all AI calls in a file, using both SDK patterns
    and heuristic footprints.

    Args:
        file_path: Path to source file

    Returns:
        List of observations
    """
    # Tier 1: SDK Detection (High Precision)
    sdk_calls = detect_ai_calls(file_path)

    # Tier 2: Heuristic Detection (High Recall)
    heuristic_calls = detect_heuristic_calls(file_path)

    observations = []
    seen_lines = set()

    # Process SDK calls first (they are more authoritative)
    for call in sdk_calls:
        obs = build_observation(file_path, call, method=DetectionMethod.SDK_VERIFIED, confidence=1.0)
        observations.append(obs)
        # Mark lines around the call as seen to avoid duplicate heuristic detections
        for line in range(call.location.line - 5, call.location.line + 6):
            seen_lines.add(line)

    # Process heuristic calls if they aren't duplicates of SDK calls
    for call in heuristic_calls:
        if call.location.line not in seen_lines:
            obs = build_observation(
                file_path,
                call,
                method=DetectionMethod.HEURISTIC,
                confidence=0.8,  # Candidate confidence
            )
            observations.append(obs)
            # Mark lines around to avoid multiple heuristic hits for same logic
            for line in range(call.location.line - 10, call.location.line + 11):
                seen_lines.add(line)

    return observations


def observe_all(file_index: FileIndex) -> list[AiCallObservation]:
    """
    Detect and observe all AI calls in indexed files.

    Args:
        file_index: Index of files to scan

    Returns:
        List of all observations
    """
    all_observations: list[AiCallObservation] = []

    for file_path in file_index.files:
        observations = observe_file(file_path)
        all_observations.extend(observations)

    return all_observations
