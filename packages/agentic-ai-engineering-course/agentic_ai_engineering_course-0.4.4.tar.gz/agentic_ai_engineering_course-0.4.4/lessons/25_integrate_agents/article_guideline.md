# Lesson 25 Guideline

## Global Context of the Lesson

### What We Are Planning to Share

Lesson 25 concludes **Part 2D** by showing how to integrate Nova and Brown as a unified multi-agent system using MCP. By the end, the reader will:

- Understand **central LLM orchestration** (where a single LLM uses tools from multiple agents) and why it's the right pattern for integrating Nova and Brown.
- Implement a **Multi-Server MCP Client** that connects to both Nova and Brown simultaneously, aggregating all their tools in one place.
- Implement a **Composed MCP Server** that uses FastMCP's `mount()` and `as_proxy()` features to create a single unified server.
- Compare both approaches and understand **when to use each** (development vs. production, flexibility vs. packaging).
- See the practical benefits of MCP as the interoperability layer that makes agent integration straightforward without custom code.

> Keep all explanations tightly scoped to what this lesson implements. If a concept was explained in L16 (MCP primitives), L17–L19 (Nova tools), or L20–L24 (Brown workflows), refer back rather than re-teach.

### Why We Think It's Valuable

MCP's standardized protocol makes integrating multiple agents remarkably simple. Both Nova and Brown already expose their capabilities as MCP tools, so connecting them requires no custom integration code—just configuration. The **Central LLM Orchestration** pattern leverages the LLM's natural reasoning to dynamically decide which agent's tools to use, making the system flexible and maintainable. By showing two approaches (multi-server client and composed server), we demonstrate MCP's versatility for both development and production scenarios.

### Expected Length of the Lesson

**~2,500–3,000 words** (without the titles and references), where we assume that 200–250 words ≈ 1 minute of reading time.

### Theory / Practice Ratio

**35% theory – 65% practical, live code and configuration**

---

## Anchoring the Lesson in the Course

### Details About the Course

This lesson is part of a 4‑part course on AI agents and LLM workflows. Keep the point of view consistent (we/us for instructors; you/your for the student). Don't re‑teach prior lessons; point forward when you reference topics taught later.

### Lesson Scope

This is **Lesson 25 (Part 2D)** on **Integrating Multiple AI Agents with MCP**.

- Connecting an MCP client to multiple independent MCP servers (Nova + Brown).
- Creating a composed MCP server that unifies multiple agents into a single endpoint.
- Understanding orchestration patterns and when to use each approach.

### Point of View

We write as a team ("we/our/us") addressing a single reader ("you/your"). Avoid singular first‑person and never use "we" to refer to the student.

### Who Is the Intended Audience

Aspiring AI engineers learning **multi-agent system integration** for the first time, specifically using the Model Context Protocol.

### Concepts Introduced in Previous Lessons

- **Part 1:** Workflows vs. agents, context engineering, structured outputs, tools/function calling, planning/reasoning (ReAct), RAG, memory, multimodal.
- **Part 2A:** Why we split research/writing, how we chose FastMCP + LangGraph, and the cost/latency & HITL design levers (L12–L14).
- **Part 2B (Nova):** 
    - **L16:** MCP foundations (server/client, tools/resources/prompts, server‑hosted prompt, transports).
    - **L17:** Ingestion layer (guideline extraction, local/GitHub/YouTube ingest, Firecrawl scraping).
    - **L18:** Research loop (Perplexity queries, structured outputs, optional HITL).
    - **L19:** Testing Nova end-to-end.
- **Part 2C (Brown):**
    - **L20:** Brown project structure and design.
    - **L21:** System design and architecture.
    - **L22:** Foundations (orchestrator-worker pattern, context engineering).
    - **L23:** Evaluator-optimizer pattern for article review and editing.
    - **L24:** Human-in-the-loop with MCP server integration (edit_article, edit_selected_text).

> **Do not** re-teach MCP concepts from L16, Nova tools from L17–L19, or Brown workflows from L20–L24. Use short forward/back references.

