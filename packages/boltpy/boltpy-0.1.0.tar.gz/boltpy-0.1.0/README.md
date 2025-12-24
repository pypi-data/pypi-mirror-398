# boltpy (BOLT)

**BOLT** = **B**ibliographic **O**rchestration for **L**iterature **T**riage

`boltpy` is a Python toolkit to collect and triage literature results from multiple scholarly sources
(Crossref, OpenAlex, PubMed, arXiv, Europe PMC, Zenodo, and optionally Elsevier Scopus).

It is designed for literature reviews where you want to:
- choose a set of keywords,
- choose which APIs/sources to query,
- provide API keys when required,
- set a maximum number of results per source,
- receive a clean, deduplicated dataset (plus an ASReview-friendly export).

---

## Features

- Multi-source harvesting (select the APIs you want)
- Per-source ceilings (`ceilings={"crossref": 150, "openalex": 200, ...}`)
- Optional API key support (Elsevier Scopus)
- Deduplication:
  - DOI-based
  - exact normalized title
  - fuzzy title matching
- Export:
  - full CSV (all fields)
  - ASReview CSV (title/abstract/authors/year/doi/url)
  - PRISMA-style counters (JSON)

---

## Install

## From GitHub
```bash
pip install "git+https://github.com/<YOUR-USER>/<YOUR-REPO>.git"

## Example

from boltpy.core import HarvestConfig, harvest

cfg = HarvestConfig(
    keywords=["your keyword 1", "your keyword 2"],
    apis=["crossref", "openalex", "pubmed", "arxiv", "europe_pmc", "zenodo"],
    default_ceiling=100,
    output_dir="outputs",          # optional: exports CSV + JSON
    export_prefix="boltpy_demo",
)

res = harvest(cfg)

# Full dataset (all fields)
print(res.full.head())

# PRISMA-like counters
print(res.prisma)

# Written files (if output_dir is set)
print(res.output_paths)
