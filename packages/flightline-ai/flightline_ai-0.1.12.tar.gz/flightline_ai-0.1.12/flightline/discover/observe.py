"""Build observations from detected calls.

Combines detection and tracing into complete AiCallObservation objects.
"""

from pathlib import Path
from typing import List

from flightline.discover.detect import DetectedCall, detect_ai_calls
from flightline.discover.heuristics import detect_heuristic_calls
from flightline.discover.ingest import FileIndex
from flightline.discover.schema import (
    AiCallObservation,
    DetectionMethod,
    ExtractionConfidence,
    ExtractionSummary,
)
from flightline.discover.trace import trace_inputs, trace_outputs


def build_observation(call: DetectedCall, method: DetectionMethod, file_content: str) -> AiCallObservation:
    """Combine detection and tracing into a single observation."""
    inputs = trace_inputs(call, file_content)
    outputs, usage = trace_outputs(call, file_content)

    # Stable identifier based on location
    # Format: file:line:method (stable unless code moves significantly)
    obs_id = f"{call.location.file}:{call.location.line}:{call.method_chain}"

    obs = AiCallObservation(
        id=obs_id,
        location=call.location,
        provider=call.provider,
        call_type=call.call_type,
        detection_method=method,
        inputs=inputs,
        outputs=outputs,
        usage=usage,
    )

    # Populate extraction summary
    obs.extraction = _build_extraction_summary(obs)

    return obs


def _build_extraction_summary(obs: AiCallObservation) -> ExtractionSummary:
    """Aggregate confidence levels for different extraction types."""
    summary = ExtractionSummary()

    # 1. Prompt confidence
    if obs.inputs.system_prompt:
        summary.prompt_confidence = obs.inputs.system_prompt.confidence
        summary.prompt_preview = obs.inputs.system_prompt.inline_content

    # 2. Input schema confidence
    # Look at context variables for the highest confidence type
    if obs.inputs.context_variables:
        best_conf = ExtractionConfidence.UNKNOWN
        best_name = None
        for cv in obs.inputs.context_variables:
            if cv.type_reference:
                # Prioritize high confidence
                if cv.confidence == ExtractionConfidence.HIGH:
                    best_conf = ExtractionConfidence.HIGH
                    best_name = cv.type_reference
                    break
                elif cv.confidence == ExtractionConfidence.MEDIUM:
                    best_conf = ExtractionConfidence.MEDIUM
                    best_name = cv.type_reference

        summary.input_schema_confidence = best_conf
        summary.input_type_name = best_name

    # 3. Output schema confidence
    if obs.outputs.validation:
        summary.output_schema_confidence = obs.outputs.validation.confidence
        summary.output_type_name = obs.outputs.validation.schema_name

    return summary


def observe_file(file_path: Path) -> List[AiCallObservation]:
    """
    Detect and trace all AI calls in a single file.

    Args:
        file_path: Path to source file

    Returns:
        List of complete observations
    """
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []

    observations = []

    # 1. SDK-verified calls
    sdk_calls = detect_ai_calls(file_path)
    for call in sdk_calls:
        observations.append(build_observation(call, DetectionMethod.SDK_VERIFIED, content))

    # 2. Heuristic calls (only if no SDK calls found in same locations)
    # This prevents duplicate observations
    heuristic_calls = detect_heuristic_calls(file_path)
    existing_lines = {obs.location.line for obs in observations}

    for call in heuristic_calls:
        if call.location.line not in existing_lines:
            observations.append(build_observation(call, DetectionMethod.HEURISTIC, content))

    return observations


def observe_all(file_index: FileIndex) -> List[AiCallObservation]:
    """
    Detect and observe all AI calls in indexed files.

    Args:
        file_index: Index of files to scan

    Returns:
        List of all observations
    """
    all_observations: List[AiCallObservation] = []

    for file_path in file_index.files:
        observations = observe_file(file_path)
        all_observations.extend(observations)

    return all_observations