### Concepts That Will Be Introduced in Future Lessons

- **L26:** Video demonstration showing how to use both agents from Cursor to produce an article end-to-end.
- **Part 3:** Evaluation, observability (including **Opik**), optimization, deployment, MCP security, CI/CD.

### Anchoring the Reader in the Educational Journey

Use earlier concepts as known (e.g., MCP primitives, tool calling, server-hosted prompts). When you must mention later topics (e.g., remote deployment, observability), keep it high‑level and note where we'll cover it.

---

### Prerequisites (explicit)

- Refer to the Course Admin lesson to get the environment ready (Python via `uv`, correct kernel in the notebook).
- **Both agents configured**: Nova with API keys (`GOOGLE_API_KEY`, `FIRECRAWL_API_KEY`), Brown with required settings.
- Repo checked out; you can run `uv run -m …` from the appropriate directories.

---

## Narrative Flow of the Lesson

- **Follow this flow when writing the lesson prose.** Keep references to previous lessons concise and linked, not re‑explained.
- **Why we're here (2-3 lines):** We've built Nova (research) and Brown (writing) as separate MCP servers. Now we integrate them so a single LLM can orchestrate both, deciding which tools to use based on the task.
- **Multi-agent orchestration patterns (brief survey):** Introduce **Central LLM Orchestration** (what we're using), and contrast briefly with Supervisor-Worker, Sequential Pipeline, and Peer-to-Peer patterns. Explain why Central LLM fits our use case.
- **The rationale:** Why Central LLM orchestration is ideal for Nova + Brown: simplicity, natural task decomposition, unified context, sequential interdependent tasks.
- **The trade-offs:** Tool overload (15-20 tool limit), sequential execution (no massive parallelism), complex inter-agent dependencies. Our system (14 tools) fits comfortably.
- **Approach 1: Multi-Server MCP Client:**
    - Show the config file (`mcp_servers_config.json`) with both Nova and Brown.
    - Show how `Client(config)` automatically connects to multiple servers.
    - Show how tool names are prefixed with server names (`nova-research-agent_`, `brown-writing-workflow_`).
    - Run the client in the notebook and from the terminal.
- **Approach 2: Composed MCP Server:**
    - Show how to create a composed server using `FastMCP.as_proxy()` and `mount()`.
    - Show the server composition config (`mcp_servers_to_compose.json`).
    - Show the composed server code that mounts both agents with cleaner prefixes (`nova_`, `brown_`).
    - Run the client connected to the composed server.
- **Comparing the approaches:**
    - Use a table showing when to use multi-server client (development, testing, flexibility) vs. composed server (production, unified deployment, simpler client config).
    - Highlight that both achieve the same goal but differ in deployment patterns.
- **Wrap & handoff:** Summarize what now works and preview L26 (demo video using both agents in Cursor) and Part 3 (deployment, observability, security).

---

## Lesson Outline

1. **Section 1 — Introduction: From Separate Agents to Unified System**
    - Quick recap: Nova (research) and Brown (writing) are MCP servers.
    - The goal: integrate them so a single LLM can use both.
    - MCP's advantage: standardized protocol, no custom integration code.
2. **Section 2 — Understanding Multi-Agent Orchestration: The MCP Approach**
    - Define **Central LLM Orchestration**: single LLM with access to tools from multiple agents.
    - Contrast with other patterns: Supervisor-Worker, Sequential Pipeline, Peer-to-Peer.
    - Why this pattern works well with MCP (unified tool interface, natural reasoning, flexibility).
3. **Section 3 — The Rationale: Why Choose Central LLM Orchestration?**
    - Simplicity and maintainability (all decisions in one place).
    - Natural task decomposition (adaptive based on results).
    - Unified context window (no siloed knowledge).
    - Perfect for sequential, interdependent tasks (research → writing).
4. **Section 4 — The Trade-offs: Understanding the Limitations**
    - Tool overload (15-20 tool limit; our 14 tools fit comfortably).
    - Sequential execution model (not suitable for massive parallelism).
    - Complex inter-agent dependencies (debate, negotiation).
    - Central LLM orchestration is the right default; use other patterns only when you hit clear limits.
5. **Section 5 — Approach 1: Multi-Server MCP Client**
    - Show `mcp_servers_config.json` with Nova and Brown.
    - Show client code: `Client(config)` with multi-server config.
    - Explain tool name prefixing (`nova-research-agent_`, `brown-writing-workflow_`).
    - Run the client in the notebook and from the terminal.
6. **Section 6 — Approach 2: Composed MCP Server**
    - Show `mcp_servers_to_compose.json` config.
    - Show composed server code using `FastMCP.as_proxy()` and `mount()`.
    - Explain how mounting works (live link, prefixed access, delegation).
    - Show client config pointing to the composed server.
    - Run the client connected to the composed server.
7. **Section 7 — Comparing the Approaches: When to Use Each**
    - Table comparing multi-server client vs. composed server.
    - Use cases: development/testing vs. production deployment.
    - Practical examples (developing agents vs. deploying to Cursor).
8. **Section 8 — Conclusion**
    - Summary: two ways to integrate agents via MCP.
    - Next lesson: L26 video demo using both agents in Cursor.
    - Part 3: deployment, observability, security.

---

## Section 1 — Introduction: From Separate Agents to Unified System

- **Quick recap of where we are.** Throughout Part 2, we built two specialized agents: **Nova** (deep research: ingests guidelines, performs web research, scrapes sources, compiles comprehensive research files) and **Brown** (writing workflow: takes research and guidelines to generate, review, and edit articles with human-in-the-loop feedback). We've been running them separately, but they're designed to work in sequence—Nova gathers the research, Brown uses that research to write.
- **The goal of this lesson.** Now we integrate them so a single LLM can orchestrate both agents, dynamically deciding which tools to use based on the task. The LLM sees all tools from both agents and chooses the right ones at the right time.
- **MCP's advantage.** Because both agents are already MCP servers, integration is straightforward. We don't need to write custom APIs or adapters. We simply connect to both servers, and the LLM sees a unified set of tools from both agents.
- **Two approaches we'll explore:**
    1. **Multi-Server MCP Client**: A single client connects to multiple independent MCP servers simultaneously.
    2. **Composed MCP Server**: A single server that internally mounts both Nova and Brown, exposing their combined capabilities as one unified endpoint.
- Both achieve the same goal but differ in their deployment and configuration patterns. We'll implement both and compare when to use each.

**Section length:** ~300 words.

---

## Section 2 — Understanding Multi-Agent Orchestration: The MCP Approach

- Leverage the associated notebook for this section.
- Before diving into implementation, let's understand the orchestration model we're using and why it matters.
- **Define Central LLM Orchestration.** In this pattern, a single, central LLM (e.g., Claude in Cursor) has access to tools from multiple specialized agents. When you give it a task, the LLM dynamically decides which agent's tools to use based on the task requirements. It maintains a single conversation context and orchestrates the workflow by selecting the appropriate tools as needed.
- **Contrast with other patterns (briefly):**
    - **Supervisor Agent**: One agent explicitly delegates entire sub-tasks to worker agents.
    - **Sequential Pipeline**: Agents always execute in a fixed order.
    - **Peer-to-Peer Communication**: Agents directly message each other.
    - **Central LLM Orchestration** (our pattern): The LLM acts as an intelligent tool selector rather than an explicit coordinator.
- **Why this pattern works well with MCP:**
    - **Unified tool interface**: Both Nova and Brown expose their capabilities as MCP tools with clear descriptions. The central LLM discovers all available tools through a single, standardized protocol.
    - **No custom integration code**: Because both agents speak MCP, we don't need adapters or APIs. The client simply connects to both servers and aggregates their tools.
    - **Natural reasoning**: The LLM's reasoning ability handles the orchestration logic. For example, it intuitively understands to use Nova's research tools first, review the results, then use Brown's writing tools with that research as input. No need to explicitly program this workflow.
    - **Flexibility**: Add or remove agents by updating the configuration file without touching code. This pattern treats specialized agents as "tool libraries" that a central reasoning engine can draw from as needed.

**Section length:** ~400 words.

---

## Section 3 — The Rationale: Why Choose Central LLM Orchestration?

- Leverage the associated notebook for this section.
- This orchestration pattern offers several compelling advantages that make it ideal for integrating Nova and Brown.
- **Simplicity and maintainability.** All decision-making happens in one place—the central LLM. The workflow is transparent and easy to understand: you can see which tools the LLM chooses in real-time as it works through a task. No complex state management or inter-agent communication protocols. This reduces cognitive overhead for understanding and debugging.
- **Natural task decomposition.** The central LLM can break down complex requests on the fly without predefined workflows. More importantly, it can adapt its strategy based on intermediate results. For example, if research reveals unexpected information, the LLM can adjust its writing approach accordingly. This adaptive behavior is especially valuable for human-in-the-loop workflows common in IDE environments—you can provide feedback at any point, and the LLM incorporates it naturally.
- **Unified context window.** The central LLM maintains a single conversation history, which means it can reference information from Nova's research when calling Brown's tools without requiring explicit data passing between agents. This avoids the "siloed knowledge" problem where critical information gets trapped in one agent's context.
- **Perfect for sequential, interdependent tasks.** Our workflow (research followed by writing) is inherently sequential, and the writing task depends heavily on research results. A central orchestrator can easily manage these dependencies because it sees the entire workflow and makes informed decisions about when to transition from research to writing.
- **Integrating Nova and Brown.** Nova gathers comprehensive research, and Brown uses that research to write articles. These agents were designed to work in sequence. Central LLM orchestration is the natural fit: the LLM understands the dependency, runs Nova's tools first, reviews the research, and then runs Brown's tools with that research as context.

**Section length:** ~350 words.

---

## Section 4 — The Trade-offs: Understanding the Limitations

- Leverage the associated notebook for this section.
- While central LLM orchestration is powerful, it's important to understand its limitations and recognize when you might need a different approach.
- **Tool overload.** As the number of available tools grows beyond approximately 15-20, LLMs begin to struggle with reliable tool selection. They may choose suboptimal tools or miss relevant ones entirely. This degradation is well-documented in research on agent systems. Our system, with **14 tools total** (11 from Nova + 3 from Brown), is comfortably within the limit. But if you were to add many more specialized agents, you'd eventually hit this ceiling and need to consider a different pattern.
- **Sequential execution model.** The pattern is inherently sequential: the LLM executes tools one at a time. If you need to research 50 companies simultaneously, a single LLM executing tools sequentially would be inefficient. In such scenarios, a Supervisor-Worker pattern with parallel execution would be better.
- **Complex inter-agent dependencies.** If agents need to negotiate with each other, engage in debate, or iteratively refine each other's work through back-and-forth exchanges, direct agent-to-agent communication would be more natural. Our pattern handles simple, linear dependencies well (Nova's output feeds into Brown), but complex multi-way interactions would become awkward.
- **Central LLM orchestration is the right default.** Despite these limitations, it's the right default choice for most agent integration scenarios. It's simple, maintainable, and leverages the LLM's natural reasoning without adding unnecessary complexity. Only consider more elaborate patterns when you hit clear scaling limits (too many tools causing selection problems) or have fundamentally different requirements (massive parallelism or complex agent negotiations).
- **Transition:** Now let's see how to implement this pattern with MCP, starting with the multi-server client approach.

