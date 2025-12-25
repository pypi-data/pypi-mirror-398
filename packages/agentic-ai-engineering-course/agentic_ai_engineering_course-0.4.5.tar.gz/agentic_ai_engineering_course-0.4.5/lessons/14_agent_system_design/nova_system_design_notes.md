## Nova Research Agent — System Design

### Purpose
- **What**: A research automation agent built on the Model Context Protocol (MCP), split into an MCP server that exposes research tools/resources/prompts and an MCP client that orchestrates an LLM-driven ReAct loop to call those tools.
- **Where**: Server in `src/nova/mcp_server`, client in `src/nova/mcp_client`.
- **Why**: To execute the research workflow described in `mcp_server/src/prompts/research_instructions_prompt.py` and produce a comprehensive `research.md` from guidelines and web sources.

---

## High-level architecture

### Components
- **MCP Server** (`mcp_server`)
  - Entry point: `src/nova/mcp_server/src/server.py`
    - Builds a `FastMCP` instance and registers:
      - Tools: `src/nova/mcp_server/src/routers/tools.py`
      - Resources: `src/nova/mcp_server/src/routers/resources.py`
      - Prompts: `src/nova/mcp_server/src/routers/prompts.py`
  - Tool implementations in `src/nova/mcp_server/src/tools/` call application handlers in `src/nova/mcp_server/src/app/` and use helpers in `src/nova/mcp_server/src/utils/`.
  - Configuration and constants in `src/nova/mcp_server/src/config/`.

- **MCP Client** (`mcp_client`)
  - Entry point: `src/nova/mcp_client/src/client.py`
    - Transport options:
      - In-memory: imports the server and runs it in-process
      - Stdio: spawns `uv run -m src.server --transport stdio` under the server directory
    - On startup, lists server tools/resources/prompts and prints them.
    - Interactive loop: accepts user input and orchestrates an LLM ReAct loop to decide which MCP tools to call.
  - Message/agent helpers in `src/nova/mcp_client/src/utils/`:
    - `handle_message_utils.py`: routes user commands and normal messages
    - `handle_agent_loop_utils.py`: runs the LLM/tool ReAct loop and executes tools via `client.call_tool`
    - `llm_utils.py`: prepares Gemini tool schemas from MCP tools and parses LLM responses

### Communication
- The client queries server capabilities (`list_tools`, `list_resources`, `list_prompts`) and executes tools by name (`call_tool("toolName", {args...})`).
- The client maps MCP tool metadata to Gemini function declarations so the LLM can propose function calls. Automatic function calling is disabled; the client explicitly inspects the LLM response and executes tools accordingly.

---

## How the client and server work together

1. The client starts and establishes an MCP connection (in-memory or stdio).
2. The client fetches and prints available tools/resources/prompts.
3. The user can load the workflow prompt via `/prompt/full_research_instructions_prompt`, which inserts the instructions into the conversation history.
4. The user asks for a task (e.g., “Run the full research workflow for directory X”).
5. The client starts the ReAct loop:
   - Converts MCP tools into Gemini tool schemas.
   - Calls the LLM with conversation history.
   - If the LLM proposes a function call matching an MCP tool, the client executes it via `client.call_tool` and appends the tool result to the conversation.
   - Repeats until the LLM emits a final answer instead of a function call.

Notes:
- The research prompt encourages parallelism for certain steps; the current client loop executes tools sequentially (one function call at a time). Several server tools internally run concurrent workloads (e.g., web/YT scraping), so you still get parallelism inside tool execution.

---

### Prompts
- `full_research_instructions_prompt` → returns the workflow instructions from `prompts/research_instructions_prompt.py`.

---

## Workflow mapping (from research_instructions_prompt.py)
Below, each step from the prompt is mapped to the exact tool(s) on the server with precise inputs/outputs as implemented.

### Step 1 — Setup
- User loads the instructions (optional but recommended) via `/prompt/full_research_instructions_prompt`.
- All subsequent tools require a `research_directory` that contains:
  - `article_guideline.md` (the prompt references this as `ARTICLE_GUIDELINE_FILE`)
  - A hidden `.nova/` folder that tools will create/populate as needed

