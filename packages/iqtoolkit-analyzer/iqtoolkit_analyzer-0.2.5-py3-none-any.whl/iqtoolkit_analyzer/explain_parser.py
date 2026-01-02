import json
from typing import List, Optional

from pydantic import BaseModel, Field


class ExplainPlan(BaseModel):
    """Represents a single node in a PostgreSQL EXPLAIN plan."""

    node_type: str = Field(..., alias="Node Type")
    relation_name: Optional[str] = Field(None, alias="Relation Name")
    alias: Optional[str] = Field(None, alias="Alias")
    filter: Optional[str] = Field(None, alias="Filter")
    index_cond: Optional[str] = Field(None, alias="Index Cond")
    actual_rows: Optional[int] = Field(None, alias="Actual Rows")
    plan_rows: Optional[int] = Field(None, alias="Plan Rows")
    actual_startup_time: Optional[float] = Field(None, alias="Actual Startup Time")
    actual_total_time: Optional[float] = Field(None, alias="Actual Total Time")
    plans: Optional[List["ExplainPlan"]] = Field(None, alias="Plans")


class ExplainParser:
    """Parses PostgreSQL EXPLAIN JSON into a structured object."""

    def parse(self, explain_json: str) -> Optional[ExplainPlan]:
        """
        Parses an EXPLAIN JSON string into a structured ExplainPlan object.

        Args:
            explain_json: The EXPLAIN plan in JSON format.

        Returns:
            An ExplainPlan object, or None if parsing fails.
        """
        if not explain_json or not explain_json.strip():
            return None

        try:
            # The actual plan is usually nested under a 'Plan' key.
            # The output of auto_explain is a list containing one element.
            plan_data = json.loads(explain_json)
            if isinstance(plan_data, list) and plan_data:
                plan_data = plan_data[0]

            if "Plan" in plan_data:
                return ExplainPlan.model_validate(plan_data["Plan"])
            else:
                return None
        except (json.JSONDecodeError, TypeError):
            # Handle cases where the string is not valid JSON or not a dict
            # logger.warning(f"Failed to parse EXPLAIN JSON: {e}")
            return None
