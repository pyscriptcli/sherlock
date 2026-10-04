#!/usr/bin/env python3
"""
Sherlock Headed Browser & Web Extraction Engine (Optimized for Playwright)
Implements visual headed scraping, live on-screen search, anti-slop cleaning,
local fact caching, and reusable Playwright automation.

Golden Rules Applied:
1. Reusable browser lifecycle with isolated, lightweight contexts
2. Intercept and abort heavy non-essential assets (images, fonts, media)
3. Fast domcontentloaded navigation + targeted selector auto-waits
4. Stealth anti-bot hygiene (masks navigator.webdriver, stealth args)
5. Controlled concurrency via asyncio.Semaphore
6. Visual Transparency: Headed browser opens visible window on screen for live visual search and inspection
7. Anti-Slop: Purges AI fluff and throat-clearing preambles from extracted text
8. Fact Cache: Automatically caches extracted facts and queries with configurable TTL
"""

import sys
import os
import re
import json
import base64
import asyncio
import urllib.parse
import urllib.request
import argparse
from html.parser import HTMLParser
from typing import List, Dict, Optional, Tuple, Any

# Ensure clean UTF-8 printing on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add scripts directory to sys.path for local module resolution
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# ----------------------------------------------------------------------
# Anti-Slop & Fact-Cache Integrations (with resilient fallbacks)
# ----------------------------------------------------------------------
try:
    from fact_cache import get_cached_fact, set_cached_fact
except Exception:
    def get_cached_fact(key: str) -> Optional[Any]:
        return None
    def set_cached_fact(key: str, data: Any, ttl_hours: float = 24.0) -> None:
        pass

try:
    from deslop_filter import deslop_text
except Exception:
    def deslop_text(text: str) -> Tuple[str, List[Dict[str, str]]]:
        return text, []


# ----------------------------------------------------------------------
# Tier 1 Clean Text Extractor (Zero-browser overhead)
# ----------------------------------------------------------------------
class SimpleTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.ignore_tags = {"script", "style", "noscript", "svg", "head", "meta"}
        self.current_tag_stack = []

    def handle_starttag(self, tag, attrs):
        self.current_tag_stack.append(tag.lower())

    def handle_endtag(self, tag):
        if self.current_tag_stack and self.current_tag_stack[-1] == tag.lower():
            self.current_tag_stack.pop()

    def handle_data(self, data):
        if any(tag in self.ignore_tags for tag in self.current_tag_stack):
            return
        cleaned = data.strip()
        if cleaned:
            self.text_parts.append(cleaned)

    def get_text(self) -> str:
        return "\n".join(self.text_parts)


def make_text_fragment_url(base_url: str, quote: str) -> str:
    """Builds a W3C Text Fragment URL for one-click browser highlighting."""
    words = quote.strip().split()
    if not words:
        return base_url

    clean_base = base_url.split("#:~:text=")[0].rstrip("#")
    if len(words) <= 6:
        encoded_text = urllib.parse.quote(" ".join(words))
        return f"{clean_base}#:~:text={encoded_text}"
    else:
        start = urllib.parse.quote(" ".join(words[:4]))
        end = urllib.parse.quote(" ".join(words[-4:]))
        return f"{clean_base}#:~:text={start},{end}"


def fetch_tier1_text(url: str, timeout: int = 10) -> str:
    """Tier 1: Pulls raw HTML and extracts clean text without browser overhead."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        html = response.read().decode("utf-8", errors="replace")

    parser = SimpleTextExtractor()
    parser.feed(html)
    return parser.get_text()


def _decode_bing_redirect(href: str) -> str:
    """Decodes Bing's redirect URL to retrieve the direct destination URL."""
    if "u=a1" in href:
        try:
            raw = href.split("u=a1")[1].split("&")[0]
            raw += "=" * (-len(raw) % 4)
            decoded = base64.b64decode(raw).decode("utf-8", errors="ignore")
            if decoded.startswith("http"):
                return decoded
        except Exception:
            pass
    return href


# ----------------------------------------------------------------------
# Reusable Playwright Engine (SherlockBrowser)
# ----------------------------------------------------------------------
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

STEALTH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-infobars",
    "--window-position=50,50",
    "--window-size=1280,850",
    "--ignore-certificate-errors",
    "--ignore-certificate-errors-spki-list",
]


async def block_non_essential_assets(route):
    """Golden Rule 2: Intercept & abort heavy resources to cut load time by 50-70%."""
    if route.request.resource_type in ["image", "media", "font"]:
        await route.abort()
    else:
        await route.continue_()


