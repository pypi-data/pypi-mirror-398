# Lesson 19 Guideline

## Global Context of the Lesson

### What We Are Planning to Share

Lesson 19 continues Part 2B by **finishing the research agent** you built across the previous lessons. We'll add the final quality‑control and compilation steps, then run the **entire, end‑to‑end workflow** and critique outputs:

- Add/inspect four MCP tools:
    - `select_research_sources_to_keep_tool.py` — filter out low‑trust Perplexity sources with a reviewable, structured decision.
    - `select_research_sources_to_scrape_tool.py` — pick the *few* high‑value URLs to scrape in full.
    - `scrape_research_urls_tool.py` — scrape/clean those URLs (Firecrawl → Markdown → brief LLM clean).
    - `create_research_file_tool.py` — compile **all** research into a neatly structured **`research.md`**.
- Run the **full agent** on 2–3 different article guidelines; analyze quality, coverage, and cost.
- Show how to use the agent in **Cursor** via the included `.mcp.json.sample`.
- Close with **extensibility ideas** and note that **deployment** is covered in **Part 3**.

### Why We Think It’s Valuable

Unfiltered web research often includes **SEO spam, weak blogs, or off‑topic links**. Without curation you either (a) ship noise or (b) waste time hand‑picking sources. This lesson gives you **automated quality gates**, a **"full‑content" path** for top sources, and a **deterministic final artifact** (`research.md`). You also learn how to surface **human‑in‑the‑loop (HITL)** checkpoints in the MCP prompt so you can **approve the kept/scraped sources** when needed—while still enjoying default automation. Finally, you see how MCP's **server‑hosted prompts** and **tools** make this workflow portable across clients like Cursor.

### Expected Length of the Lesson

**3,000 words** (without titles and references), where we assume that 200–250 words ≈ 1 minute of reading time.

### Theory / Practice Ratio

**30% theory – 70% hands‑on**

---

## Anchoring the Lesson in the Course

### Details About the Course

This piece is part of a broader course on AI agents and LLM workflows. The course consists of **4 parts**, each with multiple lessons.

Thus, it’s essential to always anchor this piece into the broader course, understanding where the reader is in their journey. You will be careful to consider the following:

- The points of view
- To not reintroduce concepts already taught in the previous lessons
- To be careful when talking about concepts introduced only in future lessons
- To always reference previous and future lessons when discussing topics outside the piece’s scope

### Lesson Scope

This is **Lesson 19 (Part 2B)** on **Final Outputs & Agent Completion**—you implement curation, deep scrapes, and the final `research.md`, then run the full workflow.

### Point of View

The course is created by a team writing for a single reader, also known as the student. Thus, for voice consistency across the course, we will always use **“we,” “our,” and “us”** to refer to the team who creates the course, and **“you” or “your”** to address the reader. Avoid singular first person and don’t use **“we”** to refer to the student.

**Example of correct point of view:**

- Instead of “Before we can choose between workflows and agents, we need a clear understanding of what they are,” write “To choose between workflows and agents, you need a clear understanding of what they are.”

### Who Is the Intended Audience

Aspiring AI engineers learning to **finish and harden a research agent** with **quality filters**, **selective deep scraping**, and a **final, structured research file**.

### Concepts Introduced in Previous Lessons

In previous lessons of the course, we introduced the following concepts:

**Part 1:**

- **Lesson 1 - AI Engineering & Agent Landscape**: Understanding the role, the stack, and why agents matter now
- **Lesson 2 - Workflows vs. Agents**: Grasping the crucial difference between predefined logic and LLM-driven autonomy
- **Lesson 3 - Context Engineering**: The art of managing information flow to LLMs
- **Lesson 4 - Structured Outputs**: Ensuring reliable data extraction from LLM responses
- **Lesson 5 - Basic Workflow Ingredients**: Implementing chaining, routing, parallel and the orchestrator-worker patterns
- **Lesson 6 - Agent Tools & Function Calling**: Giving your LLM the ability to take action
- **Lesson 7 - Planning & Reasoning**: Understanding patterns like ReAct (Reason + Act)
- **Lesson 8 - Implementing ReAct**: Building a reasoning agent from scratch
- **Lesson 9 - Agent Memory & Knowledge**: Short-term vs. long-term memory (procedural, episodic, semantic)
- **Lesson 10 - RAG Deep Dive**: Advanced retrieval techniques for knowledge-augmented agents
- **Lesson 11 - Multimodal Processing**: Working with documents, images, and complex data