### Step 1.3 — Extract URLs from guidelines
- MCP Tool: `extract_guidelines_urls(research_directory: str)`
  - Implementation: `tools/extract_guidelines_urls_tool.py`
  - Reads: `article_guideline.md`
  - Writes: `.nova/guidelines_filenames.json`
  - Output (dict):
    - `status`: "success"
    - `github_sources_count`: int
    - `youtube_sources_count`: int
    - `web_sources_count`: int
    - `local_files_count`: int
    - `output_path`: absolute path to `.nova/guidelines_filenames.json`
    - `message`: human-readable summary
  - File schema written to `.nova/guidelines_filenames.json` (keys):
    - `github_urls`: list[str]
    - `youtube_videos_urls`: list[str]
    - `other_urls`: list[str]
    - `local_file_paths`: list[str]
  - Important: Downstream tools expect different key names for local files (see callouts below).

---

## Step 2 — Process extracted resources (tools can be run independently)

### 2.1 Local files
- MCP Tool: `process_local_files(research_directory: str)`
  - Implementation: `tools/process_local_files_tool.py`
  - Reads: `.nova/guidelines_filenames.json`
  - Writes: `.nova/local_files_from_research/` copies or converted notebooks
  - Output (dict):
    - `status`: "success" or "warning" (if 0 files processed)
    - `files_processed`: int
    - `files_total`: int
    - `processed_files`: list[str] (filenames saved inside destination)
    - `warnings`: list[str]
    - `errors`: list[str]
    - `output_directory`: absolute path to `.nova/local_files_from_research/`
    - `message`: summary string
  - Expected JSON keys: The implementation uses `data.get("local_files", [])`. However, the extractor writes `local_file_paths`. If you run this step as-is, no files will be processed unless `.nova/guidelines_filenames.json` contains `local_files`. Adjustments may be required (see “Notable implementation notes”).

### 2.2 Other HTTP/HTTPS URLs (non-GitHub, non-YouTube)
- MCP Tool: `scrape_and_clean_other_urls(research_directory: str, concurrency_limit: int = 4)`
  - Implementation: `tools/scrape_and_clean_other_urls_tool.py`
  - Reads: `.nova/guidelines_filenames.json` → `other_urls`, `article_guideline.md`
  - Internals: Concurrent scraping with Firecrawl; LLM-based markdown cleaning; filenames generated safely
  - Writes: `.nova/urls_from_guidelines/*.md`
  - Output (dict):
    - `status`: "success" or "warning" (if 0 successful scrapes)
    - `urls_processed`: int (successful scrapes)
    - `urls_total`: int (attempted)
    - `files_saved`: int
    - `output_directory`: absolute path to `.nova/urls_from_guidelines/`
    - `saved_files`: list[str]
    - `message`: summary string

### 2.3 GitHub URLs
- MCP Tool: `process_github_urls(research_directory: str)`
  - Implementation: `tools/process_github_urls_tool.py`
  - Reads: `.nova/guidelines_filenames.json` → `github_urls`
  - Internals: Uses `gitingest.ingest_async` to summarize repo, tree, and content; truncates and strips base64 images; sequential by URL
  - Writes: `.nova/urls_from_guidelines_code/*.md`
  - Output (dict):
    - `status`: "success" or "warning"
    - `urls_processed`: int
    - `urls_total`: int
    - `files_saved`: int
    - `output_directory`: absolute path to `.nova/urls_from_guidelines_code/`
    - `message`: summary

### 2.4 YouTube URLs
- MCP Tool: `transcribe_youtube_urls(research_directory: str)`
  - Implementation: `tools/transcribe_youtube_videos_tool.py`
  - Reads: `.nova/guidelines_filenames.json` → `youtube_videos_urls`
  - Internals: Gemini-based transcription with retries, limited concurrency
  - Writes: `.nova/urls_from_guidelines_youtube_videos/*.md`
  - Output (dict):
    - `status`: "success"
    - `videos_processed`: int
    - `videos_total`: int
    - `output_directory`: absolute path to `.nova/urls_from_guidelines_youtube_videos/`
    - `message`: summary