class SherlockBrowser:
    """
    Reusable, modular Playwright automation engine for Sherlock and agent workflows.
    Supports:
    - Headed execution with live on-screen visual navigation & smooth scrolling
    - Visual search scout (user watches the search query and results on screen)
    - Reusable browser instance with isolated contexts (Golden Rule 1)
    - Concurrency capping via asyncio.Semaphore (Golden Rule 5)
    - Anti-bot stealth hygiene (Golden Rule 4)
    - Integrated fact caching and anti-slop cleaning
    """

    def __init__(
        self,
        headed: bool = True,
        concurrency: int = 1,
        timeout_ms: int = 25000,
        block_assets: bool = True,
        cache_enabled: bool = True,
        ttl_hours: float = 24.0,
        apply_deslop: bool = True,
    ):
        self.headed = headed
        self.concurrency = 1 if headed else concurrency
        self.timeout_ms = timeout_ms
        self.block_assets = block_assets
        self.cache_enabled = cache_enabled
        self.ttl_hours = ttl_hours
        self.apply_deslop = apply_deslop
        self.playwright = None
        self.browser = None
        self.semaphore = asyncio.Semaphore(self.concurrency)

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def start(self):
        """Launches the underlying Playwright Chromium instance."""
        try:
            from playwright.async_api import async_playwright
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=not self.headed,
                args=STEALTH_ARGS,
            )
        except ImportError:
            raise RuntimeError(
                "Playwright is not installed. Run 'pip install playwright && playwright install' to enable live browser mode."
            )

    async def close(self):
        """Cleanly terminates the browser instance and Playwright runtime."""
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

    async def visual_search(self, query: str, max_results: int = 4) -> List[str]:
        """
        Executes an on-screen visual search.
        In headed mode, the browser opens on screen, loads the search engine,
        smooth-scrolls so the user visually watches the search, and extracts the top URLs.
        """
        cache_key = f"scout:{query.strip().lower()}"
        if self.cache_enabled and not self.headed:
            cached_urls = get_cached_fact(cache_key)
            if cached_urls:
                print(f"[✓] [Cache Hit] Retrieved {len(cached_urls)} scouted URL(s) for: '{query}'")
                return cached_urls

        if not self.browser:
            await self.start()

        results = []
        mode_label = "[Headed Window]" if self.headed else "[Headless]"
        print(f"[*] {mode_label} Opening live visual search for: '{query}'...")

        context = await self.browser.new_context(
            user_agent=DEFAULT_USER_AGENT,
            viewport={"width": 1280, "height": 850},
        )
        page = await context.new_page()

        try:
            if self.block_assets:
                await page.route("**/*", block_non_essential_assets)

            await page.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            # Navigate to Bing search
            search_url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
            print(f"    -> Loading live search engine: {search_url}")
            await page.goto(search_url, wait_until="domcontentloaded", timeout=self.timeout_ms)

            # Visually scroll the search results so user sees them on screen
            if self.headed:
                print("    -> [Headed Mode] Visual inspection: scrolling search results...")
                await page.evaluate("window.scrollBy({top: 600, behavior: 'smooth'})")
                await asyncio.sleep(1.5)

            # Extract result links from DOM
            hrefs = await page.evaluate("""() => {
                const anchors = Array.from(document.querySelectorAll('li.b_algo h2 a, a.b_algo_title'));
                return anchors.map(a => a.href);
            }""")

            for h in hrefs:
                direct_url = _decode_bing_redirect(h)
                if direct_url.startswith("http") and "bing.com" not in direct_url and direct_url not in results:
                    results.append(direct_url)
                if len(results) >= max_results:
                    break

            # Fallback to DuckDuckGo HTML if Bing returned no direct links
            if not results:
                print("    -> Fallback: scouting DuckDuckGo leads...")
                ddg_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
                await page.goto(ddg_url, wait_until="domcontentloaded", timeout=15000)
                if self.headed:
                    await asyncio.sleep(1.0)
                ddg_hrefs = await page.evaluate("""() => {
                    const anchors = Array.from(document.querySelectorAll('a.result__url, a.result__snippet'));
                    return anchors.map(a => a.href);
                }""")
                for dh in ddg_hrefs:
                    if "uddg=" in dh:
                        actual = urllib.parse.unquote(dh.split("uddg=")[1].split("&")[0])
                        if actual.startswith("http") and actual not in results:
                            results.append(actual)
                    elif dh.startswith("http") and "duckduckgo" not in dh and dh not in results:
                        results.append(dh)
                    if len(results) >= max_results:
                        break

            if results and self.cache_enabled:
                set_cached_fact(cache_key, results, ttl_hours=self.ttl_hours)

            return results
        finally:
            await context.close()

    async def scrape_single_url(
        self,
        url: str,
        index: int = 1,
        total: int = 1,
        wait_selector: Optional[str] = None,
        selector: Optional[str] = None,
        screenshot_out: Optional[str] = None,
        scroll: bool = True,
        force: bool = False,
    ) -> Dict[str, Any]:
        """Scrapes a single URL within an isolated, lightweight context."""
        cache_key = f"dom:{url.strip().lower()}"
        if self.cache_enabled and not force and not self.headed:
            cached_text = get_cached_fact(cache_key)
            if cached_text:
                print(f"[✓] [Cache Hit] [{index}/{total}] Reusing cached DOM for: {url}")
                return {
                    "url": url,
                    "success": True,
                    "text": cached_text,
                    "screenshot": None,
                    "error": None,
                    "from_cache": True,
                }

        async with self.semaphore:
            mode_label = "[Headed Window]" if self.headed else "[Headless]"
            print(f"[*] {mode_label} [{index}/{total}] Navigating: {url}")

            context = await self.browser.new_context(
                user_agent=DEFAULT_USER_AGENT,
                viewport={"width": 1280, "height": 850},
                java_script_enabled=True,
            )
            page = await context.new_page()

            try:
                if self.block_assets and not screenshot_out:
                    await page.route("**/*", block_non_essential_assets)

                await page.add_init_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                )

                print(f"    -> Loading DOM: {url}")
                await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)

                if wait_selector:
                    print(f"    -> Auto-waiting for selector: '{wait_selector}'")
                    try:
                        await page.wait_for_selector(wait_selector, timeout=8000)
                    except Exception:
                        print(f"    [!] Timeout waiting for '{wait_selector}', proceeding...")

                if scroll:
                    print("    -> Smooth scrolling to trigger lazy content & dynamic DOM...")
                    await page.evaluate("window.scrollBy({top: 800, behavior: 'smooth'})")
                    await asyncio.sleep(1.0 if self.headed else 0.3)
                    await page.evaluate("window.scrollBy({top: -300, behavior: 'smooth'})")
                    await asyncio.sleep(0.5 if self.headed else 0.2)

                if self.headed:
                    print("    -> [Headed Mode] Visual inspection pause (1.5s)...")
                    await asyncio.sleep(1.5)

                text_content = await page.evaluate("() => document.body.innerText")

                # Apply anti-slop cleaning if enabled
                if self.apply_deslop and text_content:
                    text_content, _ = deslop_text(text_content)

                screenshot_saved = None
                if selector and screenshot_out:
                    print(f"    -> Capturing element proof screenshot: {selector}")
                    elem = await page.query_selector(selector)
                    if elem:
                        await elem.screenshot(path=screenshot_out)
                        screenshot_saved = screenshot_out
                        print(f"    [+] Saved screenshot to: {screenshot_out}")

                if self.cache_enabled and text_content:
                    set_cached_fact(cache_key, text_content, ttl_hours=self.ttl_hours)

                print(f"[✓] [{index}/{total}] Successfully captured: {len(text_content)} characters")

                return {
                    "url": url,
                    "success": True,
                    "text": text_content,
                    "screenshot": screenshot_saved,
                    "error": None,
                    "from_cache": False,
                }

            except Exception as e:
                print(f"[✗] [{index}/{total}] Failed: {url} -> {e}")
                return {
                    "url": url,
                    "success": False,
                    "text": "",
                    "screenshot": None,
                    "error": str(e),
                    "from_cache": False,
                }
            finally:
                await context.close()

    async def scrape_batch(
        self,
        urls: List[str],
        wait_selector: Optional[str] = None,
        selector: Optional[str] = None,
        screenshot_out: Optional[str] = None,
        scroll: bool = True,
        force: bool = False,
    ) -> List[Dict[str, Any]]:
        """Scrapes multiple URLs concurrently using worker pool."""
        if not self.browser:
            await self.start()

        total = len(urls)
        tasks = [
            self.scrape_single_url(
                url=url,
                index=i + 1,
                total=total,
                wait_selector=wait_selector,
                selector=selector,
                screenshot_out=screenshot_out if total == 1 else None,
                scroll=scroll,
                force=force,
            )
            for i, url in enumerate(urls)
        ]
        return await asyncio.gather(*tasks)


