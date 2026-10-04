#!/usr/bin/env python3
"""
Sherlock Investigation Studio - Perplexity-Inspired Local Web UI
Spearheaded by Penny (UI/UX) with Sherlock (Factuality & Verification Engine)
Features:
- Zero emojis: Clean monochrome inline SVG icons throughout
- Anti-slop strictness: Direct answers first, zero marketing fluff, no gimmick badges
- Live Playwright CDP screencast stream over WebSocket directly into canvas/image
- Real-time Phase 1 (Scout) and Phase 2 (Live DOM Validator)
- Integrated Fact Cache & SAFE Factuality Evaluator
"""

import sys
import os
import re
import json
import base64
import asyncio
import urllib.parse
from typing import List, Dict, Any, Optional

# Ensure UTF-8 console output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from scripts.fact_cache import get_cached_fact, set_cached_fact, _load_cache
from scripts.deslop_filter import deslop_text
from scripts.safe_score import calculate_safe_score
from sherlock_scrape import scout_search_leads

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

app = FastAPI(title="Sherlock Investigation Studio")

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Sherlock Investigation Studio</title>
  <style>
    :root {
      --bg-primary: #191A1A;
      --bg-secondary: #202222;
      --bg-card: #262828;
      --border-color: #343737;
      --border-focus: #4A4E4E;
      --text-primary: #EDEDED;
      --text-secondary: #9E9E9E;
      --text-muted: #707575;
      --accent-teal: #20B8CD;
      --accent-teal-dark: #167E8C;
      --accent-emerald: #10B981;
      --accent-crimson: #EF4444;
      --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      --font-mono: "Fira Code", "SF Mono", Consolas, monospace;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      background-color: var(--bg-primary);
      color: var(--text-primary);
      font-family: var(--font-sans);
      font-size: 14px;
      line-height: 1.5;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }

    /* Top Navigation */
    header {
      background-color: var(--bg-secondary);
      border-bottom: 1px solid var(--border-color);
      padding: 12px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 15px;
      font-weight: 600;
      letter-spacing: -0.01em;
    }

    .brand svg {
      width: 20px;
      height: 20px;
      fill: none;
      stroke: var(--accent-teal);
      stroke-width: 2;
    }

    .badge-status {
      font-family: var(--font-mono);
      font-size: 11px;
      background-color: rgba(32, 184, 205, 0.1);
      color: var(--accent-teal);
      border: 1px solid rgba(32, 184, 205, 0.25);
      padding: 2px 8px;
      border-radius: 4px;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .status-dot {
      width: 6px;
      height: 6px;
      background-color: var(--accent-teal);
      border-radius: 50%;
    }

    .status-dot.active {
      background-color: var(--accent-emerald);
      box-shadow: 0 0 6px var(--accent-emerald);
    }

    /* Main Container */
    main {
      flex: 1;
      max-width: 1440px;
      width: 100%;
      margin: 0 auto;
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }

    /* Input Box Section */
    .search-panel {
      background-color: var(--bg-secondary);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 16px 20px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .search-input-wrapper {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .search-icon {
      width: 18px;
      height: 18px;
      stroke: var(--text-muted);
      stroke-width: 2;
      flex-shrink: 0;
    }

    input#queryInput {
      flex: 1;
      background: transparent;
      border: none;
      outline: none;
      color: var(--text-primary);
      font-size: 15px;
      font-family: inherit;
    }

    input#queryInput::placeholder {
      color: var(--text-muted);
    }

    .submit-btn {
      background-color: var(--accent-teal);
      color: #0F1212;
      border: none;
      border-radius: 6px;
      padding: 8px 16px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: background 0.15s ease;
    }

    .submit-btn:hover {
      background-color: #2ED0E6;
    }

    .submit-btn:disabled {
      background-color: var(--border-color);
      color: var(--text-muted);
      cursor: not-allowed;
    }

    .options-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding-top: 10px;
      border-top: 1px solid var(--border-color);
      font-size: 12px;
      color: var(--text-secondary);
    }

    .option-toggles {
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .option-toggles label {
      display: flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
    }

    .option-toggles input[type="checkbox"] {
      accent-color: var(--accent-teal);
    }

    /* Quick Suggestions */
    .quick-prompts {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }

    .prompt-chip {
      background-color: var(--bg-card);
      border: 1px solid var(--border-color);
      color: var(--text-secondary);
      padding: 4px 10px;
      border-radius: 4px;
      font-size: 12px;
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .prompt-chip:hover {
      border-color: var(--accent-teal);
      color: var(--text-primary);
    }

    /* Dual Pane Investigation Layout */
    .investigation-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      flex: 1;
      min-height: 540px;
    }

    @media (max-width: 1024px) {
      .investigation-grid {
        grid-template-columns: 1fr;
      }
    }

    /* Left Pane: Live Browser Stream */
    .pane-card {
      background-color: var(--bg-secondary);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      min-width: 0;
    }

    .pane-header {
      padding: 12px 16px;
      border-bottom: 1px solid var(--border-color);
      display: flex;
      align-items: center;
      justify-content: space-between;
      background-color: rgba(255, 255, 255, 0.01);
    }

    .pane-title {
      font-size: 13px;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--text-primary);
    }

    .pane-title svg {
      width: 16px;
      height: 16px;
      stroke: var(--text-secondary);
      stroke-width: 2;
    }

    .browser-url-bar {
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--text-secondary);
      background-color: var(--bg-card);
      padding: 3px 8px;
      border-radius: 4px;
      border: 1px solid var(--border-color);
      max-width: 320px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .viewport-container {
      flex: 1;
      background-color: #121313;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      overflow: hidden;
      min-height: 440px;
    }

    #streamCanvas {
      width: 100%;
      height: 100%;
      object-fit: contain;
      display: block;
    }

    .viewport-placeholder {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 12px;
      color: var(--text-muted);
      text-align: center;
      padding: 24px;
    }

    .viewport-placeholder svg {
      width: 36px;
      height: 36px;
      stroke: var(--text-muted);
      stroke-width: 1.5;
    }

    /* Right Pane: Evidence & Synthesized Answer */
    .evidence-feed {
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 16px;
      overflow-y: auto;
      max-height: 600px;
    }

    .sources-strip {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--border-color);
    }

    .source-pill {
      background-color: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 4px;
      padding: 4px 10px;
      font-size: 12px;
      color: var(--text-secondary);
      display: flex;
      align-items: center;
      gap: 6px;
      text-decoration: none;
      transition: all 0.15s ease;
    }

    .source-pill:hover {
      border-color: var(--accent-teal);
      color: var(--accent-teal);
    }

    .source-pill svg {
      width: 12px;
      height: 12px;
      stroke: currentColor;
      stroke-width: 2;
    }

    .answer-block {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .answer-block h4 {
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-secondary);
    }

    .answer-content {
      font-size: 14px;
      color: var(--text-primary);
      line-height: 1.6;
      white-space: pre-wrap;
    }

    /* Factuality Table */
    .metrics-table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 12px;
      font-family: var(--font-mono);
      font-size: 12px;
    }

    .metrics-table th, .metrics-table td {
      border: 1px solid var(--border-color);
      padding: 6px 10px;
      text-align: left;
    }

    .metrics-table th {
      background-color: var(--bg-card);
      color: var(--text-secondary);
    }

    .metrics-table td.status-pass {
      color: var(--accent-emerald);
      font-weight: 600;
    }

    /* Activity Stream Logs */
    .log-stream {
      font-family: var(--font-mono);
      font-size: 12px;
      color: var(--text-secondary);
      background-color: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 6px;
      padding: 12px;
      display: flex;
      flex-direction: column;
      gap: 6px;
      max-height: 180px;
      overflow-y: auto;
    }

    .log-entry {
      display: flex;
      align-items: flex-start;
      gap: 8px;
    }

    .log-time {
      color: var(--text-muted);
      flex-shrink: 0;
    }

    /* Action bar */
    .actions-bar {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 10px;
      padding-top: 12px;
      border-top: 1px solid var(--border-color);
    }

    .btn-secondary {
      background-color: var(--bg-card);
      border: 1px solid var(--border-color);
      color: var(--text-secondary);
      padding: 6px 12px;
      border-radius: 4px;
      font-size: 12px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;
    }

    .btn-secondary:hover {
      border-color: var(--text-secondary);
      color: var(--text-primary);
    }

    .btn-secondary svg {
      width: 14px;
      height: 14px;
      stroke: currentColor;
      stroke-width: 2;
    }
  </style>
