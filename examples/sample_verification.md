# Sherlock Operational Examples

Here are three simple examples showing how Sherlock handles different kinds of requests:
1. `sherlock-validate` (Checking text)
2. `sherlock-search` (Researching from scratch)
3. `sherlock-help` (Giving advice and planning)

---

## 1. sherlock-validate (Checking Existing Text)

### User Prompt
> "Check this statement: In October 2023, Anthropic announced a $4 billion investment agreement from Amazon, which immediately gave Amazon a 51% controlling stake in Anthropic."

---

### Step 1 & 2: Breaking Down Claims and Checking In
Sherlock breaks down the sentence into standalone points:

> Here are the standalone statements to check:
> - [AF-1]: In October 2023, Anthropic announced an investment agreement from Amazon.
> - [AF-2]: The Amazon investment agreement with Anthropic was valued up to $4 billion.
> - [AF-3]: The investment agreement immediately gave Amazon a 51% controlling stake in Anthropic.
>
> Does this list look good to check? (Proceeding to search)

---

### Step 3 & 4: Finding Evidence and Matching Statements

- [AF-1] In October 2023, Anthropic announced an investment agreement from Amazon.
  - Status: Unsupported Leap (Wrong Month)
  - Quote: "Amazon and Anthropic announced on September 25, 2023, that Amazon will invest up to $4 billion in Anthropic."
  - Source: [Amazon Press Release](https://www.aboutamazon.com/news/company-news/amazon-anthropic-investment)
  - Explanation: The announcement was in September 2023, not October 2023.

- [AF-2] The Amazon investment agreement with Anthropic was valued up to $4 billion.
  - Status: Supported
  - Quote: "...Amazon will invest up to $4 billion in Anthropic and have a minority ownership position in the company."
  - Source: [Amazon Press Release](https://www.aboutamazon.com/news/company-news/amazon-anthropic-investment)
  - Explanation: The dollar amount matches what was reported.

- [AF-3] The investment agreement immediately gave Amazon a 51% controlling stake in Anthropic.
  - Status: Contradicted
  - Quote: "...Amazon will have a minority ownership position in the company... Amazon will not have a board seat."
  - Source: [Reuters](https://www.reuters.com/technology/amazon-invest-up-4-billion-ai-startup-anthropic-2023-09-25/)
  - Explanation: Amazon took a minority, non-controlling stake without a board seat, not a 51% controlling stake.

---

### Step 5: Score Summary

| Status | Count | Percentage |
| :--- | :--- | :--- |
| Supported | 1 | 33.3% |
| Contradicted | 1 | 33.3% |
| Unsupported Leap | 1 | 33.3% |
| Unverifiable | 0 | 0.0% |
| Total Statements | 3 | 100% |

Overall SAFE Score: 33.3%

---

Would you like me to help suggest a corrected sentence for your draft?

---

## 2. sherlock-search (Researching from Scratch)

### User Prompt
> "Find verified facts on the founding team and initial funding of Mistral AI."

### Sherlock Response

### Sherlock Research Notes: Mistral AI

- [Fact 1] Mistral AI was co-founded by Arthur Mensch, Guillaume Lample, and Timothée Lacroix in May 2023.
  - Quote: "Mistral AI was co-founded in May 2023 by Arthur Mensch (CEO), previously at DeepMind, and Guillaume Lample and Timothée Lacroix, previously at Meta."
  - Source: [Financial Times](https://www.ft.com/content/mistral-ai-founding)

- [Fact 2] In June 2023, Mistral AI completed a €105 million ($113 million) seed round.
  - Quote: "French AI start-up Mistral has raised €105m in Europe's largest ever seed round, just four weeks after it was founded."
  - Source: [Reuters](https://www.reuters.com/technology/french-ai-startup-mistral-raises-105-mln-seed-round-2023-06-13/)

- [Fact 3] The seed round was led by Lightspeed Venture Partners.
  - Quote: "The €105 million seed financing was led by Lightspeed Venture Partners..."
  - Source: [Lightspeed Venture Partners Official Announcement](https://lsvp.com/stories/backing-mistral-ai/)

---

## 3. sherlock-help (Advice and Planning)

### User Prompt
> "I have a long report on EV battery manufacturing in Southeast Asia. How should I go about checking it?"

### Sherlock Response

> Here is a simple, effective way to check a long report without getting bogged down:
>
> 1. Pull out the hard numbers first:
>    Look for numbers like factory capacity (GWh), investment amounts, dates, and ownership percentages. These are usually the places where mistakes or outdated data happen.
>
> 2. Break down compound statements:
>    If a sentence has three facts packed together, split it up. For example, "Company X built a $500M factory in Thailand and opened in July 2024" has three claims: the company, the amount, and the opening date. Check each one separately.
>
> 3. Go straight to primary sources:
>    Check government investment boards, regulatory filings, or direct press releases from the companies instead of relying on blog posts or aggregators.
>
> 4. Keep score:
>    Mark each number as either supported, wrong, or unproven so you know which parts of the report need fixing before sharing it.
