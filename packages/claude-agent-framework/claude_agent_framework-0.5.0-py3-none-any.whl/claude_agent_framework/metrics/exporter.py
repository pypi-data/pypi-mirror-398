"""
Metrics exporter for various output formats.

Supports exporting metrics to:
- JSON (structured data)
- CSV (tabular data)
- Prometheus format (for monitoring integration)
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from claude_agent_framework.metrics.collector import SessionMetrics


class MetricsExporter:
    """Export metrics to various formats."""

    @staticmethod
    def to_json(metrics: SessionMetrics, pretty: bool = True) -> str:
        """
        Export metrics to JSON string.

        Args:
            metrics: Session metrics to export
            pretty: Whether to pretty-print JSON

        Returns:
            JSON string
        """
        data = metrics.to_dict()
        if pretty:
            return json.dumps(data, indent=2, ensure_ascii=False)
        return json.dumps(data, ensure_ascii=False)

    @staticmethod
    def to_csv_summary(metrics: SessionMetrics) -> str:
        """
        Export summary metrics to CSV format.

        Args:
            metrics: Session metrics to export

        Returns:
            CSV string with summary data
        """
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(["Metric", "Value"])

        # Session info
        writer.writerow(["Session ID", metrics.session_id])
        writer.writerow(["Architecture", metrics.architecture_name])
        writer.writerow(["Duration (ms)", f"{metrics.duration_ms:.2f}"])

        # Agent metrics
        writer.writerow(["Total Agents", metrics.agent_count])
        for agent_type, count in metrics.agent_type_distribution().items():
            writer.writerow([f"  {agent_type}", count])

        # Tool metrics
        writer.writerow(["Total Tool Calls", metrics.tool_call_count])
        writer.writerow(["Successful Tools", metrics.successful_tool_calls])
        writer.writerow(["Failed Tools", metrics.failed_tool_calls])
        writer.writerow(["Tool Error Rate", f"{metrics.tool_error_rate:.2%}"])

        # Token metrics
        writer.writerow(["Input Tokens", metrics.tokens.input_tokens])
        writer.writerow(["Output Tokens", metrics.tokens.output_tokens])
        writer.writerow(["Total Tokens", metrics.tokens.total_tokens])
        writer.writerow(["Estimated Cost (USD)", f"${metrics.estimated_cost_usd:.4f}"])

        # Memory metrics
        writer.writerow(["Peak Memory (MB)", f"{metrics.peak_memory_bytes / (1024 * 1024):.2f}"])
        writer.writerow(
            ["Average Memory (MB)", f"{metrics.average_memory_bytes / (1024 * 1024):.2f}"]
        )

        return output.getvalue()

    @staticmethod
    def to_csv_agents(metrics: SessionMetrics) -> str:
        """
        Export detailed agent metrics to CSV.

        Args:
            metrics: Session metrics to export

        Returns:
            CSV string with agent details
        """
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(["Agent Type", "Duration (ms)", "Status", "Error"])

        # Agent rows
        for agent in metrics.agents:
            writer.writerow(
                [
                    agent.agent_type,
                    f"{agent.duration_ms:.2f}",
                    agent.status,
                    agent.error or "",
                ]
            )

        return output.getvalue()

    @staticmethod
    def to_csv_tools(metrics: SessionMetrics) -> str:
        """
        Export detailed tool metrics to CSV.

        Args:
            metrics: Session metrics to export

        Returns:
            CSV string with tool call details
        """
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(["Tool Name", "Duration (ms)", "Status", "Error"])

        # Tool rows
        for tool in metrics.tools:
            writer.writerow(
                [
                    tool.tool_name,
                    f"{tool.duration_ms:.2f}",
                    tool.status,
                    tool.error or "",
                ]
            )

        return output.getvalue()

    @staticmethod
    def to_prometheus(metrics: SessionMetrics, prefix: str = "claude_agent") -> str:
        """
        Export metrics in Prometheus exposition format.

        Args:
            metrics: Session metrics to export
            prefix: Metric name prefix

        Returns:
            Prometheus format string
        """
        lines: list[str] = []

        # Session duration
        lines.append(f"# HELP {prefix}_session_duration_ms Session duration in milliseconds")
        lines.append(f"# TYPE {prefix}_session_duration_ms gauge")
        lines.append(
            f'{prefix}_session_duration_ms{{session_id="{metrics.session_id}",'
            f'architecture="{metrics.architecture_name}"}} {metrics.duration_ms}'
        )

        # Agent count
        lines.append(f"# HELP {prefix}_agents_total Total number of agents spawned")
        lines.append(f"# TYPE {prefix}_agents_total counter")
        lines.append(
            f'{prefix}_agents_total{{session_id="{metrics.session_id}",'
            f'architecture="{metrics.architecture_name}"}} {metrics.agent_count}'
        )

        # Agent type distribution
        lines.append(f"# HELP {prefix}_agents_by_type Number of agents by type")
        lines.append(f"# TYPE {prefix}_agents_by_type counter")
        for agent_type, count in metrics.agent_type_distribution().items():
            lines.append(
                f'{prefix}_agents_by_type{{session_id="{metrics.session_id}",'
                f'architecture="{metrics.architecture_name}",type="{agent_type}"}} {count}'
            )

        # Tool calls
        lines.append(f"# HELP {prefix}_tool_calls_total Total number of tool calls")
        lines.append(f"# TYPE {prefix}_tool_calls_total counter")
        lines.append(
            f'{prefix}_tool_calls_total{{session_id="{metrics.session_id}",'
            f'architecture="{metrics.architecture_name}",status="success"}} '
            f"{metrics.successful_tool_calls}"
        )
        lines.append(
            f'{prefix}_tool_calls_total{{session_id="{metrics.session_id}",'
            f'architecture="{metrics.architecture_name}",status="failed"}} '
            f"{metrics.failed_tool_calls}"
        )

        # Tool error rate
        lines.append(f"# HELP {prefix}_tool_error_rate Tool call error rate (0-1)")
        lines.append(f"# TYPE {prefix}_tool_error_rate gauge")
        lines.append(
            f'{prefix}_tool_error_rate{{session_id="{metrics.session_id}",'
            f'architecture="{metrics.architecture_name}"}} {metrics.tool_error_rate}'
        )

        # Tokens
        lines.append(f"# HELP {prefix}_tokens_total Total tokens consumed")
        lines.append(f"# TYPE {prefix}_tokens_total counter")
        lines.append(
            f'{prefix}_tokens_total{{session_id="{metrics.session_id}",'
            f'architecture="{metrics.architecture_name}",type="input"}} '
            f"{metrics.tokens.input_tokens}"
        )
        lines.append(
            f'{prefix}_tokens_total{{session_id="{metrics.session_id}",'
            f'architecture="{metrics.architecture_name}",type="output"}} '
            f"{metrics.tokens.output_tokens}"
        )

        # Cost
        lines.append(f"# HELP {prefix}_cost_usd_total Estimated cost in USD")
        lines.append(f"# TYPE {prefix}_cost_usd_total gauge")
        lines.append(
            f'{prefix}_cost_usd_total{{session_id="{metrics.session_id}",'
            f'architecture="{metrics.architecture_name}"}} {metrics.estimated_cost_usd}'
        )

        # Memory
        lines.append(f"# HELP {prefix}_memory_bytes Memory usage in bytes")
        lines.append(f"# TYPE {prefix}_memory_bytes gauge")
        lines.append(
            f'{prefix}_memory_bytes{{session_id="{metrics.session_id}",'
            f'architecture="{metrics.architecture_name}",type="peak"}} '
            f"{metrics.peak_memory_bytes}"
        )
        lines.append(
            f'{prefix}_memory_bytes{{session_id="{metrics.session_id}",'
            f'architecture="{metrics.architecture_name}",type="average"}} '
            f"{metrics.average_memory_bytes}"
        )

        return "\n".join(lines) + "\n"


# Convenience functions
def export_to_json(metrics: SessionMetrics, output_path: str | Path) -> None:
    """
    Export metrics to JSON file.

    Args:
        metrics: Session metrics to export
        output_path: Path to output file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    json_str = MetricsExporter.to_json(metrics, pretty=True)
    output_path.write_text(json_str, encoding="utf-8")


