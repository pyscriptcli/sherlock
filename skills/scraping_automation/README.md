# Ground-Truth Web Scraping & Browser Automation

This directory houses high-accuracy web extractors and browser automation tools tailored for LLM reasoning and real-world fact verification.

## Skills

### 1. [`sherlock-scrape/`](sherlock-scrape/SKILL.md) (Targeted Visual Sniper)
* **Framework:** Playwright Visual DOM Scraper
* **Features:**
  * **Visual Transparency:** Runs Playwright in headed mode (`--headed`) so the user can watch Chromium open, navigate, and scroll.
  * **5 Golden Rules:** Asset interception (abort images/fonts/media), context reuse, `domcontentloaded` triggers, stealth user-agents, and semaphore concurrency.
  * **Proof Links:** Automatically produces W3C Chrome text-fragment URLs (`#:~:text=start,end`) highlighting exact quotes in yellow on the target webpage.
  * **Script:** [`sherlock-scrape/scripts/browser_fetch.py`](sherlock-scrape/scripts/browser_fetch.py)

## How Sherlock Orchestrates This Category
Sherlock triggers `sherlock-scrape/scripts/browser_fetch.py` when a page requires JavaScript hydration, or when the user requests visual proof of real-world figures (menus, prices, directories).
