"""
CLI Simulation and Benchmark Script (reproduces Sections 5 and 6):
- Table 2: Matching results across S1, S2, S3 for Proposed, Greedy, Nearest-first, Random
- Table 3: Low-bandwidth payload sizes for SMS grammar, full sync, and delta sync
- Table 4: Translation quality results on relief-domain test set
"""

import argparse
import sys
import json
from app.simulation.benchmark_runner import (
    run_matching_benchmark,
    run_low_bandwidth_benchmark,
    run_translation_benchmark
)

def print_separator(title: str):
    print("\n" + "=" * 80)
    print(f" {title.upper()}")
    print("=" * 80)

def main():
    parser = argparse.ArgumentParser(description="Disaster Relief Management Benchmark Suite (CSEAIML2026-P22)")
    parser.add_argument("--seeds", type=int, default=5, help="Number of random seeds (paper uses 30)")
    parser.add_argument("--save-report", type=str, default="benchmark_report.json", help="Path to save JSON report")
    args = parser.parse_args()

    print_separator(f"Running Disaster Relief Matching Benchmarks ({args.seeds} Seeds)")
    print(f"Evaluating Scenarios: S1 (60 vol / 25 needs), S2 (200 vol / 80 needs), S3 (600 vol / 250 needs)")
    print(f"Algorithms: Proposed (Optimal LinearSumAssignment), Constrained Greedy, Nearest-First, Random\n")

    matching_res = run_matching_benchmark(num_seeds=args.seeds)
    table2 = matching_res["table2"]

    # Format Table 2
    header2 = f"{'Scenario':<14} | {'Method':<14} | {'Qualified Cov (%)':<18} | {'Precision (%)':<14} | {'Distance (km)':<14} | {'Utility (%)':<12} | {'Runtime (ms)':<12}"
    print(header2)
    print("-" * len(header2))
    for row in table2:
        print(f"{row['Scenario']:<14} | {row['Method']:<14} | {row['Qualified coverage (%)']:<18} | {row['Skill precision (%)']:<14} | {row['Distance (km)']:<14} | {row['Utility ratio (%)']:<12} | {row['Runtime (ms)']:<12}")

    # Format Table 3
    print_separator("Table 3: Payload Sizes for Low-Bandwidth Operation (zlib level 9)")
    table3 = run_low_bandwidth_benchmark()
    header3 = f"{'Payload':<45} | {'Raw size (bytes)':<18} | {'Compressed (bytes)':<20}"
    print(header3)
    print("-" * len(header3))
    for row in table3:
        print(f"{row['Payload']:<45} | {row['Raw size (bytes)']:<18} | {row['Compressed (bytes)']:<20}")

    # Format Table 4
    print_separator("Table 4: Translation-Quality Results on Relief-Domain Test Set")
    table4 = run_translation_benchmark()
    header4 = f"{'Language pair':<20} | {'BLEU':<8} | {'chrF++':<8} | {'COMET':<8} | {'Adequacy (1-5)':<15} | {'Critical Preserved (%)':<24}"
    print(header4)
    print("-" * len(header4))
    for row in table4:
        print(f"{row['Language pair']:<20} | {row['BLEU']:<8} | {row['chrF++']:<8} | {row['COMET']:<8} | {row['Adequacy (1–5)']:<15} | {row['Critical-content preserved (%)']:<24}")

    # Save output report
    report = {
        "title": "Multilingual Coordination Chatbot for Disaster Relief NGOs and Volunteers",
        "project_id": "CSEAIML2026-P22",
        "seeds": args.seeds,
        "table2_matching": table2,
        "table3_low_bandwidth": table3,
        "table4_translation": table4
    }

    with open(args.save_report, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\n[OK] Complete report saved to: {args.save_report}")

if __name__ == "__main__":
    main()
