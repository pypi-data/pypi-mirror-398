from dataclasses import dataclass
from typing import List, Optional, Set, Tuple

from .explain_antipatterns import AntiPatternType, ExplainAntiPattern
from .explain_parser import ExplainPlan


@dataclass
class IndexRecommendation:
    """Represents a recommendation for a new index."""

    table: str
    columns: List[str]
    reason: str


class IndexRecommender:
    """Generates index recommendations from EXPLAIN plans and anti-patterns."""

    def recommend(
        self, plan: ExplainPlan, anti_patterns: List[ExplainAntiPattern]
    ) -> List[IndexRecommendation]:
        """
        Generates index recommendations.

        Args:
            plan: The parsed EXPLAIN plan.
            anti_patterns: A list of detected anti-patterns.

        Returns:
            A list of index recommendations.
        """
        recommendations = []
        for ap in anti_patterns:
            if ap.pattern_type == AntiPatternType.LARGE_SEQ_SCAN:
                # This is a naive implementation. A real implementation would need
                # to parse the filter conditions to identify the columns.
                table, columns = self._find_table_and_columns_for_seq_scan(plan)
                if table:
                    recommendations.append(
                        IndexRecommendation(
                            table=table,
                            columns=list(columns) if columns else [],
                            reason=(
                                "Sequential scan on a large table could be optimized "
                                "with an index."
                            ),
                        )
                    )
        return recommendations

    def _find_table_and_columns_for_seq_scan(
        self, node: ExplainPlan
    ) -> Tuple[Optional[str], Optional[Set[str]]]:
        """
        Finds the table and columns involved in a sequential scan.
        This is a placeholder and needs a more sophisticated implementation.
        """
        if not node:
            return None, None

        if node.node_type == "Seq Scan":
            # This is a naive way to get columns. A real implementation
            # would need to parse the 'Filter' or 'Index Cond' from the plan.
            # For now, we'll just use the relation name.
            columns: Set[str] = set()
            if node.relation_name:
                return node.relation_name, columns

        if node.plans:
            for sub_plan in node.plans:
                table, cols = self._find_table_and_columns_for_seq_scan(sub_plan)
                if table:
                    return table, cols

        return None, None
