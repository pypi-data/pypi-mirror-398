# Lesson 16: Building Your First MCP Agent with FastMCP
### A Hands-On Guide to Implementing the Nova Research Agent's MCP Server and Client

In Part 2A of this course, we designed our research agent, Nova. We decided to keep its orchestration layer thin and push the heavy lifting into a set of portable, reusable tools. To do this, we chose the Model Context Protocol (MCP) as our interoperability layer and FastMCP as our Python implementation.

This lesson marks the beginning of Part 2B, where we shift from design to hands-on implementation. We will turn our architectural diagrams into a running system. By the end of this lesson, you will run a complete MCP server and client, discover the capabilities they expose, and execute your first tool calls, all using the actual code from the `research_agent_part_2` project.

You will learn how to:
- Create and run an MCP server and client using FastMCP.
- Use both `in-memory` and `stdio` transports.
- Discover capabilities and execute tools, resources, and prompts.
- Understand the code layout for a scalable, MCP-based agent.

## Introduction: Why MCP for Our Research Agent

In our previous lessons, we explored the trade-offs between rigid LLM workflows and flexible, autonomous agents. For our research agent, Nova, we need a system that adapts at runtime, supports human steering, and allows us to reuse tools across different clients like IDEs or command-line applications. Our initial prototypes using static workflow graphs were clean but struggled with the open-ended nature of research.

To solve this, we are decoupling the agent's tools from its orchestration logic using the Model Context Protocol [[1]](https://modelcontextprotocol.io/). As we discussed in Lessons 12-14, this architecture gives us the loose coupling we need. We will expose Nova’s capabilities via a dedicated MCP server and manage the workflow with a lightweight MCP client. The entire research process is defined as a server-hosted prompt, making the workflow portable and available to any MCP-compliant client.

## Quickstart in the Notebook (In-Memory)

The fastest way to see our system in action is to run the client directly inside our course notebook. This setup uses the in-memory transport, where the MCP server is instantiated and run within the same Python kernel as the client. Make sure you have configured your environment and Gemini API key as described in the Course Admin lesson.

1.  When you run the client, it will start up and display a banner listing the available capabilities.
    ```python
    # Run the MCP client in-kernel
    import sys
    
    from research_agent_part_2.mcp_client.src.client import main as client_main
    
    
    async def run_client():
        _argv_backup = sys.argv[:]
        sys.argv = ["client"]
        try:
            await client_main()
        finally:
            sys.argv = _argv_backup
    
    
    # Start client with in-memory server
    await run_client()
    ```
    This banner is the result of the client performing **capability discovery**, where it queries the server for all the tools, resources, and prompts it exposes. It outputs:
    ```text
    INFO:     MCP Server version 0.1.0
    INFO:     - 11 tools available.
    INFO:     - 2 resources available.
    INFO:     - 1 prompt available.
    INFO:     - Type '/quit' to exit.
    INFO:     - Type '/tools', '/resources', or '/prompts' to list available capabilities.
    INFO:     - Type '/model-thinking-switch' to toggle model thinking.
    INFO:     - Type '/prompt/<prompt_name>' to load a prompt.
    INFO:     - Type '/resource/<resource_uri>' to view a resource.
    ```

2.  Now, you can interact with the agent. Try typing `Hello! Who are you?`. The agent will introduce itself.

3.  Next, use the `/tools`, `/resources`, and `/prompts` commands to see the lists of available capabilities.

4.  Then, try `/resource/system://memory` to read a resource and display memory usage statistics for the server process.

5.  Finally, type `/quit` to shut down the client.

You have just run a live MCP client, discovered its capabilities, and interacted with both the agent's LLM and a server-side resource.

## MCP in Short: Primitives, Transports, and Why It Matters

Before we dive into the code, let’s have a quick recap of MCP’s core concepts. MCP is an open protocol designed to connect LLM applications to external tools, data, and services over a standardized JSON-RPC interface. It is built on three main primitives:

