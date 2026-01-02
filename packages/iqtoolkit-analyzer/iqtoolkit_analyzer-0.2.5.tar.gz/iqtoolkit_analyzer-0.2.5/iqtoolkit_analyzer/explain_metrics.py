from dataclasses import dataclass, field
from typing import List, Optional

from .explain_parser import ExplainPlan


@dataclass
class ExplainMetrics:
    """Holds extracted metrics from an EXPLAIN plan."""

    planning_time: Optional[float] = None
    execution_time: Optional[float] = None
    total_time: Optional[float] = None
    node_types: List[str] = field(default_factory=list)
    total_nodes: int = 0
    max_rows_discrepancy: Optional[float] = None
    max_rows_discrepancy_node: Optional[str] = None
    large_seq_scans: int = 0
    filter_inefficiency: Optional[float] = None


class MetricsExtractor:
    """Extracts performance metrics from a parsed EXPLAIN plan."""

    def extract(self, plan: ExplainPlan) -> ExplainMetrics:
        """
        Extracts metrics from an ExplainPlan object.

        Args:
            plan: The parsed EXPLAIN plan.

        Returns:
            An ExplainMetrics object.
        """
        metrics = ExplainMetrics()
        self._traverse_plan(plan, metrics)
        metrics.total_nodes = len(metrics.node_types)

        if plan.actual_total_time:
            metrics.execution_time = plan.actual_total_time

        # Note: planning_time and execution_time are at the top level of the
        # full JSON output, not within the 'Plan' node itself.
        # This will be handled when we process the full JSON.
        # For now, total_time is the root node's time.
        metrics.total_time = plan.actual_total_time

        return metrics

    def _traverse_plan(self, node: ExplainPlan, metrics: ExplainMetrics) -> None:
        """Recursively traverses the plan tree to extract metrics."""
        if not node:
            return

        metrics.node_types.append(node.node_type)

        # Row discrepancy
        if node.plan_rows and node.actual_rows is not None and node.plan_rows > 0:
            discrepancy = abs(node.plan_rows - node.actual_rows) / node.plan_rows
            if (
                metrics.max_rows_discrepancy is None
                or discrepancy > metrics.max_rows_discrepancy
            ):
                metrics.max_rows_discrepancy = discrepancy
                metrics.max_rows_discrepancy_node = node.node_type

        # Large sequential scans
        if (
            node.node_type == "Seq Scan"
            and node.actual_rows is not None
            and node.actual_rows > 10000
        ):
            metrics.large_seq_scans += 1

        if node.plans:
            for sub_plan in node.plans:
                self._traverse_plan(sub_plan, metrics)
