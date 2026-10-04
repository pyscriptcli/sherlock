#!/usr/bin/env python3
"""
Sherlock Browser & Text Extraction Helper (Optimized with 5 Golden Rules)
Implements Sherlock's 3-tier retrieval strategy:
- Tier 1: Direct clean text extraction from HTML (pure Python, zero browser overhead)
- Tier 2: Live DOM & Accessibility tree extraction via Playwright
  * Rule 1: Browser reuse with isolated, lightweight contexts
  * Rule 2: Intercept & abort non-essential assets (images, fonts, media)
  * Rule 3: Fast domcontentloaded navigation + targeted selector auto-waits
  * Rule 4: Stealth & anti-bot hygiene (flags + realistic headers)
  * Rule 5: Concurrency capped via asyncio.Semaphore for batch scraping
- Mode: /sherlock-scrape -> automatically opens a headed browser window so you can watch live!
- Tier 3: Targeted element screenshot for charts/canvas
- Helper: Generates Chrome/W3C Text Fragment URLs for direct quote links
"""

import sys
import os
import re
import json
import asyncio
import urllib.parse
import urllib.request
import argparse
from html.parser import HTMLParser
from typing import List, Dict, Optional

# Ensure clean UTF-8 printing on Windows console (e.g. for Philippine Peso symbol ₱ and unicode)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


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

    def get_text(self):
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


def scout_search(query: str, max_results: int = 4) -> List[str]:
    """Scouts primary search leads using resilient multi-engine fallbacks (DuckDuckGo + Bing)."""
    results = []
    # 1. DuckDuckGo HTML
    try:
        post_data = urllib.parse.urlencode({"q": query}).encode("utf-8")
        req = urllib.request.Request(
            "https://html.duckduckgo.com/html/",
            data=post_data,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        with urllib.request.urlopen(req, timeout=8) as response:
            html = response.read().decode("utf-8", errors="replace")
        matches = re.findall(r'<a[^>]+class=[\'"][^\'"]*result__url[^\'"]*[\'"][^>]+href=[\'"]([^\'"]+)[\'"]', html)
        for m in matches:
            actual = urllib.parse.unquote(m.split("uddg=")[1].split("&")[0]) if "uddg=" in m else m.strip()
            if actual.startswith("http") and "duckduckgo" not in actual and actual not in results:
                results.append(actual)
            if len(results) >= max_results:
                break
    except Exception:
        pass

    # 2. Bing Search Fallback
    if not results:
        try:
            b_url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
            req = urllib.request.Request(
                b_url, 
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}
            )
            with urllib.request.urlopen(req, timeout=8) as response:
                html = response.read().decode("utf-8", errors="replace")
            matches = re.findall(r'<li class=[\'"]b_algo[\'"].*?<h2><a href=[\'"](https?://[^\'"]+)[\'"]', html)
            for m in matches:
                if "bing.com" not in m and m not in results:
                    results.append(m)
                if len(results) >= max_results:
                    break
        except Exception:
            pass

    return results


# ----------------------------------------------------------------------
# Optimized Playwright Engine (Applying the 5 Golden Rules)
# ----------------------------------------------------------------------

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# Golden Rule 4: Stealth Launch Arguments
STEALTH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-infobars",
    "--window-position=0,0",
    "--ignore-certificate-errors",
    "--ignore-certificate-errors-spki-list",
]


async def block_non_essential_assets(route):
    """Golden Rule 2: Abort heavy assets (images, fonts, media) to cut load time by 50-70%."""
    if route.request.resource_type in ["image", "media", "font"]:
        await route.abort()
    else:
        await route.continue_()