**Part 2A & 2B (before L19):**

- **L12** — Capstone scope (research agent + writing workflow split)
- **L13** — Frameworks comparison (why FastMCP for research; LangGraph for writing)
- **L14** — System‑design decision framework (models, cost/latency/context budgets, HITL policy)
- **L16** — MCP foundations: server/client; **tools/resources/prompts**; server-hosted prompts; discovery; thin orchestration over heavy tools.
- **L17** — Ingestion layer: URL extraction (`extract_guidelines_urls`), local file processing, scraping/cleaning (`scrape_and_clean_other_urls`), GitHub ingestion (`process_github_urls`), YouTube transcription (`transcribe_youtube_urls`), file‑first design, and critical‑failure policy.
- **L18** — Research loop: query generation (`generate_next_queries`), Perplexity integration with **structured outputs** (`run_perplexity_research`), three-round loop, and HITL feedback gates.

### Concepts That Will Be Introduced in Future Lessons

**Part 2:**

- **L20–L23:** the **writer agent workflow** (implemented with **LangGraph**) that consumes `research.md` and turns it into publishable content (with reflection loops and optional HITL).

**Part 3:**

- With the agent system built, this section focuses on the engineering practices required for production. You will learn to design and implement robust evaluation frameworks to measure and guarantee agent reliability, moving far beyond simple demos. We will cover AI observability, using specialized tools to trace, debug, and understand complex agent behaviors. Finally, you’ll explore optimization techniques for cost and performance and learn the fundamentals of deploying your agent system, ensuring it is scalable and ready for real-world use.

**Part 4:**

- In this final part of the course, you will build and submit your own advanced LLM agent, applying what you've learned throughout the previous sections. We provide a complete project template repository, enabling you to either extend our agent pipeline or build your own novel solution. Your project will be reviewed to ensure functionality, relevance, and adherence to course guidelines for the awarding of your course certification.

As a lesson on AI agent engineering, we may have to make references to new terms that haven't been introduced yet. We will discuss them in a highly intuitive manner, being careful not to confuse the reader with too many terms that haven't been introduced yet in the course.

### Anchoring the Reader in the Educational Journey

Within the course we are teaching the reader multiple topics and concepts. Thus, understanding where the reader is in their educational journey is critical for this piece. You have to use only previously introduced concepts, while being reluctant about using concepts that haven't been introduced yet.

When discussing the **concepts introduced in previous lessons** listed in the `Concepts Introduced in Previous Lessons` section, avoid reintroducing them to the reader. Especially don't reintroduce the acronyms. Use them as if the reader already knows what they are.

Avoid using all the **concepts that haven't been introduced in previous lessons** listed in the `Concepts That Will Be Introduced in Future Lessons` subsection. Whenever another concept requires references to these banned concepts, instead of directly using them, use intuitive analogies or explanations that are more general and easier to understand, as you would explain them to a 7-year-old. For example:

- If the "tools" concept wasn't introduced yet and you have to talk about agents, refer to them as "actions".
- If the "routing" concept wasn't introduced yet and you have to talk about it, refer to it as "guiding the workflow between multiple decisions". You can use the concepts that haven't been introduced in previous lessons listed in the `Concepts That Will Be Introduced in Future Lessons` subsection only if we explicitly specify them. Still, even in that case, as the reader doesn't know how that concept works, you are only allowed to use the term, while keeping the explanation extremely high-level and intuitive, as if you were explaining it to a 7-year-old. Whenever you use a concept from the `Concepts That Will Be Introduced in Future Lessons` subsection, explicitly specify in what lesson it will be explained in more detail, leveraging the particulars from the subsection. If not explicitly specified in the subsection, simply state that we will cover it in future lessons without providing a concrete lesson number.

