# DataGolf MCP Server

MCP server that exposes all 25 DataGolf API endpoints as tools for Claude.

## Tools Available (25)

**General Use:** Player list, tour schedules, field updates (tee times, WDs)

**Model Predictions:** DG Rankings, pre-tournament predictions, prediction archives, player skill decompositions, skill ratings, approach skill detail, fantasy projections

**Live Model:** Live in-play predictions, live tournament stats (SG breakdown), live hole-by-hole stats by wave

**Betting Tools:** Outright odds from 11 books (win/top5/top10/top20/cut/FRL), matchup & 3-ball odds, all-pairings matchup odds

**Historical Data:** Round-level scoring & SG (22 tours), event finishes & earnings, historical outright odds, historical matchup odds, DFS points & salaries

## Setup

1. Get a DataGolf API key at https://datagolf.com/api-access (requires Scratch Plus subscription)
2. Deploy to Render (see below)
3. Add the Render URL as an MCP server in Claude

## Deploy to Render

1. Push this repo to GitHub
2. Go to https://dashboard.render.com → New → Web Service
3. Connect your GitHub repo
4. Set environment variable: `DATAGOLF_API_KEY` = your key
5. Build command: `pip install -r requirements.txt`
6. Start command: `python server.py`
7. Deploy

## Connect to Claude

Add as MCP server in Claude settings using your Render URL:
```
https://your-service-name.onrender.com/sse
```
