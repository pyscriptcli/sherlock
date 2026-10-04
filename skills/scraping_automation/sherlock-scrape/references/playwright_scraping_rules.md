# Playwright Scraping Rules & Architecture Guide

This document outlines the 5 Golden Rules and benchmarks powering the `sherlock-scrape` skill.

---

## The 5 Golden Rules of Scalable Web Scraping

### Rule 1: Single Browser Process, Context per Session
- Launch a single Chromium browser instance at the process level.
- Spawn lightweight isolated sessions using `browser.new_context()`.
- Disposing contexts immediately after scraping reclaims ~150MB RAM per session without restarting the browser.

### Rule 2: Asset Interception & Aborting
- Intercept network traffic using `page.route("**/*", handler)`.
- Abort heavy non-essential assets (`image`, `media`, `font`).
- Reduces network transfer by 70%+ and speeds up page load times by 2x–3x.

### Rule 3: Fast Navigation with `domcontentloaded`
- Navigate using `wait_until="domcontentloaded"` rather than `networkidle` to avoid hanging on third-party telemetry, ads, or web sockets.
- Use explicit element waits (`page.wait_for_selector(target)`) only for key containers (e.g., menu lists, price tables).

### Rule 4: Anti-Bot & Stealth Hygiene
- Pass stealth launch arguments:
  - `--disable-blink-features=AutomationControlled`
  - `--no-sandbox`
  - Realistic User-Agent header
- Inject initialization scripts to mask `navigator.webdriver = true`.

### Rule 5: Concurrency Capping with `asyncio.Semaphore`
- CPU saturation is the primary bottleneck on consumer machines.
- Cap concurrent contexts to 4–6 in headless mode, and 1 in headed mode (so the user can clearly watch each page).