In all use cases avoid using acronyms that aren't explicitly stated in the guidelines. Rather use other more accessible synonyms or descriptions that are easier to understand by non-experts.

---

## Narrative Flow of the Lesson

Follow the next narrative flow when writing the end‑to‑end lesson:

- **What problem are we learning to solve? Why is it essential to solve it?**
    - Start with the problem: unfiltered research accumulates noise and wastes scraping budget
- **Why other solutions are not working and what's wrong with them.**
    - Manual curation is slow; skipping curation ships low-quality sources; scraping everything is expensive
- **At a theoretical level, explain our solution or transformation. Highlight:**
    - The theoretical foundations: LLM-as-filter for quality gates; multi-factor source selection; file-first compilation
    - Why is it better than other solutions? Automated + transparent + auditable + HITL-ready
    - What tools or algorithms can we use? MCP tools with structured outputs; Firecrawl for scraping; LLM for evaluation
- **Provide hands-on examples:** Test each tool programmatically; run the full workflow; inspect outputs
- **Go deeper into the advanced theory:** HITL gates via prompt-level controls; design iteration stories; quality rubrics
- **Provide a more complex example supporting the advanced theory:** Run the complete agent on multiple guidelines; audit quality
- **Connect our solution to the bigger field of AI Engineering. Add course next steps:** Transition to the writing workflow

---

## Lesson Outline

1. **Section 1 — Introduction**
2. **Section 2 — Completing the Workflow**
3. **Section 3 — Filter** Perplexity **Sources to Keep**
4. **Section 4 — Select Sources to Scrape in Full**
5. **Section 5 — Scrape Selected Research URLs**
6. **Section 6 — Create the Final `research.md` File**
7. **Section 7 — Human‑in‑the‑Loop (HITL) Controls via MCP**
8. **Section 8 — Testing the Complete Agent Workflow**
9. **Section 9 — Use the MCP Server in Cursor**
10. **Section 10 — Conclusion**

---

## Section 1 — Introduction

