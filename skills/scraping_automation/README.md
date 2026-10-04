# Ground-Truth Web Scraping & Browser Automation

This directory houses high-accuracy web extractors and browser automation tools tailored for LLM reasoning and real-world fact verification.

## Modules

### 1. `sherlock-scrape/` (Targeted Visual Sniper)
* **Features:**
  * **Visual Transparency:** Runs Playwright in headed mode (`--headed`) so the user can watch Chromium open, navigate, and scroll.
  * **5 Golden Rules:** Asset interception (abort images/fonts/media), context reuse, `domcontentloaded` triggers, stealth user-agents, and semaphore concurrency.
  * **Proof Links:** Automatically produces W3C Chrome text-fragment URLs (`#:~:text=start,end`) highlighting exact quotes in yellow on the target webpage.

### 2. `crawl4ai/` (High-Throughput Web Crawler)
* **Source:** [unclecode/crawl4ai](https://github.com/unclecode/crawl4ai)
* **Features:**
  * High-concurrency crawler built specifically for AI agents and RAG pipelines.
  * Native conversion of messy web pages into clean Markdown, structured JSON, and semantic chunks.
  * Handles dynamic SPAs, infinite scrolls, and proxy rotation.

## How Sherlock Orchestrates This Category
* **Single or Target Verification:** Sherlock triggers `sherlock-scrape/scripts/browser_fetch.py` when a page requires JavaScript hydration, or when the user wants visual transparency.
* **Bulk or Domain Crawling:** Uses Crawl4AI principles when crawling multi-page sites or downloading entire documentation corpuses into Markdown.
