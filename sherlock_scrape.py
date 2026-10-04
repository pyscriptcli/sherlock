#!/usr/bin/env python3
"""
Sherlock Scrape: Autonomous 2-Phase Scout & Visual Validator
Logic:
1. Phase 1: Sherlock Search (The Scout) -> Multi-engine reconnaissance, finds authoritative primary leads.
2. Phase 2: Sherlock Scrape (The Validator) -> Pops open headed Chromium browser on screen,
   smooth-scrolls through each site, extracts live DOM text, applies anti-slop, and caches results.
"""

import sys
import os
import re
import json
import asyncio
import urllib.parse
import urllib.request
import argparse
from typing import List, Dict, Optional, Any

# Ensure UTF-8 printing on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

try:
    from browser_fetch import SherlockBrowser, make_text_fragment_url, print_summary_table
    from fact_cache import get_cached_fact, set_cached_fact
    from deslop_filter import deslop_text
except ImportError:
    # Relative fallback if executed inside scripts/
    from scripts.browser_fetch import SherlockBrowser, make_text_fragment_url, print_summary_table
    from scripts.fact_cache import get_cached_fact, set_cached_fact
    from scripts.deslop_filter import deslop_text


def scout_search_leads(query: str, max_leads: int = 3) -> List[str]:
    """
    Phase 1: Multi-Engine Search Scout.
    Discovers primary leads using DuckDuckGo HTML (POST) + Bing search.
    Upgrades generic queries (e.g. cinema/movie pricing) to primary portals.
    """
    leads = []
    clean_query = query.strip()

    # Typo correction & intent upgrade for cinema / ticket searches
    cinema_keywords = ["ticket", "cinema", "cinemas", "movie", "showing", "screening"]
    if any(k in clean_query.lower() for k in cinema_keywords):
        if "philippines" not in clean_query.lower() and "sm" not in clean_query.lower():
            clean_query += " Philippines SM Cinema"

    print(f"\n[*] [Phase 1: Sherlock Search] Scouting verified leads for: '{clean_query}'...")

    # 1. DuckDuckGo HTML POST Search
    try:
        post_data = urllib.parse.urlencode({"q": clean_query}).encode("utf-8")
        req = urllib.request.Request(
            "https://html.duckduckgo.com/html/",
            data=post_data,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        with urllib.request.urlopen(req, timeout=9) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        
        matches = re.findall(r'<a[^>]+class=[\'"][^\'"]*result__url[^\'"]*[\'"][^>]+href=[\'"]([^\'"]+)[\'"]', html)
        for m in matches:
            actual = urllib.parse.unquote(m.split("uddg=")[1].split("&")[0]) if "uddg=" in m else m.strip()
            # Filter non-relevant domains
            if actual.startswith("http") and not any(bad in actual for bad in ["duckduckgo", "azlyrics", "facebook.com/login", "twitter.com/login"]):
                if actual not in leads:
                    leads.append(actual)
            if len(leads) >= max_leads:
                break
    except Exception as e:
        print(f"    [!] DuckDuckGo scout notice: {e}")

    # 2. Bing Fallback if insufficient leads
    if len(leads) < max_leads:
        try:
            b_url = f"https://www.bing.com/search?q={urllib.parse.quote(clean_query)}"
            req = urllib.request.Request(
                b_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                b_html = resp.read().decode("utf-8", errors="replace")
            b_matches = re.findall(r'<li class=[\'"]b_algo[\'"].*?<h2><a href=[\'"](https?://[^\'"]+)[\'"]', b_html)
            for bm in b_matches:
                if "bing.com" not in bm and bm not in leads:
                    leads.append(bm)
                if len(leads) >= max_leads:
                    break
        except Exception:
            pass

    return leads


async def run_pipeline(query_or_urls: List[str], headed: bool = True, concurrency: int = 1, ttl: float = 24.0, no_cache: bool = False, json_out: Optional[str] = None):
    # Determine if input is a search query or a direct list of URLs
    is_direct_urls = all(item.startswith("http://") or item.startswith("https://") for item in query_or_urls)
    
    target_urls = []
    if is_direct_urls:
        target_urls = query_or_urls
        print(f"\n[*] Direct targets provided: {len(target_urls)} URL(s)")
    else:
        search_query = " ".join(query_or_urls)
        # Check cache for recent scout
        cache_key = f"scout:{search_query.strip().lower()}"
        if not no_cache:
            cached = get_cached_fact(cache_key)
            if cached and isinstance(cached, list):
                print(f"[✓] [Cache Hit] Reusing {len(cached)} verified leads for: '{search_query}'")
                target_urls = cached

        if not target_urls:
            target_urls = scout_search_leads(search_query, max_leads=3)
            if target_urls:
                set_cached_fact(cache_key, target_urls, ttl_hours=ttl)

    if not target_urls:
        print("[!] No target URLs found or provided to scrape.")
        return

    print(f"\n[✓] Discovered {len(target_urls)} verified target lead(s):")
    for i, u in enumerate(target_urls, 1):
        print(f"  {i}. {u}")

    print("\n" + "=" * 80)
    print(f"[*] [Phase 2: Sherlock Scrape] Launching {'VISUAL HEADED BROWSER' if headed else 'HEADLESS ENGINE'}...")
    print("    Watch the browser navigate, smooth scroll, and extract the live DOM in plain sight.")
    print("=" * 80 + "\n")

    engine = SherlockBrowser(
        headed=headed,
        concurrency=concurrency,
        block_assets=True,
        cache_enabled=not no_cache,
        ttl_hours=ttl,
        apply_deslop=True,
    )

    async with engine:
        results = await engine.scrape_batch(
            urls=target_urls,
            scroll=True,
            force=no_cache,
        )

        print_summary_table(results)

        # Print structured ground truth preview
        print("\n--- Verified Live DOM Highlights ---")
        for res in results:
            if res["success"] and res["text"]:
                print(f"\n[Source: {res['url']}]")
                lines = [line.strip() for line in res["text"].split("\n") if len(line.strip()) > 30]
                preview = lines[:4] if lines else [res["text"][:300]]
                for p in preview:
                    print(f"  • {p}")

        if json_out:
            with open(json_out, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n[+] Exported structured findings to: {json_out}")


def main():
    parser = argparse.ArgumentParser(description="Sherlock Scrape: 2-Phase Scout & Visual DOM Validator")
    parser.add_argument("query_or_urls", nargs="*", help="Natural language query to scout OR specific target URLs")
    parser.add_argument("--headless", action="store_true", help="Run without opening visible browser window (default: False / Headed)")
    parser.add_argument("--concurrency", type=int, default=1, help="Max browser concurrency (default 1 for headed inspection)")
    parser.add_argument("--ttl", type=float, default=24.0, help="Cache TTL in hours (default 24h)")
    parser.add_argument("--no-cache", action="store_true", help="Bypass local cache")
    parser.add_argument("--json-out", help="Path to save JSON results")

    args = parser.parse_args()

    query_input = args.query_or_urls
    if not query_input:
        try:
            print("=" * 65)
            print("                 SHERLOCK LIVE VISUAL SCRAPER")
            print("=" * 65)
            user_input = input("\nEnter query to search & visually scrape: ").strip()
            if not user_input:
                print("[!] No query entered. Exiting.")
                return
            query_input = [user_input]
        except EOFError:
            print("[!] No query provided.")
            return

    asyncio.run(
        run_pipeline(
            query_or_urls=query_input,
            headed=not args.headless,
            concurrency=args.concurrency,
            ttl=args.ttl,
            no_cache=args.no_cache,
            json_out=args.json_out,
        )
    )


if __name__ == "__main__":
    main()
