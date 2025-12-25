# Lesson 17 Guideline

## Global Context of the Lesson

### What We Are Planning to Share

Lesson 17 continues Part 2B by **building the ingestion layer** of our MCP‑based research agent and **executing Steps 1–2** of the server‑hosted workflow. You will:

- Implement a **sources‑extractor** MCP tool that scans an `article_guideline.md` and writes a compact JSON registry used by the rest of the workflow.
    - **Schema keys (normalized)**: `github_urls`, `youtube_videos_urls`, `other_urls`, `local_file_paths`.
- Add a **parallel web scraping** MCP tool that uses **Firecrawl** to return **markdown**, followed by a **brief LLM clean pass** aligned to the guideline so only pertinent content remains.
- Process **local files** (with **Jupyter→Markdown** conversion suited for LLMs), **ingest GitHub repos** (via `gitingest`), and **transcribe YouTube videos** (via Gemini; include a fallback if direct YT URL handling is restricted).
- **Run the agent with the server‑hosted MCP prompt** for **Steps 1–2**, inspect `.nova/` artifacts, and practice **non‑critical vs. critical failure** handling with explicit triggers for each tool.

> Refer back, don’t re‑teach:
> 
> - For **MCP concepts, transports, server/client layout** → **Lesson 16** (sections *MCP in Short*, *How the MCP Server Is Organized*, *The MCP Client*).
> - For **system design levers (cost/latency/context)** → **Lesson 14** (sections *Inference‑Time Scaling*, *Context Strategy*).
> - For **why we split research vs writing** → **Lesson 12**, and **framework trade‑offs** → **Lesson 13**.

### Why We Think It’s Valuable

A research agent lives or dies by the **quality, structure, and cost** of its inputs. Persisting big payloads to files, returning **short tool summaries**, and delegating messy capture to a **specialized scraper** lowers token spend and improves reliability (see **L14** for the cost levers we’re applying here). MCP lets us expose these tools once and drive them from any client; **server‑hosted prompts** make the workflow universally discoverable (see **L16**).

### Expected Length of the Lesson

**3,200–3,600 words** (without the titles and references), where we assume that 200–250 words ≈ 1 minute of reading time.

### Theory / Practice Ratio

**25% theory – 75% hands‑on**

---

## Anchoring the Lesson in the Course

### Details About the Course

This piece sits in **Part 2B: Building our MCP Research Agent**. Keep the point of view consistent (we/us for instructors; you/your for the student). **Don’t re‑teach prior lessons;** when needed, insert explicit references:

- “See **Lesson 16**: MCP server/client, transports, capability discovery.”
- “See **Lesson 14**: cost levers (file‑first outputs, small tool returns).”
- “See **Lesson 12–13**: the agent/workflow split and framework trade‑offs.”

### Lesson Scope

This is **Lesson 17 (Part 2B)** on **Data Ingestion for the MCP Research Agent**—you implement the ingestion tools and run **Steps 1–2** of the server‑hosted workflow to populate `.nova/` artifacts **without** starting the research rounds.

### Point of View

We write as a team (“we/our/us”) addressing a single reader (“you/your”). Avoid singular first‑person and never use “we” to refer to the student.

### Who Is the Intended Audience

Aspiring AI engineers learning how to **equip an MCP agent with production‑minded ingestion tools** that balance **reliability** and **token efficiency**.

### Concepts Introduced in Previous Lessons

- **Part 1:** Workflows vs. agents; context engineering; structured outputs; tool calling; planning/reasoning (ReAct); RAG; memory; multimodal.
- **Part 2A:** **L12** (capstone scope & agent split), **L13** (framework trade‑offs), **L14** (system design levers & cost budgets).
- **Part 2B:** **L16** (MCP primer; FastMCP client/server; server‑hosted prompt; discovery; thin orchestration over heavy tools).

> In this lesson, refer back to these, don’t re‑explain them.
> 

### Concepts That Will Be Introduced in Future Lessons

- **L18–L19:** Research rounds (generate next queries; run Perplexity), curation/selection, deep scrapes, and `research.md`.
- **L20–L23:** LangGraph writing workflow (stages, reflection, HITL).
- **Part 3:** Evaluation, observability, optimization, deployment.

### Anchoring the Reader in the Educational Journey

Assume **MCP primitives** and **ReAct** are known. If you mention Perplexity loop or curation, keep it high‑level and say: “covered in **L18–L19**.” For details on MCP mechanics, say: “See **L16**.”

---

## Narrative Flow of the Lesson

