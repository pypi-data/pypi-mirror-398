"""Interpretation layer for observations.

Converts raw observations into risk tiers and actionable summaries.
This layer is versioned separately and can evolve without breaking the stable schema.
"""

from flightline.discover.schema import (
    AiCallObservation,
    DetectionMethod,
    Interpretation,
    RiskTier,
    ScenarioComplexity,
    SinkType,
    SourceType,
)

# =============================================================================
# INTERPRETATION VERSION
# =============================================================================

INTERPRETATION_VERSION = "0.1.2"


# =============================================================================
# RISK ASSESSMENT
# =============================================================================


def compute_risk_tier(obs: AiCallObservation) -> RiskTier:
    """
    Compute risk tier based on observations.

    Risk factors (in order of importance):
    1. Output controls branching + no validation = CRITICAL
    2. Output returned to caller + no validation = HIGH
    3. Output controls branching with validation = HIGH
    4. External input sources + no validation = HIGH
    5. Output with validation = MEDIUM
    6. Everything else = LOW
    """
    has_validation = obs.outputs.validation is not None
    controls_branching = obs.usage.used_in_conditional
    is_returned = obs.usage.returned_from_function

    # Check for high-risk sinks
    has_high_risk_sink = any(
        sink in {SinkType.DB_WRITE, SinkType.EMAIL_SEND, SinkType.VENDOR_DISPATCH} for sink in obs.usage.sinks
    )

    # Check for external/dynamic input sources
    has_external_inputs = any(
        cv.source_type in {SourceType.USER_INPUT, SourceType.API, SourceType.DATABASE}
        for cv in obs.inputs.context_variables
    )

    # Check if prompt comes from external source
    prompt_is_external = obs.inputs.system_prompt is not None and obs.inputs.system_prompt.source_type in {
        SourceType.API,
        SourceType.DATABASE,
        SourceType.CONFIG,
    }

    # CRITICAL: Controls flow or triggers side effect without validation
    if (controls_branching or has_high_risk_sink) and not has_validation:
        return RiskTier.CRITICAL

    # HIGH: Multiple risk factors
    if has_high_risk_sink and has_validation:
        return RiskTier.HIGH

    if is_returned and not has_validation:
        return RiskTier.HIGH

    if controls_branching and has_validation:
        return RiskTier.HIGH

    if has_external_inputs and not has_validation:
        return RiskTier.HIGH

    if prompt_is_external and not has_validation:
        return RiskTier.HIGH

    # MEDIUM: Has some guardrails
    if has_validation:
        return RiskTier.MEDIUM

    if is_returned:
        return RiskTier.MEDIUM

    # LOW: Isolated or well-guarded
    return RiskTier.LOW


def compute_scenario_complexity(obs: AiCallObservation) -> ScenarioComplexity:
    """
    Compute the complexity of scenario testing needed.

    HIGH: Classification/routing tasks, many input dimensions
    MEDIUM: User-facing output, document processing
    LOW: Internal logging, simple generation
    """
    controls_branching = obs.usage.used_in_conditional
    has_many_contexts = len(obs.inputs.context_variables) >= 2
    is_returned = obs.usage.returned_from_function

    # HIGH: Classification-like patterns
    if controls_branching:
        return ScenarioComplexity.HIGH

    # HIGH: Complex inputs
    if has_many_contexts:
        return ScenarioComplexity.HIGH

    # MEDIUM: User-facing
    if is_returned:
        return ScenarioComplexity.MEDIUM

    return ScenarioComplexity.LOW


