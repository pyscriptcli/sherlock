---
name: safe
description: >-
  Google DeepMind's Search-Augmented Factuality Evaluator (SAFE).
  Decomposes long-form prose into standalone atomic facts, queries web search,
  and evaluates precision via the Supported / Contradicted / Unsupported Leap classification.
---

# Google DeepMind SAFE (Search-Augmented Factuality Evaluator)

Automated evaluation protocol for measuring and enforcing factual accuracy in long-form language model generation.

## 4-Step Verification Workflow

### 1. Atomic Decomposition
Split complex multi-clause sentences into individual, standalone atomic facts:
- Replace all pronouns (`he`, `she`, `it`, `they`) with actual entity names.
- Ensure each fact is independently verifiable as True or False.
- Label sequentially: `[AF-1]`, `[AF-2]`, `[AF-3]`.

### 2. Search Query Formulation
For each atomic fact, generate 1–2 precise, unpadded search queries:
- Query official registries, documentation, or primary sources.
- Avoid vague keywords or speculative terms.

### 3. Evidence Match Classification
Evaluate the retrieved evidence against each statement:
- **Supported:** The source explicitly confirms the statement.
- **Contradicted:** The source explicitly refutes the statement or provides contrary figures.
- **Unsupported Leap:** The source discusses related context but does not prove this specific claim.
- **Unverifiable:** No credible public documentation exists to prove or disprove the claim.

### 4. Precision Scoring (SAFE Score)
$$\text{SAFE Score} = \frac{\text{Supported Facts}}{\text{Total Relevant Facts}} \times 100\%$$
