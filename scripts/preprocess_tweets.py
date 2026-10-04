#!/usr/bin/env python3
"""Normalize raw tweet CSV files for the susceptibility pipeline."""

from __future__ import annotations

import argparse
import ast
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm


OUTPUT_COLUMNS = [
    "tweetid",
    "userid",
    "screen_name",
    "date",
    "expanded_urls_list",
    "text",
    "tweet_type",
    "referenced_userid",
    "referenced_tweetid",
]


def parse_urls(value: object) -> list[str]:
    """Parse the Twitter `urls_list` field without executing its contents."""
    if pd.isna(value) or value == "[]":
        return []
    items = ast.literal_eval(value) if isinstance(value, str) else value
    return [item["expanded_url"] for item in items if item.get("expanded_url")]


def preprocess_file(source: Path, destination: Path) -> None:
    frame = pd.read_csv(source, dtype=str, lineterminator="\n")
    frame["expanded_urls_list"] = frame["urls_list"].map(parse_urls)
    frame = frame[frame["expanded_urls_list"].map(bool)].copy()
    frame["date"] = pd.to_datetime(frame["date"], utc=True, errors="raise")

    conditions = [
        frame["tweet_type"].eq("retweeted_tweet_without_comment"),
        frame["tweet_type"].eq("quoted_tweet"),
        frame["tweet_type"].eq("reply"),
    ]
    frame["referenced_userid"] = np.select(
        conditions,
        [frame["rt_userid"], frame["qtd_userid"], frame["reply_userid"]],
        default=None,
    )
    frame["referenced_tweetid"] = np.select(
        conditions,
        [frame["rt_tweetid"], frame["qtd_tweetid"], frame["reply_statusid"]],
        default=None,
    )

    frame = frame[OUTPUT_COLUMNS].explode("expanded_urls_list", ignore_index=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(destination, index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", type=Path, help="Directory containing raw CSV files")
    parser.add_argument("output_dir", type=Path, help="Directory for normalized CSV files")
    args = parser.parse_args()

    sources = sorted(args.input_dir.rglob("*.csv"))
    if not sources:
        parser.error(f"no CSV files found under {args.input_dir}")
    for source in tqdm(sources, desc="Preprocessing"):
        relative = source.relative_to(args.input_dir)
        preprocess_file(source, args.output_dir / relative)


if __name__ == "__main__":
    main()
