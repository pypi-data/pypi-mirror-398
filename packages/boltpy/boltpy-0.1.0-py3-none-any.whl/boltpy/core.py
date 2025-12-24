from __future__ import annotations

import csv  # for quoting
import json
import logging
import os
import re
import time
import unicodedata
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from html import unescape
from typing import Any
from xml.etree import ElementTree as ET

import feedparser
import pandas as pd
import requests
from rapidfuzz import fuzz, process

logger = logging.getLogger("boltpy")
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )


def fix_encoding(text: Any) -> str:
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize("NFKC", text)
    return text.strip()


def clean_abstract(text: Any) -> str:
    if not isinstance(text, str):
        return ""
    text = unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("Â", " ")
    return fix_encoding(text)


def normalize_title_for_exact(s: Any) -> str:
    s = fix_encoding(s).lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^\w\s]", "", s)
    return s.strip()


def normalize_doi(s: Any) -> str:
    if not isinstance(s, str):
        return ""
    s = s.strip()
    s = re.sub(r"^https?://(dx\.)?doi\.org/", "", s, flags=re.I)
    return s.lower()


def _norm_simple(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"[^\w\s]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _block_key(s: str, block_chars: int = 32) -> str:
    s = re.sub(r"\s+", "", _norm_simple(s))
    return s[:block_chars]


def deduplicate_fuzzy(
    df: pd.DataFrame,
    title_column: str = "title",
    threshold: int = 95,
    block_chars: int = 32,
    max_block: int = 200,
) -> pd.DataFrame:
    """
    Blocked fuzzy dedup by title:
    - blocks by normalized prefix
    - fuzzy compare only inside each block
    """
    df = df.copy().reset_index(drop=True)
    to_drop = set()

    df["_block"] = df[title_column].map(lambda x: _block_key(str(x or ""), block_chars=block_chars))
    for _, idx_arr in df.groupby("_block").groups.items():
        idx = list(idx_arr)
        if len(idx) <= 1:
            continue
        if len(idx) > max_block:
            continue

        titles = [str(df.at[i, title_column] or "").lower() for i in idx]
        scores = process.cdist(titles, titles, scorer=fuzz.ratio, workers=0)

        n = len(idx)
        for i in range(n):
            if idx[i] in to_drop:
                continue
            for j in range(i + 1, n):
                if scores[i][j] >= threshold:
                    to_drop.add(idx[j])

    df = df.drop(index=list(to_drop)).reset_index(drop=True)
    return df.drop(columns=["_block"])


DEFAULT_HEADERS = {"User-Agent": "boltpy/0.1 (BOLT: literature triage)"}


def http_get(url: str, **kwargs) -> requests.Response:
    retries = int(kwargs.pop("retries", 2))
    backoff = float(kwargs.pop("backoff", 1.5))
    timeout = float(kwargs.pop("timeout", 15))

    headers = {**DEFAULT_HEADERS, **kwargs.pop("headers", {})}

    for attempt in range(retries + 1):
        try:
            r = requests.get(url, timeout=timeout, headers=headers, **kwargs)
            if r.status_code in (429, 500, 502, 503, 504):
                raise requests.HTTPError(f"{r.status_code} server/backoff")
            r.raise_for_status()
            return r
        except Exception:
            if attempt == retries:
                raise
            time.sleep(backoff * (attempt + 1))

    raise RuntimeError("Unreachable")


def fetch_crossref(query: str, max_results: int = 200) -> list[dict]:
    results: list[dict] = []
    logger.info("🔍 CrossRef: %s", query)

    for offset in range(0, max_results, 100):
        url = "https://api.crossref.org/works"
        params = {
            "query.bibliographic": query,
            "filter": "from-pub-date:2010-01-01,until-pub-date:2025-04-30,type:journal-article",
            "rows": min(100, max_results - offset),
            "offset": offset,
        }
        try:
            response = http_get(url, params=params)
            items = response.json().get("message", {}).get("items", [])
        except Exception as e:
            logger.warning("CrossRef error: %s", e)
            break

        for item in items:
            title = fix_encoding((item.get("title") or [""])[0])
            raw_abstract = item.get("abstract", "")
            cleaned_abstract = clean_abstract(raw_abstract)

            authors_list: list[str] = []
            for a in item.get("author", []) or []:
                given = a.get("given", "") or ""
                family = a.get("family", "") or ""
                nm = f"{given} {family}".strip()
                if nm:
                    authors_list.append(nm)

            issued = item.get("issued", {}) or {}
            date_parts = issued.get("date-parts", [[None]]) or [[None]]
            year = date_parts[0][0] if date_parts and date_parts[0] else None

            results.append(
                {
                    "source": "crossref",
                    "title": title,
                    "authors": fix_encoding(", ".join(authors_list)),
                    "year": year,
                    "doi": normalize_doi(item.get("DOI", "")),
                    "publisher": fix_encoding(item.get("publisher", "")),
                    "journal": fix_encoding((item.get("container-title") or [""])[0]),
                    "url": item.get("URL", ""),
                    "abstract": cleaned_abstract,
                }
            )

        time.sleep(0.5)

    return results


def fetch_elsevier_scopus(query: str, api_key: str, max_results: int = 200) -> list[dict]:
    results: list[dict] = []
    logger.info("🔍 Elsevier Scopus: %s", query)

    headers = {"X-ELS-APIKey": api_key, "Accept": "application/json"}
    base_url = "https://api.elsevier.com/content/search/scopus"

    for start in range(0, max_results, 25):
        params = {"query": query, "count": min(25, max_results - start), "start": start}
        try:
            response = http_get(base_url, headers=headers, params=params)
            items = response.json().get("search-results", {}).get("entry", [])
        except Exception as e:
            logger.warning("Elsevier error: %s", e)
            break

        for item in items:
            title = fix_encoding(item.get("dc:title", ""))
            year_str = (item.get("prism:coverDate", "") or "")[:4]
            year = int(year_str) if year_str.isdigit() else None

            results.append(
                {
                    "source": "elsevier_scopus",
                    "title": title,
                    "authors": fix_encoding(item.get("dc:creator", "")),
                    "year": year,
                    "doi": normalize_doi(item.get("prism:doi", "")),
                    "publisher": "Elsevier",
                    "journal": fix_encoding(item.get("prism:publicationName", "")),
                    "url": item.get("prism:url", ""),
                    "abstract": "",
                }
            )

        time.sleep(0.5)

    return results


def fetch_pubmed(query: str, max_results: int = 200) -> list[dict]:
    results: list[dict] = []
    logger.info("🔍 PubMed: %s", query)

    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    try:
        search_resp = http_get(
            base + "esearch.fcgi",
            params={"db": "pubmed", "term": query, "retmax": max_results, "retmode": "json"},
        )
        ids = search_resp.json().get("esearchresult", {}).get("idlist", [])
        if not ids:
            return results

        fetch_resp = http_get(
            base + "efetch.fcgi",
            params={"db": "pubmed", "id": ",".join(ids), "retmode": "xml"},
        )
        root = ET.fromstring(fetch_resp.content)

        for article in root.findall(".//PubmedArticle"):
            title_elem = article.find(".//ArticleTitle")
            abstract_elem = article.find(".//Abstract/AbstractText")

            title = fix_encoding(title_elem.text if title_elem is not None else "")
            abstract = clean_abstract(abstract_elem.text if abstract_elem is not None else "")

            authors: list[str] = []
            for author in article.findall(".//Author"):
                last = author.find("LastName")
                first = author.find("ForeName")
                ln = (last.text or "").strip() if last is not None and last.text else ""
                fn = (first.text or "").strip() if first is not None and first.text else ""
                name = f"{fn} {ln}".strip()
                if name:
                    authors.append(name)

            year: int | None = None
            y1 = article.find(".//PubDate/Year")
            if y1 is not None and y1.text and y1.text.isdigit():
                year = int(y1.text)
            else:
                md = article.find(".//PubDate/MedlineDate")
                if md is not None and md.text:
                    m = re.search(r"\b(19|20)\d{2}\b", md.text)
                    if m:
                        year = int(m.group(0))

            doi = ""
            for aid in article.findall(".//ArticleIdList/ArticleId"):
                if aid.get("IdType") == "doi" and aid.text:
                    doi = normalize_doi(aid.text)
                    break

            results.append(
                {
                    "source": "pubmed",
                    "title": title,
                    "authors": fix_encoding(", ".join(authors)),
                    "year": year,
                    "doi": doi,
                    "publisher": "PubMed",
                    "journal": "",
                    "url": "",
                    "abstract": abstract,
                }
            )

    except Exception as e:
        logger.warning("PubMed error: %s", e)

    return results


def fetch_arxiv(query: str, max_results: int = 200) -> list[dict]:
    results: list[dict] = []
    logger.info("🔍 arXiv: %s", query)

    base_url = "http://export.arxiv.org/api/query"
    params = {"search_query": query, "start": 0, "max_results": max_results}
    try:
        response = http_get(base_url, params=params)
        feed = feedparser.parse(response.content)
        for entry in feed.entries:
            title = fix_encoding(entry.title)
            abstract = clean_abstract(entry.summary)
            authors = fix_encoding(", ".join(a.name for a in entry.authors))
            year = (
                int(entry.published[:4])
                if entry.published and entry.published[:4].isdigit()
                else None
            )

            results.append(
                {
                    "source": "arxiv",
                    "title": title,
                    "authors": authors,
                    "year": year,
                    "doi": "",
                    "publisher": "arXiv",
                    "journal": "",
                    "url": entry.link,
                    "abstract": abstract,
                }
            )
    except Exception as e:
        logger.warning("arXiv error: %s", e)

    return results


def _openalex_abstract(inv_idx: Any) -> str:
    if not isinstance(inv_idx, dict) or not inv_idx:
        return ""
    max_pos = 0
    for positions in inv_idx.values():
        if positions:
            max_pos = max(max_pos, max(positions))
    words = [""] * (max_pos + 1)
    for w, positions in inv_idx.items():
        for p in positions:
            if 0 <= p < len(words):
                words[p] = w
    return " ".join(words).strip()


def fetch_openalex(query: str, max_results: int = 200) -> list[dict]:
    results: list[dict] = []
    logger.info("🔍 OpenAlex: %s", query)

    base_url = "https://api.openalex.org/works"
    params = {"search": query, "per-page": max_results}
    try:
        r = http_get(base_url, params=params)
        for item in r.json().get("results", []):
            title = fix_encoding(item.get("title", ""))
            abstract = clean_abstract(_openalex_abstract(item.get("abstract_inverted_index")))

            authors = fix_encoding(
                ", ".join(
                    ((a.get("author", {}) or {}).get("display_name", "") or "")
                    for a in (item.get("authorships") or [])
                )
            )
            year = item.get("publication_year", None)

            results.append(
                {
                    "source": "openalex",
                    "title": title,
                    "authors": authors,
                    "year": year,
                    "doi": normalize_doi(item.get("doi", "")),
                    "publisher": (item.get("host_venue", {}) or {}).get("publisher", ""),
                    "journal": (item.get("host_venue", {}) or {}).get("display_name", ""),
                    "url": item.get("id", ""),
                    "abstract": abstract,
                }
            )
    except Exception as e:
        logger.warning("OpenAlex error: %s", e)

    return results


def fetch_europe_pmc(query: str, max_results: int = 200) -> list[dict]:
    results: list[dict] = []
    logger.info("🔍 Europe PMC: %s", query)

    base_url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    params = {"query": query, "format": "json", "pageSize": max_results}
    try:
        response = http_get(base_url, params=params)
        items = response.json().get("resultList", {}).get("result", [])

        for item in items:
            title = fix_encoding(item.get("title", ""))
            abstract = clean_abstract(item.get("abstractText", ""))
            authors = fix_encoding(item.get("authorString", ""))
            year_str = str(item.get("pubYear", "") or "")
            year = int(year_str) if year_str.isdigit() else None

            url = ""
            ft = item.get("fullTextUrlList", {})
            if isinstance(ft, dict):
                arr = ft.get("fullTextUrl", [])
                if arr and isinstance(arr, list):
                    url = (arr[0].get("url", "") or "").strip()

            results.append(
                {
                    "source": "europe_pmc",
                    "title": title,
                    "authors": authors,
                    "year": year,
                    "doi": normalize_doi(item.get("doi", "")),
                    "publisher": item.get("publisher", ""),
                    "journal": item.get("journalTitle", ""),
                    "url": url,
                    "abstract": abstract,
                }
            )

    except Exception as e:
        logger.warning("Europe PMC error: %s", e)

    return results


def fetch_zenodo(query: str, max_results: int = 200) -> list[dict]:
    results: list[dict] = []
    logger.info("🔍 Zenodo: %s", query)

    base_url = "https://zenodo.org/api/records"
    params = {"q": query, "size": max_results, "sort": "bestmatch"}
    try:
        response = http_get(base_url, params=params)
        items = response.json().get("hits", {}).get("hits", [])

        for item in items:
            metadata = item.get("metadata", {}) or {}
            title = fix_encoding(metadata.get("title", ""))
            abstract = clean_abstract(metadata.get("description", ""))
            creators = metadata.get("creators") or []
            authors = fix_encoding(", ".join((c.get("name", "") or "") for c in creators))

            pub_date = metadata.get("publication_date")
            year = None
            if isinstance(pub_date, str) and len(pub_date) >= 4 and pub_date[:4].isdigit():
                year = int(pub_date[:4])

            results.append(
                {
                    "source": "zenodo",
                    "title": title,
                    "authors": authors,
                    "year": year,
                    "doi": normalize_doi(metadata.get("doi", "")),
                    "publisher": metadata.get("publisher", ""),
                    "journal": "",
                    "url": (item.get("links", {}) or {}).get("html", ""),
                    "abstract": abstract,
                }
            )

    except Exception as e:
        logger.warning("Zenodo error: %s", e)

    return results


ProviderFn = Callable[..., list[dict]]

PROVIDERS: dict[str, ProviderFn] = {
    "crossref": fetch_crossref,
    "elsevier_scopus": fetch_elsevier_scopus,  # requires api key
    "pubmed": fetch_pubmed,
    "arxiv": fetch_arxiv,
    "openalex": fetch_openalex,
    "europe_pmc": fetch_europe_pmc,
    "zenodo": fetch_zenodo,
}


@dataclass(slots=True)
class HarvestConfig:
    keywords: list[str]
    apis: list[str] = field(
        default_factory=lambda: ["crossref", "openalex", "pubmed", "arxiv", "europe_pmc", "zenodo"]
    )
    api_keys: dict[str, str] = field(default_factory=dict)
    ceilings: dict[str, int] = field(default_factory=dict)  # per-API ceiling
    default_ceiling: int = 200

    # orchestration
    max_workers: int = 6
    sleep_between_keywords_s: float = 0.0

    # post-processing
    dedup_fuzzy_threshold: int = 95

    # export
    output_dir: str | None = None
    export_prefix: str = "boltpy"
    write_full_csv: bool = True
    write_asreview_csv: bool = True


@dataclass(slots=True)
class HarvestResult:
    prisma: dict[str, Any]
    full: pd.DataFrame
    asreview: pd.DataFrame
    output_paths: dict[str, str] = field(default_factory=dict)


def _resolve_ceiling(cfg: HarvestConfig, api: str) -> int:
    return int(cfg.ceilings.get(api, cfg.default_ceiling))


def _call_provider(api: str, query: str, cfg: HarvestConfig) -> tuple[str, list[dict]]:
    if api not in PROVIDERS:
        raise ValueError(f"Unknown API '{api}'. Available: {sorted(PROVIDERS)}")

    fn = PROVIDERS[api]
    ceiling = _resolve_ceiling(cfg, api)

    if api == "elsevier_scopus":
        key = cfg.api_keys.get("elsevier_scopus") or os.getenv("ELSEVIER_API_KEY", "")
        if not key:
            logger.info("Skipping elsevier_scopus: missing API key.")
            return api, []
        return api, fn(query, key, ceiling)  # type: ignore[misc]

    return api, fn(query, ceiling)  # type: ignore[misc]


def harvest(cfg: HarvestConfig) -> HarvestResult:
    prisma: dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M"),
        "by_source": {},
        "n_collected": 0,
        "n_after_df": 0,
        "n_after_nonempty": 0,
        "n_after_doi": 0,
        "n_after_title_norm": 0,
        "n_after_fuzzy": 0,
        "n_final": 0,
    }

    all_rows: list[dict] = []

    for kw in cfg.keywords:
        query = f"({kw})"
        logger.info("=== Keyword: %s ===", kw)

        with ThreadPoolExecutor(max_workers=cfg.max_workers) as ex:
            futs = [ex.submit(_call_provider, api, query, cfg) for api in cfg.apis]
            for fut in as_completed(futs):
                try:
                    api, rows = fut.result()
                    all_rows.extend(rows)
                except Exception as e:
                    logger.warning("Provider error: %s", e)

        if cfg.sleep_between_keywords_s:
            time.sleep(cfg.sleep_between_keywords_s)

    prisma["n_collected"] = len(all_rows)

    df = pd.DataFrame(all_rows)
    prisma["n_after_df"] = int(len(df))

    if len(df) == 0:
        empty = pd.DataFrame(columns=["title", "abstract", "authors", "year", "doi", "url"])
        return HarvestResult(prisma=prisma, full=df, asreview=empty, output_paths={})

    expected = [
        "source",
        "title",
        "authors",
        "year",
        "doi",
        "publisher",
        "journal",
        "url",
        "abstract",
    ]
    for col in expected:
        if col not in df.columns:
            df[col] = ""

    for col in ["source", "title", "abstract", "authors", "doi", "url", "publisher", "journal"]:
        df[col] = df[col].fillna("").astype(str).str.strip()

    df["doi"] = df["doi"].apply(normalize_doi)
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    df = df[(df["title"] != "") | (df["abstract"] != "")].copy()
    prisma["n_after_nonempty"] = int(len(df))

    prisma["by_source"] = df["source"].value_counts(dropna=False).to_dict()

    mask_doi = df["doi"] != ""
    df = pd.concat([df[mask_doi].drop_duplicates(subset=["doi"]), df[~mask_doi]], ignore_index=True)
    prisma["n_after_doi"] = int(len(df))

    df["_norm_title"] = df["title"].apply(normalize_title_for_exact)
    df = df.drop_duplicates(subset=["_norm_title"]).reset_index(drop=True)
    prisma["n_after_title_norm"] = int(len(df))

    df = df.drop(columns=["_norm_title"])
    df = deduplicate_fuzzy(df, title_column="title", threshold=cfg.dedup_fuzzy_threshold)
    prisma["n_after_fuzzy"] = int(len(df))

    has_doi = df["doi"].str.startswith("10.")
    has_url = df["url"].str.startswith(("http://", "https://"))
    df = df[
        has_doi.fillna(False) | has_url.fillna(False) | (df["title"] != "") | (df["abstract"] != "")
    ].copy()
    prisma["n_final"] = int(len(df))

    asreview_df = df[["title", "abstract", "authors", "year", "doi", "url"]].copy()

    out_paths: dict[str, str] = {}
    if cfg.output_dir:
        os.makedirs(cfg.output_dir, exist_ok=True)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        base = os.path.join(cfg.output_dir, f"{cfg.export_prefix}_{stamp}")

        if cfg.write_full_csv:
            full_path = base + "_full.csv"
            df.to_csv(full_path, index=False, encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL)
            out_paths["full_csv"] = full_path

        if cfg.write_asreview_csv:
            asr_path = base + "_asreview.csv"
            asreview_df.to_csv(
                asr_path, index=False, encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL
            )
            out_paths["asreview_csv"] = asr_path

        prisma_path = base + "_prisma.json"
        with open(prisma_path, "w", encoding="utf-8") as fp:
            json.dump(prisma, fp, ensure_ascii=False, indent=2)
        out_paths["prisma_json"] = prisma_path

    return HarvestResult(prisma=prisma, full=df, asreview=asreview_df, output_paths=out_paths)
