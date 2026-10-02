# Sherlock Retrieval Strategy and Browser Guide

This guide explains how Sherlock gathers evidence from the web cleanly, quickly, and accurately.

---

## The Core Philosophy: Text First, Pixels Last

When searching for facts, reading characters directly from the computer's memory is always better than taking a picture of text and trying to read the picture with OCR. 

Here is why:
1. Direct text has zero spelling or number mistakes.
2. It uses far fewer tokens and runs much faster.
3. It keeps the exact sentence structure so links can point straight to the quote.

Pictures and OCR should only be used when the information is actually trapped inside an image, like a chart, a graph, or a drawing.

---

## The 3-Tier Retrieval Protocol

Whenever Sherlock needs to pull evidence from a webpage or URL, it follows these three steps in order:

### Tier 1: Fast Clean Text (Search Snippets & Clean Readers)
- First check search snippets and standard text readers.
- If the page is static and clean, extract the exact text directly.
- If the text is clear and answers the question, stop here. No browser overhead needed.

### Tier 2: Live Browser DOM and Accessibility Tree (Dynamic Pages)
If a page renders blank, hides text behind JavaScript, or uses a modern frontend framework (like React or Next.js):
- Load the page in a headless browser (like Playwright).
- Wait for the network to settle and JavaScript to finish running.
- Extract the text directly from the browser's live DOM or Accessibility Tree.
- Do not take a screenshot of the words. Just pull the clean text string straight from the browser memory.

### Tier 3: Targeted Screenshot and OCR (Visual Assets Only)
If the required fact is inside a graphic (like an interactive stock chart, an SVG graph, an infographic, or a scanned PDF):
- Do not take a full-page screenshot of the whole screen.
- Dismiss any cookie banners or overlays first.
- Take a screenshot of only the specific box or element that contains the chart.
- Run vision/OCR only on that cropped image.
- If the chart shows numbers or dates, check if those same numbers exist anywhere in the page code as a sanity check.

---

## Direct Quote Links (Text Fragments)

Whenever possible, link directly to the exact sentence on the webpage using web standard text fragments:

```text
https://example.com/article#:~:text=start_words,end_words
```

When a user clicks this link in any modern browser, the browser will automatically scroll down and highlight the exact quote in yellow. This makes checking the source fast and effortless.

---

## Source Ranking Summary

When gathering evidence, prioritize sources in this order:
1. Primary records: Official filings, government releases, regulatory filings.
2. Direct announcements: Company press releases and official documentation.
3. Reputable reporting: Established news organizations with clear editorial standards.
4. Blogs and community posts: Helpful for initial leads, but must be confirmed with primary sources.