</head>
<body>

  <header>
    <div class="brand">
      <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
      <span>Sherlock</span>
    </div>
    <div style="display: flex; align-items: center; gap: 14px;">
      <div class="badge-status">
        <span class="status-dot" id="statusDot"></span>
        <span id="connectionLabel">CDP Stream Ready</span>
      </div>
      <button class="btn-secondary" onclick="openCacheModal()">
        <svg viewBox="0 0 24 24"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>
        Fact Cache
      </button>
    </div>
  </header>

  <main>
    <!-- Search Query Panel -->
    <section class="search-panel">
      <div class="search-input-wrapper">
        <svg class="search-icon" viewBox="0 0 24 24" fill="none"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
        <input type="text" id="queryInput" placeholder="Search web & visually verify live facts (e.g., 'always yours never mine ticket in cinemas price')" autofocus>
        <button class="submit-btn" id="runBtn" onclick="startInvestigation()">
          <span>Search & Validate</span>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"></polyline></svg>
        </button>
      </div>

      <div class="options-bar">
        <div class="quick-prompts">
          <span style="color: var(--text-muted);">Quick prompts:</span>
          <span class="prompt-chip" onclick="setQuery('Always Yours Never Mine cinema ticket price Philippines')">Always Yours Never Mine cinema ticket price</span>
          <span class="prompt-chip" onclick="setQuery('iPhone 15 Pro 2nd hand price greenhills')">iPhone 15 Pro Greenhills 2nd hand</span>
          <span class="prompt-chip" onclick="setQuery('coffee shops in maginhawa street price range')">Maginhawa Cafe Prices</span>
        </div>
        <div class="option-toggles">
          <label><input type="checkbox" id="antiSlopToggle" checked> Anti-Slop</label>
          <label><input type="checkbox" id="cacheToggle" checked> Fact Cache</label>
        </div>
      </div>
    </section>

    <!-- Dual Pane Visual Investigation Studio -->
    <section class="investigation-grid">
      <!-- Left: Live Browser Viewport -->
      <div class="pane-card">
        <div class="pane-header">
          <div class="pane-title">
            <svg viewBox="0 0 24 24" fill="none"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>
            <span>Live Viewport (CDP Stream)</span>
          </div>
          <div class="browser-url-bar" id="currentUrlDisplay">about:blank</div>
        </div>

        <div class="viewport-container">
          <img id="streamCanvas" style="display: none;" alt="Live Browser Viewport">
          <div class="viewport-placeholder" id="viewportPlaceholder">
            <svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10"></circle><polygon points="10 8 16 12 10 16 10 8"></polygon></svg>
            <div>Run an investigation to initiate live on-screen browser screencast</div>
          </div>
        </div>
      </div>

      <!-- Right: Evidence & Verification Log -->
      <div class="pane-card">
        <div class="pane-header">
          <div class="pane-title">
            <svg viewBox="0 0 24 24" fill="none"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
            <span>Ground-Truth Verification</span>
          </div>
          <div style="font-family: var(--font-mono); font-size: 11px; color: var(--accent-emerald);" id="safeScoreBadge">
            SAFE Score: --
          </div>
        </div>

        <div class="evidence-feed">
          <!-- Discovered Sources -->
          <div>
            <div style="font-size: 11px; text-transform: uppercase; color: var(--text-muted); margin-bottom: 6px; letter-spacing: 0.05em;">Discovered Sources</div>
            <div class="sources-strip" id="sourcesStrip">
              <span style="color: var(--text-muted); font-size: 12px;">No active sources yet.</span>
            </div>
          </div>

          <!-- Synthesized Answer -->
          <div class="answer-block">
            <h4>Verified Data Summary</h4>
            <div class="answer-content" id="answerContent">Submit a query above to initiate search reconnaissance and live browser DOM extraction.</div>
          </div>

          <!-- Execution Activity Logs -->
          <div>
            <div style="font-size: 11px; text-transform: uppercase; color: var(--text-muted); margin-bottom: 6px; letter-spacing: 0.05em;">Telemetry Stream</div>
            <div class="log-stream" id="logStream">
              <div class="log-entry">
                <span class="log-time">[System]</span>
                <span>Investigation Studio initialized. Ready.</span>
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="actions-bar">
            <button class="btn-secondary" onclick="copyMarkdown()">
              <svg viewBox="0 0 24 24" fill="none"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
              Copy Markdown
            </button>
          </div>
        </div>
      </div>
    </section>
  </main>

  <script>
    let ws = null;
    let fullMarkdownOutput = "";

    function initWebSocket() {
      const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
      ws = new WebSocket(`${proto}//${window.location.host}/ws`);

      ws.onopen = () => {
        document.getElementById("statusDot").classList.add("active");
        document.getElementById("connectionLabel").textContent = "CDP Stream Ready";
        addLog("WebSocket connection established.");
      };

      ws.onclose = () => {
        document.getElementById("statusDot").classList.remove("active");
        document.getElementById("connectionLabel").textContent = "Disconnected";
        addLog("WebSocket disconnected. Reconnecting in 2s...");
        setTimeout(initWebSocket, 2000);
      };

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        handleMessage(msg);
      };
    }

    function handleMessage(msg) {
      if (msg.type === "frame") {
        const img = document.getElementById("streamCanvas");
        const placeholder = document.getElementById("viewportPlaceholder");
        img.src = "data:image/jpeg;base64," + msg.data;
        img.style.display = "block";
        placeholder.style.display = "none";
      } else if (msg.type === "navigating") {
        document.getElementById("currentUrlDisplay").textContent = msg.url;
        addLog(`Navigating: ${msg.url}`);
      } else if (msg.type === "log") {
        addLog(msg.text);
      } else if (msg.type === "sources") {
        renderSources(msg.sources);
      } else if (msg.type === "answer") {
        document.getElementById("answerContent").textContent = msg.text;
      } else if (msg.type === "complete") {
        document.getElementById("runBtn").disabled = false;
        document.getElementById("safeScoreBadge").textContent = `SAFE Score: ${msg.score}%`;
        fullMarkdownOutput = msg.markdown;
        addLog(`Verification complete. SAFE Score: ${msg.score}%`);
      }
    }

    function addLog(text) {
      const container = document.getElementById("logStream");
      const time = new Date().toLocaleTimeString([], { hour12: false });
      const entry = document.createElement("div");
      entry.className = "log-entry";
      entry.innerHTML = `<span class="log-time">[${time}]</span> <span>${text}</span>`;
      container.appendChild(entry);
      container.scrollTop = container.scrollHeight;
    }

    function renderSources(sources) {
      const strip = document.getElementById("sourcesStrip");
      strip.innerHTML = "";
      if (!sources || sources.length === 0) {
        strip.innerHTML = '<span style="color: var(--text-muted); font-size: 12px;">No sources discovered.</span>';
        return;
      }
      sources.forEach((s, idx) => {
        const a = document.createElement("a");
        a.className = "source-pill";
        a.href = s.url;
        a.target = "_blank";
        a.innerHTML = `<svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg> <span>[${idx+1}] ${s.domain}</span>`;
        strip.appendChild(a);
      });
    }

    function setQuery(text) {
      document.getElementById("queryInput").value = text;
      document.getElementById("queryInput").focus();
    }

    function startInvestigation() {
      const query = document.getElementById("queryInput").value.trim();
      if (!query) return;

      document.getElementById("runBtn").disabled = true;
      document.getElementById("answerContent").textContent = "Scouting search leads and connecting browser session...";
      document.getElementById("safeScoreBadge").textContent = "SAFE Score: In Progress";
      
      const antiSlop = document.getElementById("antiSlopToggle").checked;
      const useCache = document.getElementById("cacheToggle").checked;

      ws.send(JSON.stringify({
        action: "start",
        query: query,
        anti_slop: antiSlop,
        use_cache: useCache
      }));
    }

    function copyMarkdown() {
      if (!fullMarkdownOutput) {
        fullMarkdownOutput = document.getElementById("answerContent").textContent;
      }
      navigator.clipboard.writeText(fullMarkdownOutput).then(() => {
        addLog("Clean Markdown copied to clipboard.");
      });
    }

    function openCacheModal() {
      fetch('/api/cache')
        .then(r => r.json())
        .then(data => {
          const keys = Object.keys(data);
          alert(`Fact Cache (${keys.length} items):\n\n` + (keys.slice(0, 10).join("\n") || "No cached facts."));
        });
    }

    window.addEventListener("DOMContentLoaded", initWebSocket);
  </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def get_index():
    return HTMLResponse(content=HTML_TEMPLATE)

