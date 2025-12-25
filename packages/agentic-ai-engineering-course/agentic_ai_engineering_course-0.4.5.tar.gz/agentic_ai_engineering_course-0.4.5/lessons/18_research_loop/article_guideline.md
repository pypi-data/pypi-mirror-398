# Lesson 18 Guideline

## Global Context of the Lesson

### What We Are Planning to Share

Lesson 18 continues Part 2B by **building the research loop** of our MCP‑based research agent and **executing Step 3** of the server‑hosted workflow. You will:

- Implement a **query generation** MCP tool that analyzes article guidelines, past research, and scraped context to identify knowledge gaps and propose targeted web-search questions with reasoning.
- Add a **Perplexity research** MCP tool that executes queries concurrently, uses **structured outputs** to return cited answers, and appends results to a persistent file for auditability.
- Run the **three-round research loop** as encoded in the MCP prompt, where each round generates new queries and fetches fresh information.
- Add **human-in-the-loop (HITL) feedback gates** by modifying the server-hosted MCP prompt invocation so the agent pauses after generating queries and waits for your approval before running Perplexity.
- Understand the **iterative design process** behind the research loop: how we experimented with query generation, structured outputs, and workflow modifications to create a controllable, production-ready system.

> Refer back, don't re‑teach:
> 
> - For **MCP concepts, transports, server/client layout, server-hosted prompts** → **Lesson 16** (sections *MCP in Short*, *How the MCP Server Is Organized*, *The MCP Client*, *Server-Hosted Prompts*).
> - For **ingestion tools (URL extraction, scraping, GitHub, YouTube)** → **Lesson 17** (all sections on data ingestion).
> - For **system design levers (cost/latency/context)** → **Lesson 14** (sections *Inference‑Time Scaling*, *Context Strategy*).
> - For **structured outputs** → **Lesson 4** (Part 1).

### Why We Think It's Valuable

A research agent lives or dies by the **quality and targeting** of its queries. Students will learn a repeatable, production-minded **research loop**: generate gap-filling queries, fetch **cited** answers via Perplexity, and add **human approval** where it matters. Along the way they'll practice essentials for AI developers: **plug-don't-build** integration, **structured outputs** for reliable parsing, **long-context** prompting for high-quality queries, **cost/latency** reasoning (rounds, concurrency, request fees), **auditability** via file-first artifacts, and **operational safety** with human oversight. Net result: agents that are **controllable, explainable, and economical**—and a workflow that students can reuse across projects.

### Expected Length of the Lesson

**2,800–3,200 words** (without the titles and references), where we assume that 200–250 words ≈ 1 minute of reading time.

### Theory / Practice Ratio

**30% theory – 70% hands‑on**

---

## Anchoring the Lesson in the Course

### Details About the Course

This piece is part of a broader course on AI agents and LLM workflows. The course consists of 4 parts, each with multiple lessons.

Thus, it's essential to always anchor this piece into the broader course, understanding where the reader is in its journey. You will be careful to consider the following:
- The points of view
- To not reintroduce concepts already taught in the previous lesson.
- To be careful when talking about concepts introduced only in future lessons
- To always reference previous and future lessons when discussing topics outside the piece's scope.

### Lesson Scope

This is **Lesson 18 (Part 2B)** on **The Research Loop with Query Generation, Perplexity Integration, and Human‑in‑the‑Loop Feedback**.

### Point of View

The course is created by a team writing for a single reader, also known as the student. Thus, for voice consistency across the course, we will always use 'we,' 'our,' and 'us' to refer to the team who creates the course, and 'you' or 'your' to address the reader. Avoid singular first person and don't use 'we' to refer to the student.

Examples of correct point of view:
- Instead of "Before we can choose between workflows and agents, we need a clear understanding of what they are." word it as "To choose between workflows and agents, you need a clear understanding of what they are."

### Who Is the Intended Audience

Aspiring AI engineers learning to **extend an MCP research agent with intelligent query generation, web research via Perplexity, structured outputs, and human‑in‑the‑loop gates**.

### Concepts Introduced in Previous Lessons

In previous lessons of the course, we introduced the following concepts:

