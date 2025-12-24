"""
Token Usage Tracking for TOON Format.

Automatically logs token usage statistics for inter-agent communication
to measure and validate TOON format savings.

Features:
- Automatic logging of encode/decode operations
- Daily aggregation of token savings
- CSV export for analysis
- Rich UI statistics display

Storage:
- Metrics stored in .claude/metrics/
- Daily files: .claude/metrics/YYYY-MM-DD.json
- Aggregated stats: .claude/metrics/summary.json
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class TokenMetric:
    """Single token usage measurement."""

    timestamp: str
    operation: str  # "encode" or "decode"
    from_agent: Optional[str]
    to_agent: Optional[str]
    json_tokens: int
    toon_tokens: int
    savings_tokens: int
    savings_percent: float
    format_used: str  # "TOON" or "JSON"
    data_type: str  # "plan", "report", "message", "other"


@dataclass
class DailySummary:
    """Daily aggregated statistics."""

    date: str
    total_operations: int
    total_json_tokens: int
    total_toon_tokens: int
    total_savings_tokens: int
    average_savings_percent: float
    operations_by_type: Dict[str, int]
    operations_by_agent_pair: Dict[str, int]


class TokenUsageTracker:
    """
    Track token usage for TOON format operations.

    Automatically logs all encode/decode operations and provides
    statistics on token savings.

    Examples:
        >>> tracker = TokenUsageTracker()
        >>>
        >>> # Log an encoding operation
        >>> tracker.log_encode(
        ...     data={"tasks": [...]},
        ...     json_tokens=150,
        ...     toon_tokens=90,
        ...     from_agent="orchestrator",
        ...     to_agent="bug-fixer",
        ...     data_type="plan"
        ... )
        >>>
        >>> # Get today's stats
        >>> stats = tracker.get_daily_stats()
        >>> print(f"Saved {stats.total_savings_tokens} tokens today")
    """

    def __init__(self, metrics_dir: Optional[Path] = None):
        """
        Initialize token usage tracker.

        Args:
            metrics_dir: Directory to store metrics (default: .claude/metrics/)
        """
        if metrics_dir is None:
            # Use project root .claude/metrics/
            self.metrics_dir = Path.cwd() / ".claude" / "metrics"
        else:
            self.metrics_dir = Path(metrics_dir)

        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_summary_exists()

    def _ensure_summary_exists(self):
        """Ensure summary.json exists with default structure."""
        summary_path = self.metrics_dir / "summary.json"
        if not summary_path.exists():
            summary = {
                "created": datetime.utcnow().isoformat() + "Z",
                "last_updated": datetime.utcnow().isoformat() + "Z",
                "total_operations": 0,
                "total_savings_tokens": 0,
                "total_json_tokens": 0,
                "total_toon_tokens": 0,
                "average_savings_percent": 0.0,
            }
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)

    def _get_daily_file(self, date: Optional[datetime] = None) -> Path:
        """Get path to daily metrics file."""
        if date is None:
            date = datetime.utcnow()
        filename = f"{date.strftime('%Y-%m-%d')}.json"
        return self.metrics_dir / filename

    def log_operation(
        self,
        operation: str,
        json_tokens: int,
        toon_tokens: int,
        savings_percent: float,
        format_used: str = "TOON",
        from_agent: Optional[str] = None,
        to_agent: Optional[str] = None,
        data_type: str = "other",
    ):
        """
        Log a single token usage operation.

        Args:
            operation: "encode" or "decode"
            json_tokens: Token count with JSON format
            toon_tokens: Token count with TOON format
            savings_percent: Percentage saved
            format_used: Format actually used ("TOON" or "JSON")
            from_agent: Source agent (if applicable)
            to_agent: Destination agent (if applicable)
            data_type: Type of data ("plan", "report", "message", "other")
        """
        metric = TokenMetric(
            timestamp=datetime.utcnow().isoformat() + "Z",
            operation=operation,
            from_agent=from_agent,
            to_agent=to_agent,
            json_tokens=json_tokens,
            toon_tokens=toon_tokens,
            savings_tokens=json_tokens - toon_tokens,
            savings_percent=savings_percent,
            format_used=format_used,
            data_type=data_type,
        )

        # Append to daily file
        daily_file = self._get_daily_file()
        metrics = []
        if daily_file.exists():
            with open(daily_file, "r", encoding="utf-8") as f:
                metrics = json.load(f)

        metrics.append(asdict(metric))

        with open(daily_file, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)

        # Update summary
        self._update_summary(metric)

    def log_encode(
        self,
        data: Any,
        json_tokens: int,
        toon_tokens: int,
        savings_percent: float,
        from_agent: Optional[str] = None,
        to_agent: Optional[str] = None,
        data_type: str = "other",
        format_used: str = "TOON",
    ):
        """
        Log an encoding operation.

        Args:
            data: Data being encoded (for reference)
            json_tokens: Token count with JSON
            toon_tokens: Token count with TOON
            savings_percent: Percentage saved
            from_agent: Source agent
            to_agent: Destination agent
            data_type: Type of data being encoded
            format_used: Format used ("TOON" or "JSON")
        """
        self.log_operation(
            operation="encode",
            json_tokens=json_tokens,
            toon_tokens=toon_tokens,
            savings_percent=savings_percent,
            format_used=format_used,
            from_agent=from_agent,
            to_agent=to_agent,
            data_type=data_type,
        )

    def log_decode(
        self,
        toon_str: str,
        json_tokens: int,
        toon_tokens: int,
        savings_percent: float,
        from_agent: Optional[str] = None,
        to_agent: Optional[str] = None,
        data_type: str = "other",
    ):
        """
        Log a decoding operation.

        Args:
            toon_str: TOON string being decoded
            json_tokens: Equivalent JSON token count
            toon_tokens: TOON token count
            savings_percent: Percentage saved
            from_agent: Source agent
            to_agent: Destination agent
            data_type: Type of data
        """
        self.log_operation(
            operation="decode",
            json_tokens=json_tokens,
            toon_tokens=toon_tokens,
            savings_percent=savings_percent,
            format_used="TOON",
            from_agent=from_agent,
            to_agent=to_agent,
            data_type=data_type,
        )

    def _update_summary(self, metric: TokenMetric):
        """Update summary.json with new metric."""
        summary_path = self.metrics_dir / "summary.json"

        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)

        # Update totals
        summary["total_operations"] += 1
        summary["total_json_tokens"] += metric.json_tokens
        summary["total_toon_tokens"] += metric.toon_tokens
        summary["total_savings_tokens"] += metric.savings_tokens

        # Recalculate average
        if summary["total_json_tokens"] > 0:
            summary["average_savings_percent"] = round(
                (summary["total_savings_tokens"] / summary["total_json_tokens"]) * 100,
                1,
            )

        summary["last_updated"] = datetime.utcnow().isoformat() + "Z"

        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

    def get_daily_stats(self, date: Optional[datetime] = None) -> Optional[DailySummary]:
        """
        Get statistics for a specific day.

        Args:
            date: Date to get stats for (default: today)

        Returns:
            DailySummary or None if no data for that day
        """
        daily_file = self._get_daily_file(date)
        if not daily_file.exists():
            return None

        with open(daily_file, "r", encoding="utf-8") as f:
            metrics = json.load(f)

        if not metrics:
            return None

        total_json = sum(m["json_tokens"] for m in metrics)
        total_toon = sum(m["toon_tokens"] for m in metrics)
        total_savings = sum(m["savings_tokens"] for m in metrics)

        # Calculate average savings
        avg_savings = (total_savings / total_json * 100) if total_json > 0 else 0

        # Count by type
        ops_by_type = {}
        for m in metrics:
            data_type = m["data_type"]
            ops_by_type[data_type] = ops_by_type.get(data_type, 0) + 1

        # Count by agent pair
        ops_by_pair = {}
        for m in metrics:
            if m["from_agent"] and m["to_agent"]:
                pair = f"{m['from_agent']} → {m['to_agent']}"
                ops_by_pair[pair] = ops_by_pair.get(pair, 0) + 1

        return DailySummary(
            date=daily_file.stem,
            total_operations=len(metrics),
            total_json_tokens=total_json,
            total_toon_tokens=total_toon,
            total_savings_tokens=total_savings,
            average_savings_percent=round(avg_savings, 1),
            operations_by_type=ops_by_type,
            operations_by_agent_pair=ops_by_pair,
        )

    def get_summary(self) -> Dict[str, Any]:
        """
        Get overall summary statistics.

        Returns:
            Dictionary with total statistics
        """
        summary_path = self.metrics_dir / "summary.json"
        with open(summary_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_weekly_stats(self, weeks: int = 1) -> List[DailySummary]:
        """
        Get statistics for the last N weeks.

        Args:
            weeks: Number of weeks to retrieve (default: 1)

        Returns:
            List of DailySummary for each day with data
        """
        stats = []
        today = datetime.utcnow()

        for i in range(weeks * 7):
            date = today - timedelta(days=i)
            daily = self.get_daily_stats(date)
            if daily:
                stats.append(daily)

        return stats

    def export_csv(self, output_path: Path, days: int = 7):
        """
        Export metrics to CSV file.

        Args:
            output_path: Path to output CSV file
            days: Number of days to export (default: 7)
        """
        import csv

        rows = []
        today = datetime.utcnow()

        for i in range(days):
            date = today - timedelta(days=i)
            daily_file = self._get_daily_file(date)
            if daily_file.exists():
                with open(daily_file, "r", encoding="utf-8") as f:
                    metrics = json.load(f)
                    rows.extend(metrics)

        if not rows:
            return

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "timestamp",
                "operation",
                "from_agent",
                "to_agent",
                "data_type",
                "json_tokens",
                "toon_tokens",
                "savings_tokens",
                "savings_percent",
                "format_used",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)


# Global tracker instance
_tracker: Optional[TokenUsageTracker] = None


def get_tracker() -> TokenUsageTracker:
    """Get global token usage tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = TokenUsageTracker()
    return _tracker
