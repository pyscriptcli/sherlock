# Sherlock Sub-Skills & Engine Ecosystem

This directory houses the specialized toolkits, research engines, and scrapers orchestrated by `/sherlock`.

```
skills/
├── factuality_verification/       # Category 1: Atomic proposition checkers
│   ├── long-form-factuality/      # Google DeepMind SAFE & LongFact benchmark
│   ├── factscore/                 # FActScore atomic factuality evaluation
│   └── README.md
│
├── research_synthesis/            # Category 2: Multi-step autonomous research
│   ├── storm/                     # Stanford STORM multi-perspective RAG
│   ├── open-deep-research/        # LangChain recursive research agent
│   └── README.md
│
├── scraping_automation/           # Category 3: Ground-truth web extractors
│   ├── sherlock-scrape/           # Visual headed Playwright sniper
│   ├── crawl4ai/                  # High-concurrency LLM crawler
│   └── README.md
│
└── anti_slop/                     # Category 4: Anti-bloat & prose sanitizers
    ├── kill-ai-slop/              # AI tics & prose fluff filter
    ├── deslop/                    # Git diff & code cleaner
    ├── aislop/                    # Deterministic prose linter
    ├── ponytail/                  # Senior dev YAGNI & standard library ladder
    └── README.md
```

## Orchestration Overview

| Category | Primary Trigger | Engine / Script | Role in Sherlock |
| :--- | :--- | :--- | :--- |
| **Factuality & Verification** | Claim validation, factual scoring | `long-form-factuality`, `safe_score.py` | Breaks text into atomic facts and scores precision |
| **Research & Synthesis** | Broad investigations, market surveys | `storm`, `open-deep-research` | Collects multi-angle perspectives and cited outlines |
| **Scraping Automation** | Live prices, JS SPAs, visual auditing | `browser_fetch.py`, `crawl4ai` | Captures rendered DOM text with one-click proof links |
| **Anti-Slop** | Output formatting, code verification | `kill-ai-slop`, `ponytail` | Eliminates filler words, enforces direct answers and lean code |