# ----------------------------------------------------------------------
# CLI Output Presentation
# ----------------------------------------------------------------------
def print_summary_table(results: List[Dict[str, Any]]):
    """Prints a clean, anti-slop CLI summary report table."""
    print("\n" + "=" * 80)
    print("                      SHERLOCK SCRAPE SUMMARY REPORT")
    print("=" * 80)
    print(f"{'Target URL':<46} | {'Status':<9} | {'Chars':<7} | {'Cache':<6}")
    print("-" * 80)
    for res in results:
        url_display = res['url'] if len(res['url']) <= 46 else res['url'][:43] + "..."
        status_display = "SUCCESS" if res["success"] else "FAILED"
        chars_display = str(len(res["text"])) if res["success"] else "0"
        cache_display = "HIT" if res.get("from_cache") else "LIVE"
        print(f"{url_display:<46} | {status_display:<9} | {chars_display:<7} | {cache_display:<6}")
    print("=" * 80 + "\n")


# ----------------------------------------------------------------------
# Main Execution Pipeline
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Sherlock Headed Browser & Web Extraction Engine (Playwright Reusable Architecture)"
    )
    parser.add_argument("urls", nargs="*", help="Target URL(s) to inspect and extract")
    parser.add_argument("--urls-file", help="File containing list of URLs to scrape")
    parser.add_argument("--scout", help="Search query to automatically scout leads and extract (opens browser to search!)")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless background mode (default: False / Headed)")
    parser.add_argument("--headed", action="store_true", default=True, help="Run browser in visible headed mode (default: True)")
    parser.add_argument("--concurrency", type=int, default=2, help="Max concurrent browser contexts")
    parser.add_argument("--quote", help="Optional quote to generate W3C text fragment link for")
    parser.add_argument("--wait-selector", help="CSS selector to auto-wait for before capturing DOM")
    parser.add_argument("--selector", help="CSS selector of element to screenshot (charts/canvas)")
    parser.add_argument("--screenshot-out", default="screenshot.png", help="Path to save element screenshot")
    parser.add_argument("--allow-images", action="store_true", help="Do not block images/fonts during fetch")
    parser.add_argument("--no-scroll", action="store_true", help="Disable smooth scrolling")
    parser.add_argument("--no-cache", action="store_true", help="Bypass local verified fact cache")
    parser.add_argument("--ttl", type=float, default=24.0, help="Cache TTL in hours (default: 24h)")
    parser.add_argument("--no-deslop", action="store_true", help="Disable anti-slop cleaning on extracted text")
    parser.add_argument("--json-out", help="Save extracted results to JSON file")

    args = parser.parse_args()

    # Headed determination: Default is True (user explicitly sees the browser on screen)
    # unless --headless is explicitly specified.
    is_headed = not args.headless

    async def run_pipeline():
        engine = SherlockBrowser(
            headed=is_headed,
            concurrency=args.concurrency,
            block_assets=not args.allow_images,
            cache_enabled=not args.no_cache,
            ttl_hours=args.ttl,
            apply_deslop=not args.no_deslop,
        )

        async with engine:
            urls = []
            if args.urls_file and os.path.exists(args.urls_file):
                with open(args.urls_file, "r", encoding="utf-8") as f:
                    urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            elif args.urls:
                urls = list(args.urls)

            # If scout query is provided, perform live search (headed by default!)
            if args.scout:
                print(f"[*] Visual Lead Scout initiated for: '{args.scout}'")
                scouted = await engine.visual_search(args.scout, max_results=args.concurrency or 3)
                if scouted:
                    print(f"[✓] Discovered {len(scouted)} target lead(s):")
                    for u in scouted:
                        print(f"  • {u}")
                        if u not in urls:
                            urls.append(u)
                else:
                    print("[-] No search results returned from scout.")

            if not urls:
                print("[!] No target URLs provided or discovered. Please provide URLs or a --scout query.")
                return

            if args.quote and len(urls) == 1:
                print("\nW3C Chrome Text Fragment Link:")
                print(make_text_fragment_url(urls[0], args.quote))
                print("-" * 50)

            mode_label = "VISUAL HEADED BROWSER (Watching Live on Screen)" if is_headed else "HEADLESS BACKGROUND ENGINE"
            print(f"\n[*] Executing Sherlock Scrape [{mode_label}] across {len(urls)} target(s)...")

            results = await engine.scrape_batch(
                urls=urls,
                wait_selector=args.wait_selector,
                selector=args.selector,
                screenshot_out=args.screenshot_out,
                scroll=not args.no_scroll,
                force=args.no_cache,
            )

            print_summary_table(results)

            if len(results) == 1 and results[0]["success"]:
                print("--- Extracted Clean DOM Preview (First 500 chars) ---")
                print(results[0]["text"][:500].strip())
                if results[0].get("screenshot"):
                    print(f"\n[+] Saved proof screenshot: {results[0]['screenshot']}")

            if args.json_out:
                with open(args.json_out, "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                print(f"[+] Saved structured output to: {args.json_out}")

    asyncio.run(run_pipeline())


if __name__ == "__main__":
    main()
