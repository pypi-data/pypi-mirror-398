"""Logic for comparing discovery outputs."""

from typing import Any

from flightline.discover.schema import DiscoveryOutput, RiskTier


def compare_discoveries(current: DiscoveryOutput, baseline: DiscoveryOutput) -> dict[str, Any]:
    """
    Compare two discovery outputs and return the differences.

    Args:
        current: Current discovery output
        baseline: Baseline discovery output

    Returns:
        Dict with new, removed, and changed nodes
    """
    current_ids = {node.id: node for node in current.nodes}
    baseline_ids = {node.id: node for node in baseline.nodes}

    new_nodes = [node for node_id, node in current_ids.items() if node_id not in baseline_ids]
    removed_nodes = [node for node_id, node in baseline_ids.items() if node_id not in current_ids]

    risk_changes = []

    tier_order = {
        RiskTier.CRITICAL: 0,
        RiskTier.HIGH: 1,
        RiskTier.MEDIUM: 2,
        RiskTier.LOW: 3,
    }

    for node_id, node in current_ids.items():
        if node_id in baseline_ids:
            old_node = baseline_ids[node_id]
            old_tier = old_node.interpretation.risk_tier if old_node.interpretation else RiskTier.LOW
            new_tier = node.interpretation.risk_tier if node.interpretation else RiskTier.LOW

            if old_tier != new_tier:
                old_val = tier_order.get(old_tier, 4)
                new_val = tier_order.get(new_tier, 4)

                direction = "increased" if new_val < old_val else "decreased"

                risk_changes.append(
                    {"id": node_id, "old_tier": old_tier, "new_tier": new_tier, "direction": direction, "node": node}
                )

    return {"new": new_nodes, "removed": removed_nodes, "risk_changes": risk_changes}
