#!/usr/bin/env python3
"""Calculate paper-level IAR and SAR scores from adoptions and exposures."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


KEY = ["userid", "expanded_urls_list"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adoptions", required=True, type=Path)
    parser.add_argument(
        "--exposures", required=True, type=Path, nargs="+", help="One or more exposure shard CSVs"
    )
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    adoptions = pd.read_csv(args.adoptions, dtype=str, usecols=KEY).drop_duplicates()
    adoptions["expanded_urls_list"] = adoptions["expanded_urls_list"].str.lower()
    exposures = pd.concat(
        [
            pd.read_csv(
                path,
                dtype={"exposed_userid": str, "expanded_urls_list": str, "count": int},
            )
            for path in args.exposures
        ],
        ignore_index=True,
    )
    exposures = exposures.rename(columns={"exposed_userid": "userid"})
    exposures["expanded_urls_list"] = exposures["expanded_urls_list"].str.lower()
    exposures = exposures.groupby(KEY, as_index=False)["count"].sum()

    overlap = exposures.merge(adoptions, on=KEY, how="inner")
    adopted_n = adoptions.groupby("userid").size().rename("adopted_urls")
    exposed_n = exposures.groupby("userid")["count"].sum().rename("exposure_events")
    overlap_n = overlap.groupby("userid")["count"].sum().rename("successful_exposure_events")
    adopted_after_exposure_n = (
        overlap.groupby("userid").size().rename("adopted_urls_after_exposure")
    )

    metrics = pd.concat(
        [adopted_n, exposed_n, overlap_n, adopted_after_exposure_n], axis=1
    ).fillna(0)
    metrics["IAR"] = metrics["successful_exposure_events"].div(
        metrics["exposure_events"]
    ).fillna(0)
    metrics["SAR"] = 1 - metrics["adopted_urls_after_exposure"].div(metrics["adopted_urls"])
    metrics["SAR"] = metrics["SAR"].fillna(0)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    metrics.reset_index().to_csv(args.output, index=False)


if __name__ == "__main__":
    main()
