"""
Usage tracking utilities for LLMs and Agents.
"""

from typing import List, Dict, Any, Optional


class UsageTracker:
    """
    Tracks usage records as a list of dictionaries.
    
    Each record contains usage and cost information. For Agent usage,
    records also include conversation_id.
    """
    
    def __init__(self, include_conversation_id: bool = False) -> None:
        """
        Initialize a UsageTracker.
        
        Args:
            include_conversation_id: If True, records will include conversation_id field.
                Used for Agent tracking. Default: False (for LLM tracking).
        """
        self.include_conversation_id = include_conversation_id
        self.records: List[Dict[str, Any]] = []
    
    def add_record(
        self,
        usage: Optional[Dict[str, Any]] = None,
        cost: Optional[Dict[str, Any]] = None,
        llm: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> None:
        """
        Add a usage record from usage and cost dictionaries.
        
        Args:
            usage: Dictionary with input_tokens, output_tokens, and total_tokens.
                   None if not available.
            cost: Dictionary with input_cost, output_cost, and total_cost.
                  None if not available.
            llm: Optional LLM identifier (key or model name). None if not available.
            conversation_id: Optional conversation ID. Only used if include_conversation_id is True.
        """
        # Extract tokens from usage dictionary - use None for missing values
        input_tokens = usage.get("input_tokens") if usage else None
        output_tokens = usage.get("output_tokens") if usage else None
        total_tokens = usage.get("total_tokens") if usage else None
        
        # Extract costs from cost dictionary - use None for missing values
        input_cost = cost.get("input_cost") if cost else None
        output_cost = cost.get("output_cost") if cost else None
        total_cost = cost.get("total_cost") if cost else None
        
        record = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
        }
        
        if llm is not None:
            record["llm"] = llm
        
        if self.include_conversation_id and conversation_id is not None:
            record["conversation_id"] = conversation_id
        
        self.records.append(record)
    
    def get_dataframe(self):
        """
        Convert usage records to a pandas DataFrame.
        
        Returns:
            pandas DataFrame with all usage records.
        
        Raises:
            ImportError: If pandas is not installed.
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "pandas is required to convert usage records to DataFrame. "
                "Install it with: pip install pandas"
            )
        
        if not self.records:
            # Return empty DataFrame with correct columns
            columns = [
                "input_tokens", "output_tokens", "total_tokens",
                "input_cost", "output_cost", "total_cost"
            ]
            # Check if any record would have llm (we can't check empty list, so assume it might)
            if True:  # llm is optional, so we include it if it might be used
                columns.insert(0, "llm")
            if self.include_conversation_id:
                columns.insert(1, "conversation_id")
            return pd.DataFrame(columns=columns)
        
        return pd.DataFrame(self.records)
    
    def get_aggregated_dataframe(
        self,
        group_by: Optional[List[str]] = None,
    ):
        """
        Get aggregated usage as a DataFrame.
        
        Args:
            group_by: List of columns to group by. If None and include_conversation_id is True,
                defaults to ["llm", "conversation_id"]. If None and include_conversation_id is False,
                defaults to ["llm"] if llm is present, otherwise returns totals only.
        
        Returns:
            pandas DataFrame with aggregated usage, including total columns.
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "pandas is required to get aggregated usage DataFrame. "
                "Install it with: pip install pandas"
            )
        
        df = self.get_dataframe()
        
        if df.empty:
            return df
        
        # Determine default group_by
        if group_by is None:
            group_by = []
            if "llm" in df.columns:
                group_by.append("llm")
            if self.include_conversation_id and "conversation_id" in df.columns:
                group_by.append("conversation_id")
        
        if not group_by:
            # No grouping - return totals
            return pd.DataFrame([{
                "input_tokens": df["input_tokens"].sum(),
                "output_tokens": df["output_tokens"].sum(),
                "total_tokens": df["total_tokens"].sum(),
                "input_cost": df["input_cost"].sum(),
                "output_cost": df["output_cost"].sum(),
                "total_cost": df["total_cost"].sum(),
            }])
        
        # Group by specified columns and aggregate
        numeric_columns = [
            "input_tokens", "output_tokens", "total_tokens",
            "input_cost", "output_cost", "total_cost"
        ]
        aggregated = df.groupby(group_by, as_index=False)[numeric_columns].sum()
        
        return aggregated
    
    def get_total_usage(
        self,
        llm: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Optional[int]]:
        """
        Get total usage (tokens) optionally filtered by llm and/or conversation_id.
        
        Args:
            llm: Optional LLM identifier to filter by. If None, includes all LLMs.
            conversation_id: Optional conversation ID to filter by. Only used if include_conversation_id is True.
        
        Returns:
            Dictionary with "input_tokens", "output_tokens", and "total_tokens".
            Values are None if no records match or if all token values are None.
        """
        filtered_records = self._filter_records(llm=llm, conversation_id=conversation_id)
        
        if not filtered_records:
            return {
                "input_tokens": None,
                "output_tokens": None,
                "total_tokens": None,
            }
        
        input_tokens_list = [r["input_tokens"] for r in filtered_records if r["input_tokens"] is not None]
        output_tokens_list = [r["output_tokens"] for r in filtered_records if r["output_tokens"] is not None]
        total_tokens_list = [r["total_tokens"] for r in filtered_records if r["total_tokens"] is not None]
        
        return {
            "input_tokens": sum(input_tokens_list) if input_tokens_list else None,
            "output_tokens": sum(output_tokens_list) if output_tokens_list else None,
            "total_tokens": sum(total_tokens_list) if total_tokens_list else None,
        }
    
    def get_total_cost(
        self,
        llm: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Optional[float]]:
        """
        Get total cost optionally filtered by llm and/or conversation_id.
        
        Args:
            llm: Optional LLM identifier to filter by. If None, includes all LLMs.
            conversation_id: Optional conversation ID to filter by. Only used if include_conversation_id is True.
        
        Returns:
            Dictionary with "input_cost", "output_cost", and "total_cost".
            Values are None if no records match or if all cost values are None.
        """
        filtered_records = self._filter_records(llm=llm, conversation_id=conversation_id)
        
        if not filtered_records:
            return {
                "input_cost": None,
                "output_cost": None,
                "total_cost": None,
            }
        
        input_cost_list = [r["input_cost"] for r in filtered_records if r["input_cost"] is not None]
        output_cost_list = [r["output_cost"] for r in filtered_records if r["output_cost"] is not None]
        total_cost_list = [r["total_cost"] for r in filtered_records if r["total_cost"] is not None]
        
        return {
            "input_cost": sum(input_cost_list) if input_cost_list else None,
            "output_cost": sum(output_cost_list) if output_cost_list else None,
            "total_cost": sum(total_cost_list) if total_cost_list else None,
        }
    
    def _filter_records(
        self,
        llm: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Filter records by llm and/or conversation_id.
        
        Args:
            llm: Optional LLM identifier to filter by.
            conversation_id: Optional conversation ID to filter by.
        
        Returns:
            List of filtered records.
        """
        filtered = self.records
        
        if llm is not None:
            filtered = [r for r in filtered if r.get("llm") == llm]
        
        if conversation_id is not None and self.include_conversation_id:
            filtered = [r for r in filtered if r.get("conversation_id") == conversation_id]
        
        return filtered