**Section length:** ~350 words.

---

## Section 5 — Approach 1: Multi-Server MCP Client

- Leverage the associated notebook for this section.
- The first approach is to create an MCP client that connects to multiple MCP servers simultaneously. FastMCP's `Client` class supports this out of the box by accepting a configuration object that specifies multiple servers.

### 5.1 Multi-Server Configuration File

- Leverage the associated notebook for this section.
- Leverage the associated notebook for this section.
- Let's look at the configuration file that defines both Nova and Brown servers.
- **Show the config** from `agents_integration/mcp_client/mcp_servers_config.json`:
- Explain: This configuration tells the MCP client how to launch both servers. Each server has a unique name, uses the `stdio` transport (communicates via stdin/stdout), and specifies the command and arguments to start the server.

### 5.2 Creating the Multi-Server Client

- Leverage the associated notebook for this section.
- Now let's see how the client code loads this configuration and connects to both servers.
- **Show the client code** from `agents_integration/mcp_client/src/client.py`:
- **Key insight:** `Client(config)` accepts a multi-server configuration. When you call `list_tools()`, `list_resources()`, or `list_prompts()`, the client automatically aggregates capabilities from all connected servers.

### 5.3 How Capabilities Are Named

- Leverage the associated notebook for this section.
- When you have multiple servers, how do you distinguish which tool belongs to which server? FastMCP handles this by prefixing the tool names with the server name.
- **Examples:**
    - Nova's `extract_guidelines_urls` tool becomes `nova-research-agent_extract_guidelines_urls`
    - Brown's `generate_article` tool becomes `brown-writing-workflow_generate_article`
