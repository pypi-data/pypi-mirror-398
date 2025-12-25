'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2025-06-15 10:08:52 +0200
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-06-16 08:22:17 +0200
FilePath     : plot_cutflow.py
Description  :

Copyright (c) 2025 by everyone, All Rights Reserved.
'''

from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Patch

import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ROOT imports
import ROOT as r
from ROOT import RDF

from rich import print as rprint


@dataclass
class CutFlowData:
    """Data structure for cut flow analysis results."""

    cut_names: List[str]
    events_passed: List[int]
    step_efficiencies: List[float]
    cumul_efficiencies: List[float]
    step_efficiency_errors: Optional[List[float]] = None

    def __post_init__(self):
        """Validate that all lists have the same length."""
        lengths = [
            len(self.cut_names),
            len(self.events_passed),
            len(self.step_efficiencies),
            len(self.cumul_efficiencies),
        ]
        if self.step_efficiency_errors is not None:
            lengths.append(len(self.step_efficiency_errors))
        if len(set(lengths)) > 1:
            raise ValueError(f"All lists must have same length. Got: {lengths}")

    @classmethod
    def from_dict(cls, data: dict) -> 'CutFlowData':
        """Create CutFlowData from dictionary."""
        return cls(
            cut_names=data['cut_names'],
            events_passed=data['events_passed'],
            step_efficiencies=data['step_efficiencies'],
            cumul_efficiencies=data['cumul_efficiencies'],
            step_efficiency_errors=data.get('step_efficiency_errors'),
        )


def extract_cutflow_data(report: RDF.RCutFlowReport) -> CutFlowData:
    """Extract and process cut flow data from RDataFrame report."""
    # Extract cut info from report using iterators
    cut_names: list[str] = []
    events_passed: list[int] = []
    events_all: list[int] = []

    it = report.begin()
    end = report.end()

    while it != end:
        cut_info = it.__deref__()
        cut_names.append(cut_info.GetName())
        events_passed.append(cut_info.GetPass())
        events_all.append(cut_info.GetAll())
        it.__preinc__()

    # Add original dataset as the first entry
    if events_all:
        orig_total = events_all[0]
        cut_names.insert(0, "No cuts")
        events_passed.insert(0, orig_total)
        events_all.insert(0, orig_total)

    # Calculate efficiencies
    step_efficiencies: list[float] = []
    cumul_efficiencies: list[float] = []

    for i, (passed, total) in enumerate(zip(events_passed, events_all)):
        if i == 0:
            step_efficiencies.append(100.0)
            cumul_efficiencies.append(100.0)
        else:
            prev_passed = events_passed[i - 1]
            step_eff = passed / prev_passed * 100 if prev_passed > 0 else 0
            step_efficiencies.append(step_eff)

            cumul_eff = passed / events_all[0] * 100 if events_all[0] > 0 else 0
            cumul_efficiencies.append(cumul_eff)

    # Print summary
    rprint(f"Found {len(cut_names)} entries (including original):")
    for i, (name, passed, total) in enumerate(zip(cut_names, events_passed, events_all)):
        if i == 0:
            rprint(f"  {i+1}. {name}: {passed} events (100.0%)")
        else:
            step_eff = step_efficiencies[i]
            cumul_eff = cumul_efficiencies[i]
            rprint(f"  {i+1}. {name}: {passed}/{events_passed[i-1]} (step: {step_eff:.1f}%, cumulative: {cumul_eff:.1f}%)")

    return CutFlowData(
        cut_names=cut_names,
        events_passed=events_passed,
        step_efficiencies=step_efficiencies,
        cumul_efficiencies=cumul_efficiencies,
    )


############################## ! use plotly #####################################


def plot_cut_flow_plotly(cutflow_data: CutFlowData, output_file: str):
    """Create a static cut flow plot using Plotly from processed data."""

    cut_names: list[str] = cutflow_data.cut_names
    events_passed: list[int] = cutflow_data.events_passed
    step_efficiencies: list[float] = cutflow_data.step_efficiencies
    cumul_efficiencies: list[float] = cutflow_data.cumul_efficiencies

    # Create subplot with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add bars separately for legend control
    # Original dataset bar
    fig.add_trace(
        go.Bar(
            x=[cut_names[0]],
            y=[events_passed[0]],
            name="Original Dataset",
            marker_color='lightcoral',
            text=[f'{events_passed[0]:,}<br>({cumul_efficiencies[0]:.1f}%)'],
            textposition="outside",
            showlegend=True,
        ),
        secondary_y=False,
    )

    # After cuts bars
    if len(cut_names) > 1:
        fig.add_trace(
            go.Bar(
                x=cut_names[1:],
                y=events_passed[1:],
                name="After Cuts",
                marker_color='steelblue',
                text=[f'{count:,}<br>({eff:.1f}%)' for count, eff in zip(events_passed[1:], cumul_efficiencies[1:])],
                textposition="outside",
                showlegend=True,
            ),
            secondary_y=False,
        )

    # Add line (step efficiency)
    fig.add_trace(
        go.Scatter(
            x=cut_names[1:],
            y=step_efficiencies[1:],
            mode='lines+markers+text',
            name="Step Efficiency",
            line=dict(color='red', width=3),
            marker=dict(size=8),
            text=[f'{eff:.1f}%' for eff in step_efficiencies[1:]],
            textposition="bottom right",
            textfont=dict(color='red', size=10),
            showlegend=True,
        ),
        secondary_y=True,
    )

    # Update layout
    fig.update_xaxes(title_text="Selection Stage")

    # Give more space for text labels above bars
    height_scale_factor = 1.10
    max_events = max(events_passed)
    fig.update_yaxes(
        title_text="Events Surviving",
        secondary_y=False,
        range=[0, max_events * height_scale_factor],
    )  # Add 15% extra space above

    fig.update_yaxes(title_text="Events Surviving", secondary_y=False)
    fig.update_yaxes(title_text="Step Efficiency (%)", secondary_y=True, range=[0, 100 * height_scale_factor])

    fig.update_layout(
        title="Cut Flow Analysis: Events Surviving & Efficiencies",
        width=1000,
        height=600,
        # Scientific color scheme and styling
        template='simple_white',  # Clean scientific template
        plot_bgcolor='white',
        paper_bgcolor='white',
        # Clean axes
        xaxis=dict(showline=True, mirror=True),
        yaxis=dict(showline=True, mirror=True),
    )

    # Save the plot
    output_file = Path(output_file).resolve().as_posix()
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    fig.write_image(output_file, width=1000, height=600, scale=2, engine="kaleido")
    rprint(f'Static plot saved to {output_file}')


################################# ! use matplotlib #####################################


def plot_cut_flow_matplotlib(cutflow_data: CutFlowData, output_file: str):
    """Create a static cut flow plot using matplotlib from processed data."""

    cut_names: list[str] = cutflow_data.cut_names
    events_passed: list[int] = cutflow_data.events_passed
    step_efficiencies: list[float] = cutflow_data.step_efficiencies
    cumul_efficiencies: list[float] = cutflow_data.cumul_efficiencies

    # Create single figure with dual y-axes
    if len(cut_names) <= 6:
        figwidth = 14
    else:
        figwidth = 14 + (len(cut_names) - 6) * 0.5
    fig, ax1 = plt.subplots(figsize=(figwidth, 8))

    # Left y-axis: Events surviving (bars)
    x_pos = range(len(cut_names))
    colors = ['lightcoral'] + ['steelblue'] * (len(cut_names) - 1)  # Different color for original
    bars = ax1.bar(x_pos, events_passed, color=colors, alpha=0.6, edgecolor='black', linewidth=0.5, width=0.6)
    ax1.set_xlabel('Selection Stage', fontsize=12)
    ax1.set_ylabel('Events Surviving', fontsize=12, color='steelblue')
    ax1.tick_params(axis='y', labelcolor='steelblue')
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(cut_names, rotation=45, ha='right', fontsize=11)
    ax1.grid(True, alpha=0.3)

    # Set y-axis range with more space for two-row text
    max_events = max(events_passed)
    height_scale_factor = 1.19
    ax1.set_ylim(0, max_events * height_scale_factor)  # Add 15% extra space above bars

    # Right y-axis: Efficiencies (lines)
    ax2 = ax1.twinx()
    line1 = ax2.plot(x_pos[1:], step_efficiencies[1:], 'ro-', linewidth=2, markersize=8, label='Step Efficiency', alpha=0.8)
    # line2 = ax2.plot(x_pos, cumul_efficiencies, 'go-', linewidth=2, markersize=8, label='Cumulative Efficiency', alpha=0.8)
    ax2.set_ylabel('Efficiency (%)', fontsize=12, color='darkred')
    ax2.tick_params(axis='y', labelcolor='darkred')
    ax2.set_ylim(0, 100 * height_scale_factor)  # Fixed range since we know max is 100%

    # Add combined labels: event count (cumulative efficiency %)
    for i, (bar, count, cumul_eff) in enumerate(zip(bars, events_passed, cumul_efficiencies)):
        height = bar.get_height()
        label = f'{count:,}\n({cumul_eff:.1f}%)'

        # Increase spacing above bars for two-row text
        ax1.text(i, height + max_events * 0.02, label, ha='center', va='bottom', fontweight='bold', fontsize=9, rotation=0)

    for i, step_eff in enumerate(step_efficiencies[1:], 1):  # Start from index 1
        ax2.text(i + 0.05, step_eff - 2, f'{step_eff:.1f}%', ha='left', va='top', fontweight='bold', color='red', fontsize=8, rotation=0)

    # Add legend for bars
    legend_elements = [
        Patch(facecolor='lightcoral', alpha=0.6, label='Original Dataset'),
        Patch(facecolor='steelblue', alpha=0.6, label='After Cuts'),
        plt.Line2D([0], [0], color='red', marker='o', linestyle='-', label='Step Efficiency'),
    ]
    ax1.legend(handles=legend_elements, loc='upper right')

    plt.title('Cut Flow Analysis: Events Surviving & Efficiencies', fontsize=14, fontweight='bold')
    plt.tight_layout()

    # Save the plot
    output_file = Path(output_file).resolve().as_posix()
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    rprint(f'Cut flow plot saved to {output_file}')
    plt.close()
