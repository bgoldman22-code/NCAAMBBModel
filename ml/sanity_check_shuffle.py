#!/usr/bin/env python3
"""Sanity checks for spread grading and P&L logic.

This script compares the real model's spread results against:
1. A shuffle test (model spreads randomly permuted).
2. A naive "always bet the closing favorite" baseline.

If the shuffled or baseline strategies show large positive ROI, it indicates
there is still a grading bug or hidden leakage.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).parent.parent / "data"
RESULTS_FILE = DATA_DIR / "walkforward_results_with_scores.csv"


def _spread_summary(
    df: pd.DataFrame,
    edge_column: str,
    min_edge: float,
    stake: float,
    label: str,
) -> Dict[str, float]:
    """Compute spread win% and ROI for a particular edge column."""
    required_cols = {edge_column, "home_covered"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns for spread summary: {missing}")

    bets = df[df[edge_column].abs() >= min_edge].copy()
    if bets.empty:
        return {"label": label, "bets": 0, "win_rate": np.nan, "roi": np.nan}

    home_cov = bets["home_covered"].astype(bool)
    bet_home = bets[edge_column] > 0
    won = np.where(bet_home, home_cov, ~home_cov)

    wins = won.sum()
    losses = len(bets) - wins
    profit = wins * (stake * 0.909) - losses * stake
    roi = (profit / (len(bets) * stake)) * 100

    return {
        "label": label,
        "bets": int(len(bets)),
        "win_rate": (wins / len(bets)) * 100,
        "roi": roi,
    }


def baseline_favorite_strategy(df: pd.DataFrame, stake: float) -> Dict[str, float]:
    """Always bet the closing favorite (if spread != 0)."""
    if "close_spread" not in df.columns:
        raise ValueError("close_spread column missing for baseline test")

    bets = df[df["close_spread"] != 0].copy()
    if bets.empty:
        return {"label": "Baseline favorite", "bets": 0, "win_rate": np.nan, "roi": np.nan}

    bet_home = bets["close_spread"] < 0  # home favorite => negative spread
    home_cov = bets["home_covered"].astype(bool)
    won = np.where(bet_home, home_cov, ~home_cov)

    wins = won.sum()
    losses = len(bets) - wins
    profit = wins * (stake * 0.909) - losses * stake
    roi = (profit / (len(bets) * stake)) * 100

    return {
        "label": "Baseline favorite",
        "bets": int(len(bets)),
        "win_rate": (wins / len(bets)) * 100,
        "roi": roi,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Spread grading sanity checks")
    parser.add_argument("--results-file", type=Path, default=RESULTS_FILE)
    parser.add_argument("--min-edge", type=float, default=2.0, help="Spread edge threshold")
    parser.add_argument("--stake", type=float, default=100.0)
    parser.add_argument("--seed", type=int, default=42, help="RNG seed for shuffle test")
    args = parser.parse_args()

    df = pd.read_csv(args.results_file)
    if "matched" in df.columns:
        match_mask = df["matched"] == True
    elif "result_matched" in df.columns:
        match_mask = df["result_matched"] == True
    else:
        raise ValueError("Results file missing 'matched'/'result_matched' columns")

    matched = df[match_mask].copy()
    if matched.empty:
        raise ValueError("No matched games available for sanity check")

    # Ensure required columns exist
    required = {"edge_spread", "close_spread", "home_covered"}
    missing = required - set(matched.columns)
    if missing:
        raise ValueError(f"Missing columns in results file: {missing}")

    # Real model summary
    real_summary = _spread_summary(
        matched,
        edge_column="edge_spread",
        min_edge=args.min_edge,
        stake=args.stake,
        label=f"Real model (edge ≥ {args.min_edge})",
    )

    # Shuffle test: randomly permute model spreads, recompute edges
    rng = np.random.default_rng(args.seed)
    shuffled = matched.copy()
    shuffled_spreads = shuffled["model_spread"].to_numpy(copy=True)
    rng.shuffle(shuffled_spreads)
    shuffled["edge_spread_shuffled"] = shuffled_spreads - shuffled["close_spread"]

    shuffled_summary = _spread_summary(
        shuffled,
        edge_column="edge_spread_shuffled",
        min_edge=args.min_edge,
        stake=args.stake,
        label="Shuffled model (edge ≥ {0})".format(args.min_edge),
    )

    # Baseline favorite strategy
    baseline_summary = baseline_favorite_strategy(matched, stake=args.stake)

    print("\nSPREAD SANITY CHECKS")
    print("====================")
    for summary in (real_summary, shuffled_summary, baseline_summary):
        print(
            f"{summary['label']}:\n"
            f"  Bets: {summary['bets']}\n"
            f"  Win%: {summary['win_rate']:.2f}%\n"
            f"  ROI : {summary['roi']:.2f}%\n"
        )


if __name__ == "__main__":
    main()
