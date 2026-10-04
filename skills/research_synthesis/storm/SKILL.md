---
name: storm
description: >-
  Stanford University's STORM (Synthesis of Topic Outlines through Retrieval and Multi-perspective Question Asking).
  Researches topics by simulating expert dialogues from diverse angles to generate Wikipedia-quality cited reports.
---

# Stanford STORM (Multi-Perspective Research)

Autonomous research and topic synthesis protocol developed by the Stanford Open Virtual Assistant Lab (OVAL).

## Research Workflow

### 1. Perspective Simulation
Instead of querying a single generic prompt, identify 3–5 diverse expert viewpoints:
- Technical / Architecture Specialist
- Historical / Evolution Specialist
- Practical / Implementation Practitioner
- Critic / Limitations Reviewer

### 2. Information Foraging
Query search indexes from each perspective to discover angles and data that standard single-pass search queries miss.

### 3. Topic Outline Curation
Organize discovered findings into a hierarchical table of contents:
- Overview & Definitions
- Core Mechanisms / Timeline
- Technical Trade-offs & Comparisons
- Real-World Applications & Citations

### 4. Cited Report Drafting
Draft each section strictly grounded in retrieved evidence. Every claim must feature a direct quote and source URL.