def export_to_csv(
    metrics: SessionMetrics,
    output_dir: str | Path,
    prefix: str = "metrics",
) -> dict[str, Path]:
    """
    Export metrics to multiple CSV files.

    Creates three files:
    - {prefix}_summary.csv - Summary metrics
    - {prefix}_agents.csv - Agent details
    - {prefix}_tools.csv - Tool call details

    Args:
        metrics: Session metrics to export
        output_dir: Directory for output files
        prefix: Filename prefix

    Returns:
        Dictionary mapping file type to path
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    files: dict[str, Path] = {}

    # Summary
    summary_path = output_dir / f"{prefix}_summary.csv"
    summary_path.write_text(MetricsExporter.to_csv_summary(metrics), encoding="utf-8")
    files["summary"] = summary_path

    # Agents
    agents_path = output_dir / f"{prefix}_agents.csv"
    agents_path.write_text(MetricsExporter.to_csv_agents(metrics), encoding="utf-8")
    files["agents"] = agents_path

    # Tools
    tools_path = output_dir / f"{prefix}_tools.csv"
    tools_path.write_text(MetricsExporter.to_csv_tools(metrics), encoding="utf-8")
    files["tools"] = tools_path

    return files


def export_to_prometheus(metrics: SessionMetrics, output_path: str | Path) -> None:
    """
    Export metrics to Prometheus format file.

    Args:
        metrics: Session metrics to export
        output_path: Path to output file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    prom_str = MetricsExporter.to_prometheus(metrics)
    output_path.write_text(prom_str, encoding="utf-8")