- The client code groups capabilities by extracting these prefixes. Show a snippet from `agents_integration/mcp_client/src/utils/command_utils.py`:
- This makes it easy to see which capabilities come from which server.

### 5.4 Running the Multi-Server Client

- Leverage the associated notebook for this section.
- From the terminal.
- Expected output** (show a trimmed version).
- When you type `/tools`, you'll see all tools from both servers with prefixes like `brown-writing-workflow_generate_article` and `nova-research-agent_extract_guidelines_urls`.

### 5.5 Running in the Notebook

- Leverage the associated notebook for this section.
- Show the notebook cell (from Section 3.5).
- After running, you can type `/tools`, `/resources`, `/prompts`, or `/quit` to explore. This demonstrates that the client successfully connected to both servers and aggregated their capabilities.

**Section length:** ~600 words (without code blocks).

---

## Section 6 — Approach 2: Composed MCP Server

- Leverage the associated notebook for this section.
- The second approach is to create a new MCP server that composes Nova and Brown together. Instead of the client connecting to multiple servers, you create a single composed server that internally proxies requests to the underlying servers.
- **When to use this:** Package multiple agents as a single deployable unit, simplify client-side configuration (client only knows about one server), add coordination logic between agents.

### 6.1 Server Composition Configuration

- Leverage the associated notebook for this section.
- First, we define which servers to compose. Show `agents_integration/mcp_server/mcp_servers_to_compose.json`.
- This looks identical to the multi-server client config, but it's used differently—it tells the composed server which servers to mount.

