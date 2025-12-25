# Offline human review

## 1. Critical
- [4] Group 1:
    - Remove AI slop like "let's be blunt," "painfully obvious," and "cut through the hype".
    - Avoid marketing-y or purple-prose phrasing. Specifically avoid:
        - "let's be blunt", "painfully obvious", "cut through the hype"
        - "embracing" and its derivatives
        - "crucial" and its derivatives
        - "leverage", "fast-moving world (of AI)", "But here's the good news"
        - "this is where X comes in"
        - "imagine …" openings
        - "is more than a …" constructions (e.g., "X is more than a …; it's …")
        - "In the early days …", "These aren't just theoretical problems; they are …"
    - When making examples, replace "imagine we have ..." with "suppose we have ...".
    - Remove filler words/phrases: "the best part is", "surprisingly", "simply", "neatly", "powerful design pattern".

## 2. Important
- [2] Group 2:
    - Break long code sections into shorter code blocks followed by brief explanations so users can follow step-by-step.
    - At the start of the article, clearly highlight what will be covered with a concise, itemized overview.

## 3. Minor
- [1] Group 3:
    - Do not use the "—" character; use a standard hyphen.
- [1] Group 4:
    - Prefer concise, skimmable sentences; avoid paragraphs that pack multiple key ideas.
- [1] Group 5:
    - Section 2: Give a brief example of how mock search could be replaced with actual search APIs (Google Search, Bing, specialized knowledge bases) in production.
- [1] Group 6:
    - Section 5: Provide a deeper code output analysis. Briefly discuss how this basic implementation could be extended with more sophisticated tools, better error handling, and more complex reasoning patterns. Explain the `Message` / `MessageRole` classes and helper functions like `pretty_print_message`.

## ! Clashing

## Legend

A group is formatted as follows:
"[<frequency_number>] Group <group_number>:
    - <review>
    - <review>
    - ...
"