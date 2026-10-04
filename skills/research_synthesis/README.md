# Autonomous Research & Synthesis Engines

This directory contains autonomous multi-step research engines designed to gather multi-angle perspectives, discover recursive citations, and synthesize comprehensive reports.

## Modules

### 1. `storm/` (Stanford University OVAL)
* **Source:** [stanford-oval/storm](https://github.com/stanford-oval/storm)
* **Core Concepts:**
  * **Synthesis of Topic Outlines through Retrieval and Multi-perspective Question Asking.**
  * Simulates expert conversations from diverse perspectives to uncover blind spots before drafting sections.
  * Produces Wikipedia-style comprehensive cited reports.

### 2. `open-deep-research/` (LangChain)
* **Source:** [langchain-ai/open_deep_research](https://github.com/langchain-ai/open_deep_research)
* **Core Concepts:**
  * Multi-agent iterative research architecture powered by LangGraph.
  * Recursively queries search engines, evaluates page relevance, extracts key context, and compiles long-form briefings.

## How Sherlock Orchestrates This Category
When `/sherlock` is invoked for broad, complex, or open-ended investigations (e.g. market overviews, technical surveys, historical timelines):
1. Sherlock delegates to the `research` subagent using the multi-perspective methodology from STORM.
2. Keeps findings cited with direct page quotes and source URLs.