- **The problem we’re solving (Ingestion Debt):**
    
    Real research agents fail not for lack of “reasoning,” but because inputs are **noisy, redundant, and expensive** to pass to models. We need a **file‑first, tool‑light** ingestion layer that converts heterogeneous sources into **LLM‑ready markdown** and returns **short, structured tool summaries**.
    
- **What goes wrong without this design (Five anti‑patterns):**
    - Dumping entire pages into prompts (explodes token costs; see **L14**).
    - Browser‑grade scrapers (HTML noise, dynamic sites break).
    - Returning full content from tools (bloats context; hard to retry).
    - Inconsistent file naming/paths (collisions; hard to audit).
- **Our approach (MCP + file‑first artifacts):**
    - **MCP server‑hosted prompt** (discoverable recipe; see **L16**).
    - Specialized tools: **extract → process local → scrape & clean → GitHub ingest → YT transcribe**.
    - Each tool **persists artifacts** and returns a **compact `{status, counts, output_path, message}`**.
- **Walkthrough of Steps 1–2 (hands‑on):**
    - Run the server‑hosted prompt for **Steps 1–2** only.
    - Inspect `.nova/` folders; confirm counts match actual files.
    - Observe **concurrency**, **timeouts**, **retries**, and **cache**.
- **Advanced considerations you apply today (not just theory):**
    - **Clean‑pass constraints**: “remove irrelevancies, **don’t summarize**,” keep content traceable to source.
    - **Front‑matter metadata** in saved markdown (URL, captured‑at, tool version) for auditability.
    - **Critical vs non‑critical** failure policy for each tool, with concrete triggers.
- **Worked example (multi‑source guideline):**
    
    A guideline cites a GitHub repo, 2 web pages, 1 notebook, and a YouTube talk. Show the extractor’s JSON, the four tool results, and the finalized `.nova/` tree; call out a failure (e.g., one page blocked) and how the critical policy responds.
    
- **Zoom out (how this unlocks L18–L19):**
    
    Clean, deduped, on‑disk artifacts reduce **context cost** and enable reliable **Perplexity rounds** and **deep scrapes** later. See **L18–L19** for the research loop.
    

---

## Lesson Outline

1. **From MCP Setup to Ingestion: the Plan**
2. **Workflow & Endpoints: where the ingestion tools live**
3. **Tool to extract URLs & local references from the guideline**
4. **Tool to organize local files for LLMs (incl. Jupyter→Markdown)**
5. **Tool to scrape & clean web pages in parallel**
6. **Tool to ingest content from GitHub**
7. **Tool to transcribe and structure YouTube videos**
8. **Run Steps 1–2 end‑to‑end: inspect `.nova/`, handle failures, and wrap‑up**

---

## Section 1 — From MCP Setup to Ingestion: the Plan

- **Assume L16 is done**: you have a running MCP server and client; you know **in‑memory** and **stdio** transports, and how to list tools/resources/prompts. If you need the refresher, **see L16**.
- **Why ingestion first**: We're cementing a **file‑first contract** that future steps read selectively (see **L14** for cost heuristics).
- **Notebook mapping**: 
    - Follow **Notebook Section 1 – "Setup"** cell by cell. This section covers API key configuration (Gemini, Firecrawl, optional GitHub) and initial environment setup. Copy the cells as-is with minimal adjustments to your paths and API keys.
    - Follow **Notebook Section 2 – "Understanding the Research Agent Workflow"** to see the MCP prompt excerpt that defines Steps 1–2. Copy the content as-is (it's illustrative; don't modify the prompt structure).
- **Return policy**: Tools return **short dicts** and **write heavy content to files** for token efficiency.

---

## Section 2 — Workflow & Endpoints: where the ingestion tools live

**For the article, copy the following from Notebook Section 2 – "Understanding the Research Agent Workflow" with minimal edits:**

1. **Markdown intro** (the opening paragraph explaining the two-phase approach)
2. **The MCP prompt excerpt** (the full markdown code block defining Steps 1.1–2.4 with all the details about URL categories, file extensions, and tool names)
3. **Explanatory prose** following the prompt

Then add your own subsection that **explicitly references the MCP tool registration** in the code:

- **Open the repo** to locate the server‑hosted prompt and tool routers.
- In `mcp_server/src/routers/tools.py`, verify registration for **five ingestion endpoints** used in Steps **1–2**:
    
    `extract_guidelines_urls`, `process_local_files`, `scrape_and_clean_other_urls`, `process_github_urls`, `transcribe_youtube_urls`.
    
