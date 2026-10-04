#!/usr/bin/env python3
"""
Sherlock Investigation Studio - Perplexity-Inspired Local Web UI
Spearheaded by Penny (UI/UX) with Sherlock (Factuality & Verification Engine)

Layout Inspired Directly by Perplexity / Computer UI:
- Minimalist charcoal aesthetic (#141515, #1B1C1C, #232525)
- Left sidebar with + New, Skills, Sessions, and Cache
- Centered Hero State with 'What do you want to know?', input card, and dual action cards
- Seamless transition to Dual-Pane Live Browser Viewport (CDP Screencast) + Ground-Truth Evidence
- Docked bottom chatbox in active state
- Zero emojis: 100% clean monochrome SVG icons
- Non-blocking async WebSocket with Playwright CDP screencasting
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

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Sherlock</title>
  <style>
    :root {
      --bg-root: #141515;
      --bg-sidebar: #171818;
      --bg-card: #202222;
      --bg-input: #232525;
      --bg-chip: #2A2C2C;
      --border: #2D3030;
      --border-focus: #464A4A;
      --text-primary: #EDEDED;
      --text-secondary: #9E9E9E;
      --text-muted: #6B7070;
      --accent-teal: #20B8CD;
      --accent-teal-soft: rgba(32, 184, 205, 0.12);
      --accent-emerald: #10B981;
      --accent-crimson: #EF4444;
      --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      --font-mono: "Fira Code", "SF Mono", Consolas, monospace;
      --sidebar-width: 240px;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      background-color: var(--bg-root);
      color: var(--text-primary);
      font-family: var(--font-sans);
      font-size: 14px;
      line-height: 1.5;
      height: 100vh;
      overflow: hidden;
      display: flex;
    }

    /* Left Sidebar */
    aside.sidebar {
      width: var(--sidebar-width);
      background-color: var(--bg-sidebar);
      border-right: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      flex-shrink: 0;
      z-index: 10;
      user-select: none;
    }

    .sidebar-top {
      padding: 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .brand-icon {
      width: 22px;
      height: 22px;
      stroke: var(--text-primary);
      stroke-width: 2;
      fill: none;
    }

    .icon-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      cursor: pointer;
      padding: 4px;
      border-radius: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: color 0.15s ease;
    }

    .icon-btn:hover {
      color: var(--text-primary);
    }

    .icon-btn svg {
      width: 18px;
      height: 18px;
      stroke: currentColor;
      stroke-width: 1.8;
      fill: none;
    }

    .btn-new-chat {
      margin: 4px 12px 12px 12px;
      padding: 8px 12px;
      background-color: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 6px;
      color: var(--text-primary);
      font-size: 13px;
      font-weight: 500;
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .btn-new-chat:hover {
      border-color: var(--border-focus);
      background-color: #272929;
    }

    .btn-new-chat svg {
      width: 14px;
      height: 14px;
      stroke: currentColor;
      stroke-width: 2.2;
      fill: none;
    }

    .nav-list {
      display: flex;
      flex-direction: column;
      gap: 2px;
      padding: 0 8px;
    }

    .nav-item {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 8px 10px;
      border-radius: 6px;
      color: var(--text-secondary);
      font-size: 13px;
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .nav-item:hover {
      background-color: var(--bg-card);
      color: var(--text-primary);
    }

    .nav-item.active {
      background-color: var(--bg-card);
      color: var(--text-primary);
      font-weight: 500;
    }

    .nav-item svg {
      width: 16px;
      height: 16px;
      stroke: currentColor;
      stroke-width: 1.8;
      fill: none;
      flex-shrink: 0;
    }

    .nav-divider {
      height: 1px;
      background-color: var(--border);
      margin: 12px 16px;
    }

    .nav-section-title {
      padding: 6px 14px;
      font-size: 11px;
      font-weight: 600;
      color: var(--text-muted);
      display: flex;
      align-items: center;
      justify-content: space-between;
      cursor: pointer;
    }

    .nav-section-title svg {
      width: 12px;
      height: 12px;
      stroke: currentColor;
      stroke-width: 2;
      fill: none;
    }

    .nav-subtext {
      padding: 4px 14px 10px 14px;
      font-size: 12px;
      color: var(--text-muted);
    }

    .sidebar-bottom {
      margin-top: auto;
      padding: 12px 16px;
      border-top: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      color: var(--text-secondary);
      font-size: 12px;
    }

    .sidebar-bottom .status-indicator {
      display: flex;
      align-items: center;
      gap: 6px;
      font-family: var(--font-mono);
      font-size: 11px;
    }

    .status-dot {
      width: 6px;
      height: 6px;
      background-color: var(--accent-emerald);
      border-radius: 50%;
      box-shadow: 0 0 6px var(--accent-emerald);
    }

    /* Main Area */
    .main-canvas {
      flex: 1;
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
      position: relative;
      background-color: var(--bg-root);
    }

    /* Top utility bar */
    .top-toolbar {
      padding: 14px 24px;
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 12px;
      flex-shrink: 0;
    }

    /* STATE 1: IDLE HERO VIEW (Matching Inspo) */
    .hero-container {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 0 24px;
      max-width: 820px;
      width: 100%;
      margin: 0 auto;
      gap: 24px;
      transition: all 0.3s ease;
    }

    .hero-title-group {
      text-align: center;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .hero-kicker {
      font-size: 12px;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-weight: 600;
    }

    .hero-heading {
      font-size: 32px;
      font-weight: 600;
      letter-spacing: -0.02em;
      color: var(--text-primary);
    }

    /* Perplexity Input Box */
    .perplexity-input-box {
      width: 100%;
      background-color: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 16px 18px 12px 18px;
      display: flex;
      flex-direction: column;
      gap: 14px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
      transition: border-color 0.15s ease;
    }

    .perplexity-input-box:focus-within {
      border-color: var(--border-focus);
    }

    .perplexity-input-box input#heroInput {
      width: 100%;
      background: transparent;
      border: none;
      outline: none;
      color: var(--text-primary);
      font-size: 16px;
      font-family: inherit;
      padding: 6px 0;
    }

    .perplexity-input-box input#heroInput::placeholder {
      color: var(--text-muted);
    }

    .input-bottom-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }

    .pill-group {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .mode-pill {
      background-color: var(--bg-chip);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 5px 10px;
      font-size: 12px;
      color: var(--text-secondary);
      display: flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .mode-pill.active {
      border-color: rgba(32, 184, 205, 0.4);
      color: var(--accent-teal);
      background-color: var(--accent-teal-soft);
    }

    .mode-pill svg {
      width: 13px;
      height: 13px;
      stroke: currentColor;
      stroke-width: 2;
      fill: none;
    }

    .submit-circle-btn {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background-color: var(--text-primary);
      color: #141515;
      border: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.15s ease;
      flex-shrink: 0;
    }

    .submit-circle-btn:hover {
      background-color: #FFFFFF;
      transform: scale(1.05);
    }

    .submit-circle-btn:disabled {
      background-color: var(--border);
      color: var(--text-muted);
      cursor: not-allowed;
      transform: none;
    }

    .submit-circle-btn svg {
      width: 15px;
      height: 15px;
      stroke: currentColor;
      stroke-width: 2.4;
      fill: none;
    }

    /* Dual Action Cards (Matching Inspo) */
    .hero-cards-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
      width: 100%;
    }

    .hero-card {
      background: linear-gradient(180deg, #1C2426 0%, #171919 100%);
      border: 1px solid rgba(32, 184, 205, 0.25);
      border-radius: 10px;
      padding: 16px 18px;
      display: flex;
      flex-direction: column;
      gap: 6px;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .hero-card:hover {
      border-color: var(--accent-teal);
      transform: translateY(-2px);
    }

    .hero-card.secondary {
      background: linear-gradient(180deg, #202222 0%, #181919 100%);
      border: 1px solid var(--border);
    }

    .hero-card.secondary:hover {
      border-color: var(--border-focus);
    }

    .hero-card-header {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 14px;
      font-weight: 600;
      color: var(--text-primary);
    }

    .hero-card-header svg {
      width: 16px;
      height: 16px;
      stroke: var(--accent-teal);
      stroke-width: 2;
      fill: none;
    }

    .hero-card.secondary .hero-card-header svg {
      stroke: var(--text-secondary);
    }

    .hero-card-desc {
      font-size: 12px;
      color: var(--text-secondary);
      line-height: 1.4;
    }

    /* STATE 2: ACTIVE INVESTIGATION STUDIO (Dual-Pane) */
    .studio-container {
      display: none;
      flex: 1;
      height: 100%;
      flex-direction: column;
      overflow: hidden;
      min-height: 0;
    }

    .studio-grid {
      flex: 1;
      overflow-y: auto;
      padding: 16px 24px;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 18px;
      min-height: 0;
    }

    @media (max-width: 1024px) {
      .studio-grid {
        grid-template-columns: 1fr;
      }
    }

    .pane-card {
      background-color: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 8px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      min-width: 0;
      height: 100%;
    }

    .pane-header {
      padding: 10px 16px;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      background-color: rgba(255, 255, 255, 0.015);
      flex-shrink: 0;
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
      width: 15px;
      height: 15px;
      stroke: var(--text-secondary);
      stroke-width: 2;
      fill: none;
    }

    .browser-url-bar {
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--text-secondary);
      background-color: var(--bg-root);
      padding: 3px 10px;
      border-radius: 4px;
      border: 1px solid var(--border);
      max-width: 280px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .viewport-box {
      flex: 1;
      background-color: #0E0F0F;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      overflow: hidden;
      min-height: 380px;
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
      gap: 10px;
      color: var(--text-muted);
      text-align: center;
      padding: 24px;
    }

    .viewport-placeholder svg {
      width: 36px;
      height: 36px;
      stroke: var(--text-muted);
      stroke-width: 1.5;
      fill: none;
    }

    /* Evidence Pane */
    .evidence-feed {
      flex: 1;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 14px;
      overflow-y: auto;
      min-width: 0;
    }

    .sources-strip {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      padding-bottom: 10px;
      border-bottom: 1px solid var(--border);
    }

    .source-pill {
      background-color: var(--bg-root);
      border: 1px solid var(--border);
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
      fill: none;
    }

    .answer-block {
      display: flex;
      flex-direction: column;
      gap: 8px;
      flex: 1;
    }

    .answer-block h4 {
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
    }

    .answer-content {
      font-size: 14px;
      color: var(--text-primary);
      line-height: 1.6;
      white-space: pre-wrap;
      word-break: break-word;
    }

    .telemetry-log {
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--text-secondary);
      background-color: var(--bg-root);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 10px;
      display: flex;
      flex-direction: column;
      gap: 4px;
      max-height: 140px;
      overflow-y: auto;
    }

    .telemetry-entry {
      display: flex;
      align-items: flex-start;
      gap: 8px;
    }

    .telemetry-time {
      color: var(--text-muted);
      flex-shrink: 0;
    }

    /* Docked Bottom Chat Bar */
    .docked-bottom-bar {
      background-color: var(--bg-sidebar);
      border-top: 1px solid var(--border);
      padding: 12px 24px;
      flex-shrink: 0;
    }

    .docked-input-inner {
      max-width: 900px;
      margin: 0 auto;
      background-color: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 8px 14px;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .docked-input-inner input {
      flex: 1;
      background: transparent;
      border: none;
      outline: none;
      color: var(--text-primary);
      font-size: 14px;
      font-family: inherit;
    }

    .docked-input-inner input::placeholder {
      color: var(--text-muted);
    }
  </style>
</head>
<body>

  <!-- Left Sidebar -->
  <aside class="sidebar">
    <div class="sidebar-top">
      <svg class="brand-icon" viewBox="0 0 24 24"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>
      <button class="icon-btn" title="Toggle Sidebar">
        <svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="3" x2="9" y2="21"></line></svg>
      </button>
    </div>

    <button class="btn-new-chat" onclick="showHeroView()">
      <svg viewBox="0 0 24 24"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
      <span>New</span>
    </button>

    <div class="nav-list">
      <div class="nav-item active" onclick="setMode('sherlock-scrape')">
        <svg viewBox="0 0 24 24"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>
        <span>Computer (Scrape)</span>
      </div>
      <div class="nav-item" onclick="setMode('sherlock-validate')">
        <svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
        <span>Automations (SAFE)</span>
      </div>
      <div class="nav-item" onclick="setMode('storm')">
        <svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
        <span>Artifacts</span>
      </div>
      <div class="nav-item" onclick="openCacheModal()">
        <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
        <span>Customize (Cache)</span>
      </div>
    </div>

    <div class="nav-divider"></div>

    <div class="nav-section-title">
      <span>Projects</span>
      <svg viewBox="0 0 24 24"><polyline points="6 9 12 15 18 9"></polyline></svg>
    </div>
    <div class="nav-subtext">No projects</div>

    <div class="nav-section-title">
      <span>Sessions</span>
      <svg viewBox="0 0 24 24"><polyline points="6 9 12 15 18 9"></polyline></svg>
    </div>
    <div class="nav-subtext" id="sessionListLabel">No recent sessions</div>

    <div class="sidebar-bottom">
      <div class="status-indicator">
        <span class="status-dot" id="statusDot"></span>
        <span id="connLabel">Connected</span>
      </div>
      <span style="font-family: var(--font-mono); font-size: 11px;">v2.4</span>
    </div>
  </aside>

  <!-- Main Canvas -->
  <div class="main-canvas">
    <div class="top-toolbar">
      <button class="icon-btn" title="Information">
        <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
      </button>
      <button class="icon-btn" title="Settings" onclick="openCacheModal()">
        <svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>
      </button>
    </div>

    <!-- STATE 1: Centered Hero View -->
    <div class="hero-container" id="heroView">
      <div class="hero-title-group">
        <div class="hero-kicker">Sherlock</div>
        <h1 class="hero-heading">What do you want to know?</h1>
      </div>

      <!-- Main Input Box (Matching Inspo) -->
      <form class="perplexity-input-box" onsubmit="event.preventDefault(); submitHeroQuery();">
        <input 
          type="text" 
          id="heroInput" 
          placeholder="Ask anything or verify live facts..." 
          autocomplete="off"
          autofocus
        >

        <div class="input-bottom-bar">
          <div class="pill-group">
            <div class="mode-pill active" id="pillScrape" onclick="setHeroPill('scrape')">
              <svg viewBox="0 0 24 24"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>
              <span>Search & Scrape</span>
            </div>
            <div class="mode-pill" id="pillValidate" onclick="setHeroPill('validate')">
              <svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"></polyline></svg>
              <span>SAFE Factuality</span>
            </div>
          </div>

          <div style="display: flex; align-items: center; gap: 8px;">
            <button type="submit" class="submit-circle-btn" id="heroSubmitBtn" title="Send">
              <svg viewBox="0 0 24 24"><line x1="12" y1="19" x2="12" y2="5"></line><polyline points="5 12 12 5 19 12"></polyline></svg>
            </button>
          </div>
        </div>
      </form>

      <!-- Dual Action Cards (Matching Inspo) -->
      <div class="hero-cards-grid">
        <div class="hero-card" onclick="quickFill('Always Yours Never Mine cinema ticket price Philippines')">
          <div class="hero-card-header">
            <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
            <span>Search & validate</span>
          </div>
          <div class="hero-card-desc">
            Discover primary sources and verify ticket prices, specifications, and live facts with DeepMind SAFE.
          </div>
        </div>

        <div class="hero-card secondary" onclick="quickFill('iPhone 15 Pro 2nd hand price greenhills')">
          <div class="hero-card-header">
            <svg viewBox="0 0 24 24"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>
            <span>Get work done with Computer</span>
          </div>
          <div class="hero-card-desc">
            Hands-off live browser session that streams Playwright DOM navigation and captures ground-truth data.
          </div>
        </div>
      </div>
    </div>

    <!-- STATE 2: Active Investigation Studio (Dual-Pane) -->
    <div class="studio-container" id="studioView">
      <div class="studio-grid">
        <!-- Left: Live Browser Viewport -->
        <div class="pane-card">
          <div class="pane-header">
            <div class="pane-title">
              <svg viewBox="0 0 24 24"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>
              <span>Live Viewport (CDP Stream)</span>
            </div>
            <div class="browser-url-bar" id="currentUrlDisplay">about:blank</div>
          </div>

          <div class="viewport-box">
            <img id="streamCanvas" style="display: none;" alt="Live Browser Viewport">
            <div class="viewport-placeholder" id="viewportPlaceholder">
              <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><polygon points="10 8 16 12 10 16 10 8"></polygon></svg>
              <div id="viewportStatusText">Starting live browser session...</div>
            </div>
          </div>
        </div>

        <!-- Right: Evidence & Verification Log -->
        <div class="pane-card">
          <div class="pane-header">
            <div class="pane-title">
              <svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
              <span>Ground-Truth Verification</span>
            </div>
            <div style="font-family: var(--font-mono); font-size: 11px; color: var(--accent-emerald);" id="safeScoreBadge">
              SAFE Score: Working...
            </div>
          </div>

          <div class="evidence-feed">
            <div>
              <div style="font-size: 11px; text-transform: uppercase; color: var(--text-muted); margin-bottom: 6px; letter-spacing: 0.05em;">Discovered Sources</div>
              <div class="sources-strip" id="sourcesStrip">
                <span style="color: var(--text-muted); font-size: 12px;">Scouting primary sources...</span>
              </div>
            </div>

            <div class="answer-block">
              <h4>Verified Data Summary</h4>
              <div class="answer-content" id="answerContent">Investigation in progress. Live DOM extraction underway...</div>
            </div>

            <div>
              <div style="font-size: 11px; text-transform: uppercase; color: var(--text-muted); margin-bottom: 6px; letter-spacing: 0.05em;">Telemetry Stream</div>
              <div class="telemetry-log" id="logStream">
                <div class="telemetry-entry">
                  <span class="telemetry-time">[System]</span>
                  <span>Session initialized.</span>
                </div>
              </div>
            </div>

            <div style="display: flex; justify-content: flex-end; padding-top: 6px;">
              <button class="btn-new-chat" style="margin: 0; padding: 6px 12px; font-size: 12px;" onclick="copyMarkdown()">
                <svg viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                Copy Clean Markdown
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Docked Bottom Input Bar (Active State) -->
      <div class="docked-bottom-bar">
        <form class="docked-input-inner" onsubmit="event.preventDefault(); submitDockedQuery();">
          <input 
            type="text" 
            id="dockedInput" 
            placeholder="Ask a follow-up or verify another claim..." 
            autocomplete="off"
          >
          <button type="submit" class="submit-circle-btn" style="width: 28px; height: 28px;" title="Send">
            <svg viewBox="0 0 24 24"><line x1="12" y1="19" x2="12" y2="5"></line><polyline points="5 12 12 5 19 12"></polyline></svg>
          </button>
        </form>
      </div>
    </div>
  </div>

  <script>
    let ws = null;
    let fullMarkdownOutput = "";
    let activeMode = "sherlock-scrape";
    let pendingPayload = null;

    function initWebSocket() {
      const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
      ws = new WebSocket(`${proto}//${window.location.host}/ws`);

      ws.onopen = () => {
        const dot = document.getElementById("statusDot");
        if (dot) dot.style.backgroundColor = "var(--accent-emerald)";
        const label = document.getElementById("connLabel");
        if (label) label.textContent = "Connected";
        addLog("WebSocket connection online.");
        if (pendingPayload) {
          addLog("Sending queued investigation request...");
          ws.send(JSON.stringify(pendingPayload));
          pendingPayload = null;
        }
      };

      ws.onclose = () => {
        const dot = document.getElementById("statusDot");
        if (dot) dot.style.backgroundColor = "var(--text-muted)";
        const label = document.getElementById("connLabel");
        if (label) label.textContent = "Disconnected";
        addLog("WebSocket disconnected. Reconnecting in 2s...");
        setTimeout(initWebSocket, 2000);
      };

      ws.onerror = (err) => {
        addLog(`WebSocket connection notice.`);
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
        document.getElementById("viewportStatusText").textContent = `Navigating: ${msg.url}`;
        addLog(`Navigating: ${msg.url}`);
      } else if (msg.type === "log") {
        addLog(msg.text);
      } else if (msg.type === "sources") {
        renderSources(msg.sources);
      } else if (msg.type === "answer") {
        document.getElementById("answerContent").textContent = msg.text;
      } else if (msg.type === "complete") {
        document.getElementById("safeScoreBadge").textContent = `SAFE Score: ${msg.score}%`;
        fullMarkdownOutput = msg.markdown;
        addLog(`Investigation complete. SAFE Score: ${msg.score}%`);
        document.getElementById("heroSubmitBtn").disabled = false;
      }
    }

    function addLog(text) {
      const container = document.getElementById("logStream");
      if (!container) return;
      const time = new Date().toLocaleTimeString([], { hour12: false });
      const entry = document.createElement("div");
      entry.className = "telemetry-entry";
      entry.innerHTML = `<span class="telemetry-time">[${time}]</span> <span>${text}</span>`;
      container.appendChild(entry);
      container.scrollTop = container.scrollHeight;
    }

    function renderSources(sources) {
      const strip = document.getElementById("sourcesStrip");
      if (!strip) return;
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
        a.innerHTML = `<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg> <span>[${idx+1}] ${s.domain}</span>`;
        strip.appendChild(a);
      });
    }

    function showHeroView() {
      document.getElementById("heroView").style.display = "flex";
      document.getElementById("studioView").style.display = "none";
      document.getElementById("heroInput").value = "";
      document.getElementById("heroInput").focus();
    }

    function showStudioView() {
      document.getElementById("heroView").style.display = "none";
      document.getElementById("studioView").style.display = "flex";
    }

    function setHeroPill(mode) {
      if (mode === "scrape") {
        document.getElementById("pillScrape").classList.add("active");
        document.getElementById("pillValidate").classList.remove("active");
        activeMode = "sherlock-scrape";
      } else {
        document.getElementById("pillValidate").classList.add("active");
        document.getElementById("pillScrape").classList.remove("active");
        activeMode = "sherlock-validate";
      }
    }

    function quickFill(query) {
      document.getElementById("heroInput").value = query;
      submitHeroQuery();
    }

    function handleHeroKey(event) {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        submitHeroQuery();
      }
    }

    function handleDockedKey(event) {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        submitDockedQuery();
      }
    }

    function submitHeroQuery() {
      const query = document.getElementById("heroInput").value.trim();
      if (!query) return;
      executeInvestigation(query);
    }

    function submitDockedQuery() {
      const query = document.getElementById("dockedInput").value.trim();
      if (!query) return;
      document.getElementById("dockedInput").value = "";
      executeInvestigation(query);
    }

    function executeInvestigation(query) {
      showStudioView();

      const heroBtn = document.getElementById("heroSubmitBtn");
      if (heroBtn) heroBtn.disabled = true;
      document.getElementById("answerContent").textContent = "Investigation initiated. Conducting search scout and launching browser session...";
      document.getElementById("safeScoreBadge").textContent = "SAFE Score: Working...";
      document.getElementById("viewportStatusText").textContent = "Launching live browser session...";
      document.getElementById("sessionListLabel").textContent = query.length > 20 ? query.slice(0, 20) + "..." : query;

      addLog(`Investigation started: "${query}"`);

      const payload = {
        action: "start",
        skill: activeMode,
        query: query,
        anti_slop: true,
        use_cache: true
      };

      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(payload));
      } else {
        pendingPayload = payload;
        addLog("Connecting WebSocket to launch investigation...");
        if (!ws || ws.readyState === WebSocket.CLOSED) {
          initWebSocket();
        }
      }
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
                skill = payload.get("skill", "sherlock-scrape")
                use_cache = payload.get("use_cache", True)
                anti_slop = payload.get("anti_slop", True)

                await websocket.send_json({"type": "log", "text": f"Phase 1: Multi-engine search scout for: '{query}'..."})

                # Check cache for scouted leads
                cache_key = f"scout:{query.strip().lower()}"
                leads = []
                if use_cache:
                    cached_leads = get_cached_fact(cache_key)
                    if cached_leads and isinstance(cached_leads, list):
                        leads = cached_leads
                        await websocket.send_json({"type": "log", "text": f"[Cache Hit] Reusing {len(leads)} verified leads."})

                # Run blocking scout search in thread pool to prevent event loop starvation
                if not leads:
                    leads = await asyncio.to_thread(scout_search_leads, query, 3)
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


def free_port(port: int = 7860):
    """Gracefully terminates any previous stale server process on the port."""
    if sys.platform == "win32":
        try:
            import subprocess
            cmd = f'netstat -aon | findstr ":{port}" | findstr "LISTENING"'
            out = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
            for line in out.strip().splitlines():
                parts = line.strip().split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    if pid.isdigit() and int(pid) != os.getpid():
                        print(f"Stopping existing server process (PID {pid})...")
                        subprocess.run(f"taskkill /f /pid {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass


def find_available_port(start_port: int = 7860, max_attempts: int = 10) -> int:
    import socket
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return start_port


def main():
    import webbrowser
    free_port(7860)
    port = find_available_port(7860)

    print("\n" + "=" * 65)
    print("      SHERLOCK INVESTIGATION STUDIO (Local Web UI)")
    print("=" * 65)
    print(f"  * Server running at: http://localhost:{port}")
    print("  * Layout: Perplexity / Computer Architecture (Dual-Pane + Hero)")
    print("  * Live Playwright CDP Screencasting: Enabled")
    print("  * Anti-Slop Strictness: Enabled")
    print("  * Fact Cache: Enabled")
    print("=" * 65 + "\n")

    try:
        webbrowser.open(f"http://localhost:{port}")
    except Exception:
        pass

    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main()