async def scrape_single_url(
    browser,
    semaphore: asyncio.Semaphore,
    url: str,
    index: int = 1,
    total: int = 1,
    wait_selector: Optional[str] = None,
    selector: Optional[str] = None,
    screenshot_out: Optional[str] = None,
    block_assets: bool = True,
    headed: bool = False,
    scroll: bool = True,
    timeout_ms: int = 25000,
) -> Dict:
    """Scrapes a single URL within an isolated, lightweight context."""
    # Golden Rule 5: Concurrency Capping
    async with semaphore:
        mode_label = "[Headed Window]" if headed else "[Headless]"
        print(f"[*] {mode_label} [{index}/{total}] Opening session: {url}")

        # Golden Rule 1: Lightweight Context per session
        context = await browser.new_context(
            user_agent=DEFAULT_USER_AGENT,
            viewport={"width": 1280, "height": 850},
            java_script_enabled=True,
        )
        page = await context.new_page()

        try:
            # Golden Rule 2: Intercept & block heavy resources
            if block_assets and not screenshot_out:
                await page.route("**/*", block_non_essential_assets)

            # Golden Rule 4: Mask navigator.webdriver
            await page.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            # Golden Rule 3: Fast domcontentloaded navigation
            print(f"    -> Loading DOM: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)

            # Targeted wait if specific selector requested
            if wait_selector:
                print(f"    -> Auto-waiting for target element: '{wait_selector}'")
                try:
                    await page.wait_for_selector(wait_selector, timeout=8000)
                except Exception:
                    print(f"    [!] Timeout waiting for '{wait_selector}', proceeding with available DOM...")

            # Natural scrolling in headed mode to trigger lazy-loaded dynamic content
            if scroll:
                print("    -> Scrolling page to trigger dynamic/lazy content...")
                await page.evaluate("window.scrollBy({top: 800, behavior: 'smooth'})")
                await asyncio.sleep(1.0 if headed else 0.4)
                await page.evaluate("window.scrollBy({top: -300, behavior: 'smooth'})")
                await asyncio.sleep(0.5 if headed else 0.2)

            # Extra visual breather if user is watching in headed mode
            if headed:
                print("    -> [Headed Mode] Visual inspection pause (1.5s)...")
                await asyncio.sleep(1.5)

            # Extract live rendered text from DOM
            text_content = await page.evaluate("() => document.body.innerText")

            screenshot_saved = None
            if selector and screenshot_out:
                print(f"    -> Capturing visual proof of selector: {selector}")
                elem = await page.query_selector(selector)
                if elem:
                    await elem.screenshot(path=screenshot_out)
                    screenshot_saved = screenshot_out
                    print(f"    [+] Saved proof screenshot to {screenshot_out}")

            print(f"[✓] [{index}/{total}] Successfully captured: {len(text_content)} characters")

            return {
                "url": url,
                "success": True,
                "text": text_content,
                "screenshot": screenshot_saved,
                "error": None,
            }
        except Exception as e:
            print(f"[✗] [{index}/{total}] Failed: {url} -> {e}")
            return {
                "url": url,
                "success": False,
                "text": "",
                "screenshot": None,
                "error": str(e),
            }
        finally:
            # Golden Rule 1: Immediately dispose context to reclaim memory
            await context.close()


async def run_playwright_pipeline(
    urls: List[str],
    concurrency: int = 4,
    wait_selector: Optional[str] = None,
    selector: Optional[str] = None,
    screenshot_out: Optional[str] = None,
    block_assets: bool = True,
    headed: bool = False,
    scroll: bool = True,
) -> List[Dict]:
    """Runs the batch Playwright scraping pipeline using a shared browser and worker pool."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return [{
            "url": url,
            "success": False,
            "text": "",
            "screenshot": None,
            "error": "Playwright is not installed. Run 'pip install playwright && playwright install' to enable live browser mode.",
        } for url in urls]

    results = []
    # Golden Rule 1: Launch single browser instance
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=not headed,
            args=STEALTH_ARGS,
        )
        # Cap concurrency to 1 if headed so user can clearly watch each tab
        effective_concurrency = 1 if headed else concurrency
        semaphore = asyncio.Semaphore(effective_concurrency)

        total_urls = len(urls)
        tasks = [
            scrape_single_url(
                browser=browser,
                semaphore=semaphore,
                url=url,
                index=i + 1,
                total=total_urls,
                wait_selector=wait_selector,
                selector=selector,
                screenshot_out=screenshot_out if total_urls == 1 else None,
                block_assets=block_assets,
                headed=headed,
                scroll=scroll,
            )
            for i, url in enumerate(urls)
        ]

        results = await asyncio.gather(*tasks)
        await browser.close()

    return results


def print_summary_table(results: List[Dict]):
    """Prints a clean CLI summary table of all scraping results."""
    print("\n" + "=" * 80)
    print("                      SHERLOCK SCRAPE SUMMARY REPORT")
    print("=" * 80)
    print(f"{'Target URL':<48} | {'Status':<10} | {'Chars Extracted':<15}")
    print("-" * 80)
    for res in results:
        url_display = res['url'] if len(res['url']) <= 48 else res['url'][:45] + "..."
        status_display = "SUCCESS" if res["success"] else "FAILED"
        chars_display = str(len(res["text"])) if res["success"] else "0"
        print(f"{url_display:<48} | {status_display:<10} | {chars_display:<15}")
    print("=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Sherlock 3-Tier Web Extraction Tool (Optimized)")
    parser.add_argument("urls", nargs="*", help="One or more target URLs to extract evidence from")
    parser.add_argument("--urls-file", help="File containing a list of URLs to scrape in parallel")
    parser.add_argument("--concurrency", type=int, default=4, help="Max concurrent browser contexts (Golden Rule 5)")
    parser.add_argument("--quote", help="Optional quote to generate text fragment link for")
    parser.add_argument("--browser", action="store_true", help="Use optimized Playwright browser (Tier 2)")
    parser.add_argument("--headed", action="store_true", help="Open a visible browser window so you can watch live (/sherlock-scrape)")
    parser.add_argument("--no-scroll", action="store_true", help="Disable natural scrolling behavior")
    parser.add_argument("--wait-selector", help="Specific CSS selector to wait for before extracting text")
    parser.add_argument("--selector", help="CSS selector of element to screenshot (Tier 3)")
    parser.add_argument("--screenshot-out", default="chart.png", help="Path to save element screenshot")
    parser.add_argument("--allow-images", action="store_true", help="Do not block images/fonts during fetch")
    parser.add_argument("--json-out", help="Save extracted results to a structured JSON file")
    parser.add_argument("--scout", help="Search query to automatically scout leads and extract (Multi-engine)")

    args = parser.parse_args()

    # Automatic lead scouting if --scout is provided
    scouted_urls = []
    if args.scout:
        print(f"[*] Scouting search leads for: '{args.scout}'...")
        scouted_urls = scout_search(args.scout, max_results=args.concurrency)
        if scouted_urls:
            print(f"[✓] Discovered {len(scouted_urls)} lead(s):")
            for u in scouted_urls:
                print(f"  • {u}")
        else:
            print("[-] No direct search hits discovered.")

    # Collect target URLs
    urls = []
    if args.urls_file and os.path.exists(args.urls_file):
        with open(args.urls_file, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    elif args.urls:
        urls = list(args.urls)

    if scouted_urls:
        for u in scouted_urls:
            if u not in urls:
                urls.append(u)

    if not urls:
        print("[!] No target URLs provided or found via search scout.")
        return

    # Quote link generation
    if args.quote and len(urls) == 1:
        print("Text Fragment Link:")
        print(make_text_fragment_url(urls[0], args.quote))
        print("-" * 50)

    # If --headed is specified, automatically enable browser mode
    use_browser = args.browser or args.headed or len(urls) > 1

    if use_browser:
        mode_str = "VISUAL HEADED BROWSER (/sherlock-scrape)" if args.headed else "FAST HEADLESS ENGINE"
        print(f"[*] Launching Sherlock Engine [{mode_str}] on {len(urls)} target(s)...")
        print(f"[*] Concurrency limit: {1 if args.headed else args.concurrency} | Assets blocked: {'NO' if args.allow_images else 'YES'}")
        
        results = asyncio.run(
            run_playwright_pipeline(
                urls=urls,
                concurrency=args.concurrency,
                wait_selector=args.wait_selector,
                selector=args.selector,
                screenshot_out=args.screenshot_out,
                block_assets=not args.allow_images,
                headed=args.headed,
                scroll=not args.no_scroll,
            )
        )

        # Print summary report table
        print_summary_table(results)

        # Output detailed text preview for single URL runs
        if len(results) == 1:
            res = results[0]
            if res["success"]:
                print("--- Live DOM Text Preview (First 500 chars) ---")
                print(res["text"][:500].strip())
                if res.get("screenshot"):
                    print(f"\n[+] Element screenshot saved: {res['screenshot']}")

        # Save to JSON if requested
        if args.json_out:
            with open(args.json_out, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"[+] Saved structured results to: {args.json_out}")

    else:
        # Single URL fast path (Tier 1)
        target_url = urls[0]
        print(f"[*] Fetching {target_url} via direct text reader (Tier 1)...")
        try:
            text = fetch_tier1_text(target_url)
            print(f"[✓] Status: Success ({len(text)} chars extracted)")
            print("\n--- Clean Text Preview (First 500 chars) ---")
            print(text[:500].strip())
        except Exception as e:
            print(f"[✗] Tier 1 fetch failed: {e}. Try running with --browser or --headed for dynamic pages.")


if __name__ == "__main__":
    main()
