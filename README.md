# The Susceptibility Paradox in Online Social Influence

**Modeling influence-driven and spontaneous adoption in online social networks**

Luca Luceri<sup>1,2,*</sup>, Jinyi Ye<sup>1,2,*</sup>, Julie Jiang<sup>1,2</sup>, Emilio Ferrara<sup>1,2</sup>

<sup>1</sup>USC Information Sciences Institute &nbsp; <sup>2</sup>Thomas Lord Department of Computer Science, University of Southern California  
<sup>*</sup>Equal contribution

ICWSM 2025, Copenhagen, Denmark

[![Paper](https://img.shields.io/badge/Paper-10.1609%2Ficwsm.v19i1.35864-red.svg)](https://doi.org/10.1609/icwsm.v19i1.35864)
[![ICWSM 2025](https://img.shields.io/badge/ICWSM-2025-blue.svg)](https://ojs.aaai.org/index.php/ICWSM/issue/view/658)
[![arXiv](https://img.shields.io/badge/arXiv-2406.11553-b31b1b.svg)](https://arxiv.org/abs/2406.11553)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**TL;DR: We distinguish influence-driven from spontaneous URL adoption on Twitter/X and show that susceptibility to influence is homophilous, follows a Generalized Friendship Paradox, and can be predicted largely from friends' susceptibility.**

## Overview

This repository contains the research code and analysis notebooks for *The Susceptibility Paradox in Online Social Influence*. The study analyzes two large-scale Twitter datasets covering the 2020 U.S. presidential election and the COVID-19 pandemic.

We model a URL share as an **adoption**. After user `u` first retweets, quotes, or replies to user `v`, subsequent URL posts by `v` are treated as potential **exposures** for `u`. For exposed URL set `E` and adopted URL set `A`, we define:

- **Influence-driven Adoption Rate (IAR):** `|E ∩ A| / |E|`
- **Spontaneous Adoption Rate (SAR):** `1 - |E ∩ A| / |A|`

The main analysis retains users who shared at least 10 URLs during the observation period and approximates friendship using reciprocal interactions.

## Key findings

- IAR and SAR are strongly negatively correlated but capture distinct adoption behaviors.
- Both metrics are homophilous in reciprocal interaction networks; IAR is consistently more homophilous than SAR.
- The Generalized Friendship Paradox holds for IAR: users' friends are generally more susceptible to influence. It does not hold for SAR.
- Friends' mean IAR alone predicts user IAR reasonably well, whereas SAR benefits more from account metadata and network features.

## Repository structure

```text
.
├── main.ipynb                 # Main analysis: metrics, networks, models, sensitivity
├── paper_visualization.ipynb  # Paper figure generation
├── scripts/
│   ├── preprocess_tweets.py
│   ├── compute_exposures.py
│   ├── compute_metrics.py
│   └── extract_user_attributes.py
├── jobs/
│   └── compute_exposures_array.slurm
├── img/                       # Exported paper figures
├── requirements.txt
├── CITATION.cff
└── LICENSE
```

## Requirements

Python 3.9 or newer is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Data

The original tweet datasets and intermediate CSV files are not included because of their size and applicable data-sharing restrictions. To run the pipeline, prepare these files for either the `covid` or `election` dataset:

| File | Required content |
|---|---|
| `target_users_<dataset>.csv` | `userid` column |
| `target_users_first_adoptions_<dataset>.csv` | First adoption per user and URL |
| `target_users_first_interaction_<dataset>.csv` | First interaction with each referenced user |
| `over10_adoptions_<dataset>.csv` | Retained URL-adoption events |

Dated inputs use `userid`, `date`, and `expanded_urls_list`; interaction tables additionally use `referenced_userid`.

Raw tweet CSVs processed by `preprocess_tweets.py` are expected to contain:

```text
tweetid, userid, screen_name, date, text, tweet_type, urls_list,
rt_userid, rt_tweetid, qtd_userid, qtd_tweetid,
reply_userid, reply_statusid
```

## Running the pipeline

### 1. Preprocess tweets

```bash
python scripts/preprocess_tweets.py data/raw/covid data/processed/covid_tweets
```

This parses URL lists, normalizes referenced users and tweets, and emits one row per tweet–URL pair.

### 2. Prepare the analysis cohort

Use the corresponding sections of `main.ipynb` to select users with at least 10 URL adoptions and create the first-adoption and first-interaction tables. Update the notebook's cluster-specific paths before execution.

### 3. Compute exposures

```bash
python scripts/compute_exposures.py \
  --first-adoptions data/processed/target_users_first_adoptions_covid.csv \
  --first-interactions data/processed/target_users_first_interaction_covid.csv \
  --all-adoptions data/processed/over10_adoptions_covid.csv \
  --target-users data/processed/target_users_covid.csv \
  --start 0 --stop 5000 \
  --output outputs/exposure_covid/part_0.csv
```

The full datasets require substantial memory and should be divided into user shards. `jobs/compute_exposures_array.slurm` provides a configurable SLURM array-job template.

### 4. Calculate IAR and SAR

```bash
python scripts/compute_metrics.py \
  --adoptions data/processed/target_users_first_adoptions_covid.csv \
  --exposures outputs/exposure_covid/part_*.csv \
  --output outputs/susceptibility_covid.csv
```

The output contains adoption counts, exposure-event counts, successful exposure counts, IAR, and SAR for each user. As in the original analysis, IAR weights a URL by the number of observed exposure events, while SAR counts each adopted user–URL pair once.

### 5. Run the paper analyses

`main.ipynb` contains the susceptibility correlation, homophily, friendship-paradox, prediction, and sensitivity analyses. `paper_visualization.ipynb` regenerates the figures in `img/`. Both notebooks preserve some paths from the original computing cluster; replace `/scratch*`, `/project*`, and `/home1*` paths before running them.

## Reproducibility notes

- Exposure is an observational proxy, not a record of feed impressions.
- Sharing a URL does not necessarily imply endorsement.
- The paper applies a two-month buffer before counting adoptions in the susceptibility metrics.
- Results depend on reciprocal interaction networks and the 10-URL activity threshold used in the main experiment.
- The notebooks are research records and contain exploratory cells in addition to the final analyses.

## Citation

If you use this code, please cite:

```bibtex
@article{luceri2025susceptibility,
  title   = {The Susceptibility Paradox in Online Social Influence},
  author  = {Luceri, Luca and Ye, Jinyi and Jiang, Julie and Ferrara, Emilio},
  journal = {Proceedings of the International AAAI Conference on Web and Social Media},
  volume  = {19},
  number  = {1},
  pages   = {1122--1138},
  year    = {2025},
  doi     = {10.1609/icwsm.v19i1.35864},
  url     = {https://doi.org/10.1609/icwsm.v19i1.35864}
}
```

The citation above matches the [official ICWSM record](https://ojs.aaai.org/index.php/ICWSM/article/view/35864). Machine-readable metadata is also available in `CITATION.cff`.

## Contact

For questions about the code or reproduction, contact Jinyi Ye at [jinyiy@usc.edu](mailto:jinyiy@usc.edu).

## License

The code in this repository is released under the [MIT License](LICENSE). Third-party datasets and the published paper remain subject to their respective terms and copyright.