- **Problem framing:** Open-ended research without **quality gates** accumulates noisy, redundant, or off-topic sources. We need a repeatable way to **filter** Perplexity results for trust/authority, **select** the best URLs for full scraping, and **compile** everything into a single, well-cited `research.md`.
- **Quick reference to what we've learned in previous lessons:** Take the core ideas of what we've learned in previous lessons from the `Concepts Introduced in Previous Lessons` subsection of the `Anchoring the Lesson in the Course` section.
- **Transition to what we'll learn in this lesson:** After presenting what we learned in the past, make a transition to what we will learn in this lesson. Take the core ideas of the lesson from the `What We Are Planning to Share` subsection and highlight the importance and existence of the lesson from the `Why We Think It's Valuable` subsection of the `Global Context of the Lesson` section.
- **Section length:** ~250–300 words.

---

## Section 2 — Completing the Research Workflow

**For the article, copy the following from Notebook Section 2 – "Completing the Research Workflow":**

1. **Markdown intro** (the opening paragraph explaining the remaining steps in the workflow)
2. **The MCP prompt excerpt** (the full markdown code block showing Steps 4, 5, and 6 with all substeps: 4.1 filter sources, 5.1-5.2 select and scrape, 6.1 create research file)

Then add your own subsection explaining the workflow structure:

- **Show the remaining steps (4–6) in the server‑hosted MCP prompt** (stored in `mcp_server/src/prompts/research_instructions_prompt.py` and shown in Notebook Section 2). Read **Steps 4–6** verbatim.
    - **Step 4:** Filter Perplexity results by quality using `select_research_sources_to_keep` tool.
    - **Step 5:** Identify sources for full scrape using `select_research_sources_to_scrape`, then scrape them with `scrape_research_urls`.
    - **Step 6:** Compile everything into `research.md` with `create_research_file`.
    - *Comment:* Notice the **file‑first** pattern continues—all outputs live under `.nova/` except the final `research.md` at the root.
- **Revisit the critical‑failure policy from the MCP prompt** (recap from **L16-L17**): Any tool that processes **0/N** items when items were expected halts the workflow and asks for guidance—this preserves reliability.
- **Artifacts recap:** output files live under `.nova/` and **short tool returns** keep token costs low; the final `research.md` sits at the root of the research directory.
    - **→ Transition:** Now we'll examine each tool in detail.

**Section length:** ~220–280 words.

---

## Section 3 — Filter Perplexity Sources to Keep

**For the article, copy the following from Notebook Section 3 – "Filtering Research Sources for Quality":**

**Subsection 3.1 — Understanding the Tool Implementation**

1. **Copy the markdown intro** (the opening paragraph starting with "The `select_research_sources_to_keep` tool addresses a critical problem...")
2. **Copy the entire Subsection 3.1** including:
   - The markdown explanation about what the tool does (reads guidelines and Perplexity results, evaluates sources, outputs two files)
   - The Python code block showing `async def select_research_sources_to_keep_tool(...)` (the full function with docstring, path setup, context gathering, LLM selection call, file writing, and return statement)
   - The explanatory prose following the code (explaining the `select_sources` function and `PROMPT_SELECT_SOURCES` prompt)

**Subsection 3.2 — The Source Evaluation Prompt**

3. **Copy the entire Subsection 3.2** including:
   - The markdown heading "Here's the prompt used to evaluate the sources:"
   - The Python code block showing `PROMPT_SELECT_SOURCES` (the full prompt template with article_guidelines and sources_data placeholders, selection criteria bullets, and return format)
   - The closing prose explaining the prompt's role as quality gatekeeper

**Subsection 3.3 — Testing the Source Selection Tool**

4. **Copy the test cell setup and explanation**:
   - The markdown heading "Let's test the source filtering tool..."
   - The Python code cell showing the import and call to `select_research_sources_to_keep_tool`
   - The markdown cell following with the result dict explanation

**For your notebook practice:**
- Execute the code cell from Section 3 with your sample research folder
- Understand the **three-input pattern**: article guidelines, Perplexity results, and LLM-based evaluation
- Observe the returned structure: `{status, sources_selected_count, selected_source_ids, sources_selected_path, results_selected_path, message}`
- Open both output files: `.nova/perplexity_sources_selected.md` (comma-separated IDs) and `.nova/perplexity_results_selected.md` (filtered content)
- Notice how the selection criteria balance **domain reputation**, **content quality**, and **relevance to guidelines**

**Optional HITL after keep‑selection:** Because the workflow instructions live in an **MCP prompt**, you can ask the agent to **show kept IDs** and **pause** for approval before continuing. No code changes required—add the instruction when invoking the prompt.

**Developer note (design iteration):**
- We originally went **straight to `research.md`** after the loop. Spammy results forced us to add this **automated keep step**. Later we realized some Perplexity URLs were **worth scraping in full**; we added a **second selector** rather than re‑running research or editing the guideline mid‑flight.

**Why this matters:** This tool exemplifies **quality gates** that prevent noise from polluting downstream artifacts, and demonstrates **LLM-as-filter** for automated curation.

**Section length:** ~380–460 words.

---

## Section 4 — Select Sources to Scrape in Full

**For the article, copy the following from Notebook Section 4 – "Selecting Sources for Full Content Scraping":**

**Subsection 4.1 — Understanding the Selection Logic**

1. **Copy the markdown intro** (the opening paragraph starting with "After filtering for quality, we need to identify...")
2. **Copy the entire Subsection 4.1** including:
   - The markdown explanation about what the tool does (analyzes filtered results, selects up to max_sources URLs based on four-factor rubric, outputs prioritized list)
   - The Python code block showing `async def select_research_sources_to_scrape_tool(...)` (the full function with docstring, path setup, context gathering including scraped guideline context, LLM selection call, file writing, and return statement)
   - The explanatory prose following the code (explaining the `select_top_sources` function and `PROMPT_SELECT_TOP_SOURCES` prompt)

**Subsection 4.2 — The Source Selection Prompt**

3. **Copy the entire Subsection 4.2** including:
   - The markdown heading "The tool uses a prompt to choose the most valuable sources:"
   - The Python code block showing `PROMPT_SELECT_TOP_SOURCES` (the full prompt template with the four-dimensional evaluation framework: relevance, authority, quality, uniqueness)
   - The closing prose explaining why the four-factor rubric matters and what the reasoning requirement provides

**Subsection 4.3 — Testing the Source Selection Tool**

4. **Copy the test cell setup and explanation**:
   - The markdown heading "Now let's test the source selection tool..."
   - The Python code cell showing the import and call to `select_research_sources_to_scrape_tool` with `max_sources=3`
   - The output display showing the selected URLs and reasoning

**For your notebook practice:**
- Execute the code cell from Section 4 with your sample research folder
- Understand the **four-factor rubric**: relevance, authority, quality, uniqueness vs. already-scraped content
- Observe the returned structure: `{status, sources_selected, sources_selected_count, output_path, reasoning, message}`
- Open `.nova/urls_to_scrape_from_research.md` to verify the selected URLs (one per line)
- Read the `reasoning` field to understand why these specific URLs were chosen
- Notice the **default limit of 5 sources** balances comprehensive coverage with API costs

**Optional HITL after scrape‑selection:** Ask the agent (via the MCP prompt) to **display the chosen URLs** and **pause** for edits before scraping. This gate is especially useful when time or credits are tight.

**Why this matters:** This tool demonstrates **resource allocation optimization**—spending scraping budget only on high-leverage sources that add unique value.

**Section length:** ~340–420 words.

---

## Section 5 — Scrape Selected Research URLs

**For the article, copy the following from Notebook Section 5 – "Scraping Selected Research URLs":**

1. **Copy the markdown intro** (the opening paragraph starting with "The `scrape_research_urls_tool` handles the full content extraction...")
2. **Copy the test cell**:
   - The Python code cell showing the import and call to `scrape_research_urls_tool` with `concurrency_limit=3`
   - The output display showing the scraping results dict

Then add your own subsection explaining the design:

- **Goal:** `scrape_research_urls_tool` reads `.nova/urls_to_scrape_from_research.md`, de‑dupes against previously scraped guideline URLs, then **scrapes** each new URL using **Firecrawl** (robust, markdown‑oriented capture) and runs a **short LLM clean pass** to remove nav/boilerplate while keeping **content relevant to the guideline**. Outputs land in `.nova/urls_from_research/`.
- **Concurrency + timeouts** keep throughput healthy while avoiding vendor throttles. Firecrawl is purpose‑built to **convert pages to Markdown** and handle modern sites (dynamic content, JS, caching). This is why we **plug‑in rather than build**. This was already explained in **L16**, so reference it.
- **Compare to L16 scraper:** Functionally similar to `scrape_and_clean_other_urls` from ingestion; in fact, you could consolidate both into one tool. The main difference: this one reads from a different input file (`urls_to_scrape_from_research.md` vs. `guidelines_filenames.json`) and writes to a different output folder (`urls_from_research/` vs. `urls_from_guidelines/`).

**For your notebook practice:**
- Execute the code cell from Section 5 with your sample research folder
- Observe the returned structure: `{status, urls_processed, urls_total, original_urls_count, deduplicated_count, files_saved, output_directory, saved_files, message}`
- Open `.nova/urls_from_research/` folder and verify the scraped markdown files
- Open a couple saved files to verify **clean, LLM‑ready** Markdown with proper front matter (URL, captured-at timestamp)
- Notice the **deduplication** against guideline URLs to avoid redundant scraping

**Why this matters:** Full scrapes provide **depth** beyond snippet-level summaries, enriching the final research artifact with comprehensive context.

**Section length:** ~280–340 words.

---

## Section 6 — Create the Final `research.md` File

**For the article, copy the following from Notebook Section 6 – "Creating the Final Research File":**

**Subsection 6.1 — Understanding the Compilation Process**

1. **Copy the markdown intro** (the opening paragraph starting with "The `create_research_file_tool` is the final step...")
2. **Copy the entire Subsection 6.1** including:
   - The markdown explanation about what the tool does (combines all research data from multiple sources into comprehensive markdown file)
   - The Python code block showing `def create_research_file_tool(...)` (the full function with docstring, path setup, data collection from multiple folders, section building, file writing, and return statement)
   - The closing prose explaining that no detailed code walkthrough is needed (standard Python file I/O)

**Subsection 6.2 — The Research File Structure**

3. **Copy the entire Subsection 6.2** including:
   - The markdown heading "The final research file `research.md` is organized into collapsible sections..."
   - The markdown code block showing the example structure with all sections (Research Results from Web Search, Scraped Sources from Guidelines, Code Sources, YouTube Transcripts, Additional Research Sources)
   - The closing sentence about comprehensive coverage and navigability

**Subsection 6.3 — Testing the Research File Creation**

4. **Copy the test cell setup and output**:
   - The markdown heading "Now let's test the final compilation tool..."
   - The Python code cell showing the import and call to `create_research_file_tool`
   - The output display showing the result dict and first 1000 characters of `research.md`

**For your notebook practice:**
- Execute the code cell from Section 6 with your sample research folder
- Observe the returned structure: `{status, markdown_file, research_results_count, scraped_sources_count, code_sources_count, youtube_transcripts_count, additional_sources_count, message}`
- Open `research.md` at the root of your research folder
- Verify the file structure: collapsible sections with `<details>` tags, proper markdown formatting
- Note how the **"Query → Source [n]: URL → Answer"** blocks preserve **citations** created upstream via structured outputs
- Verify that content from all sources is present: filtered Perplexity results, guideline sources (web/GitHub/YouTube), and research sources

**Why this matters:** This tool demonstrates **data aggregation** and **structured formatting** that makes research consumable for both humans and downstream AI agents (the writing workflow in **L19–L22**).

**Section length:** ~300–360 words.

---

## Section 7 — Human‑in‑the‑Loop (HITL) Controls via MCP

**For the article, copy the following from Notebook Section 7 – "Human-in-the-Loop Feedback Integration":**

1. **Copy the markdown intro** (the entire paragraph starting with "As we saw in the previous lesson, it's possible to integrate human feedback..." and listing the three HITL examples)
2. **Copy the closing prose** (the paragraph explaining flexibility and noting it's possible because of MCP prompt design)

Then add your own subsection explaining HITL design:

- **Prompt‑level controls:** Because your **workflow recipe** is a **server‑hosted MCP prompt** (**see L16**), you can add instructions like "pause after keep‑selection and show me the IDs" or "after scrape‑selection, display URLs and await my approval" without editing code. Clients (like Cursor) discover and execute these prompts.
- **Where to place gates:** 
    - After **4.1** (show kept source IDs and wait for approval/modifications)
    - After **5.1** (show selected URLs and wait for approval/edits before scraping)
    - Optional gates can go after any tool; just be mindful of latency/cost.
- **No code changes needed:** The **server‑hosted prompt** accepts policy tweaks as plain text, enabling:
    - Adding constraints without modifying the codebase
    - Using the same prompt in different modes (fully autonomous vs. HITL) by different users
    - Reversible changes—just modify the invocation message
    - Example use cases: "Only keep sources from .edu or .gov domains", "Select exactly 3 URLs to scrape", "Show me the final research file before writing it", etc.
    - **→ Transition:** The next section shows you how to run the complete workflow.

**Section length:** ~220–280 words.

---

## Section 8 — Testing the Complete Agent Workflow

**For the article, copy the following from Notebook Section 8 – "Testing the Complete Agent Workflow":**

1. **Copy the markdown intro** (the opening paragraph starting with "Now let's test the complete end-to-end research agent workflow...")
2. **Copy the Python code cell** showing the client initialization:
   - The import statements
   - The `async def run_client()` function
   - The call to `await run_client()`
3. **Copy the extensive LLM output** (the truncated output showing available tools/resources/prompts, LLM reasoning in "Thoughts" sections, and the complete workflow execution including all steps)
4. **Copy the markdown list of instructions** (the cell starting with "Once the client is running, you can:" and listing the 4 numbered steps)

Then add your own subsection with testing guidance:

- **Spin up the MCP client** (in‑memory or stdio), `/prompt/full_research_instructions_prompt`, then provide your `research_directory`. The agent prints **numbered steps**, follows the **critical‑failure policy**, and streams tool results.
- **Test on different article guidelines:** For each, record:
    - Counts of kept sources (from Step 4)
    - URLs selected for deep scrape (from Step 5.1)
    - Files saved from scraping (from Step 5.2)
    - Final `research.md` size and structure (from Step 6)
- **Quality audit checklist:**
    - Kept sources come from **reputable** domains (.edu, .gov, official docs, established news); answers support the **specific** guideline sections.
    - Deep‑scraped content **reduces reliance** on snippet‑level summaries and adds unique insights.
    - `research.md` is **navigable** (collapsible sections), **deduplicated** (no repeated content), and **well‑cited** (thanks to structured outputs from **L17**).
    - Compare **coverage** (do sources span the guideline?), **trust** (domain mix), and **depth** (do deep scrapes add substance?).

**For your notebook practice:**
- Execute the client initialization cell to start the interactive MCP client
- Follow the workflow:
    1. Type `/prompt/full_research_instructions_prompt`
    2. Provide your research folder path: `The research folder is /path/to/research_folder. Run the complete workflow from start to finish.`
    3. Watch the agent execute all 6 steps (or Steps 1-6 if starting fresh)
    4. Observe tool calls and LLM reasoning (shown in "Thoughts" sections)
    5. After completion, explore the `.nova/` folder and `research.md` file
    6. Type `/quit` to exit
- Verify all expected files were created:
    - `.nova/perplexity_sources_selected.md` (selected IDs)
    - `.nova/perplexity_results_selected.md` (filtered content)
    - `.nova/urls_to_scrape_from_research.md` (URLs for deep scrape)
    - `.nova/urls_from_research/` (scraped markdown files)
    - `research.md` (final comprehensive file at root)

**Why prompts on the server?** Any MCP client can discover and run the same recipe, ensuring reproducibility and discoverability (**see L16**).

**Section length:** ~320–400 words.

---

## Section 9 — Use the MCP Server in Cursor

**For the article, copy the following from Notebook Section 9 – "Using Cursor with the MCP Server":**

1. **Copy the markdown intro** (the opening paragraph starting with "Our research agent can also be used directly within Cursor IDE...")
2. **Copy the `.mcp.json.sample` file content** (the full JSON code block showing the MCP server configuration)
3. **Copy the setup instructions** (the numbered list showing how to configure Cursor):
   - The 4 setup steps (open Cursor settings, update mcp.json, save and restart, verify connection)
   - The workflow instructions (open new chat, type `/research-agent`, invoke the prompt, provide research directory and optional HITL instructions)

Then add the remaining subsections:

**Quick troubleshooting & tips**

4. **Copy the troubleshooting section** from the notebook:
   - **Paths:** Ensure the `-directory` path is **absolute** and points to `src/nova/mcp_server`.
   - **Python env:** `uv` must be on your shell `PATH`; run `uv run -m src.server --transport stdio` manually in that folder to smoke-test.
   - **API keys:** Confirm required env vars (e.g., `GOOGLE_API_KEY`, `FIRECRAWL_API_KEY`) are available to the server process.

**Ideas for expanding the research agent**

5. **Copy the expansion ideas** from the notebook:
   - Add a **domain whitelist/blacklist** control to the keep‑selector.
   - Add a **fact‑checking** or **quote‑extraction** tool post‑scrape.
   - Add a **deduplication** tool to cluster near‑duplicate paragraphs across sources.
   - Add a **cost report** tool that tallies API calls + scrape counts per run.

**For your practice:**
- Follow the setup instructions to configure Cursor with your MCP server
- Test the workflow in Cursor with different article guidelines
- Experiment with HITL instructions (pause after keep-selection, pause after scrape-selection, etc.)
- Verify that the same workflow works identically in both the notebook client and Cursor

**Why Cursor integration matters:** It demonstrates the **portability** of MCP-based agents—the same tools/prompts work across any MCP client without code changes.

**Section length:** ~280–340 words.

## Section 10 — Conclusion

**For the article, write your own conclusion following this structure:**

- **What you built:** A **production-minded research agent** that (1) **filters** Perplexity results for trustworthiness and relevance, (2) **selects** high-value URLs for full scraping, (3) **scrapes** those URLs with Firecrawl + LLM cleaning, and (4) **compiles** everything into a single, well-cited `research.md`. Optional **HITL gates** make it **controllable**; a **file-first** design makes it **auditable** and **portable** across MCP clients.
    - **→ Transition:** Tie this to production concerns.

- **Why it matters:**
    - **Quality control:** Automated filtering removes SEO spam and low-trust sources before they pollute the final artifact.
    - **Resource optimization:** Selective deep scraping focuses budget on high-leverage content that adds unique value.
    - **Auditability:** All artifacts persist in `.nova/` with clear provenance; `research.md` preserves citations created via structured outputs.
    - **Interoperability:** Because the **prompt lives on the server** (**see L16 or L15**), any MCP client can run the same recipe—Cursor, Claude Desktop, custom clients, etc.
    - **Human oversight:** HITL gates at steps 4.1 and 5.1 let you review kept sources and scrape selections before spending API credits.
    - **Complete workflow:** You now have a **start-to-finish research pipeline**: ingest sources (**L17**) → run research rounds (**L18**) → filter/scrape/compile (**L19**).
    - **→ Transition:** What's next?

- To transition from this lesson to the next, specify what we will learn in future lessons. First mention what we will learn in next lesson, which is Lesson <x>. Next leverage the concepts listed in subsection `Concepts That Will Be Introduced in Future Lessons` to make slight references to other topics we will learn during this course. To stay focused, specify only the ones that are present in this current lesson.

**Section length:** ~300–380 words.

---

## Article Code

Links to code used in this lesson (always prioritize this notebook):

1. **Notebook — L19 Final Outputs & Agent Completion**
   "/Users/fabio/Desktop/course-ai-agents/lessons/19_final_outputs/notebook.ipynb"

---

## Sources

1. **Model Context Protocol — Prompts** (server‑hosted, discoverable workflows). ([Model Context Protocol](https://modelcontextprotocol.io/docs/concepts/prompts?utm_source=chatgpt.com))
2. **Model Context Protocol — Tools** (exposing executable actions). ([Model Context Protocol](https://modelcontextprotocol.io/docs/concepts/tools?utm_source=chatgpt.com))
3. **Perplexity — Structured Outputs** (JSON Schema & regex). ([Perplexity](https://docs.perplexity.ai/guides/structured-outputs?utm_source=chatgpt.com))
4. **Firecrawl — Scrape to Markdown** (product & API). ([Firecrawl Docs](https://docs.firecrawl.dev/features/scrape?utm_source=chatgpt.com))
5. **Cursor — MCP integration** (how prompts/tools appear in Cursor; configuration guidance). ([Cursor](https://cursor.com/docs/context/mcp?utm_source=chatgpt.com))
6. **OpenAI Agents SDK — MCP explainer** (analogy & context; optional). ([OpenAI GitHub Pages](https://openai.github.io/openai-agents-python/mcp/?utm_source=chatgpt.com))
7. **Google AI — Gemini Video Understanding** (for YouTube transcription capability; context from L17/L16). ([Google AI for Developers](https://ai.google.dev/gemini-api/docs/video-understanding?utm_source=chatgpt.com))
8. **Firecrawl — Advanced Scraping Guide** (code examples). ([Firecrawl Docs](https://docs.firecrawl.dev/advanced-scraping-guide?utm_source=chatgpt.com))
9. **gitingest — LLM‑ready repo digests** (site). ([gitingest.com](https://gitingest.com/?utm_source=chatgpt.com))
10. **FastMCP — MCP JSON configuration** (background for .mcp.json usage across clients). ([FastMCP](https://gofastmcp.com/integrations/mcp-json-configuration?utm_source=chatgpt.com))

---