def generate_observations_summary(obs: AiCallObservation) -> list[str]:
    """Generate human-readable summary of key observations."""
    summaries = []

    # Detection method
    if obs.detection_method == DetectionMethod.HEURISTIC:
        summaries.append("Candidate AI operation (detected via footprint)")

    # Output flow
    if obs.usage.used_in_conditional:
        cond_type = obs.usage.conditional_type.value if obs.usage.conditional_type else "conditional"
        if obs.usage.conditional_location:
            summaries.append(f"Output controls {cond_type} at L{obs.usage.conditional_location.line}")
        else:
            summaries.append(f"Output controls {cond_type} statement")

    if obs.usage.returned_from_function:
        summaries.append("Output returned from function")

    if obs.usage.passed_to_functions:
        funcs = ", ".join(obs.usage.passed_to_functions[:3])
        if len(obs.usage.passed_to_functions) > 3:
            funcs += f" (+{len(obs.usage.passed_to_functions) - 3} more)"
        summaries.append(f"Output passed to: {funcs}")

    # Validation
    if obs.outputs.validation:
        summaries.append(f"{obs.outputs.validation.type.value} validation present")
    else:
        summaries.append("No schema validation on output")

    # Input sources
    if obs.inputs.system_prompt:
        source = obs.inputs.system_prompt.source_type.value
        hint = obs.inputs.system_prompt.source_hint
        if hint:
            summaries.append(f"Prompt from {source}: {hint[:50]}")
        else:
            summaries.append(f"Prompt from {source} source")

    for cv in obs.inputs.context_variables[:3]:
        summaries.append(f"Context '{cv.name}' from {cv.source_type.value}")

    # Template engine
    if obs.inputs.template_engine:
        summaries.append(f"Uses {obs.inputs.template_engine} templates")

    return summaries


def generate_suggested_focus(obs: AiCallObservation) -> list[str]:
    """Generate suggested testing focus areas."""
    suggestions = []

    # Heuristic verification
    if obs.detection_method == DetectionMethod.HEURISTIC:
        suggestions.append("Verify if this candidate is an AI operation")

    # Based on output flow
    if obs.usage.used_in_conditional:
        suggestions.append("Test classification across full output space")
        suggestions.append("Focus on boundary cases between categories")

    if obs.usage.returned_from_function:
        suggestions.append("Test output format consistency")

    # Based on validation
    if not obs.outputs.validation:
        if obs.outputs.expected_format == "json":
            suggestions.append("Probe for JSON format violations")
        suggestions.append("Test with adversarial inputs")

    # Based on input sources
    external_sources = [
        cv
        for cv in obs.inputs.context_variables
        if cv.source_type in {SourceType.USER_INPUT, SourceType.DATABASE, SourceType.API}
    ]

    if external_sources:
        suggestions.append("Verify behavior with varied context data")

        if any(cv.source_type == SourceType.USER_INPUT for cv in external_sources):
            suggestions.append("Test with malformed user input")

        if any(cv.source_type == SourceType.DATABASE for cv in external_sources):
            suggestions.append("Test with edge case database records")

    # Prompt source
    if obs.inputs.system_prompt and obs.inputs.system_prompt.source_type == SourceType.API:
        suggestions.append("Test across prompt versions")

    # Limit suggestions
    return suggestions[:5]


# =============================================================================
# MAIN INTERPRETATION
# =============================================================================


def interpret_observation(obs: AiCallObservation) -> Interpretation:
    """
    Generate interpretation for an observation.

    Args:
        obs: AiCallObservation to interpret

    Returns:
        Interpretation with risk tier and suggestions
    """
    return Interpretation(
        version=INTERPRETATION_VERSION,
        risk_tier=compute_risk_tier(obs),
        scenario_complexity=compute_scenario_complexity(obs),
        observations_summary=generate_observations_summary(obs),
        suggested_focus=generate_suggested_focus(obs),
    )


def interpret_all(observations: list[AiCallObservation]) -> list[AiCallObservation]:
    """
    Add interpretations to all observations.

    Args:
        observations: List of observations

    Returns:
        Same observations with interpretation field populated
    """
    for obs in observations:
        obs.interpretation = interpret_observation(obs)

    return observations


def sort_by_risk(observations: list[AiCallObservation]) -> list[AiCallObservation]:
    """
    Sort observations by risk tier (highest first).

    Args:
        observations: List of observations

    Returns:
        Sorted list (CRITICAL first, LOW last)
    """
    tier_order = {
        RiskTier.CRITICAL: 0,
        RiskTier.HIGH: 1,
        RiskTier.MEDIUM: 2,
        RiskTier.LOW: 3,
    }

    def sort_key(obs: AiCallObservation) -> tuple[int, str]:
        tier = obs.interpretation.risk_tier if obs.interpretation else RiskTier.LOW
        return (tier_order.get(tier, 4), obs.location.file)

    return sorted(observations, key=sort_key)
