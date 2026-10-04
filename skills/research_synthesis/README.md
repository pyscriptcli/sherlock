# Autonomous Research & Synthesis Engines

This directory contains autonomous multi-step research engines designed to gather multi-angle perspectives, discover recursive citations, and synthesize comprehensive reports.

## Skills

### 1. [`storm/`](storm/SKILL.md) (Stanford University OVAL)
* **Framework:** Synthesis of Topic Outlines through Retrieval and Multi-perspective Question Asking
* **Core Concepts:**
  * Simulates expert conversations from diverse perspectives to uncover blind spots before drafting sections.
  * Produces comprehensive, cited Wikipedia-style reports.

### 2. [`deep-research/`](deep-research/SKILL.md)
* **Framework:** Recursive Information Foraging
* **Core Concepts:**
  * Multi-turn query decomposition and link traversal across deep documentation layers.
  * Context consolidation and cross-verification across authoritative sources.

## How Sherlock Orchestrates This Category
When `/sherlock` is invoked for broad, complex, or open-ended investigations (e.g. market overviews, technical surveys, historical timelines):
1. Sherlock delegates to the `research` subagent using the multi-perspective methodology from STORM.
2. Keeps findings cited with direct page quotes and source URLs.