### 6.2 Creating the Composed Server

- Leverage the associated notebook for this section.
- Now let's see how to create a composed server using FastMCP's composition features. Show code from `agents_integration/mcp_server/src/main.py`.
- **Break down the key steps:**
    1. Create a `FastMCP` instance. This is our composed server.
    2. For each server to compose:
        - Create a `Client` that connects to that server
        - Use `FastMCP.as_proxy(client)` to create a proxy object
        - Use `mcp.mount(proxy, prefix=prefix)` to mount it with a prefix
- **The magic of `mount()`:** It takes all capabilities from the proxy and adds them to the composed server with the specified prefix. This is how `extract_guidelines_urls` becomes `nova_extract_guidelines_urls` (cleaner prefixes than the multi-server client).

### 6.3 How Mounting Works

- Leverage the associated notebook for this section.
- **Live link:** The parent server establishes a connection to the mounted server.
- **Dynamic updates:** Changes to the mounted server are immediately reflected when accessed through the parent.
- **Prefixed access:** The parent server uses prefixes to route requests to the mounted server.
- **Delegation:** Requests for components matching the prefix are delegated to the mounted server at runtime.
- **Performance note:** Due to the live link, operations like `list_tools()` are impacted by the slowest mounted server. For local servers (like ours), this is negligible. For HTTP-based servers, there can be latency (300-400ms).

### 6.4 Running the Composed Server

