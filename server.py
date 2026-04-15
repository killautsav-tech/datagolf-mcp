"""
DataGolf MCP Server — Full API Coverage
Exposes all 25 DataGolf API endpoints as MCP tools for Claude.
Deploy on Render as a web service.
"""

import os
import json
import httpx
from mcp.server.fastmcp import FastMCP

# ── Config ────────────────────────────────────────────────────────────────────
API_KEY = os.environ.get("DATAGOLF_API_KEY", "")
BASE_URL = "https://feeds.datagolf.com"

mcp = FastMCP("DataGolf")


# ── Helper ────────────────────────────────────────────────────────────────────
async def _call(endpoint: str, params: dict | None = None) -> str:
    """Call the DataGolf API and return JSON text."""
    if not API_KEY:
        return json.dumps({"error": "DATAGOLF_API_KEY environment variable is not set."})

    url = f"{BASE_URL}/{endpoint}"
    query = {"key": API_KEY, "file_format": "json"}
    if params:
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        query.update(params)

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(url, params=query)
            resp.raise_for_status()
            return resp.text
        except httpx.HTTPStatusError as e:
            return json.dumps({"error": f"HTTP {e.response.status_code}", "detail": e.response.text[:500]})
        except Exception as e:
            return json.dumps({"error": str(e)})


# ═════════════════════════════════════════════════════════════════════════════
# 1. GENERAL USE
# ═════════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def get_player_list() -> str:
    """Get the master list of all players who have played on a major tour since 2018, or are playing this week. Returns player IDs, names, country, and amateur status."""
    return await _call("get-player-list")


@mcp.tool()
async def get_schedule(
    tour: str = "pga",
    season: str | None = None,
    upcoming_only: str = "no",
) -> str:
    """Get the season schedule for a tour. Includes event names/IDs, course names/IDs, locations (city/country + lat/lng), and winners for completed events.

    Args:
        tour: Tour code — pga, euro, kft, alt (LIV), or all.
        season: Season year (e.g. 2026). Defaults to current season.
        upcoming_only: 'yes' to show only upcoming events, 'no' for full season.
    """
    return await _call("get-schedule", {"tour": tour, "season": season, "upcoming_only": upcoming_only})


@mcp.tool()
async def get_field_updates(
    tour: str = "pga",
) -> str:
    """Get this week's field list with tee times, start holes, WDs, Monday qualifiers, courses, and player IDs.

    Args:
        tour: Tour code — pga, euro, kft, opp (opposite field PGA), alt (LIV), upcoming_pga (next week).
    """
    return await _call("field-updates", {"tour": tour})


# ═════════════════════════════════════════════════════════════════════════════
# 2. MODEL PREDICTIONS
# ═════════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def get_dg_rankings() -> str:
    """Get the current Data Golf top-500 rankings with skill estimates and OWGR ranks."""
    return await _call("preds/get-dg-rankings")


@mcp.tool()
async def get_pre_tournament_predictions(
    tour: str = "pga",
    add_position: str | None = None,
    dead_heat: str = "yes",
    odds_format: str = "american",
) -> str:
    """Get full-field pre-tournament probabilistic forecasts (win, top 5, top 10, top 20, make cut) from both baseline and course-history models.

    Args:
        tour: Tour code — pga, euro, kft, opp, alt.
        add_position: Comma-separated extra finish positions to include (e.g. '1,2,3,30').
        dead_heat: 'yes' to adjust for dead-heat rules, 'no' for raw.
        odds_format: percent, american, decimal, or fraction.
    """
    return await _call("preds/pre-tournament", {
        "tour": tour, "add_position": add_position,
        "dead_heat": dead_heat, "odds_format": odds_format,
    })


@mcp.tool()
async def get_pre_tournament_predictions_archive(
    event_id: str | None = None,
    year: str = "2026",
    odds_format: str = "american",
) -> str:
    """Get archived pre-tournament predictions for a past PGA Tour event.

    Args:
        event_id: DataGolf event ID (use get_historical_raw_data_event_ids to find IDs). Omit for most recent.
        year: Calendar year of the event (2020–2026).
        odds_format: percent, american, decimal, or fraction.
    """
    return await _call("preds/pre-tournament-archive", {
        "event_id": event_id, "year": year, "odds_format": odds_format,
    })


@mcp.tool()
async def get_player_decompositions(
    tour: str = "pga",
) -> str:
    """Get detailed strokes-gained prediction breakdowns for every player in the upcoming tournament field. Shows the components driving each player's overall prediction.

    Args:
        tour: Tour code — pga, euro, opp, alt.
    """
    return await _call("preds/player-decompositions", {"tour": tour})


@mcp.tool()
async def get_skill_ratings(
    display: str = "value",
) -> str:
    """Get skill ratings and ranks for all players with sufficient measured rounds. Covers driving, approach, around-the-green, putting, and overall.

    Args:
        display: 'value' for raw numbers, 'rank' for rankings.
    """
    return await _call("preds/skill-ratings", {"display": display})


