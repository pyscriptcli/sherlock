# Factuality & Verification Frameworks

This directory contains research-grade frameworks for decomposing long-form text into atomic statements and verifying each statement against public web indexes.

## Modules

### 1. `long-form-factuality/` (Google DeepMind)
* **Source:** [google-deepmind/long-form-factuality](https://github.com/google-deepmind/long-form-factuality)
* **Core Concepts:**
  * **SAFE (Search-Augmented Factuality Evaluator):** Decomposes complex prose into independent atomic facts (`[AF-n]`) and issues iterative search queries to classify each fact as Supported, Contradicted, or Irrelevant.
  * **LongFact:** 2,280 human-curated fact-checking prompts across 38 domains.
  * **F1@K Metric:** Balances fact precision with user-desired answer length.

### 2. `factscore/` (EMNLP 2023)
* **Source:** [shmsw25/FActScore](https://github.com/shmsw25/FActScore)
* **Core Concepts:**
  * **Atomic Proposition Extraction:** Breaks compound sentences into standalone propositions.
  * **Knowledge Base Validation:** Measures the percentage of generated atomic facts that are supported by reliable reference corpuses.

## How Sherlock Orchestrates This Category
When `/sherlock` is invoked in `sherlock-validate` mode:
1. Sherlock extracts atomic claims inline (`[AF-1]`, `[AF-2]`).
2. Checks them against retrieved search results.
3. Scores the output using `scripts/safe_score.py` based on the SAFE precision formula:
   $$\text{SAFE Score} = \frac{\text{Supported Claims}}{\text{Total Relevant Claims}} \times 100\%$$