- **Copy the tool registration code block** from Notebook Cell 9 (the Python code showing `def register_mcp_tools(...)` with all five tool definitions). Include all the docstrings and function signatures as-is.
- The **server‑hosted prompt** (`mcp_server/src/prompts/research_instructions_prompt.py`) enumerates **Steps 1–6** and the **critical‑stop policy**.
- **Short returns only**: `{status, counts, output_path, message}`—not full content.

**Add an additional subsection** explaining the design rationale:

- **Copy the prose from Notebook Cell 10** (the markdown explanation about token efficiency, context management, selective reading, and error handling) as-is into the article.

> Reference cue: For MCP primitives and discovery, see L16. 

---

## Section 3 — Tool to extract URLs & local references from the guideline

**For the article, copy the following from Notebook Section 3 – "Extracting URLs from Guidelines":**

1. **Markdown intro** (the opening paragraphs explaining the tool goal and its role in the pipeline)
2. **Subsection 3.1 – "URLs Extraction"**: Copy the **entire subsection** including:
   - The markdown explanation
   - The source code block showing `def extract_urls(...)`
   - The explanation of the regex pattern
3. **Subsection 3.2 – "Local File Path Extraction"**: Copy the **entire subsection** including:
   - The markdown explanation of the `extract_local_paths` function
   - The key behaviors (extension constraints, URL exclusion)
4. **Subsection 3.3 – "Running the Tool"**: Copy the **entire subsection** including:
   - The markdown instruction to test the tool
   - The Python code cell importing and calling `extract_guidelines_urls_tool`
   - The printed output example
5. **Output structure prose** (Cell 16): Copy the markdown code block showing the expected JSON output structure
6. **Closing explanation** (Cell 17): Copy the closing explanation about agent decision-making

**For your notebook practice:**
- Execute all code cells from Section 3 in sequence with your sample research folder to verify the tool works and observe actual output.

**Why this matters**: This tool **seeds Step 2** and enforces a **stable on‑disk contract**. It exemplifies the **file‑first + short output** design principle.

---

## Section 4 — Tool to organize local files for LLMs (incl. Jupyter→Markdown)

**For the article, copy the following from Notebook Section 4 – "Processing Local Files":**

1. **Markdown intro** (the opening paragraphs explaining the tool goal and why Jupyter→Markdown conversion matters)
2. **Tool implementation code block** (Cell 18): Copy the **full Python code block** showing `def process_local_files_tool(...)` with:
   - Complete function signature and docstring
   - All logic for loading JSON metadata, creating destination folders, handling `.ipynb` conversion
   - The full return statement with all keys (`status`, `files_processed`, `files_total`, `processed_files`, `warnings`, `errors`, `output_directory`, `message`)
3. **Explanatory prose** (the text explaining what the code does step-by-step)
4. **Note about NotebookToMarkdownConverter** (the paragraph explaining that this class handles notebook conversion and keeping outputs)

**For your notebook practice:**
- Do NOT implement this tool yourself; the code shown in the notebook is what should go into the article.
- Execute Cell 18 to verify the tool works (if local files are referenced in your guidelines).
- Key behaviors to understand: loads `guidelines_filenames.json`, creates destination folder, converts `.ipynb` to **LLM‑friendly markdown** using `NotebookToMarkdownConverter` (keeps code + outputs, truncates very long outputs).
- **Edge behavior**: If 0 local files, the tool returns `status="success"` with 0 counts (**non‑critical**). This allows the agent to continue to the other Step‑2 sub‑steps.

**Why markdown**: predictable structure, selective reads, lower token waste (**see L14**).

---

## Section 5 — Tool to scrape & clean web pages in parallel

**For the article, copy the following from Notebook Section 5 – "Web Scraping with Firecrawl and LLM Cleaning":**

1. **Markdown intro** (the opening paragraphs explaining the tool goal and the two-stage approach)
2. **Tool implementation code block** (Cell 19): Copy the **full Python code block** showing `async def scrape_and_clean_other_urls_tool(...)` with:
   - Complete function signature and docstring
   - All logic for reading `GUIDELINES_FILENAMES_FILE`, handling empty URL lists, scraping concurrently, and returning results
   - The full return statement with all keys
3. **Subsection 5.1 – "The Two-Stage Cleaning Process"**: Copy the **entire subsection** including:
   - The markdown explanation of the two stages
   - The `async def scrape_url(...)` code block (Cell 21) with comments about Firecrawl, retries, timeouts, and `maxAge` parameter
   - The `async def clean_markdown(...)` code block (Cell 22) with full error handling
   - The `PROMPT_CLEAN_MARKDOWN` template (the full markdown block showing the LLM cleaning instructions)
   - The prose explaining the cleaning process and token efficiency gains
