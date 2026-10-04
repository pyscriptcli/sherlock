# Factuality & Verification Frameworks

This directory contains research-grade frameworks for decomposing long-form text into atomic statements and verifying each statement against public web indexes.

## Skills

### 1. [`safe/`](safe/SKILL.md) (Google DeepMind)
* **Framework:** Search-Augmented Factuality Evaluator (SAFE)
* **Core Concepts:**
  * Decomposes complex prose into independent atomic facts (`[AF-n]`).
  * Issues targeted search queries to classify each fact as Supported, Contradicted, Unsupported Leap, or Unverifiable.
  * Calculates factual precision via the SAFE Score formula.

### 2. [`factscore/`](factscore/SKILL.md) (EMNLP 2023)
* **Framework:** Fine-grained Atomic Evaluation of Factual Precision
* **Core Concepts:**
  * Deconstructs long-form generation into the smallest self-contained atomic propositions.
  * Disambiguates entities and referents.

## How Sherlock Orchestrates This Category
When `/sherlock` is invoked in `sherlock-validate` mode:
1. Sherlock extracts atomic claims inline (`[AF-1]`, `[AF-2]`).
2. Checks them against retrieved search results.
3. Scores the output using `scripts/safe_score.py` based on the SAFE precision formula:
   $$\text{SAFE Score} = \frac{\text{Supported Claims}}{\text{Total Relevant Claims}} \times 100\%$$
