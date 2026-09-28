"""Pulls company-wise problems from liquidslr/leetcode-company-wise-problems."""
import os
import pandas as pd
import requests
import streamlit as st

REPO = "liquidslr/leetcode-company-wise-problems"
API = f"https://api.github.com/repos/{REPO}/contents"
FALLBACK = ["Amazon", "Google", "Microsoft", "Meta", "Apple", "Adobe", "Uber", "Goldman Sachs"]


def _headers():
    h = {"Accept": "application/vnd.github+json"}
    if os.getenv("GITHUB_TOKEN"):  # optional: lifts the 60 req/hour anonymous limit
        h["Authorization"] = f"Bearer {os.getenv('GITHUB_TOKEN')}"
    return h


@st.cache_data(ttl=86400, show_spinner=False)
def list_companies():
    try:
        r = requests.get(API, headers=_headers(), timeout=15)
        r.raise_for_status()
        return sorted(x["name"] for x in r.json()
                      if x["type"] == "dir" and not x["name"].startswith("."))
    except Exception:
        return FALLBACK


@st.cache_data(ttl=86400, show_spinner=False)
def list_files(company):
    """Returns {label: download_url} e.g. {'All': ..., 'Thirty Days': ...}."""
    r = requests.get(f"{API}/{requests.utils.quote(company)}", headers=_headers(), timeout=15)
    r.raise_for_status()
    files = {}
    for f in sorted(r.json(), key=lambda x: x["name"]):
        if f["name"].endswith(".csv"):
            label = f["name"][:-4].split(". ", 1)[-1]  # "5. All.csv" -> "All"
            files[label] = f["download_url"]
    return files


@st.cache_data(ttl=3600, show_spinner=False)
def load(url):
    df = pd.read_csv(url)
    df.columns = [c.strip().lower() for c in df.columns]
    fc = [c for c in df.columns if "freq" in c]
    df["freq"] = (pd.to_numeric(df[fc[0]].astype(str).str.rstrip("%"), errors="coerce").fillna(0)
                  if fc else 0)
    df["difficulty"] = df["difficulty"].astype(str).str.strip().str.title()
    return df


def pick(df, n):
    """Most frequently asked problems, ordered Easy -> Medium -> Hard."""
    order = ["Easy", "Medium", "Hard"]
    pools = {d: df[df["difficulty"] == d].sort_values("freq", ascending=False)
             .to_dict("records") for d in order}
    seq = (order + ["Medium", "Hard"] * n)[:n]
    out = []
    for target in seq:
        pool = pools[target] or next((p for p in pools.values() if p), None)
        if not pool:
            break
        out.append(pool.pop(0))
    out.sort(key=lambda r: order.index(r["difficulty"]) if r["difficulty"] in order else 1)
    return out
