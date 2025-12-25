# Lesson 16 Guideline

## Global Context of the Lesson

### What We Are Planning to Share

Lesson 16 begins **Part 2B,** moving from design choices to **hands‑on MCP** with **FastMCP** using the actual **`research_agent_part_2`** code. By the end, the reader will:

- Run an **MCP server** (exposes Tools, Resources, Prompts) and an **MCP client** (orchestrates).
- Use two transports the project supports **today**: **in‑memory** and **stdio**.
- Discover capabilities (`list_tools`, `list_resources`, `list_prompts`), call **one tool** and **one resource**, and **load the server‑hosted workflow prompt**.
- Understand the **code layout** (server routers, client run modes, capability discovery, agent loop) and **why heavy work lives in tools** while orchestration stays light.

> Keep all explanations tightly scoped to what this lesson implements. If a concept was explained in L12–L14, refer back rather than re-teach.

### Why We Think It's Valuable

**MCP** is our **interoperability layer** that lets you expose tools once and reuse them from many clients (IDEs, shells, services). Moving our research agent to MCP gave us **loose coupling** (tools evolve independently), **token efficiency** (work happens in tools; the LLM in the client decides *what* to do, thus also optimizing for good context for each task, the orchestrator LLM in the client doesn't need to load the tokens necessary to get each task done.), and **portability** (the same server works with our thin client *and* external MCP clients like Cursor). Placing the **workflow prompt on the server** ensures any MCP client can initiate the same recipe. (For the architectural rationale, **see L12–L14**.)

### Expected Length of the Lesson

**~3,000 words** (without the titles and references), where we assume that 200–250 words ≈ 1 minute of reading time.

### Theory / Practice Ratio

**30% theory – 70% practical, live code and CLI**

---

## Anchoring the Lesson in the Course

### Details About the Course

This lesson is part of a 4‑part course on AI agents and LLM workflows. Keep the point of view consistent (we/us for instructors; you/your for the student). Don’t re‑teach prior lessons; point forward when you reference topics taught later.

### Lesson Scope

This is **Lesson 16 (Part 2B)** on **Building the Research Agent with MCP & FastMCP**.

- Running the **MCP server/client** for Nova, call capabilities, and map the code.

### Point of View

We write as a team (“we/our/us”) addressing a single reader (“you/your”). Avoid singular first‑person and never use “we” to refer to the student.

### Who Is the Intended Audience

Aspiring AI engineers learning **MCP‑based agent engineering** for the first time.

### Concepts Introduced in Previous Lessons

- **Part 1:** Workflows vs. agents, context engineering, structured outputs, tools/function calling, planning/reasoning (ReAct), RAG, memory, multimodal.
- **Part 2A:** why we split research/writing, how we chose FastMCP for tool portability, and the cost/latency & HITL design levers.
    - **L12 (Scope):** Two agents (Nova research via MCP/FastMCP; Brown writing via LangGraph). Why we split research (steerable) vs writing (deterministic). `research.md` is the handoff artifact.
    - **L13 (Frameworks):** Decision axes; MCP as portability layer; FastMCP for tools; LangGraph for durable writing workflow with checkpoints/HITL.
    - **L14 (System-design):** Decision framework: model choice, cost/latency, HITL policy; tradeoffs and when to push work into tools vs orchestration.
    - **L15 (System-design video):** Project structure overview; where server/client live; high-level flow.

> **Do not** re-teach the L12 architecture, L13 framework comparisons, or L14 system-design theory. Use short forward/back references.
> 

### Concepts That Will Be Introduced in Future Lessons

- **L17–L19:** Implement the research tools (ingestion, Perplexity loop, curation, full scrapes, `research.md`).
- **L20–L23:** Brown’s writing workflows in LangGraph (with MCP front).
- **Part 3:** Evaluation, observability (including **Opik**), optimization, deployment.

### Anchoring the Reader in the Educational Journey

Use earlier concepts as known (e.g., tools, structured outputs). When you must mention later topics (e.g., observability), keep it high‑level and note where we’ll cover it.

---

### Prerequisites (explicit)

- Refer to the Course Admin lesson to get the environment ready (Python via `uv`, correct kernel in the notebook).
- **Gemini** API key configured (`GOOGLE_API_KEY`), as shown in the notebook setup.
- Repo checked out; you can run `uv run -m …` from the appropriate directory.

---

## Narrative Flow of the Lesson

- **Follow this flow when writing the lesson prose.** Keep references to L12–L14 concise and linked, not re‑explained.
- **Why we’re here (3 lines):** In L12–L14 we decided to keep Nova’s orchestration thin and push work into MCP tools. L16 turns that into a running system.
- **Immediate demo:** Start the **in‑notebook** client (in‑memory server): say “Hello,” run `/tools`, `/resources`, `/prompts`, `/resource/system://memory`, `/quit`. Explain the startup banner and “capability discovery.”
- **MCP in one paragraph:** Tools (actions), Resources (read‑only), Prompts (instruction blocks), JSON‑RPC, discovery. Mention **in‑memory** and **stdio** transports only—what this project actually uses today.
- **Server + client (two run modes):** Create the FastMCP server (`create_mcp_server`), then the client in **in‑memory** and in **stdio**. Connect `stdio` to the way IDEs integrate (details later in the course).
- **One tool & one resource:** Call **`extract_guidelines_urls`** and verify `.nova/guidelines_filenames.json`. Then read **`system://memory`** to show a Resource. Contrast side‑effects (tools) vs read-only (resources).
- **Load the workflow prompt:** `/prompt/full_research_instructions_prompt`. Emphasize why the **prompt lives on the server** (any MCP client can kick off the same recipe). Point to the **Mermaid** diagram already shown in **L12** for visual recall.
- **Code map, not a tour:**
    - Server: `server.py` → `routers/{tools,resources,prompts}.py` → implementations; `settings.py`.
    - Client: run mode switch, capability discovery, command parsing, **agent loop** (function call → MCP tool call → append result).
- **Reasoning toggle as applied L14:** Use `/model-thinking-switch` to show **reasoning budget** in action—no theory, just the effect.
- **Terminal runs & pitfalls:** Run CLI with both transports. Show one expected error (bad research path) and explain the agent’s behavior and **critical failure** policy encoded in the prompt.
- **Wrap & handoff:** Summarize what now works and preview L17–L19 (implement each tool step-by-step). Defer **observability/security hardening** to Part 3.

---

## Lesson Outline

1. **Section 1 — Introduction: Why MCP for our research agent**
    - Tight reminder: Nova needs run‑time adaptability, human steering, and **tool reuse across clients**.
    - MCP gives loose coupling and portability. *Reference* L12–L14; don’t re-teach.
2. **Section 2 — MCP in short: primitives, transports, and why it matters**
    - One-paragraph MCP definition; primitives; **in‑memory** vs **stdio**; brief **security** footnote → Part 3.
3. **Section 3 — Quickstart in the notebook (in‑memory)**
    - Start the client in‑kernel; type:
    `Hello! Who are you?` → `/tools` → `/resources` → `/prompts` → `/resource/system://memory` → `/quit`.
    Explain banner and discovery.
4. **Section 4 — How the MCP server is organized**
    - `mcp_server/server.py` creates FastMCP and registers routers.
    - Routers and implementations: show **one** `@mcp.tool` (`extract_guidelines_urls`), **one** `@mcp.resource` (`system://memory`), **one** `@mcp.prompt` (full research instructions).
    - Settings via `pydantic_settings`.
    - Verify `.nova/guidelines_filenames.json` after the tool call.
5. **Section 5 — The MCP client: transports, capability discovery, command parsing**
    - **Run modes:** `-transport in-memory` vs `-transport stdio` (spawns server via `uv …`).
    - **Discovery:** `list_tools/resources/prompts` and the startup banner.
    - **Commands:** `/tools`, `/resources`, `/prompts`, `/prompt/<name>`, `/resource/<uri>`, `/model-thinking-switch`, `/quit`.
    - **Agent loop:** LLM proposes function call → verify it’s an MCP tool → execute → append result; no function call = final answer.
    - Note: **Opik wired but off** here; observability in Part 3.
6. **Section 6 — Try it in the terminal: commands & two run modes**
    - In‑memory:
        
        ```bash
        uv run -m src.client
        # or
        uv run -m src.client --transport in-memory
        ```
        
    - stdio:
        
        ```bash
        uv run -m src.client --transport stdio
        ```
        
    - **Try:** `/tools` (expect **11 tools**), `/resources` (expect **2 resources**), `/prompts` (expect **1 prompt**), `/resource/system://memory`, `/model-thinking-switch`.
7. **Section 7 — Conclusion**
    1. You ran an **MCP server** and **client**, discovered capabilities, executed one tool and one resource, and loaded the server‑hosted workflow prompt. Next: **L17–L19** implement and exercise each tool; **Part 3** adds observability and security hardening.

---

## Section 1 — Introduction: Why MCP for our research agent

- **State the real problem & stakes.** Open with a concise explanation from L12/L13 about the LangGraph‑only prototype movig to a ReAct loop structure for flexibility and how MCP enabled portability. Keep it to 2–3 sentences to stay brisk and segue to the MCP overview. We need a research stack that **adapts at run time**, supports **human steering**, and **reuses the same tools** across editors or apps. Static workflow graphs (our early attempt) looked clean but didn’t handle open‑ended exploration well.
- To decouple tooling from orchestration, we introduce MCP. We expose capabilities via an **MCP server** and orchestrate with an **MCP client** using **FastMCP**; the **workflow** is defined once as an **MCP prompt** available to *any* client.

**Section length:** ~300 words.

---

## Section 2 — MCP in **short**: primitives, transports, and why it matters

- Before touching code, let’s understand MCP’s building blocks.
- **Define MCP at a glance.** An **open protocol** for connecting LLM apps to external data/functions over **JSON‑RPC**. Servers expose **Tools** (actions), **Resources** (read‑only), and **Prompts** (reusable instruction blocks). Clients **discover** capabilities (`list_tools/resources/prompts`) and **call** them.
- **Transports & topology.** Two we’ll use: **in‑memory** (same process; great for notebooks/tests) and **stdio** (separate process; mirrors IDE/editor integrations).
- **Why MCP fits this agent.** Interoperability (write tools once; reuse from many clients), separation of concerns (agent decides *what*; tools do work), and **prompt‑encoded workflows** so **any MCP client** can start the same recipe.
- **Security footnote.** MCP itself is transport/protocol; secure secrets and identity when moving beyond local dev (keys, OAuth, restricted scopes). We’ll return to hardening in Part 3.
- Show here code of a quickstart of using FastMCP with Python to create a simple MCP server with one tool and an MCP client that connects to it (in-memory) and uses that tool. Leverage the FastMCP documentation for this.

**Section length:** ~400 words.

---

## Section 3 — Quickstart in the notebook (in‑memory)

- **Setup.** Assume environment & `uv` are ready from Course Admin. Note that the notebook uses **Gemini** API for the demo and runs **in‑memory**.
- Show code from section 2 of the notebook, which is about how to run the MCP client (with the in-memory MCP server) and use it directly from the notebook. Ask the reader to type:
    
    `Hello! Who are you?` → `/tools` → `/resource/system://memory` → `/quit`. Describe the banner (“Available Tools/Resources/Prompts”) they’ll see. Comment the outputs produced by the agent to the user messages.
    

**Section length:** ~350 words.

---

## Section 4 — How the MCP server is organized

- Leverage the section 3 of the associated notebook for this section.
- **Map the server.**
    - `mcp_server/server.py` → creates `FastMCP` and calls **routers**.
    - `mcp_server/routers/` → `tools.py`, `resources.py`, `prompts.py` register endpoints.
    - `mcp_server/tools|resources|prompts/` → implementations & prompt content.
    - `mcp_server/config/settings.py` → **pydantic_settings** for name/version, keys, model choices.
- Let’s peek at how one tool, one resource, and one prompt are registered. **Tool registration** (see section 3.1 of the notebook)**.** Show `@mcp.tool()` for **`extract_guidelines_urls(research_directory: str)`** and say it writes `.nova/guidelines_filenames.json`. Include the **programmatic** example that calls `extract_guidelines_urls_tool()` with a real path (students replace with their absolute path).
    - **Show one tool endpoint.** From `routers/tools.py`, paste the wrapper for `extract_guidelines_urls(research_directory: str)`. Summarize inputs/outputs.
- Next, a resource. **Resource registration (mirror section 3.2 of the notebook).** Show `@mcp.resource("system://memory")` and the sample JSON output (process/system memory).
    - **Show one resource endpoint.** From `routers/resources.py`, paste `@mcp.resource("system://memory")`.
- Finally, the prompt. **Prompt registration (mirror section 3.3 of the notebook).** Show `@mcp.prompt()` returning the **research instructions**.
    - **Show one prompt endpoint.** From `routers/prompts.py`, paste `@mcp.prompt()` for `full_research_instructions_prompt`, and note that the full text lives in `prompts/research_instructions_prompt.py`.
- Next, see how the client discovers and uses these.

**Section length:** ~600 words.

---

## Section 5 — The MCP client: transports, capability discovery, command parsing

- Leverage section 4 and 4.1 of the notebook for this section.
- Two run modes for the MCP client in **`client.py`.** Show the **`-transport`** switch:
    - **`in-memory`** → import `create_mcp_server()` and pass to `Client(server)`.
    - **`stdio`** → launch the server in a separate process via `uv -m src.server --transport stdio`.
        
        Explain that stdio mirrors how external MCP clients (e.g., Cursor) connect.
        
- On startup, we ask the server what it offers. Show `get_capabilities_from_mcp_client()` calling `list_tools/resources/prompts` and `print_startup_info()` printing counts and names. This matches the notebook’s banner.
- Next, we parse input. **Command parsing.** `parse_user_input()` classifies:
    
    `/tools`, `/resources`, `/prompts`, `/prompt/<name>`, `/resource/<uri>`, `/model‑thinking‑switch`, `/quit`, and **normal messages** (which go to the agent loop).
    
- **Agent loop.** In `handle_agent_loop()` we:
    1. Build an LLM config from MCP tools (function declarations) with thinking on/off.
    2. Call the LLM with conversation history.
    3. If the model proposes a **function call**, verify it matches an MCP tool and **execute** via `client.call_tool(name, args)`; append results and continue.
    4. If there’s no function call, treat it as a **final answer** and end the loop.
        
        *Transition →* “Now we’ll load the workflow prompt and run the first step.”
        
- **Utilities & settings.** Briefly list the `utils/` modules (startup, command router, loop, LLM helpers) and note `settings.py` (pydantic_settings) for API keys, model selection, logging, default transport, and server path. Mention **Opik** is wired for LLM call monitoring but will be covered in **Part 3**.

**Section length:** ~600 words.

---

## Section 6 — Try it in the terminal: commands & two run modes

- **Run with in‑memory server.**
    
    ```bash
    uv run -m src.client
    # or explicitly
    uv run -m src.client --transport in-memory
    ```
    
    Expect the banner with counts for **tools/resources/prompts** and the list of commands.
    
- Now try the real transport. **Run with stdio transport.**
    
    ```bash
    uv run -m src.client --transport stdio
    ```
    
    The client launches the server process and connects via stdio.
    
- Explore the command set. **Commands to try (exact strings).**
    - `/tools` — list the **11 tools** with descriptions
    - `/resources` → lists the available resources, like `/resource/system://memory`
    - `/prompts` → describes the  `/prompt/full_research_instructions_prompt` MCP prompt, which is the only available MCP prompt
    - `/model-thinking-switch` — toggle reasoning traces on/off (switch between a “reasoning” model mode and a non‑reasoning mode display).

**Section length:** ~500 words.

---

## Section 7 — Conclusion

- **Wrap‑up.** You stood up an **MCP server** exposing **tools/resources/prompts**, and used an **MCP client** to discover capabilities and run them. This is the foundation for the next three lessons.
- **Next lessons.**
    - **L17:** Use the **MCP prompt** which encodes the full research workflow, and implement guideline ingestion & URL processing tools.
    - **L18:** Add human‑in‑the‑loop gates and handle **critical failure** gracefully.
    - **L19:** Tie together full scrapes and produce `research.md`.
    - **L20–L23:** Switch mental models for the **writing workflow** in LangGraph (checkpoints/interrupts).

**Section length:** ~400 words.

---

## Article Code

Prioritize the official course notebook:

1. **Notebook 1 — L16 FastMCP (Server & Client Quickstart)**
"/Users/omar/Documents/ai_repos/course-ai-agents/lessons/16_fastmcp/notebook.ipynb"

---

## Golden Sources

- Model Context Protocol — Overview & Docs
    https://modelcontextprotocol.io/
    
- MCP Concepts: Tools, Resources, Prompts
    https://modelcontextprotocol.io/docs/concepts/tools
    https://modelcontextprotocol.io/docs/concepts/resources
    https://modelcontextprotocol.io/docs/concepts/prompts
    
- MCP Transports (Streamable HTTP, STDIO; legacy SSE notes)
    https://modelcontextprotocol.io/docs/concepts/transports
    
- Anthropic’s MCP docs (background & positioning)
    https://docs.anthropic.com/en/docs/mcp
    
- FastMCP (official site & repo)
    https://gofastmcp.com/
    https://github.com/jlowin/fastmcp
    
- MCP Inspector (official docs)
    https://modelcontextprotocol.io/docs/tools/inspector
    
- YouTube: MCP Prompts (the use case) — video that clarifies prompt usage
    https://www.youtube.com/watch?v=mKEq_YaJjPI

## Other Sources
    
- Why MCP matters in practice (industry view)
    https://decodingml.substack.com/p/why-mcp-breaks-old-enterprise-ai

- “Stop vibe‑testing your MCP server” (in‑memory testing mindset)
    https://www.jlowin.dev/blog/stop-vibe-testing-mcp-servers

- Cursor & Claude Code MCP configuration (practical client notes)
    https://docs.cursor.com/context/model-context-protocol
    https://docs.anthropic.com/en/docs/claude-code/mcp

- Streamable HTTP + transport changes (spec updates & discussion)
    https://github.com/modelcontextprotocol/modelcontextprotocol

## Cross‑Lesson References

- “As introduced in **Lesson 12** (system overview and the Nova/Brown split)…”
- “As compared in **Lesson 13** (framework choice and why FastMCP for research tools)…”
- “Applying **Lesson 14** (reasoning budgets and control levers), we use `/model-thinking-switch` to toggle thinking.”