---

## Step 3 — Research loop (repeatable)

### 3.1 Generate next queries
- MCP Tool: `generate_next_queries(research_directory: str, n_queries: int = 5)`
  - Implementation: `tools/generate_next_queries_tool.py`
  - Reads: `article_guideline.md`, `.nova/perplexity_results.md` (if exists), `.nova/urls_from_guidelines/*.md`
  - Writes: `.nova/next_queries.md` (overwrites)
  - Output (dict):
    - `status`: "success"
    - `queries_count`: int
    - `queries`: list[tuple[str, str]] → [(query, reason), ...]
    - `output_path`: absolute path to `.nova/next_queries.md`
    - `message`: summary + formatted query list

### 3.2 Run Perplexity research for those queries
- MCP Tool: `run_perplexity_research(research_directory: str, queries: list[str])`
  - Implementation: `tools/run_perplexity_research_tool.py`
  - Reads: None mandatory; creates/updates results file
  - Internals: Structured Perplexity call, appends normalized “Source [id]” sections
  - Writes: `.nova/perplexity_results.md` (appends)
  - Output (dict):
    - `status`: "success"
    - `queries_processed`: int
    - `sources_added`: int (number of source blocks appended)
    - `output_path`: absolute path to `.nova/perplexity_results.md`
    - `message`: summary

---

## Step 4 — Filter Perplexity results by quality

### 4.1 Select sources to keep
- MCP Tool: `select_research_sources_to_keep(research_directory: str)`
  - Implementation: `tools/select_research_sources_to_keep_tool.py`
  - Reads: `article_guideline.md`, `.nova/perplexity_results.md`
  - Writes:
    - `.nova/perplexity_sources_selected.md`: comma-separated IDs
    - `.nova/perplexity_results_selected.md`: filtered markdown containing only selected source blocks
  - Output (dict):
    - `status`: "success"
    - `sources_selected_count`: int
    - `selected_source_ids`: list[int]
    - `sources_selected_path`: absolute path to IDs file
    - `results_selected_path`: absolute path to filtered results file
    - `message`: summary

---

## Step 5 — Identify accepted sources to scrape fully

### 5.1 Select research sources to scrape
- MCP Tool: `select_research_sources_to_scrape(research_directory: str, max_sources: int = 5)`
  - Implementation: `tools/select_research_sources_to_scrape_tool.py`
  - Reads: `article_guideline.md`, `.nova/perplexity_results_selected.md`, content from `.nova/urls_from_guidelines/*.md`
  - Writes: `.nova/urls_to_scrape_from_research.md` (one URL per line)
  - Output (dict):
    - `status`: "success"
    - `urls_selected_count`: int
    - `selected_urls`: list[str]
    - `selection_reasoning`: str
    - `urls_output_path`: absolute path to `.nova/urls_to_scrape_from_research.md`
    - `message`: summary

### 5.2 Scrape selected research URLs (full content)
- MCP Tool: `scrape_research_urls(research_directory: str, concurrency_limit: int = 4)`
  - Implementation: `tools/scrape_research_urls_tool.py`
  - Reads: `.nova/urls_to_scrape_from_research.md`; optionally deduplicates against `.nova/guidelines_filenames.json` (`other_urls` + `github_urls`)
  - Categorizes: YouTube vs other URLs; transcribes YouTube; scrapes/cleans other URLs concurrently
  - Writes: `.nova/urls_from_research/*.md`
  - Output (dict):
    - `status`: "success" or "warning"
    - `urls_processed`: int (successful scrapes for non-YouTube; YouTube transcriptions are not counted in `urls_processed` but appear in the report message)
    - `urls_total`: int (new URLs after deduplication, both categories)
    - `original_urls_count`: int (before deduplication)
    - `deduplicated_count`: int
    - `files_saved`: int
    - `output_directory`: absolute path to `.nova/urls_from_research/`
    - `saved_files`: list[str]
    - `message`: summary

