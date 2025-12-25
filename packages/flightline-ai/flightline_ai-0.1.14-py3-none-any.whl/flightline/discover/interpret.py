"""Interpretation layer for observations.

Converts raw observations into risk tiers and actionable summaries.
This layer is versioned separately and can evolve without breaking the stable schema.
"""

from typing import List, Tuple

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

INTERPRETATION_VERSION = "0.1.0"


# =============================================================================
# INTERPRETATION LOGIC
# =============================================================================


def interpret_observation(obs: AiCallObservation) -> Interpretation:
    """Analyze a raw observation and assign risk/complexity."""

    # 1. Determine Risk Tier
    # Start with LOW and increase based on "blast radius" signals
    risk = RiskTier.LOW

    # Signal: Writing to database or API
    has_side_effects = any(s in obs.usage.sinks for s in (SinkType.DATABASE, SinkType.API))

    # Signal: High-risk input sources
    has_external_inputs = any(
        cv.source_type in (SourceType.USER_INPUT, SourceType.API) for cv in obs.inputs.context_variables
    ) or (obs.inputs.system_prompt and obs.inputs.system_prompt.source_type in (SourceType.USER_INPUT, SourceType.API))

    # Signal: Lack of validation
    has_validation = obs.outputs.validation is not None

    # Logic for risk assignment
    if has_side_effects and has_external_inputs and not has_validation:
        risk = RiskTier.CRITICAL
    elif has_side_effects and has_external_inputs:
        risk = RiskTier.HIGH
    elif has_side_effects or has_external_inputs:
        risk = RiskTier.MEDIUM

    # 2. Determine Scenario Complexity
    complexity = ScenarioComplexity.SIMPLE
    if has_external_inputs:
        complexity = ScenarioComplexity.COMPLEX
    if has_side_effects:
        complexity = ScenarioComplexity.ADVERSARIAL

    # 3. Generate summary and focus
    return Interpretation(
        version=INTERPRETATION_VERSION,
        risk_tier=risk,
        scenario_complexity=complexity,
        observations_summary=generate_observations_summary(obs),
        suggested_focus=generate_suggested_focus(obs),
    )


def generate_observations_summary(obs: AiCallObservation) -> List[str]:
    """Create human-readable highlights of the observation."""
    summary = []

    # Source highlights
    if obs.detection_method == DetectionMethod.SDK_VERIFIED:
        summary.append(f"Verified {obs.provider.value.upper()} integration")
    else:
        summary.append("Detected via custom heuristic match")

    # Input highlights
    if obs.inputs.system_prompt and obs.inputs.system_prompt.source_type == SourceType.INLINE:
        summary.append("Hardcoded system prompt found")

    ext_vars = [
        cv.name for cv in obs.inputs.context_variables if cv.source_type in (SourceType.USER_INPUT, SourceType.API)
    ]
    if ext_vars:
        summary.append(f"Injects external context: {', '.join(ext_vars[:2])}")

    # Flow highlights
    if SinkType.DATABASE in obs.usage.sinks:
        summary.append("Output flows to database (side effects)")
    if SinkType.API in obs.usage.sinks:
        summary.append("Output flows to external API (side effects)")

    if obs.outputs.validation:
        summary.append(f"Validated via {obs.outputs.validation.type.value.upper()}")
    else:
        summary.append("No explicit output validation detected")

    return summary


def generate_suggested_focus(obs: AiCallObservation) -> List[str]:
    """Identify key areas for testing based on observation."""
    focus = []

    if SinkType.DATABASE in obs.usage.sinks:
        focus.append("Validate data integrity of database writes")

    if any(cv.source_type == SourceType.USER_INPUT for cv in obs.inputs.context_variables):
        focus.append("Test for prompt injection via user-controlled variables")

    if not obs.outputs.validation:
        focus.append("Verify handling of malformed or unexpected LLM responses")

    if obs.usage.used_in_conditional:
        focus.append("Verify branching logic for different LLM output scenarios")

    return focus


# =============================================================================
# BATCH INTERPRETATION
# =============================================================================


def interpret_all(observations: List[AiCallObservation]) -> List[AiCallObservation]:
    """Apply interpretation to all observations."""
    for obs in observations:
        obs.interpretation = interpret_observation(obs)
    return observations


def sort_by_risk(observations: List[AiCallObservation]) -> List[AiCallObservation]:
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

    def sort_key(obs: AiCallObservation) -> Tuple[int, str]:
        tier = obs.interpretation.risk_tier if obs.interpretation else RiskTier.LOW
        return (tier_order.get(tier, 4), obs.location.file)

    return sorted(observations, key=sort_key)
