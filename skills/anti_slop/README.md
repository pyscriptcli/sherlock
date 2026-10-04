# Anti-Slop, De-bloat & Minimalist Engineering

This directory contains deterministic linters, git diff cleaners, and architectural philosophies that purge AI boilerplate, conversational fluff, and unnecessary complexity.

## Modules

### 1. `kill-ai-slop/` (Prose & Visual AI Tic Cleaner)
* **Source:** [yetone/kill-ai-slop](https://github.com/yetone/kill-ai-slop)
* **Core Concepts:** Identifies and strips pervasive LLM prose tells: "delve", "testament to", "it is worth noting", "tapestry", sycophantic intros, and generic multi-paragraph summaries.

### 2. `deslop/` (Git Diff & Code Cleaner)
* **Source:** [dabit3/deslop](https://github.com/dabit3/deslop)
* **Core Concepts:** Scans code changes for AI developer anti-patterns: excessive debug statements, redundant defensive `try-catch` blocks, empty boilerplate functions, and obvious comments.

### 3. `aislop/` (Deterministic Prose Linter)
* **Source:** [scanaislop/aislop](https://github.com/scanaislop/aislop)
* **Core Concepts:** Static heuristic analyzer checking text against known mechanical indicators of machine-generated prose without runtime LLM overhead.

### 4. `ponytail/` (Senior Developer YAGNI Ladder)
* **Philosophy:** Forces the laziest solution that actually works: standard library first, native platform features before dependencies, one line before fifty, and zero unrequested abstractions.

## How Sherlock Orchestrates This Category
* **Every Output:** Sherlock enforces Anti-Slop Rule 8—delivering the direct answer in the first 1–3 sentences with zero throat-clearing fluff.
* **Code Facts / Repros:** Sherlock applies Ponytail's ladder to ensure any verification script or diagnostic test is as lean and minimal as possible.