4. **Subsection 5.2 – "Why Use External Scraping Services?"**: Copy the **entire subsection** including all the markdown explanation of web scraping complexity and benefits

**For your notebook practice:**
- Execute all code cells from Section 5 in sequence with your sample research folder
- Understand the **`concurrency_limit`** argument (recommend 4 for stability under vendor load) in the tool calls
- Observe the returned structure: `status`, `urls_processed` vs `urls_failed`, `successful_urls_count`, `failed_urls_count`, `output_directory`, `message`
- Execute the test cell (Cell 25) that runs `scrape_and_clean_other_urls_tool` and observe the actual output dict structure

---

## Section 6 — Tool to ingest content from GitHub

**For the article, copy the following from Notebook Section 6 – "Processing GitHub URLs":**

1. **Markdown intro** (the opening paragraphs explaining why code repos need a specialized tool)
2. **Tool explanation prose** (Cell 27): Copy the paragraph explaining `process_github_urls_tool` and the **`gitingest`** library. Include:
   - The explanation of what gitingest does (fetch repository structure and content optimized for LLMs)
   - The note about public and private repo support with token usage
   - The note that you won't show the code here but can check how it works in the codebase
3. **Test execution guidance** (Cell 28): Copy the code cell showing the test call to `process_github_urls_tool` with comments about public repositories
4. **Output explanation** (Cell 29): Copy the prose explaining the result and where to find the extracted information

**For your notebook practice:**
- Do NOT implement this tool yourself; the implementation is in the codebase (referenced in the notebook).
- Execute Cell 28 to verify the tool works with a sample GitHub URL
- Understand the return structure: `{status, urls_processed, urls_total, files_saved, output_directory, message}`
- Observe the actual output dict structure

**Why a repo‑specific tool?** Repos require different heuristics (trees, code, notebooks); gitingest standardizes this into a digest.

---

## Section 7 — Tool to transcribe and structure YouTube videos

**For the article, copy the following from Notebook Section 7 – "YouTube Video Transcription":**

1. **Markdown intro** (the opening paragraphs explaining the tool goal and why videos add valuable context)
2. **Tool explanation prose** (Cell 30): Copy the paragraph explaining `transcribe_youtube_videos_tool` and the helper function. Include:
   - The explanation of Gemini's multimodal video understanding capabilities
3. **Core implementation code block** (Cell 30, second code block): Copy the **full Python code block** showing `async def transcribe_youtube(...)` with:
   - Complete function signature and docstring
   - All logic including client initialization, prompt formatting, parts construction with `types.Part(file_data=types.FileData(file_uri=url))`
   - The API call to `generate_content` with proper error handling
   - The output file writing
4. **Documentation reference**: Copy the prose explaining Gemini's video transcription capability and the link to the documentation
5. **Test execution guidance** (Cell 31): Copy the code cell showing the test call to `transcribe_youtube_videos_tool` with comments about time-intensive processing
6. **Output explanation** (Cell 32): Copy the prose explaining the result, the time estimate for processing, and the note about concurrency

**For your notebook practice:**
- Do NOT implement this tool yourself; the implementation is in the codebase (referenced in the notebook).
- Execute Cell 31 to verify the tool works (note: this is time-consuming, especially for long videos)
- Understand the return structure: `{status, videos_processed, videos_total, output_directory, message}`
- Observe the actual output dict structure
- **Concurrency note**: Keep concurrency conservative to respect API quotas (see the code comments for the knob)
- **Time estimate**: A 39-minute video typically takes ~4.5 minutes to process

---

## Section 8 — Run Steps 1–2 end‑to‑end: inspect `.nova/`, handle failures, and wrap‑up

**For the article, copy the following from Notebook Section 8 – "Running the Full Agent with MCP Prompt":**

1. **Markdown intro** (Cell 33): Copy the opening paragraphs explaining that the tools are now ready and what the reader can do next
2. **Instructions for running the client** (Cell 33, continued): Copy the numbered list of steps:
   - Start the workflow
   - Answer the agent
   - Watch the agent work
   - Examine outputs
3. **Try these commands in sequence** (Cell 33, end): Copy the inline list showing:
   - `/prompt/full_research_instructions_prompt`
   - The message format for providing the research folder path and asking to run Steps 1–2
   - `/quit` to exit