*   **Tools**: Actions that can have side effects, like writing a file, calling an API, or running a computation [[2]](https://modelcontextprotocol.io/docs/concepts/tools).
*   **Resources**: Provide read-only access to data, such as files, system information, or database records [[3]](https://modelcontextprotocol.io/docs/concepts/resources).
*   **Prompts**: Reusable, server-hosted instruction blocks that can define entire workflows, ensuring any client can initiate the same process consistently [[4]](https://modelcontextprotocol.io/docs/concepts/prompts).

Clients interact with an MCP server by first discovering its capabilities (e.g., `list_tools`, `list_resources`, `list_prompts`) and then calling them as needed. Communication happens over a transport. In this project, we will use the two transports that FastMCP supports out of the box [[5]](https://modelcontextprotocol.io/docs/concepts/transports):

1.  **In-memory**: The client and server run in the same process. This is fast, has no network overhead, and is perfect for development and testing.
2.  **stdio**: The client spawns the server as a separate subprocess and communicates with it over standard input/output streams (`stdin`/`stdout`). This model mirrors how external applications, like IDEs, integrate with MCP servers.

Using MCP makes our tools interoperable, separates the concerns of our agent, and makes our core research workflow portable. A simple FastMCP server can be created with just a few lines of Python [[6]](https://github.com/jlowin/fastmcp).

1.  First, we define the server and a tool.
    ```python
    from fastmcp import FastMCP, Client
    
    # Create an MCP server
    mcp = FastMCP("Demo")
    
    # Add an addition tool
    @mcp.tool()
    def add(a: int, b: int) -> int:
        """Add two numbers"""
        return a + b
    ```

2.  Next, we can connect a client and call the tool.
    ```python
    async def run_client():
        # Connect to the server using the in-memory transport
        async with Client(mcp) as client:
            # Call the "add" tool
            result = await client.call_tool("add", {"a": 5, "b": 3})
            print(result.content[0].text)
    
    # It outputs: 8
    ```

<aside>
💡 Security Note: MCP is a protocol and does not enforce security. When moving beyond local development, you are responsible for securing your servers with authentication mechanisms like API keys or OAuth and implementing proper access controls. We will cover security hardening in Part 3 of this course.
</aside>

## How the MCP Server Is Organized

Now that you have seen the system run, let's look at how the server is structured. The code lives in the `src/mcp_server/` directory and follows a layout similar to a FastAPI application for clarity and scalability.

-   **`server.py`**: The main entry point. It creates a `FastMCP` app instance and registers the routers that expose our capabilities.
-   **`routers/`**: This directory contains `tools.py`, `resources.py`, and `prompts.py`. Each file imports the actual implementations and registers them with the FastMCP app using decorators.
-   **`tools/`, `resources/`, `prompts/`**: These directories contain the business logic for each capability.
-   **`config/settings.py`**: This file uses `pydantic-settings` to manage configuration like the server's name, version, API keys, and model choices [[7]](https://gofastmcp.com/).

Let's examine how one of each primitive type is registered.

### Tool Registration and Execution

In `src/mcp_server/routers/tools.py`, we register the `extract_guidelines_urls` tool. The `@mcp.tool()` decorator exposes this function to any connected client. This tool performs an action with a side effect: it reads guideline files from a directory and writes the extracted URLs to a new file at `.nova/guidelines_filenames.json`.

1.  Here is the registration code.
    ```python
    from ..tools.guidelines_tools import extract_guidelines_urls_tool
    
    @mcp.tool(
        name="extract_guidelines_urls",
        description="Extracts URLs from research guidelines files.",
    )
    async def extract_guidelines_urls(
        research_directory: str,
    ) -> dict:
        """Extracts URLs from research guidelines files."""
        return await extract_guidelines_urls_tool(
            research_directory=research_directory,
        )
    ```

2.  We can run this tool programmatically. The following code calls the tool with a sample research folder. Remember to update the `research_folder` path to the absolute path on your machine.
    ```python
    from research_agent_part_2.mcp_server.src.tools import extract_guidelines_urls_tool
    
    research_folder = "/your/absolute/path/to/sample_research_folder"
    extract_guidelines_urls_tool(research_folder=research_folder)
    ```

3.  After the tool runs successfully, you can verify its output. Check the `data/sample_research_folder` directory. You should find a new `.nova` folder containing a `guidelines_filenames.json` file with the URLs extracted from the guideline.

### Resource Registration

In `src/mcp_server/routers/resources.py`, we register the `system://memory` resource. The `@mcp.resource()` decorator makes the function's return value available at the specified URI. Unlike a tool, a resource is read-only and should not have side effects.

```python
from ..resources.system_resources import get_memory_resource

@mcp.resource("system://memory")
async def system_memory() -> dict:
    """Returns memory usage statistics."""
    return await get_memory_resource()
```

### Prompt Registration and Loading

In `src/mcp_server/routers/prompts.py`, we register our main workflow prompt. The `@mcp.prompt()` decorator exposes a string containing the detailed, multi-step instructions for conducting research.

1.  Here is the registration code.
    ```python
    from ..prompts.research_instructions_prompt import research_instructions_prompt
    
    @mcp.prompt("full_research_instructions_prompt")
    def full_research_instructions_prompt() -> str:
        """The main prompt that drives the research agent's workflow."""
        return research_instructions_prompt
    ```

2.  By hosting the prompt on the server, we ensure that any MCP client can initiate the exact same research workflow, a concept we visualized with the Mermaid diagram in Lesson 12. To see this in action, run the client and use the command `/prompt/full_research_instructions_prompt`. The client will fetch the prompt from the server and inject its content directly into the conversation, preparing the agent to begin the research task.

Now that we have seen how the server is structured and how its capabilities are registered, let's examine how the client discovers and interacts with them.

## The MCP Client: Transports, Capability Discovery, and Command Parsing

The client code, located in `src/client/`, connects to the server, parses user input, and orchestrates the agent's logic.

The client in `client.py` supports two run modes, controlled by the `--transport` command-line argument:

1.  `--transport in-memory` (default): The client imports the `create_mcp_server` function from the server code and passes the server instance directly to the `fastmcp.Client`.
2.  `--transport stdio`: The client launches the server as a separate process (`uv run -m src.server --transport stdio`) and communicates with it over standard I/O. This is how external clients like IDEs connect [[8]](https://docs.cursor.com/context/model-context-protocol), [[9]](https://docs.anthropic.com/en/docs/claude-code/mcp).

Upon startup, the client calls `get_capabilities_from_mcp_client()`, which uses the `client.list_tools()`, `client.list_resources()`, and `client.list_prompts()` methods to query the server. The results are then printed in the startup banner.

The `parse_user_input()` function routes user input. If the input starts with a `/`, it is treated as a command (like `/tools` or `/quit`). Otherwise, it is passed to the agent loop to be processed by the LLM.

The core of the client is the `handle_agent_loop()` function. This is where the ReAct-style reasoning occurs:

1.  It builds a configuration for the LLM, dynamically including the list of available MCP tools as function declarations.
2.  It sends the current conversation history to the LLM.
3.  If the LLM's response includes a request to call a tool, the client verifies that it is a valid MCP tool.
4.  It executes the tool by calling `client.call_tool(name, args)` and appends the result to the conversation history. The loop then continues.
5.  If the LLM responds without a tool call, the client treats it as the final answer, prints it, and the loop terminates for that turn.

This loop cleanly separates the LLM's role (deciding *what* to do) from the tools' role (doing the work). The project also includes utility modules for handling startup, commands, and LLM interactions, with configuration managed by `pydantic-settings` in `settings.py`.

## Try It in the Terminal: Commands & Two Run Modes

Now, let's run the full client-server application from your terminal.

1.  First, run it using the **in-memory** transport. This is the default.
    ```bash
    uv run -m src.client
    ```
    You can also specify it explicitly:
    ```bash
    uv run -m src.client --transport in-memory
    ```
    You should see the same startup banner as in the notebook, listing the available tools, resources, and prompts.

2.  Next, run it using the **stdio** transport. This will launch a separate server process in the background.
    ```bash
    uv run -m src.client --transport stdio
    ```
    The behavior will be identical from your perspective, but you are now communicating between two separate processes.

3.  In either mode, try out the following commands:
    -   `/tools`: Lists all 11 tools available for research tasks.
    -   `/resources`: Shows the available resources, including `system://memory`.
    -   `/prompts`: Describes the one available workflow prompt, `full_research_instructions_prompt`.
    -   `/resource/system://memory`: Fetches and displays the server's memory statistics.
    -   `/model-thinking-switch`: This toggles the agent's "thinking" traces on and off. As we discussed in Lesson 14, this is a practical application of managing reasoning budgets.

### Handling Common Errors

Robust systems handle failure gracefully. Let's see what happens when we provide invalid input. Run the client and ask it to execute the `extract_guidelines_urls` tool with a non-existent directory path.

`Run the "extract_guidelines_urls" tool with the "path/to/nonexistent/folder" directory.`

The tool will fail, but the system will not crash. The MCP server will return a structured error, and the agent, guided by its instructions, will report the failure clearly to you, explaining that the path does not exist and asking for a valid one. This demonstrates the critical failure policy we designed, ensuring the agent can recover from errors and continue its task with human guidance.

## Conclusion

You have now stood up a complete MCP-based agent system. You ran an MCP server exposing tools, resources, and prompts, and used an MCP client to discover and execute its capabilities using both in-memory and stdio transports. This foundation is essential for the upcoming lessons.

-   In **Lesson 17**, we will use the server-hosted prompt to kick off the full research workflow and begin implementing the tools for ingesting guidelines and processing URLs.
-   In **Lessons 18 and 19**, we will implement the remaining tools, including those for web scraping, data curation, and handling human-in-the-loop decision points.
-   Later, in **Part 3**, we will return to this system to add observability with Opik and discuss security hardening for production environments.

## References
1. Model Context Protocol. (n.d.). *Model Context Protocol*. https://modelcontextprotocol.io/
2. MCP Concepts: Tools. (n.d.). *Model Context Protocol*. https://modelcontextprotocol.io/docs/concepts/tools
3. MCP Concepts: Resources. (n.d.). *Model Context Protocol*. https://modelcontextprotocol.io/docs/concepts/resources
4. MCP Concepts: Prompts. (n.d.). *Model Context Protocol*. https://modelcontextprotocol.io/docs/concepts/prompts
5. MCP Transports. (n.d.). *Model Context Protocol*. https://modelcontextprotocol.io/docs/concepts/transports
6. jlowin/fastmcp. (n.d.). *GitHub*. https://github.com/jlowin/fastmcp
7. Lowin, J. (n.d.). *FastMCP*. https://gofastmcp.com/
8. Model Context Protocol (MCP). (n.d.). *Cursor*. https://docs.cursor.com/context/model-context-protocol
9. Connect Claude Code to tools via MCP. (n.d.). *Anthropic*. https://docs.anthropic.com/en/docs/claude-code/mcp