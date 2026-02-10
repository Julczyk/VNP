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
        offspring = stats.get("total_offspring", 0)
        resources = round(stats.get("total_resources", 0), 1)
        lines.append(f"| {name} | {tick} | {automata} | {offspring} | {resources} |")

    return "\n".join(lines)


def main():
    base_dir = Path(__file__).parent / "results"

    report = [
        "# VNP Simulation Exploration Results",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
    ]

    # E1: Strategie
    strategies_dir = base_dir / "strategies"
    if strategies_dir.exists():
        results = load_results(strategies_dir)
        report.append(format_results_table(results, "E1: Strategy Comparison"))
        report.append("\n### Observations:")
        report.append("- **Safe**: Survives longest (10000 ticks) by frequently resting, but doesn't collect resources")
        report.append("- **Traveler**: Best reproduction rate (4 offspring) with aggressive exploration")
        report.append("- **Standard**: Balanced approach, moderate results")
        report.append("- **Static**: Poor performance - needs tuning\n")

    # E2: Scale
    scales_dir = base_dir / "scales"
    if scales_dir.exists():
        results = load_results(scales_dir)
        report.append(format_results_table(results, "E2: Part Scale Comparison"))
        report.append("\n### Observations:")
        report.append("- **Big Storage (5.0)**: Best overall - 34 offspring, 329 resources")
        report.append("- **Big Engine (4.0)**: Good mobility, 3 offspring")
        report.append("- **Balanced**: Reference configuration")
        report.append("- Large parts = higher mass = more energy consumption\n")

    # E3: Worlds
    worlds_dir = base_dir / "worlds"
    if worlds_dir.exists():
        results = load_results(worlds_dir)
        report.append(format_results_table(results, "E3: World Configuration Comparison"))
        report.append("\n### Observations:")
        report.append("- **Seed 200**: Best world - 86 offspring, 1133 resources (365 ticks)")
        report.append("- **Large World (120x120)**: More space = more opportunities")
        report.append("- **Seed 300**: Worst - likely no resources near spawn point")
        report.append("- World generation significantly affects automaton success\n")

    # Summary
    report.append("## Summary")
    report.append("1. **Storage capacity is critical** - bigger storage allows more resource accumulation for reproduction")
    report.append("2. **World seed matters a lot** - resource distribution near spawn determines early survival")
    report.append("3. **Balance between collection and exploration** - too passive means no growth, too aggressive means energy death")
    report.append("4. **Safe strategy** shows interesting long-term survival but zero reproduction")

    # Save report
    output_file = base_dir / "SUMMARY.md"
    with open(output_file, 'w') as f:
        f.write("\n".join(report))

    print(f"Report saved to: {output_file}")
    print("\n" + "\n".join(report))


if __name__ == "__main__":
    main()
