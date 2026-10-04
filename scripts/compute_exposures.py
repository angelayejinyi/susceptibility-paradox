#!/usr/bin/env python3
"""Compute URL exposures for one configurable shard of target users."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from tqdm import tqdm


def read_dated_csv(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype=str)
    frame["date"] = pd.to_datetime(frame["date"], utc=True, errors="raise")
    return frame


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Infer exposure after each user's first observed interaction."
    )
    parser.add_argument("--first-adoptions", required=True, type=Path)
    parser.add_argument("--first-interactions", required=True, type=Path)
    parser.add_argument("--all-adoptions", required=True, type=Path)
    parser.add_argument("--target-users", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--start", type=int, default=0, help="Inclusive user-row offset")
    parser.add_argument("--stop", type=int, help="Exclusive user-row offset")
    args = parser.parse_args()

    first_adoptions = read_dated_csv(args.first_adoptions)
    interactions = read_dated_csv(args.first_interactions)
    all_adoptions = read_dated_csv(args.all_adoptions)
    users = pd.read_csv(args.target_users, dtype=str)["userid"].iloc[args.start : args.stop].tolist()

    interactions = interactions[interactions["userid"].isin(users)]
    first_adoptions = first_adoptions[first_adoptions["userid"].isin(users)]
    all_adoptions = all_adoptions[
        all_adoptions["userid"].isin(interactions["referenced_userid"].dropna().unique())
    ]

    results: list[pd.DataFrame] = []
    for user_id in tqdm(users, desc="Users"):
        user_interactions = interactions[interactions["userid"].eq(user_id)]
        # The original analysis used one first-interaction date per source user.
        first_seen = (
            user_interactions.groupby("referenced_userid", as_index=False)["date"]
            .min()
            .rename(columns={"referenced_userid": "userid", "date": "min_date"})
        )
        candidates = all_adoptions.merge(first_seen, on="userid", how="inner")
        candidates = candidates[candidates["date"] > candidates["min_date"]].copy()
        candidates["exposed_userid"] = user_id

        own = first_adoptions[["userid", "expanded_urls_list", "date"]]
        exposed = candidates.merge(
            own,
            left_on=["exposed_userid", "expanded_urls_list"],
            right_on=["userid", "expanded_urls_list"],
            how="left",
            suffixes=("_source", "_own"),
        )
        # Keep exposure events that precede the target user's first adoption,
        # plus URLs that the target user never adopted.
        exposed = exposed[
            exposed["date_own"].isna() | (exposed["date_source"] < exposed["date_own"])
        ].copy()
        exposed["expanded_urls_list"] = exposed["expanded_urls_list"].str.lower()
        counts = (
            exposed.groupby(["exposed_userid", "expanded_urls_list"])
            .size()
            .reset_index(name="count")
        )
        results.append(counts)

    output = pd.concat(results, ignore_index=True) if results else pd.DataFrame(
        columns=["exposed_userid", "expanded_urls_list", "count"]
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, index=False)


if __name__ == "__main__":
    main()