@mcp.tool()
async def get_approach_skill(
    period: str = "l24",
) -> str:
    """Get detailed approach performance stats: SG per shot, proximity, GIR, good shot rate, poor shot avoidance — broken down by yardage and lie.

    Args:
        period: Time window — l24 (last 24 months), l12 (last 12 months), ytd (year to date).
    """
    return await _call("preds/approach-skill", {"period": period})


@mcp.tool()
async def get_fantasy_projections(
    tour: str = "pga",
    site: str = "draftkings",
    slate: str = "main",
) -> str:
    """Get default fantasy projections for DraftKings, FanDuel, or Yahoo contests.

    Args:
        tour: Tour code — pga, euro, opp, alt.
        site: Fantasy site — draftkings, fanduel, yahoo.
        slate: Contest type — main, showdown, showdown_late, weekend, captain (non-main only for DraftKings).
    """
    return await _call("preds/fantasy-projection-defaults", {
        "tour": tour, "site": site, "slate": slate,
    })


# ═════════════════════════════════════════════════════════════════════════════
# 3. LIVE MODEL
# ═════════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def get_live_predictions(
    tour: str = "pga",
    dead_heat: str = "no",
    odds_format: str = "american",
) -> str:
    """Get LIVE in-play finish probabilities (updates every 5 minutes) for the current tournament.

    Args:
        tour: Tour code — pga, euro, opp, kft, alt.
        dead_heat: 'yes' to adjust for dead-heat rules.
        odds_format: percent, american, decimal, or fraction.
    """
    return await _call("preds/in-play", {
        "tour": tour, "dead_heat": dead_heat, "odds_format": odds_format,
    })


@mcp.tool()
async def get_live_tournament_stats(
    stats: str = "sg_putt,sg_arg,sg_app,sg_ott,sg_t2g,sg_total,distance,accuracy,gir,prox_fw,prox_rgh,scrambling",
    round: str = "event_avg",
    display: str = "value",
) -> str:
    """Get LIVE strokes-gained and traditional stats for every player in the current PGA Tour tournament.

    Args:
        stats: Comma-separated stat codes. Options: sg_putt, sg_arg, sg_app, sg_ott, sg_t2g, sg_bs, sg_total, distance, accuracy, gir, prox_fw, prox_rgh, scrambling, great_shots, poor_shots.
        round: Which round(s) — event_cumulative, event_avg, 1, 2, 3, 4.
        display: 'value' for raw numbers, 'rank' for rankings.
    """
    return await _call("preds/live-tournament-stats", {
        "stats": stats, "round": round, "display": display,
    })


@mcp.tool()
async def get_live_hole_stats(
    tour: str = "pga",
) -> str:
    """Get LIVE hole-by-hole scoring averages and distributions (birdies, pars, bogeys) broken down by tee-time wave. Useful for wave advantage analysis.

    Args:
        tour: Tour code — pga, euro, opp, kft, alt.
    """
    return await _call("preds/live-hole-stats", {"tour": tour})


# ═════════════════════════════════════════════════════════════════════════════
# 4. BETTING TOOLS
# ═════════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def get_outright_odds(
    tour: str = "pga",
    market: str = "win",
    odds_format: str = "american",
) -> str:
    """Get current outright/finish-position odds from 11 sportsbooks alongside DataGolf model predictions. Markets: win, top_5, top_10, top_20, make_cut, mc (miss cut), frl (first round leader).

    Args:
        tour: Tour code — pga, euro, kft, opp, alt.
        market: Betting market — win, top_5, top_10, top_20, make_cut, mc, frl.
        odds_format: percent, american, decimal, or fraction.
    """
    return await _call("betting-tools/outrights", {
        "tour": tour, "market": market, "odds_format": odds_format,
    })


@mcp.tool()
async def get_matchup_odds(
    tour: str = "pga",
    market: str = "tournament_matchups",
    odds_format: str = "american",
) -> str:
    """Get current matchup and 3-ball odds from 8 sportsbooks alongside DataGolf model predictions.

    Args:
        tour: Tour code — pga, euro, opp, alt.
        market: Market type — tournament_matchups, round_matchups, 3_balls.
        odds_format: percent, american, decimal, or fraction.
    """
    return await _call("betting-tools/matchups", {
        "tour": tour, "market": market, "odds_format": odds_format,
    })


@mcp.tool()
async def get_matchup_all_pairings(
    tour: str = "pga",
    odds_format: str = "american",
) -> str:
    """Get DataGolf matchup/3-ball odds for EVERY pairing in the next round. Useful for finding value across all groupings.

    Args:
        tour: Tour code — pga, euro, opp, alt.
        odds_format: percent, american, decimal, or fraction.
    """
    return await _call("betting-tools/matchups-all-pairings", {
        "tour": tour, "odds_format": odds_format,
    })