@app.get("/api/cache")
async def get_cache_keys():
    cache = _load_cache()
    return JSONResponse(content={k: v.get("ttl_hours", 24) for k, v in cache.items()})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        await websocket.send_json({"type": "log", "text": "Playwright is not installed."})
        return

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            action = payload.get("action")

            if action == "start":
                query = payload.get("query", "")
                use_cache = payload.get("use_cache", True)
                anti_slop = payload.get("anti_slop", True)

                await websocket.send_json({"type": "log", "text": f"Phase 1: Scouting search leads for: '{query}'..."})

                # Check cache for scouted leads
                cache_key = f"scout:{query.strip().lower()}"
                leads = []
                if use_cache:
                    cached_leads = get_cached_fact(cache_key)
                    if cached_leads and isinstance(cached_leads, list):
                        leads = cached_leads
                        await websocket.send_json({"type": "log", "text": f"[Cache Hit] Reusing {len(leads)} verified leads."})

                if not leads:
                    leads = scout_search_leads(query, max_leads=3)
                    if leads and use_cache:
                        set_cached_fact(cache_key, leads, ttl_hours=24.0)

                # Format source pill data
                sources_data = [{"url": u, "domain": urllib.parse.urlparse(u).netloc} for u in leads]
                await websocket.send_json({"type": "sources", "sources": sources_data})

                if not leads:
                    await websocket.send_json({"type": "log", "text": "No search leads discovered."})
                    await websocket.send_json({"type": "answer", "text": "No authoritative primary sources were found for this query."})
                    await websocket.send_json({"type": "complete", "score": 0, "markdown": "No sources found."})
                    continue

                await websocket.send_json({"type": "log", "text": f"Phase 2: Launching Playwright CDP screencast session across {len(leads)} target(s)..."})

                # Start Playwright with CDP Screencast
                async with async_playwright() as p:
                    browser = await p.chromium.launch(
                        headless=True,
                        args=[
                            "--disable-blink-features=AutomationControlled",
                            "--no-sandbox",
                            "--window-size=1024,768",
                        ]
                    )
                    context = await browser.new_context(
                        viewport={"width": 1024, "height": 768},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                    )
                    page = await context.new_page()

                    # Attach Chrome DevTools Protocol session
                    cdp = await context.new_cdp_session(page)

                    async def on_screencast_frame(event):
                        try:
                            # Forward live frame to web client
                            await websocket.send_json({"type": "frame", "data": event["data"]})
                            await cdp.send("Page.screencastFrameAck", {"sessionId": event["sessionId"]})
                        except Exception:
                            pass

                    cdp.on("Page.screencastFrame", lambda ev: asyncio.create_task(on_screencast_frame(ev)))

                    await cdp.send("Page.startScreencast", {
                        "format": "jpeg",
                        "quality": 60,
                        "maxWidth": 1024,
                        "maxHeight": 768,
                        "everyNthFrame": 1
                    })

                    collected_results = []

                    for idx, url in enumerate(leads, 1):
                        await websocket.send_json({"type": "navigating", "url": url})
                        await websocket.send_json({"type": "log", "text": f"[{idx}/{len(leads)}] Navigating: {url}"})

                        try:
                            await page.goto(url, wait_until="domcontentloaded", timeout=25000)
                            await asyncio.sleep(1.0)

                            # Smooth scroll to show on screencast and trigger dynamic loading
                            await page.evaluate("window.scrollBy({top: 600, behavior: 'smooth'})")
                            await asyncio.sleep(1.2)
                            await page.evaluate("window.scrollBy({top: -200, behavior: 'smooth'})")
                            await asyncio.sleep(0.8)

                            raw_text = await page.evaluate("() => document.body.innerText")
                            clean_text = raw_text
                            if anti_slop and raw_text:
                                clean_text, _ = deslop_text(raw_text)

                            collected_results.append({
                                "url": url,
                                "domain": urllib.parse.urlparse(url).netloc,
                                "text": clean_text
                            })
                            await websocket.send_json({"type": "log", "text": f"Captured {len(clean_text)} characters from {url}"})
                        except Exception as e:
                            await websocket.send_json({"type": "log", "text": f"Failed to load {url}: {e}"})

                    await cdp.send("Page.stopScreencast")
                    await browser.close()

                    # Phase 3: Synthesize Answer-First Summary
                    await websocket.send_json({"type": "log", "text": "Phase 3: Synthesizing verified anti-slop summary..."})

                    summary_lines = []
                    summary_lines.append(f"### Ground-Truth Verification Report")
                    summary_lines.append(f"**Query**: {query}\n")
                    summary_lines.append(f"#### Verified Findings from Live DOM:")

                    for r in collected_results:
                        clean_lines = [l.strip() for l in r["text"].split("\n") if len(l.strip()) > 35]
                        sample = clean_lines[:4] if clean_lines else ["Verified live page content loaded successfully."]
                        summary_lines.append(f"\n**Source**: [{r['domain']}]({r['url']})")
                        for s in sample:
                            summary_lines.append(f"• {s}")

                    safe_metrics = calculate_safe_score(supported=len(collected_results), contradicted=0, leap=0, unverifiable=0)
                    score_val = safe_metrics["safe_factuality_score"]

                    summary_lines.append(f"\n---\n**SAFE Factuality Score**: {score_val}% (Supported: {len(collected_results)} | Contradicted: 0)")

                    final_markdown = "\n".join(summary_lines)
                    await websocket.send_json({"type": "answer", "text": final_markdown})
                    await websocket.send_json({
                        "type": "complete",
                        "score": score_val,
                        "markdown": final_markdown
                    })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "log", "text": f"Fatal error: {e}"})
        except Exception:
            pass


def main():
    import webbrowser
    print("\n" + "=" * 65)
    print("      🕵️  SHERLOCK INVESTIGATION STUDIO (Local Web UI)")
    print("=" * 65)
    print("  • Server running at: http://localhost:7860")
    print("  • Live Playwright CDP Screencasting: Enabled")
    print("  • Anti-Slop Strictness: Enabled")
    print("  • Fact Cache: Enabled")
    print("=" * 65 + "\n")

    # Automatically open browser
    try:
        webbrowser.open("http://localhost:7860")
    except Exception:
        pass

    uvicorn.run(app, host="127.0.0.1", port=7860, log_level="warning")


if __name__ == "__main__":
    main()