---

## Step 6 — Generate final research file

### 6.1 Create `research.md`
- MCP Tool: `create_research_file(research_directory: str)`
  - Implementation: `tools/create_research_file_tool.py`
  - Reads (if present):
    - Preferred: `.nova/perplexity_results_selected.md`
    - Fallback: `.nova/perplexity_results.md`
    - Plus sections from:
      - `.nova/urls_from_research/*.md`
      - `.nova/urls_from_guidelines_code/*.md`
      - `.nova/urls_from_guidelines_youtube_videos/*.md`
      - `.nova/urls_from_guidelines/*.md`
  - Writes: `research.md` at the root of `research_directory`
  - Output (dict):
    - `status`: "success"
    - `markdown_file`: absolute path to `research.md`
    - `research_results_count`: int (number of grouped query sections)
    - `scraped_sources_count`: int (from `urls_from_research`)
    - `code_sources_count`: int (from `urls_from_guidelines_code`)
    - `youtube_transcripts_count`: int (from `urls_from_guidelines_youtube_videos`)
    - `additional_sources_count`: int (from `urls_from_guidelines`)
    - `message`: summary

---

## Files, folders, and constants
Key constants from `mcp_server/src/config/constants.py`:
- Files written under `.nova/`:
  - `guidelines_filenames.json`
  - `perplexity_results.md`
  - `perplexity_results_selected.md`
  - `perplexity_sources_selected.md`
  - `next_queries.md`
  - `urls_to_scrape_from_research.md`
  - Folders: `urls_from_guidelines/`, `urls_from_guidelines_code/`, `urls_from_guidelines_youtube_videos/`, `local_files_from_research/`, `urls_from_research/`
- Root files:
  - `article_guideline.md` (input)
  - `research.md` (final output)

---

## Notable implementation notes and edge cases
- **Local files key mismatch**:
  - Extractor writes `local_file_paths` in `.nova/guidelines_filenames.json`.
  - `process_local_files_tool` reads `local_files`.
  - If unchanged, no local files will be processed by step 2.1. Resolve by aligning the key (either update the extractor to write `local_files` or adjust the processing tool to read `local_file_paths`).
- **Parallelism**:
  - The server tools implement async concurrency internally (web/YT scraping and transcription). The client’s ReAct loop executes tools one at a time; true cross-tool parallelism would require client-side orchestration changes.
- **Perplexity result format**:
  - Results are appended as normalized blocks: `### Source [id]: <url>`, plus `Query:` and `Answer:` sections, separated by `-----`. Several downstream parsers depend on this format.
- **YouTube transcription**:
  - Concurrency limited via `YOUTUBE_TRANSCRIPTION_MAX_CONCURRENT_REQUESTS`; retried on server errors, timeouts are handled with messages written to files.
- **GitHub processing**:
  - `gitingest` output is sanitized to remove base64 image payloads and truncated if too long.
- **Scraping**:
  - Uses Firecrawl with a 1-week cache for speed; content cleaned via LLM prompt constrained to removal of non-content elements.

---

## End-to-end flow summary
1. Load instructions prompt (optional).
2. Run `extract_guidelines_urls` to seed `.nova/guidelines_filenames.json`.
3. Process extracted resources:
   - `process_local_files` (requires `local_files` key) → copies/exports referenced files
   - `scrape_and_clean_other_urls` → `.nova/urls_from_guidelines/`
   - `process_github_urls` → `.nova/urls_from_guidelines_code/`
   - `transcribe_youtube_urls` → `.nova/urls_from_guidelines_youtube_videos/`
4. Repeat research loop:
   - `generate_next_queries` → `.nova/next_queries.md`
   - `run_perplexity_research` → append to `.nova/perplexity_results.md`
5. Curate results:
   - `select_research_sources_to_keep` → filter IDs and selected results
   - `select_research_sources_to_scrape` → write `.nova/urls_to_scrape_from_research.md`
6. Scrape full sources: `scrape_research_urls` → `.nova/urls_from_research/`
7. Compile final output: `create_research_file` → `research.md`.
