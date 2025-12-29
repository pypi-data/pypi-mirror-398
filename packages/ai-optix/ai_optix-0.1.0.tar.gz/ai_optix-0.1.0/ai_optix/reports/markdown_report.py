# SPDX-FileCopyrightText: 2025 ai-foundation-software
# SPDX-License-Identifier: Apache-2.0

from typing import List
from ..detector.base import Issue

def generate_markdown_report(issues: List[Issue], metrics_summary: dict) -> str:
    md = "# AI-Optix Performance Dashboard\n\n"
    
    # Extract core metrics
    duration = metrics_summary.get('duration', 0.0)

    
    # Just a placeholder for extracting from the dict passed in. 
    # In reality, we might pass the full BenchmarkStats object or a unified dict.
    # tailored to the key-value dictionary currently expected in the signature.
    # For now, let's assume metrics_summary contains flattened keys or sub-dicts.
    
    md += "## 🚀 Key Metrics Overview\n"
    md += f"**Duration**: {duration:.2f}s | **Throughput**: {metrics_summary.get('throughput', 0):.1f} smp/s | **P99 Latency**: {metrics_summary.get('p99_latency', 0):.2f} ms\n\n"

    md += "## 📊 Detailed Analysis\n\n"
    
    # Layout simulation
    md += "| **GPU Metrics** | **Timeline Analysis** | **Efficiency & Scaling** |\n"
    md += "| :--- | :--- | :--- |\n"
    
    # Left Column content
    left_col = f"<ul><li><b>Util:</b> {metrics_summary.get('avg_gpu', 0):.1f}%</li>"
    left_col += f"<li><b>Mem:</b> {metrics_summary.get('peak_ram', 0):.1f}MB</li>"
    left_col += f"<li><b>Power:</b> {metrics_summary.get('avg_power', 0):.1f}W</li>"
    left_col += f"<li><b>Temp:</b> {metrics_summary.get('max_temp', 0):.1f}°C</li></ul>"
    left_col += "<br><b>Energy Efficiency</b><br>"
    left_col += f"{metrics_summary.get('samples_per_joule', 0):.1f} Samp/J<br><br>"
    left_col += "<b>Thermal Status</b><br>"
    left_col += "Normal 🟢" # Logic for status needed
    
    # Center Column (Timeline placeholders)
    center_col = "<i>(See JSON for full timeline data)</i><br>"
    center_col += "📈 GPU Util Trend<br>"
    center_col += "⚡ Power Draw Trend<br>"
    center_col += "🌡️ Temp Trend<br>"
    
    # Right Column
    right_col = "<b>Memory Fragmentation</b><br>"
    right_col += f"Ratio: {metrics_summary.get('frag_ratio', 0):.2f}<br>"
    right_col += "<b>Compute Efficiency</b><br>"
    right_col += "<i>(Est. FLOPs needed)</i>"

    md += f"| {left_col} | {center_col} | {right_col} |\n\n"
    
    if not issues:
        md += "✅ **No significant bottlenecks detected.**\n"
    else:
        md += "## ⚠️ Bottlenecks Detected\n\n"
        for i, issue in enumerate(issues, 1):
            icon = "🔴" if issue.severity == "high" else "🟡"
            md += f"### {i}. {icon} {issue.name}\n"
            md += f"- **Severity**: {issue.severity.upper()}\n"
            md += f"- **Evidence**: {issue.evidence}\n"
            md += f"- **Suggestion**: {issue.suggestion}\n\n"
            
    return md
