#!/usr/bin/env python3
"""Extract the latest available metadata for a specified set of users."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from tqdm import tqdm


DEFAULT_COLUMNS = [
    "userid",
    "screen_name",
    "description",
    "friends_count",
    "listed_count",
    "followers_count",
    "favourites_count",
    "statuses_count",
    "verified",
    "state",
    "country",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path, help="Root of historical CSV files")
    parser.add_argument("--users", required=True, type=Path, help="CSV containing a userid column")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    remaining = set(pd.read_csv(args.users, dtype=str)["userid"])
    rows: list[pd.DataFrame] = []
    # Reverse lexical order matches the original latest-to-earliest scan when
    # files and month directories use ISO dates.
    for path in tqdm(sorted(args.source.rglob("*.csv"), reverse=True), desc="Metadata files"):
        if not remaining:
            break
        frame = pd.read_csv(path, dtype=str, usecols=lambda name: name in DEFAULT_COLUMNS)
        found = frame[frame["userid"].isin(remaining)].drop_duplicates("userid", keep="first")
        if not found.empty:
            rows.append(found)
            remaining.difference_update(found["userid"])

    result = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=DEFAULT_COLUMNS)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.reindex(columns=DEFAULT_COLUMNS).to_csv(args.output, index=False)
    print(f"wrote {len(result):,} users; {len(remaining):,} were not found")


if __name__ == "__main__":
    main()