**Part 1:** Workflows vs. agents, context engineering, structured outputs, tools/function calling, planning/reasoning (ReAct), RAG, memory, multimodal.

**Part 2A & 2B (before L18):**

- **L12**—Capstone scope (research agent + writing workflow split)
- **L13**—Frameworks comparison (why FastMCP for research; LangGraph for writing)
- **L14**—System‑design decision framework (models, cost/latency/context budgets, HITL policy)
- **L16 — MCP foundations**: server/client; **tools/resources/prompts**; server-hosted prompts; discovery; thin orchestration over heavy tools.
- **L17 — Ingestion**: URL extraction (`extract_guidelines_urls`), local file processing, scraping/cleaning (`scrape_and_clean_other_urls`), GitHub ingestion (`process_github_urls`), YouTube transcription (`transcribe_youtube_urls`), file‑first design, and critical‑failure policy.

### Concepts That Will Be Introduced in Future Lessons

- **Part 2:**
    - **L19:** Final outputs—curation, deep scrapes, and assembling `research.md`.
    - **L20–L23:** Implement the **LangGraph** writing workflow (stages, reflection loops, HITL).
- **Part 3:** Evaluation, observability, optimization, deployment.
- **Part 4:** Your capstone project.

### Anchoring the Reader in the Educational Journey

Within the course we are teaching the reader multiple topics and concepts. Thus, understanding where the reader is in their educational journey is critical for this piece. You have to use only previously introduced concepts, while being reluctant about using concepts that haven't been introduced yet.

When discussing the **concepts introduced in previous lessons** listed in the `Concepts Introduced in Previous Lessons` section, avoid reintroducing them to the reader. Especially don't reintroduce the acronyms. Use them as if the reader already knows what they are.

Avoid using all the **concepts that haven't been introduced in previous lessons** listed in the `Concepts That Will Be Introduced in Future Lessons` subsection. Whenever another concept requires references to these banned concepts, instead of directly using them, use intuitive analogies or explanations that are more general and easier to understand, as you would explain them to a 7-year-old. For example:
- If the "tools" concept wasn't introduced yet and you have to talk about agents, refer to them as "actions".
- If the "routing" concept wasn't introduced yet and you have to talk about it, refer to it as "guiding the workflow between multiple decisions".

You can use the concepts that haven't been introduced in previous lessons listed in the `Concepts That Will Be Introduced in Future Lessons` subsection only if we explicitly specify them. Still, even in that case, as the reader doesn't know how that concept works, you are only allowed to use the term, while keeping the explanation extremely high-level and intuitive, as if you were explaining it to a 7-year-old.

Whenever you use a concept from the `Concepts That Will Be Introduced in Future Lessons` subsection, explicitly specify in what lesson it will be explained in more detail, leveraging the particulars from the subsection. If not explicitly specified in the subsection, simply state that we will cover it in future lessons without providing a concrete lesson number.

In all use cases avoid using acronyms that aren't explicitly stated in the guidelines. Rather use other more accessible synonyms or descriptions that are easier to understand by non-experts.

---

## Narrative Flow of the Lesson

Follow the next narrative flow when writing the end‑to‑end lesson:

- What problem are we learning to solve? Why is it essential to solve it?
    - Start with a personal story where we encountered the problem
- Why other solutions are not working and what's wrong with them.
- At a theoretical level, explain our solution or transformation. Highlight:
    - The theoretical foundations.
    - Why is it better than other solutions?
    - What tools or algorithms can we use?
- Provide some hands-on examples.
- Go deeper into the advanced theory.
- Provide a more complex example supporting the advanced theory.
- Connect our solution to the bigger field of AI Engineering. Add course next steps.

---

## Lesson Outline

1. **Section 1 — Introduction**
2. **Section 2 — Understanding the Research Loop**
3. **Section 3 — Why We Use Perplexity (The Philosophy)**
4. **Section 4 — Query Generation: The Brain of the Research Loop**
5. **Section 5 — Perplexity Integration: Concurrent Execution and Structured Outputs**
6. **Section 6 — Testing the Tools Programmatically**
7. **Section 7 — Human-in-the-Loop: Adding Feedback Gates**
8. **Section 8 — Conclusion: costs, reliability, next steps**

---

## Section 1 — Introduction

