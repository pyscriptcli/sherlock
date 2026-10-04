# Sherlock Categorized Skills Ecosystem

This directory houses the curated, modular skills orchestrated by `/sherlock`.

```
skills/
├── factuality_verification/       # Category 1: Atomic fact checkers
│   ├── safe/                      # Google DeepMind SAFE protocol
│   ├── factscore/                 # FActScore atomic proposition evaluator
│   └── README.md
│
├── research_synthesis/            # Category 2: Multi-step autonomous research
│   ├── storm/                     # Stanford STORM multi-perspective RAG
│   ├── deep-research/             # Recursive multi-turn research protocol
│   └── README.md
│
├── scraping_automation/           # Category 3: Ground-truth web extractors
│   ├── sherlock-scrape/           # Visual headed Playwright DOM sniper
│   │   ├── SKILL.md
│   │   ├── references/
│   │   └── scripts/browser_fetch.py
│   └── README.md
│
└── anti_slop/                     # Category 4: Anti-bloat & prose sanitizers
    ├── anti-slop/                 # Banned AI tics & verbal fluff filter
    ├── ponytail/                  # Senior dev YAGNI & standard library ladder
    └── README.md
```

## Orchestration Overview

| Category | Primary Trigger | Target Skill | Role in Sherlock |
| :--- | :--- | :--- | :--- |
| **Factuality & Verification** | Claim validation, factual scoring | `safe`, `factscore` | Breaks text into atomic facts and scores precision |
| **Research & Synthesis** | Broad investigations, deep research | `storm`, `deep-research` | Collects multi-angle perspectives and cited outlines |
| **Scraping Automation** | Live prices, JS SPAs, visual auditing | `sherlock-scrape` | Captures rendered DOM text with one-click proof links |
| **Anti-Slop** | Output formatting, code verification | `anti-slop`, `ponytail` | Eliminates filler words, enforces direct answers and lean code |
