from dataclasses import dataclass
from enum import Enum
from typing import List

from .explain_metrics import ExplainMetrics
from .explain_parser import ExplainPlan


class AntiPatternType(Enum):
    LARGE_SEQ_SCAN = "Large Sequential Scan"
    HIGH_ESTIMATION_ERROR = "High Estimation Error"
    INEFFICIENT_FILTER = "Inefficient Filter"


@dataclass
class ExplainAntiPattern:
    """Represents a detected anti-pattern in an EXPLAIN plan."""

    pattern_type: AntiPatternType
    description: str
    severity: str = "Medium"


class AntiPatternDetector:
    """Detects anti-patterns in EXPLAIN plans."""

    def detect(
        self, plan: ExplainPlan, metrics: ExplainMetrics
    ) -> List[ExplainAntiPattern]:
        """
        Detects anti-patterns in a parsed EXPLAIN plan.

        Args:
            plan: The parsed EXPLAIN plan.
            metrics: The extracted metrics from the plan.

        Returns:
            A list of detected anti-patterns.
        """
        anti_patterns = []

        if metrics.large_seq_scans > 0:
            anti_patterns.append(
                ExplainAntiPattern(
                    pattern_type=AntiPatternType.LARGE_SEQ_SCAN,
                    description=(
                        f"Detected {metrics.large_seq_scans} sequential scan(s) "
                        "on large tables (>10k rows)."
                    ),
                    severity="High",
                )
            )

        if (
            metrics.max_rows_discrepancy is not None
            and metrics.max_rows_discrepancy > 10
        ):
            anti_patterns.append(
                ExplainAntiPattern(
                    pattern_type=AntiPatternType.HIGH_ESTIMATION_ERROR,
                    description=(
                        "Planner's row estimation was off by "
                        f"{metrics.max_rows_discrepancy:.1%} on node "
                        f"'{metrics.max_rows_discrepancy_node}'. Consider running "
                        "ANALYZE."
                    ),
                    severity="Medium",
                )
            )

        # This is a naive check. A better one would traverse the tree and check each
        # filter.
        if self._has_inefficient_filter(plan):
            anti_patterns.append(
                ExplainAntiPattern(
                    pattern_type=AntiPatternType.INEFFICIENT_FILTER,
                    description=(
                        "A filter removed a very high percentage of rows, suggesting "
                        "a missing index."
                    ),
                    severity="High",
                )
            )

        return anti_patterns

    def _has_inefficient_filter(self, node: ExplainPlan) -> bool:
        """Recursively check for inefficient filters."""
        if not node:
            return False

        if (
            node.node_type == "Filter"
            and node.plan_rows
            and node.actual_rows is not None
        ):
            if node.plan_rows > 1000 and (node.actual_rows / node.plan_rows) < 0.01:
                return True

        if node.plans:
            for sub_plan in node.plans:
                if self._has_inefficient_filter(sub_plan):
                    return True

        return False