**For the article, copy the following from Notebook Section 1 (the introductory markdown cell):**

1. **Opening paragraph** (Notebook cell 1, the markdown introduction starting with "In this lesson, we'll dive deep...")
2. **Learning Objectives** (the bulleted list in the same cell)

Then add your own brief context paragraph:

- **Problem framing:** Open-ended research drifts without a control loop. We need a repeatable way to **detect gaps**, **propose targeted queries**, **fetch cited answers**, and **pause for human approval** before spending more budget.
- **Quick reference to what we've learned in previous lessons:** Take the core ideas of what we've learned in previous lessons from the `Concepts Introduced in Previous Lessons` subsection of the `Anchoring the Lesson in the Course` section.
- **Transition to what we'll learn in this lesson:** After presenting what we learned in the past, make a transition to what we will learn in this lesson. Take the core ideas of the lesson from the `What We Are Planning to Share` subsection and highlight the importance and existence of the lesson from the `Why We Think It's Valuable` subsection of the `Global Context of the Lesson` section.

**Section length:** ~220–260 words

---

## Section 2 — Understanding the Research Loop

**For the article, copy the following from Notebook Section 2 – "Understanding the Research Loop":**

1. **Markdown intro** (the opening paragraph explaining the research loop's role)
2. **The MCP prompt excerpt** (the full markdown code block showing the 3-round research loop with steps 3.1 and 3.2)

Then add your own subsection explaining the workflow structure:

- **Open the server‑hosted MCP prompt** (stored in `mcp_server/src/prompts/research_instructions_prompt.py` and shown in Notebook Section 2). Read **Step 3** verbatim.
    - *Comment:* Notice the **file‑first** pattern—overwrite `next_queries.md` each round, but **append** Perplexity results.
    - **Critical‑failure policy (recap from L17):** If any Step-2 tool reports **0/N successes** (e.g., scraped 0/N URLs when URLs were expected), the prompt instructs the agent to **halt and ask for guidance** before entering Step 3.
    - **→ Transition:** Now explain the "why Perplexity" choice.

**Section length:** ~220–260 words

---

## Section 3 — Why We Use Perplexity (The Philosophy)

**For the article, copy the following from Notebook Section 3 – "The Philosophy: Plugging Into Specialized Services":**

1. **Markdown intro** (the opening paragraph starting with "Before diving into the implementation...")
2. **The "Why use external services like Perplexity?" heading and explanation** (the full paragraph explaining Perplexity's role)
3. **The bulleted list** (comprehensive source coverage, real-time information retrieval, advanced ranking, dynamic content handling, rate limiting)
4. **Closing sentence** (about focusing on unique elements: query generation, human feedback integration, workflow orchestration)

Then add a brief subsection on the technical benefits:

- **Structured outputs (high‑level):** We request responses as **objects** (URL + answer text), which our code turns into normalized markdown (**see L4** for structured outputs primer).
- **Async/concurrency:** The Perplexity tool runs multiple queries simultaneously to keep the loop fast; results are appended to a single file for auditability.
    - **→ Transition:** With the "why" established, step into **how we generate questions** and route them through Perplexity.

**Section length:** ~220–260 words

---

## Section 4 — Query Generation: The Brain of the Research Loop

**For the article, copy the following from Notebook Section 4 – "Query Generation: The Brain of the Research Loop":**

1. **Markdown intro** (the opening sentence starting with "The `generate_next_queries` tool is where the magic happens...")

**Subsection 4.1 — Understanding the Implementation**

2. **Copy the entire Subsection 4.1** including:
   - The markdown explanation about the core implementation
   - The Python code block from Cell showing `async def generate_next_queries_tool(...)` (the full function with docstring, path setup, context gathering, LLM call, file writing, and return statement)
   - The explanatory prose following the code (explaining the three types of context: Article Guidelines, Past Research, Scraped Content)
   - The paragraph explaining how the LLM analyzes all three contexts simultaneously

**Subsection 4.2 — The LLM-Powered Query Generation**

3. **Copy the entire Subsection 4.2** including:
   - The markdown introduction explaining the `generate_queries_with_reasons` function
   - The Python code block showing `async def generate_queries_with_reasons(...)` (the full function)
   - The prompt code block showing `PROMPT_GENERATE_QUERIES_AND_REASONS` (the full prompt template)
   - The explanatory prose about the prompt's instructions
   - The Pydantic models code block showing `QueryAndReason` and `GeneratedQueries`
   - The closing prose explaining justifications (dual purpose: helping LLM reasoning, aiding debugging/HITL)

**Subsection 4.3 — Testing Query Generation**

4. **Copy the test cell setup and explanation**:
   - The markdown heading "Let's test the `generate_queries_with_reasons` function to see how it works in practice:"
   - The Python code cell showing the test (Cells with example inputs and the call to `generate_queries_with_reasons`)
   - The markdown cell titled "**Understanding the Output**" with the entire explanation of what to observe (Gap Analysis, Section Mapping, Query Quality, Reasoning Transparency, Progressive Complexity)

**For your notebook practice:**
- Execute the code cells from Section 4 in sequence with your sample research folder
- Understand the three contexts being analyzed: article guidelines, past research, scraped content
- Observe the generated queries and their reasons—notice how they target knowledge gaps
- Verify that the queries are stored in `.nova/next_queries.md` (overwritten each round)

**Why this matters:** This tool exemplifies **long-context prompting** (can reach ~100k tokens), **structured outputs** for reliable parsing, and **reasoning transparency** for HITL feedback.

**Section length:** ~520–620 words

---

## Section 5 — Perplexity Integration: Concurrent Execution and Structured Outputs

**For the article, copy the following from Notebook Section 5 – "Perplexity Integration":**

**Subsection 5.1 — The Research Tool Implementation**

1. **Copy the entire Subsection 5.1** including:
   - The markdown introduction explaining that the tool is the orchestrator
   - The Python code block showing `async def run_perplexity_research_tool(...)` (the full function with docstring, path setup, empty query handling, concurrent execution with `asyncio.gather`, result processing, and return statement)
   - The markdown section titled "**How this function works:**" with the numbered explanation (Path Setup, Concurrent Execution, Result Processing, Cumulative Storage)
   - The closing sentence about fast execution and audit trail

**Subsection 5.2 — Structured Perplexity Responses**

2. **Copy the entire Subsection 5.2** including:
   - The markdown introduction starting with "The core Perplexity integration uses structured outputs..."
   - The Python code block showing the Pydantic models (`SourceAnswer`, `PerplexityResponse`) and the `async def run_perplexity_search(...)` function
   - The markdown section titled "When you run a Perplexity search as above..." with the example output showing `full_answer`, `answer_by_source`, and `citations` dictionaries
   - The closing prose explaining what the structured format ensures (bullet points)

**Subsection 5.3 — The Perplexity Search Prompt**

3. **Copy the entire Subsection 5.3** including:
   - The markdown introduction about the prompt design
   - The Python code block showing `PROMPT_WEB_SEARCH` (the full prompt template)
   - The closing sentence about what the prompt ensures

**For your notebook practice:**
- Do NOT implement these tools yourself; the implementation is in the codebase (referenced in the notebook)
- Understand the **concurrent execution** pattern: `asyncio.gather(*tasks)` runs all queries in parallel
- Observe the **structured outputs**: Pydantic models ensure consistent `{url, answer}` format
- Note the **append-only file** pattern: results from each round build up in `perplexity_results.md`
- Understand the **prompt design**: up to 300 words per source, single source per section, focus on official sources

**Why structured outputs?** They ensure reliable parsing, enable downstream processing, and maintain citations for auditability (**see L4** for structured outputs deep-dive).

**Section length:** ~420–520 words

---

## Section 6 — Testing the Tools Programmatically

**For the article, copy the following from Notebook Section 6 – "Testing the tools":**

**Subsection 6.1 — Testing the Query Generation Tool**

1. **Copy the markdown heading and introduction** ("Let's test the query generation tool programmatically...")
2. **Copy the Python code cell** (Cell showing the import and call to `generate_next_queries_tool`)
3. **Copy the markdown explanation of the output** (the cell showing the expected JSON structure with example queries and reasons)

**Subsection 6.2 — Testing the Perplexity Research Tool**

4. **Copy the markdown heading and introduction** ("Now let's test the Perplexity research functionality:")
5. **Copy the Python code cell** (Cell showing the import of `run_perplexity_research_tool`, test queries definition, and the call with results printing)
6. **Copy the markdown explanation of the output** (Cell showing "Tool call output:" and "Content of the resulting file:" with example Perplexity results in the structured format)

**For your notebook practice:**
- Execute Cell with `generate_next_queries_tool`—update the `research_folder` path to your actual sample folder
- Observe the tool's return: `{status, queries_count, queries, output_path, message}`
- Execute Cell with `run_perplexity_research_tool` with 2-3 test queries
- Observe the tool's return: `{status, queries_processed, sources_added, output_path, message}`
- Open `.nova/perplexity_results.md` and verify the structured format: `### Source [n]: <url>`, `Query: ...`, `Answer: ...`, `-----`
- Notice how citations are preserved and answers are substantial (~up to 300 words)

