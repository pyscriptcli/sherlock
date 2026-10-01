# Sherlock Operational Examples

This document demonstrates execution traces for Sherlock's three primary routing branches:
1. `sherlock-validate`
2. `sherlock-search`
3. `sherlock-help`

---

## 1. `sherlock-validate` (Post-Checker)

### Scenario: Fact-checking an investment summary claim

#### User Input
> "Check this statement: In October 2023, Anthropic announced a $4 billion investment agreement from Amazon, which immediately gave Amazon a 51% controlling stake in Anthropic."

---

#### Step 1 & 2: Atomic Decomposition & HITL Pause
Sherlock decomposes the claim into independent, de-contextualized atomic statements:

> **[Decomposed Atomic Facts]**
> - `[AF-1]`: In October 2023, Anthropic announced an investment agreement from Amazon.
> - `[AF-2]`: The Amazon investment agreement with Anthropic was valued up to $4 billion.
> - `[AF-3]`: The investment agreement immediately gave Amazon a 51% controlling stake in Anthropic.
>
> *Proceed with multi-step search verification across these 3 claims? (Proceeding)*

---

#### Step 3 & 4: Multi-Step Retrieval & Valuation Notes

- **[AF-1] In October 2023, Anthropic announced an investment agreement from Amazon.**
  - **Status**: ⚠️ **Unsupported Leap** *(Date Discrepancy)*
  - **Quote**: "Amazon and Anthropic announced on September 25, 2023, that Amazon will invest up to $4 billion in Anthropic."
  - **Source**: [Amazon Press Release](https://www.aboutamazon.com/news/company-news/amazon-anthropic-investment)
  - **Analysis**: The initial announcement occurred in September 2023, not October 2023.

- **[AF-2] The Amazon investment agreement with Anthropic was valued up to $4 billion.**
  - **Status**: ✅ **Supported**
  - **Quote**: "...Amazon will invest up to $4 billion in Anthropic and have a minority ownership position in the company."
  - **Source**: [Amazon Press Release](https://www.aboutamazon.com/news/company-news/amazon-anthropic-investment)
  - **Analysis**: Verbatim match with reported terms.

- **[AF-3] The investment agreement immediately gave Amazon a 51% controlling stake in Anthropic.**
  - **Status**: ❌ **Contradicted**
  - **Quote**: "...Amazon will have a minority ownership position in the company... Amazon will not have a board seat."
  - **Source**: [SEC / Official Statements via Reuters](https://www.reuters.com/technology/amazon-invest-up-4-billion-ai-startup-anthropic-2023-09-25/)
  - **Analysis**: Explicitly contradicted; Amazon took a minority, non-controlling stake with no board seat, not a 51% controlling stake.

---

#### Step 5: Scorecard & Final HITL

| Status | Count | Percentage |
| :--- | :--- | :--- |
| **Supported** | 1 | 33.3% |
| **Contradicted** | 1 | 33.3% |
| **Unsupported Leap** | 1 | 33.3% |
| **Unverifiable** | 0 | 0.0% |
| **Total Evaluated** | 3 | 100% |

**Overall SAFE Factuality Score**: **33.3%**

> [!QUESTION]
> Would you like a forensic deep-dive into the regulatory scrutiny (FTC/CMA) surrounding Amazon's minority stake, or a corrected text replacement for your document?

---

## 2. `sherlock-search` (Strict Researcher)

### User Input
> "Gather verifiable facts on the founding team and initial funding of Mistral AI."

### Sherlock Response

### 📋 Sherlock Evidence Dossier: Mistral AI Inception

- **[FACT-1] Mistral AI was co-founded by Arthur Mensch, Guillaume Lample, and Timothée Lacroix in May 2023.**
  - **Quote**: "Mistral AI was co-founded in May 2023 by Arthur Mensch (CEO), previously at DeepMind, and Guillaume Lample and Timothée Lacroix, previously at Meta."
  - **Source**: [Financial Times](https://www.ft.com/content/mistral-ai-founding)

- **[FACT-2] In June 2023, Mistral AI completed a €105 million ($113 million) seed round.**
  - **Quote**: "French AI start-up Mistral has raised €105m in Europe's largest ever seed round, just four weeks after it was founded."
  - **Source**: [Reuters](https://www.reuters.com/technology/french-ai-startup-mistral-raises-105-mln-seed-round-2023-06-13/)

- **[FACT-3] The seed round was led by Lightspeed Venture Partners.**
  - **Quote**: "The €105 million seed financing was led by Lightspeed Venture Partners..."
  - **Source**: [Lightspeed Venture Partners Official Announcement](https://lsvp.com/stories/backing-mistral-ai/)

---

## 3. `sherlock-help` (Advisor)

### User Input
> "I need to verify a 20-page market research report on Southeast Asian EV manufacturing before delivering to the CEO. How should I approach it?"

### Sherlock Response

> **Sherlock Strategy Briefing: Verification Battle Plan**
>
> Don't read 20 pages passively—that is how hallucinations and stale data slip through. Execute this 4-phase protocol:
>
> 1. **Claim Triage & Red-Flag Extraction**:
>    - Scan exclusively for quantitative claims: capacity gigawatt-hours (GWh), tax holiday durations, facility capex figures, and joint-venture equity splits.
>    - Ignore corporate narrative and aspirational mission statements.
>
> 2. **Atomic Decomposition**:
>    - Strip out compound sentences. A sentence like *"BYD inaugurated its $486M plant in Rayong, Thailand, targeting 150,000 units annually starting July 2024"* contains four distinct atomic claims. Verify each independently.
>
> 3. **Source Triangulation Hierarchy**:
>    - Target Board of Investment (BOI) filings and official ministry portals (e.g. Thailand BOI, Indonesia BKPM) over secondary industry blogs.
>    - Cross-reference automaker investor relations (IR) releases for exact commercial operation dates (COD).
>
> 4. **Entailment Audit**:
>    - Tag every metric as Supported, Contradicted, Unsupported Leap, or Unverifiable. Demand 100% support for all board-level summary slides.
