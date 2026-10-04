# Anti-Slop, De-bloat & Minimalist Engineering

This directory contains deterministic linters, git diff cleaners, and architectural philosophies that purge AI boilerplate, conversational fluff, and unnecessary complexity.

## Skills

### 1. [`anti-slop/`](anti-slop/SKILL.md)
* **Focus:** Banned AI tics, throat-clearing openings, and filler removal.
* **Core Rules:**
  * Bans "delve", "testament to", "tapestry", "in today's digital landscape", and conversational greetings.
  * Delivers the direct answer in the first sentence.
  * Enforces `Unverifiable` for missing proof—zero speculative padding.

### 2. [`ponytail/`](ponytail/SKILL.md)
* **Focus:** Senior developer YAGNI ladder & anti-overengineering.
* **Core Rules:**
  * Reaches for standard library before third-party packages.
  * Native platform features over custom abstractions.
  * One line before fifty.

## How Sherlock Orchestrates This Category
* **Every Output:** Sherlock enforces Anti-Slop Rule 8—delivering the direct answer in the first 1–3 sentences with zero throat-clearing fluff.
* **Code Facts / Repros:** Sherlock applies Ponytail's ladder to ensure any verification script or diagnostic test is as lean and minimal as possible.