4. **Client initialization code** (Cell 34): Copy the **full Python code block** showing the async function to start the in-memory MCP client
5. **Sample output** (Cell 34, output): Copy the truncated LLM output showing:
   - Available tools/resources/prompts
   - LLM reasoning (the "Thoughts" section)
   - LLM response explaining the numbered workflow steps
6. **Explanation of observed behavior** (Cell 35): Copy the prose explaining what to notice in the output (skipped tools, agent reasoning, final message)
7. **Artifact exploration** (from Notebook Section 9 – "Exploring Generated Files"): Copy the full section including:
   - The markdown intro explaining the file structure
   - The directory tree diagram showing `.nova/` folder contents
   - The explanatory prose about file persistence, context management, selective access, and auditability
   - The note about database alternatives in production

**For your notebook practice:**
- Execute the cells in order, starting with the client initialization
- Follow the interactive workflow: type the prompt command, provide your research folder path, instruct the agent to run Steps 1–2 only
- Observe the agent's tool calls and LLM reasoning (shown in "Thoughts" section)
- After completion, explore the `.nova/` folder structure to verify all expected files were created
- Exit with `/quit`

**Why prompts on the server?** Any MCP client can discover and run the same recipe, ensuring reproducibility and discoverability.

---

### Critical vs. Non‑critical Failure Policy (reference for understanding the agent behavior)

The article should include an explanation of how the workflow handles failures. Reference the following concrete triggers for Steps 1–2 so readers understand the agent's decision-making:

- **extract_guidelines_urls**
    - **Critical**: `article_guideline.md` missing or unreadable → stop and ask for a valid path.
    - **Non‑critical**: any category count is 0 (pipeline continues).
- **process_local_files**
    - **Critical**: destination write failures across all files (e.g., permission issues).
    - **Non‑critical**: 0 files to process; individual file errors (record in `warnings`/`errors`).
- **scrape_and_clean_other_urls**
    - If `other_urls > 0` **and** `urls_processed == 0` → **Critical stop**.
    - If `other_urls == 0` → **Non‑critical** (skip).
- **process_github_urls**
    - If `github_urls > 0` **and** `urls_processed == 0` → **Critical stop**.
    - If `github_urls == 0` → **Non‑critical** (skip).
- **transcribe_youtube_urls**
    - If `youtube_videos_urls > 0` **and** `videos_processed == 0` → **Critical stop**.
    - If `youtube_videos_urls == 0` → **Non‑critical** (skip).
- **Token efficiency:** keep heavy text out of the LLM’s context; the agent sees **short summaries + file paths**, and reads only what it needs later.
- **Auditability:** artifacts persist; easy to diff and debug.

---

## Article Code

Links to code used in this lesson (always prioritize this notebook):

1. **Notebook — L17 Data Ingestion**
    "/Users/omar/Documents/ai_repos/agentic-ai-engineering-course/lessons/17_data_ingestion/notebook.ipynb"

---

## Sources

0. Local files to use during research and writing:
    - [NOVA_SYSTEM_DESIGN]("/Users/omar/Documents/ai_repos/agentic-ai-engineering-course/lessons/14_agent_system_design/nova_system_design_notes.md")
1. **MCP — Tools** (server‑exposed actions & schemas). ([Model Context Protocol](https://modelcontextprotocol.io/docs/concepts/tools))
2. **MCP — Prompts** (server‑hosted, discoverable workflow recipes). ([Model Context Protocol](https://modelcontextprotocol.io/docs/concepts/prompts))
3. **MCP — Resources** (read‑only data exposed by servers). ([Model Context Protocol](https://modelcontextprotocol.io/docs/concepts/resources))
4. **Firecrawl — Product & API** (scrape to markdown; dynamic sites; caching; timeouts). ([Firecrawl - The Web Data API for AI](https://www.firecrawl.dev/))
5. **Gemini API — Video understanding** (pass YouTube URLs; transcription). ([Google AI for Developers](https://ai.google.dev/gemini-api/docs/video-understanding))
6. **gitingest** — site + GitHub (LLM‑ready repo digests; private repo token notes). ([gitingest.com](https://gitingest.com/))
7. **Vertex AI — Video understanding** (Gemini video in Vertex). ([Google Cloud](https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/video-understanding))
8. **MCP explainer (alt framing & analogy)** — helpful context; optional. ([OpenAI GitHub](https://openai.github.io/openai-agents-python/mcp/))
9. **Background news on MCP** (industry adoption context). ([The Verge](https://www.theverge.com/2024/11/25/24305774/anthropic-model-context-protocol-data-sources))