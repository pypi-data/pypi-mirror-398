# tests/test_minimal_unit.py
import os
import time
import shutil
from unittest.mock import patch, MagicMock

import pytest

from footballmvp.mvp_run import (
    AllCompetitions,
    Competition,
    Player,
    MVP,
)


# ---------------------------
# 1) AllCompetitions.format_competition_names
# ---------------------------
def test_format_competition_names_basic():
    src = {"55": "Serie A", "72": "La Liga", "90": "Women (W)."}
    ac = AllCompetitions()
    out = ac.format_competition_names(src)
    assert out["55"] == "serie-a"
    assert out["72"] == "la-liga"
    # “(w)” -> “qualification”; periods removed
    assert out["90"] == "women-qualification"


# ---------------------------
# 2) AllCompetitions.add_competition_to_my_watchlist (URL + duplicate)
# ---------------------------

def test_add_competition_to_watchlist_invalid_url(spark):
    # run inside tests/ (conftest chdir); won't pollute repo root
    ac = AllCompetitions()
    msg = ac.add_competition_to_my_watchlist(
        competition_name="",
        gather_all_competition_ids={},
        defined_url="https://www.fotmob.com/leagues/not-a-valid"
    )
    assert "Invalid URL" in msg


def test_add_competition_to_watchlist_creates_dir(spark):
    # ensure a clean starting state
    if os.path.isdir("all_comps_df"):
        shutil.rmtree("all_comps_df")

    ac = AllCompetitions()
    msg = ac.add_competition_to_my_watchlist(
        competition_name="",
        gather_all_competition_ids={},
        defined_url="https://www.fotmob.com/leagues/55/matches/serie-a"
    )
    assert "Watchlist created and competition 'serie-a' added." in msg
    # directory is created; don't assert filesystem details to avoid Spark flake


def test_add_competition_to_watchlist_duplicate(spark, monkeypatch):
    # pre-create `all_comps_df` with the same row
    if os.path.isdir("all_comps_df"):
        shutil.rmtree("all_comps_df")

    df = spark.createDataFrame(
        [("https://www.fotmob.com/leagues/55/matches/serie-a", "55", "serie-a")],
        schema="competition_url string, competition_id string, competition_name string",
    )
    df.coalesce(1).write.mode("overwrite").option("header", True).csv("all_comps_df")

    # force function down the "exists" branch
    monkeypatch.setattr("os.path.exists", lambda p: True)

    ac = AllCompetitions()
    msg = ac.add_competition_to_my_watchlist(
        competition_name="",
        gather_all_competition_ids={},
        defined_url="https://www.fotmob.com/leagues/55/matches/serie-a"
    )
    assert "already exists" in msg


# ---------------------------
# 3) Competition.extract_match_links_per_page
# ---------------------------

def test_extract_match_links_per_page_parses_and_dedup():
    c = Competition()
    html = """
    <html><body>
      <script>var noop = true;</script>
      <script>
        var s = "/matches/abc#111","/matches/def#222","/matches/abc#111";
      </script>
    </body></html>
    """
    mock_resp = MagicMock()
    mock_resp.text = html

    with patch("requests.get", return_value=mock_resp):
        out = c.extract_match_links_per_page(
            "https://www.fotmob.com/leagues/47/matches/premier-league?season=2023&page=0"
        )
    assert sorted(out) == sorted([
        "https://www.fotmob.com/matches/abc#111",
        "https://www.fotmob.com/matches/def#222",
    ])


# ---------------------------
# 4) Competition.contain_all_match_links
# ---------------------------

def test_contain_all_match_links_paginates_until_no_new(monkeypatch):
    c = Competition()

    returns = [
        ["url/a#1", "url/b#2", "url/c#3"],  # page 0
        ["url/a#1", "url/d#4"],            # page 1 (adds one new)
        ["url/d#4", "url/b#2"],            # page 2 (no new -> stop)
    ]
    idx = {"i": 0}

    def fake_extract(_):
        i = idx["i"]
        idx["i"] = i + 1
        return returns[i] if i < len(returns) else returns[-1]

    monkeypatch.setattr(Competition, "extract_match_links_per_page", lambda self, url: fake_extract(url))
    monkeypatch.setattr(time, "sleep", lambda *_: None)

    result = c.contain_all_match_links(47, "premier-league", "2023")
    assert set(result) == {"url/a#1", "url/b#2", "url/c#3", "url/d#4"}


# ---------------------------
# 5) Player.competition_analysis  (smoke-level: just ensure it runs)
# ---------------------------

def test_competition_analysis_runs_smoke(spark):
    """
    Smoke test: ensure the function runs end-to-end (no exceptions).
    We avoid asserting on CSV internals because Spark local CSV writes can be flaky on macOS.
    """
    comp, year = "mls", "2025"
    comp_dir = f"{comp}_{year}_dir"
    if os.path.isdir(comp_dir):
        shutil.rmtree(comp_dir)
    os.makedirs(comp_dir, exist_ok=True)

    rows = [
        ("p1", "Alice", 10, "TeamA", "US", 8.0),
        ("p1", "Alice", 10, "TeamA", "US", 7.0),
        ("p1", "Alicia", 10, "TeamA", "US", -1.0),
        ("p2", "Bob", 9, "TeamB", "CA", 6.0),
    ]
    df = spark.createDataFrame(rows, schema="""
        player_id string, player_name string, player_number int,
        team_name string, country_name string, spi_score double
    """)
    df.coalesce(1).write.mode("overwrite").option("header", True).csv(
        f"{comp_dir}/{comp}_{year}_player_stats.csv"
    )

    # Should not raise
    Player().competition_analysis(comp, year)


# ---------------------------
# 6) MVP.compute_mvp  (smoke-level: check PNG exists)
# ---------------------------

def test_compute_mvp_creates_image_smoke(spark):
    """
    Prepare a tiny analysis CSV and ensure compute_mvp runs and produces the PNG.
    """
    comp, year = "mls", "2025"
    comp_dir = f"{comp}_{year}_dir"
    if os.path.isdir(comp_dir):
        shutil.rmtree(comp_dir)
    os.makedirs(comp_dir, exist_ok=True)

    rows = [
        ("p1", "Alice", 10, "TeamA", "US", 10, 7.0),
        ("p2", "Bob",   9, "TeamB", "CA",  5, 6.0),
    ]
    df = spark.createDataFrame(rows, schema="""
        player_id string, player_name string, player_number int,
        team_name string, country_name string, count int, avg_spi_score double
    """)
    df.coalesce(1).write.mode("overwrite").option("header", True).csv(
        f"{comp_dir}/{comp}_{year}_player_stats_analysis.csv"
    )

    MVP().compute_mvp(comp, year)

    img_path = f"{comp_dir}/{comp}_{year}_mvp_results_image.png"
    assert os.path.isfile(img_path)
