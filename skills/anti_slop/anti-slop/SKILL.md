---
name: anti-slop
description: >-
  Deterministic rules and filters for eliminating AI conversational fluff, sycophancy,
  mechanical tics, and defensive boilerplate from text and code.
---

# Anti-Slop & Prose De-bloat

Enforces strict human-level writing standards by stripping machine-generated filler and verbal artifacts.

## Banned AI Tics & Buzzwords

Never include these pervasive machine-generated filler patterns:
* **The "Delve" Family:** "delve", "delving into", "dive deep", "unpacking", "navigating the complexities".
* **The "Tapestry" Family:** "tapestry", "beacon", "testament to", "rich mosaic", "symphony of".
* **Throat-Clearing Openings:** "In today's fast-paced digital landscape...", "It is important to remember...", "It's worth noting that...".
* **Sycophantic Conversational Filler:** "Certainly! I'd be happy to help with that!", "Great question!", "I hope this finds you well!".
* **Redundant Summaries:** "In conclusion...", "To summarize the above points...", "All in all...".

## Core Rules

1. **Answer First:** The very first sentence must deliver the direct answer or factual verdict.
2. **Zero Speculative Padding:** When information is missing, write `Unverifiable` in one clean sentence. Do not invent hypothetical explanations.
3. **No Unrequested Scaffolding:** No boilerplate, no generic intros, no defensive hedges.