- Leverage the associated notebook for this section.
- To use the composed server, you need a client config that points to it. Show `agents_integration/mcp_client/mcp_composed_server_config.json`:
- From the terminal.
- Expected output.
    
- **Notice the difference in prefixes:**
    - Multi-server client: `nova-research-agent_`, `brown-writing-workflow_`
    - Composed server: `nova_`, `brown_` (cleaner!)

### 6.5 Running in the Notebook

- Leverage the associated notebook for this section.
- Show the notebook cell.  
- From the client's perspective, it's connecting to a single server (`nova-brown-composed`), but that server internally proxies to both Nova and Brown. The client sees cleaner tool names like `nova_extract_guidelines_urls` and `brown_generate_article`.

**Section length:** ~650 words (without code blocks).

---

## Section 7 — Comparing the Approaches: When to Use Each

- Leverage the associated notebook for this section.
- Both approaches achieve the same goal: using Nova and Brown together. But they have different use cases and trade-offs.
- Show the comparison table from the notebook.
- **Transition:** In the next lesson (L26), you'll see a video demonstration of using both agents from Cursor to research and write an article end-to-end. In Part 3, we'll cover deploying these servers remotely, adding observability with Opik, and implementing security measures.

**Section length:** ~400 words (including table).

---

## Section 8 — Conclusion

- **Wrap‑up.** You've integrated Nova and Brown as a unified multi-agent system using MCP. You learned about **Central LLM Orchestration** (where a single LLM dynamically selects tools from multiple agents) and implemented it in two ways: **Multi-Server MCP Client** (client connects to multiple independent servers) and **Composed MCP Server** (single server that mounts multiple agents). You understand when to use each approach (development vs. production) and the trade-offs involved.
- **The power of MCP.** MCP's standardized protocol made this integration straightforward. No custom APIs, no adapters—just configuration. Both agents expose their capabilities as MCP tools, and the client (or composed server) aggregates them into a unified interface. This modularity is MCP's core value: write agents once, integrate them anywhere.
- **Next lessons:**
    - **L26:** Video demonstration showing how to use both agents from Cursor to produce an article end-to-end. You'll see the full research-to-writing workflow in action with human-in-the-loop feedback.
    - **Part 3:** Production engineering practices:
        - **Deployment**: Deploy composed servers remotely with HTTP transports.
        - **Observability**: Add monitoring with Opik to track LLM calls, costs, and latency.
        - **Security**: Implement authentication, rate limiting, and secure secrets management for MCP servers.
        - **Evaluation**: AI Evals for testing agent quality and reliability.
        - **CI/CD**: Automated testing and deployment pipelines.

**Section length:** ~300 words.

---

## Article Code

Prioritize the official course notebook:

1. **Notebook 1 — L25 Integrating Multiple AI Agents with MCP**
   "/Users/fabio/Desktop/course-ai-agents/lessons/25_integrate_agents/notebook.ipynb"

---

## Golden Sources

- **Model Context Protocol — Overview & Docs**
  https://modelcontextprotocol.io/
  
- **MCP Concepts: Tools**
  https://modelcontextprotocol.io/docs/concepts/tools
  
- **FastMCP — Server Composition (mount, as_proxy)**
  https://gofastmcp.com/servers/composition
  
- **FastMCP (official site)**
  https://gofastmcp.com/
  
- **Anthropic — Building Effective Agents**
  https://www.anthropic.com/engineering/building-effective-agents

## Other Sources

- **Multi-Agent Orchestration Patterns (2025)**
  https://www.marktechpost.com/2025/08/09/9-agentic-ai-workflow-patterns-transforming-ai-agents-in-2025/
  
- **Single-Agent vs Multi-Agent Systems**
  https://learn.microsoft.com/en-us/dynamics365/guidance/resources/contact-center-multi-agent-architecture-design
  
- **LangGraph and AutoGen Multi-Agent Architectures**
  https://collabnix.com/multi-agent-and-multi-llm-architecture-complete-guide-for-2025/
  
- **Cursor MCP configuration**
  https://docs.cursor.com/context/model-context-protocol