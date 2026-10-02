#!/usr/bin/env python3
"""
Sherlock Browser & Text Extraction Helper
Implements Sherlock's 3-tier retrieval strategy:
- Tier 1: Direct clean text extraction from HTML
- Tier 2: Live DOM & Accessibility tree extraction via headless browser (if Playwright is installed)
- Tier 3: Targeted element screenshot for charts/canvas
- Helper: Generates Chrome/W3C Text Fragment URLs for direct quote links
"""

import sys
import os
import re
import urllib.parse
import urllib.request
import argparse
from html.parser import HTMLParser


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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        html = response.read().decode("utf-8", errors="replace")

    parser = SimpleTextExtractor()
    parser.feed(html)
    return parser.get_text()


def fetch_with_playwright(url: str, selector: str = None, screenshot_out: str = None) -> dict:
    """
    Tier 2 & Tier 3: Uses Playwright to load dynamic pages.
    Pulls live text and optionally screenshots a specific element (like a chart).
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {
            "error": "Playwright is not installed. Run 'pip install playwright && playwright install' to enable live browser mode.",
            "text": ""
        }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=30000)

        # Pull live text from DOM
        text_content = page.evaluate("() => document.body.innerText")

        screenshot_saved = None
        if selector and screenshot_out:
            element = page.query_selector(selector)
            if element:
                element.screenshot(path=screenshot_out)
                screenshot_saved = screenshot_out

        browser.close()
        return {
            "text": text_content,
            "screenshot": screenshot_saved
        }


def main():
    parser = argparse.ArgumentParser(description="Sherlock 3-Tier Web Extraction Tool")
    parser.add_argument("url", help="Target URL to extract evidence from")
    parser.add_argument("--quote", help="Optional quote to generate text fragment link for")
    parser.add_argument("--browser", action="store_true", help="Use headless browser (Tier 2)")
    parser.add_argument("--selector", help="CSS selector of element to screenshot (Tier 3)")
    parser.add_argument("--screenshot-out", default="chart.png", help="Path to save element screenshot")

    args = parser.parse_args()

    if args.quote:
        print("Text Fragment Link:")
        print(make_text_fragment_url(args.url, args.quote))
        print("-" * 50)

    if args.browser:
        print(f"Fetching {args.url} via headless browser...")
        res = fetch_with_playwright(args.url, selector=args.selector, screenshot_out=args.screenshot_out)
        if "error" in res and res["error"]:
            print(res["error"])
        else:
            print("\n--- Live DOM Text Preview (First 500 chars) ---")
            print(res["text"][:500])
            if res.get("screenshot"):
                print(f"\nElement screenshot saved to: {res['screenshot']}")
    else:
        print(f"Fetching {args.url} via direct text reader (Tier 1)...")
        try:
            text = fetch_tier1_text(args.url)
            print("\n--- Clean Text Preview (First 500 chars) ---")
            print(text[:500])
        except Exception as e:
            print(f"Tier 1 fetch failed: {e}. Try running with --browser for dynamic pages.")


if __name__ == "__main__":
    main()