**Why test programmatically?** It helps you understand the tool contracts before seeing them in the full agent workflow.

**Section length:** ~240–300 words

---

## Section 7 — Human-in-the-Loop: Adding Feedback Gates

**For the article, copy the following from Notebook Section 7 – "Human-in-the-Loop":**

1. **Markdown intro** (the opening paragraph starting with "One of the most powerful aspects...")

**Subsection 7.1 — How Human Feedback Works**

2. **Copy the entire Subsection 7.1** including:
   - The markdown explanation of how the agent pauses after generating queries
   - The bulleted examples of modification instructions ("Ask for my feedback after...", "Show me the proposed queries...", "Let me select which queries...")
   - The markdown sentence "Let's see how to run the complete research agent..."

3. **Copy the Python code cell** (Cell showing the client initialization code: `from research_agent_part_2.mcp_client.src.client import main as client_main` and the `async def run_client()` function with the call to `await run_client()`)

4. **Copy the truncated LLM output** (the extensive output showing available tools/resources/prompts, LLM reasoning in "Thoughts" sections, and the agent's step-by-step execution of the workflow including:
   - Initial workflow explanation
   - Steps 1-2 execution (URL extraction, local files, scraping, GitHub, YouTube)
   - Step 3.1 execution (query generation)
   - Agent pausing and displaying queries with reasons
   - Waiting for approval
   - Step 3.2 execution (Perplexity research) after approval
   - Second round of query generation and approval cycle

5. **Copy the markdown list of commands** (the cell explaining "Once the client is running, try these commands in sequence:" with the numbered steps showing `/prompt/full_research_instructions_prompt`, the message format for providing feedback modifications, observing agent behavior, providing feedback options, and continuing the loop)

Then add your own explanatory subsection:

- **Inject feedback gates by modifying prompt invocation:** When invoking `/prompt/full_research_instructions_prompt`, add policy lines that create a review stop between **3.1** and **3.2**:
    - Example: "**Stop after generating queries each round; show them to me; run Perplexity only on my approved subset; stop the workflow after Step 3.**"
    - *Comment:* No code changes needed; the **server‑hosted prompt** accepts policy tweaks as plain text. This capability of easily editing agentic workflows is very useful because:
        - You can add constraints without modifying the codebase
        - The same prompt can be used in different modes (fully autonomous vs. HITL) by different users
        - Changes are reversible—just modify the invocation message
        - Example use cases: "Only use queries mentioning security", "Generate 10 queries instead of 5", "Skip YouTube processing", etc.

- **Iterative design story:** Explain how we arrived at this design:
    - We started directly with those two steps: generating questions and answering them with Perplexity
    - Then we experimented to find how many rounds of research worked best (3 rounds gave good coverage without excessive cost)
    - Then we changed the output format of the Perplexity search to explicitly list the URLs and their content (related to the article guideline), and we used **structured outputs** (**see L4**) for that
    - Last, we experimented with providing to the agent modifications to the agentic workflow (e.g. asking it to ask for user feedback before running every query), and it worked out of the box

- **Other tests that students could do:**
    - Approve **as‑is** (all queries)
    - **Edit** queries inline (modify the question text)
    - **Select a subset** (e.g., "Only run queries 1, 3, and 5")
    - **Replace queries** (e.g., "Replace query 2 with: [your custom query]")
    - Keep an eye on `.nova/next_queries.md` (overwritten each round) and `.nova/perplexity_results.md` (appended each round) to verify what was proposed vs. what ran

**For your notebook practice:**
- Execute the client initialization cell to start the interactive MCP client
- Follow the workflow:
    1. Type `/prompt/full_research_instructions_prompt`
    2. Provide your research folder path and request HITL modifications (as shown in the notebook)
    3. Watch the agent execute Steps 1-2 (ingestion)
    4. Observe the agent pause after generating queries in Step 3.1
    5. Review the generated queries and their reasons
    6. Approve, modify, or select a subset
    7. Observe the agent run Perplexity with your approved queries
    8. Repeat the cycle for 3 rounds
    9. Type `/quit` to exit
- Verify the `.nova/` folder contents: `next_queries.md` (latest round), `perplexity_results.md` (all rounds cumulative)

**Why HITL matters:** Human oversight ensures **budget control**, **quality assurance**, and **alignment** with research goals before spending on Perplexity API calls.

**Section length:** ~480–600 words

---

## Section 8 — Conclusion: costs, reliability, next steps

**For the article, write your own conclusion following this structure:**

- **What you built:** A controllable **three‑round research loop** that (a) **generates** gap‑filling queries using long-context analysis, (b) **fetches** cited answers via Perplexity with **structured outputs**, and (c) can **pause** for human approval between query generation and execution.
    - **→ Transition:** Tie this to production concerns.

- **Why it matters:**
    - **Reliability:** Structured outputs + normalized markdown → easier parsing/audits in later lessons.
    - **Cost awareness:** A single file aggregates results; three rounds limit drift and help you reason about spend. Check the Perplexity pricing page (see Sources) and use your actual token counts for accurate estimates. Example: If each query costs ~$0.02 (Sonar Pro), 5 queries × 3 rounds = $0.30 per article.
    - **Interoperability:** Because the **prompt lives on the server** (**see L16**), any MCP client can run the same recipe—with or without HITL.
    - **Human oversight:** HITL gates prevent budget waste and ensure queries align with research goals before API calls.
    - **Auditability:** All results persist in `.nova/perplexity_results.md` with citations, enabling later review and selection.
    - **→ Transition:** What's next?

- To transition from this lesson to the next, specify what we will learn in future lessons. First mention what we will learn in next lesson, which is Lesson <x>. Next leverage the concepts listed in subsection `Concepts That Will Be Introduced in Future Lessons` to make slight references to other topics we will learn during this course. To stay focused, specify only the ones that are present in this current lesson.

**Section length:** ~300–380 words

---

## Article Code

Links to code used in this lesson (always prioritize this notebook):

1. **Notebook — L18 Research Loop**
   "/Users/fabio/Desktop/course-ai-agents/lessons/18_research_loop/notebook.ipynb"

---

## Sources

1. **Perplexity — Pricing** (token costs, request fee model, examples). ([Perplexity](https://docs.perplexity.ai/getting-started/pricing))
2. **Perplexity — Structured Outputs** (JSON Schema & Regex). ([Perplexity](https://docs.perplexity.ai/guides/structured-outputs?utm_source=chatgpt.com))
3. **Perplexity — Chat Completions (API reference)**. ([Perplexity](https://docs.perplexity.ai/api-reference/chat-completions-post?utm_source=chatgpt.com))
4. **Perplexity — OpenAI Compatibility Guide**. ([Perplexity](https://docs.perplexity.ai/guides/chat-completions-guide?utm_source=chatgpt.com))
5. **Model Context Protocol — Prompts (server‑hosted, discoverable)**. ([Model Context Protocol](https://modelcontextprotocol.io/docs/concepts/prompts?utm_source=chatgpt.com))
6. **Perplexity — Sonar Pro model page** (additional pricing pointers/positioning). ([Perplexity](https://docs.perplexity.ai/getting-started/models/models/sonar-pro?utm_source=chatgpt.com))
7. **Google Cloud — What is MCP?** (high‑level explainer for context). ([Google Cloud](https://cloud.google.com/discover/what-is-model-context-protocol?utm_source=chatgpt.com))
