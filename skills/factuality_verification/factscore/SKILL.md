---
name: factscore
description: >-
  Fine-grained Atomic Evaluation of Factual Precision (FActScore).
  Extracts atomic propositions from complex generated text and evaluates
  the proportion of verifiable units backed by reliable reference knowledge.
---

# FActScore (Fine-grained Atomic Evaluation)

Deconstructs long-form generation into the smallest verifiable atomic propositions.

## Proposition Extraction Rules

1. **Self-Contained Units:** Every proposition must be understandable without reading prior or subsequent sentences.
2. **Entity Grounding:** Disambiguate all referents (replace "the company" with "Apple Inc.", "the model" with "Gemini 2.5 Pro").
3. **Property Isolation:** Split compound claims into distinct propositions:
   * *Sentence:* "The concert will be held on March 13, 2027 at Philippine Sports Stadium in Bulacan."
   * *Proposition 1:* The concert date is March 13, 2027.
   * *Proposition 2:* The concert venue is Philippine Sports Stadium.
   * *Proposition 3:* The venue is located in Bulacan.
4. **Precision Measure:** Calculate supported propositions over total extracted units.