# ═════════════════════════════════════════════════════════════════════════════
# 5. HISTORICAL RAW DATA
# ═════════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def get_historical_raw_data_event_ids(
    tour: str = "pga",
) -> str:
    """Get the list of tournaments and IDs available in the historical raw data archive. Use these IDs to query round-level scoring and SG data.

    Args:
        tour: Tour code — pga, euro, kft, jpn, anz, kor, liv, and many more.
    """
    return await _call("historical-raw-data/event-list", {"tour": tour})


@mcp.tool()
async def get_historical_rounds(
    tour: str = "pga",
    event_id: str = "all",
    year: str = "2026",
) -> str:
    """Get round-level scoring, traditional stats, strokes-gained, and tee time data for a specific historical event. Covers 22 global tours.

    Args:
        tour: Tour code — pga, euro, kft, jpn, anz, kor, liv, etc.
        event_id: Event ID from get_historical_raw_data_event_ids, or 'all' for every event in that year.
        year: Calendar year (1983–2026 for majors, 2004–2026 for PGA Tour).
    """
    return await _call("historical-raw-data/rounds", {
        "tour": tour, "event_id": event_id, "year": year,
    })


# ═════════════════════════════════════════════════════════════════════════════
# 6. HISTORICAL EVENT STATS
# ═════════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def get_historical_event_data_ids(
    tour: str = "pga",
) -> str:
    """Get the list of tournaments and IDs available in the historical event data archive (finishes, earnings, points).

    Args:
        tour: pga.
    """
    return await _call("historical-event-data/event-list", {"tour": tour})


@mcp.tool()
async def get_historical_event_finishes(
    tour: str = "pga",
    event_id: str = "14",
    year: str = "2025",
) -> str:
    """Get event-level finishes, earnings, FedExCup points, and DG Points for a PGA Tour event.

    Args:
        tour: pga.
        event_id: Event ID from get_historical_event_data_ids.
        year: Calendar year (2025, 2026).
    """
    return await _call("historical-event-data/events", {
        "tour": tour, "event_id": event_id, "year": year,
    })


# ═════════════════════════════════════════════════════════════════════════════
# 7. HISTORICAL ODDS
# ═════════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def get_historical_odds_event_ids(
    tour: str = "pga",
) -> str:
    """Get the list of tournaments and IDs available in the historical odds archive.

    Args:
        tour: Tour code — pga, euro, alt.
    """
    return await _call("historical-odds/event-list", {"tour": tour})


@mcp.tool()
async def get_historical_outrights(
    tour: str = "pga",
    event_id: str | None = None,
    year: str = "2025",
    market: str = "win",
    book: str = "draftkings",
    odds_format: str = "american",
) -> str:
    """Get historical opening and closing outright odds at a specific sportsbook for a past event. Includes bet outcomes.

    Args:
        tour: Tour code — pga, euro, alt.
        event_id: Event ID (omit for most recent, or 'all' for full year).
        year: Calendar year (2019–2026).
        market: Market — win, top_5, top_10, top_20, make_cut, mc.
        book: Sportsbook — draftkings, fanduel, betmgm, caesars, pinnacle, bet365, bovada, betonline, betway, circa, etc.
        odds_format: percent, american, decimal, or fraction.
    """
    return await _call("historical-odds/outrights", {
        "tour": tour, "event_id": event_id, "year": year,
        "market": market, "book": book, "odds_format": odds_format,
    })


@mcp.tool()
async def get_historical_matchups(
    tour: str = "pga",
    event_id: str | None = None,
    year: str = "2025",
    book: str = "draftkings",
    odds_format: str = "american",
) -> str:
    """Get historical opening and closing matchup/3-ball odds at a specific sportsbook for a past event. Includes bet outcomes.

    Args:
        tour: Tour code — pga, euro, alt.
        event_id: Event ID (omit for most recent, or 'all' for full year).
        year: Calendar year (2019–2026).
        book: Sportsbook — draftkings, fanduel, betmgm, caesars, pinnacle, bet365, bovada, circa, etc.
        odds_format: percent, american, decimal, or fraction.
    """
    return await _call("historical-odds/matchups", {
        "tour": tour, "event_id": event_id, "year": year,
        "book": book, "odds_format": odds_format,
    })


# ═════════════════════════════════════════════════════════════════════════════
# 8. HISTORICAL DFS
# ═════════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def get_historical_dfs_event_ids() -> str:
    """Get the list of tournaments and IDs available in the historical DFS data archive."""
    return await _call("historical-dfs-data/event-list")


@mcp.tool()
async def get_historical_dfs_points(
    tour: str = "pga",
    site: str = "draftkings",
    event_id: str = "535",
    year: str = "2025",
) -> str:
    """Get historical DFS salaries, ownerships, and scoring breakdowns for a past event.

    Args:
        tour: Tour code — pga, euro.
        site: Fantasy site — draftkings, fanduel.
        event_id: Event ID from get_historical_dfs_event_ids.
        year: Calendar year (2017–2025).
    """
    return await _call("historical-dfs-data/points", {
        "tour": tour, "site": site, "event_id": event_id, "year": year,
    })


# ═════════════════════════════════════════════════════════════════════════════
# RUN
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = port
    mcp.run(transport="sse")
