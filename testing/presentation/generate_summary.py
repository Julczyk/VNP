#!/usr/bin/env python3
"""
Generuje podsumowanie wynikow eksploracji symulacji.
"""

import json
from pathlib import Path
from datetime import datetime


def load_results(directory: Path) -> dict:
    """Wczytuje wszystkie wyniki JSON z katalogu."""
    results = {}
    for f in directory.glob("*.json"):
        name = f.stem.replace("_results", "")
        with open(f, 'r') as fp:
            results[name] = json.load(fp)
    return results


def format_results_table(results: dict, title: str) -> str:
    """Formatuje wyniki jako tabele markdown."""
    lines = [f"## {title}\n"]
    lines.append("| Program | Final Tick | Automata | Offspring | Resources |")
    lines.append("|---------|------------|----------|-----------|-----------|")

    for name, data in sorted(results.items()):
        tick = data.get("final_tick", "?")
        automata = data.get("final_automata_count", 0)
        stats = data.get("stats_summary", {})
        offspring = stats.get("total_offspring", 0) if stats else 0
        resources = round(stats.get("total_resources", 0), 1) if stats else 0
        lines.append(f"| {name} | {tick} | {automata} | {offspring} | {resources} |")

    return "\n".join(lines)


def format_mixed_results(results: dict) -> str:
    """Formatuje wyniki symulacji mieszanych."""
    lines = ["## E4: Mixed Strategy Simulations\n"]

    for name, data in sorted(results.items()):
        lines.append(f"### {name}")
        lines.append(f"- Final tick: {data.get('final_tick', '?')}")
        lines.append(f"- Total automata at end: {data.get('final_automata_count', 0)}")

        if 'final_by_strategy' in data:
            lines.append("- Survivors by strategy:")
            for strat, count in sorted(data['final_by_strategy'].items()):
                lines.append(f"  - {strat}: {count}")
        lines.append("")

    return "\n".join(lines)


def main():
    base_dir = Path(__file__).parent / "results"

    report = [
        "# VNP Simulation Exploration Results",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Memory Convention",
        "- X[0] = energy (0.0-1.0)",
        "- X[1] = direction to resource (scanner result)",
        "- X[2] = distance to resource (scanner result)",
        "",
    ]

    # E1: Strategie
    strategies_dir = base_dir / "strategies"
    if strategies_dir.exists():
        results = load_results(strategies_dir)
        if results:
            report.append(format_results_table(results, "E1: Strategy Comparison (25 automata start)"))
            report.append("\n### Strategy Observations:")
            report.append("- **intelligent**: Adapts behavior based on energy levels")
            report.append("- **simple**: Baseline strategy - scan, collect, move")
            report.append("- **safe**: Prioritizes energy conservation")
            report.append("- **traveler**: Fast exploration with quick movements")
            report.append("- **standard**: Balanced approach")
            report.append("- **static**: Stays in place when collecting\n")

    # E2: Scale
    scales_dir = base_dir / "scales"
    if scales_dir.exists():
        results = load_results(scales_dir)
        if results:
            report.append(format_results_table(results, "E2: Part Scale Comparison"))
            report.append("\n### Scale Observations:")
            report.append("- Larger parts = higher mass = more energy consumption")
            report.append("- Storage capacity is critical for reproduction\n")

    # E3: Worlds
    worlds_dir = base_dir / "worlds"
    if worlds_dir.exists():
        results = load_results(worlds_dir)
        if results:
            report.append(format_results_table(results, "E3: World Configuration Comparison"))
            report.append("\n### World Observations:")
            report.append("- **easy_resources**: Higher resource thresholds = more resources")
            report.append("- **hard_resources**: Lower thresholds = fewer resources")
            report.append("- World seed significantly affects automaton success\n")

    # E4: Mixed
    mixed_dir = base_dir / "mixed"
    if mixed_dir.exists():
        results = load_results(mixed_dir)
        if results:
            report.append(format_mixed_results(results))
            report.append("### Mixed Strategy Observations:")
            report.append("- Different strategies compete for resources")
            report.append("- Some strategies may outperform others in mixed environments\n")

    # Summary
    report.append("## Key Findings")
    report.append("1. **Energy management** is crucial for long-term survival")
    report.append("2. **Storage capacity** enables resource accumulation for reproduction")
    report.append("3. **World configuration** (seed, thresholds) dramatically affects outcomes")
    report.append("4. **Strategy selection** depends on environment and competition")
    report.append("5. **Idle loop prevention** is essential - always have a fallback action")

    # Save report
    output_file = base_dir / "SUMMARY.md"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        f.write("\n".join(report))

    print(f"Report saved to: {output_file}")
    print("\n" + "\n".join(report))


if __name__ == "__main__":
    main()
