#!/usr/bin/env python3
"""
Sherlock Local Knowledge & Verified Fact Cache
Zero-dependency JSON-backed cache with Time-To-Live (TTL) expiration.
Prevents duplicate web scraping and redundant token consumption.
"""

import sys
import os
import json
import time
import argparse
from typing import Optional, Dict, Any

# Ensure clean UTF-8 printing on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".cache")
CACHE_FILE = os.path.join(CACHE_DIR, "verified_facts.json")


def _load_cache() -> Dict[str, Any]:
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_cache(data: Dict[str, Any]):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_cached_fact(key: str) -> Optional[Dict[str, Any]]:
    """Retrieves a cached verified claim if not expired."""
    cache = _load_cache()
    norm_key = key.strip().lower()
    item = cache.get(norm_key)
    if not item:
        return None
    
    expires_at = item.get("expires_at", 0)
    if time.time() > expires_at:
        del cache[norm_key]
        _save_cache(cache)
        return None
    
    return item.get("data")


def set_cached_fact(key: str, data: Any, ttl_hours: float = 168.0):
    """
    Stores a verified claim or dataset in the cache.
    Default TTL: 168 hours (7 days).
    For volatile prices: pass ttl_hours=24.
    For static hardware/history: pass ttl_hours=720 (30 days).
    """
    cache = _load_cache()
    norm_key = key.strip().lower()
    cache[norm_key] = {
        "created_at": time.time(),
        "expires_at": time.time() + (ttl_hours * 3600),
        "ttl_hours": ttl_hours,
        "data": data
    }
    _save_cache(cache)


def clear_expired() -> int:
    """Removes all expired entries and returns the count removed."""
    cache = _load_cache()
    now = time.time()
    valid_keys = [k for k, v in cache.items() if v.get("expires_at", 0) > now]
    removed = len(cache) - len(valid_keys)
    if removed > 0:
        cleaned = {k: cache[k] for k in valid_keys}
        _save_cache(cleaned)
    return removed


def main():
    parser = argparse.ArgumentParser(description="Sherlock Verified Fact Cache")
    subparsers = parser.add_subparsers(dest="command")

    get_p = subparsers.add_parser("get", help="Get a cached fact")
    get_p.add_argument("key", help="Fact key or query")

    set_p = subparsers.add_parser("set", help="Cache a fact")
    set_p.add_argument("key", help="Fact key or query")
    set_p.add_argument("value", help="Fact value or JSON string")
    set_p.add_argument("--ttl-hours", type=float, default=168.0, help="TTL in hours (default: 168 = 7 days)")

    subparsers.add_parser("list", help="List all active cached facts")
    subparsers.add_parser("clear", help="Clear all expired facts")

    args = parser.parse_args()

    if args.command == "get":
        fact = get_cached_fact(args.key)
        if fact is not None:
            print(json.dumps(fact, indent=2) if isinstance(fact, (dict, list)) else fact)
            sys.exit(0)
        else:
            print(f"[-] Key '{args.key}' not found or expired.", file=sys.stderr)
            sys.exit(1)

    elif args.command == "set":
        try:
            val = json.loads(args.value)
        except Exception:
            val = args.value
        set_cached_fact(args.key, val, ttl_hours=args.ttl_hours)
        print(f"[✓] Cached '{args.key}' (TTL: {args.ttl_hours}h)")

    elif args.command == "list":
        cache = _load_cache()
        clear_expired()
        cache = _load_cache()
        print(f"Total active cached facts: {len(cache)}")
        for k, v in cache.items():
            rem_hrs = (v['expires_at'] - time.time()) / 3600
            print(f"  • {k} (expires in {rem_hrs:.1f}h)")

    elif args.command == "clear":
        removed = clear_expired()
        print(f"[✓] Cleared {removed} expired cache entries.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
