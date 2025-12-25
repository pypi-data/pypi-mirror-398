# Lesson 19: Final Outputs and Agent Completion
### Hardening Our Research Agent with Quality Gates, Deep Scraping, and Human-in-the-Loop Controls

In the previous lessons, we built the core of our research agent. We started with the ingestion layer in Lesson 17, processing various sources like web pages, GitHub repositories, and YouTube videos. Then, in Lesson 18, we implemented the research loop, using Perplexity with structured outputs to generate and answer new queries. However, open-ended research without quality gates often accumulates noisy, redundant, or off-topic sources. This can pollute our final output and waste our scraping budget.

We need a repeatable way to filter research results for trust and authority, select the best URLs for a more intensive full-content scrape, and compile everything into a single, well-cited `research.md` file. This lesson will show you how to implement these final quality-control and compilation steps to complete the agent. You will learn to build automated quality gates, create a path for "full-content" analysis of top sources, and produce a deterministic final research artifact. We will also demonstrate how to use the Model Context Protocol (MCP) to create Human-in-the-Loop (HITL) checkpoints, allowing you to approve sources when needed without sacrificing automation.

## Completing the Research Workflow

As we have seen in previous lessons, our research agent follows a systematic workflow. We have already covered the initial data ingestion and the research loop. Now, we will implement the final steps that ensure the quality of our research and compile the results into a final, usable format.

The complete workflow includes these final steps:

```markdown
4. Filter Perplexity results by quality:
    4.1 Run the "select_research_sources_to_keep" tool to automatically evaluate each source 
    for trustworthiness, authority and relevance.

5. Identify which of the accepted sources deserve a full scrape:
    5.1 Run the "select_research_sources_to_scrape" tool to choose up to 5 diverse, 
    authoritative sources whose full content will add most value.
    5.2 Run the "scrape_research_urls" tool to scrape/clean each selected URL's full content.

6. Write final research file:
    6.1 Run the "create_research_file" tool to combine all research data into a 
    comprehensive research.md file.
```

These final steps are defined in the server-hosted MCP prompt we introduced in Lesson 16 [[1]](https://modelcontextprotocol.io/docs/concepts/tools?utm_source=chatgpt.com). This design continues the file-first pattern, where all intermediate outputs are stored in the `.nova/` directory, while the final `research.md` artifact is placed at the root of the research directory for easy access. This makes the entire process auditable and easy to debug.

This workflow also adheres to the critical-failure policy we established in Lesson 17. If any tool processes zero items when some were expected, the workflow halts and asks for your guidance. This prevents the agent from proceeding with incomplete or faulty data, ensuring the reliability of the final output. Now, let's examine each of the final tools in detail.

## Filter Perplexity Sources to Keep

The `select_research_sources_to_keep` tool solves a common problem we discovered during development: Perplexity results often include sources from untrustworthy blogs, SEO spam, or low-quality content that would pollute our research.

### Understanding the Tool Implementation

This tool takes a research directory as input and automatically filters Perplexity results for quality. It reads the article guidelines and raw Perplexity results, then uses an LLM to evaluate each source based on trustworthiness, authority, and relevance criteria. The tool outputs two files: a list of selected source IDs and a filtered markdown file containing only the approved sources. This automated filtering saves time while ensuring research quality [[2]](https://docs.perplexity.ai/guides/structured-outputs?utm_source=chatgpt.com).

1.  Here is the implementation of the tool. It gathers the necessary context, calls an LLM to select the sources, and then writes the results to the corresponding files.
    ```python
    async def select_research_sources_to_keep_tool(research_directory: str) -> Dict[str, Any]:
        """
        Automatically select high-quality sources from Perplexity results.
    
        Uses an LLM to evaluate each source in perplexity_results.md for trustworthiness,
        authority, and relevance based on the article guidelines. Writes the comma-separated
        IDs of accepted sources to perplexity_sources_selected.md and saves a filtered
        markdown file perplexity_results_selected.md containing only the accepted sources.
    
        Args:
            research_directory: Path to the research directory containing article guidelines and research data
    
        Returns:
            Dict with status, selection results, and file paths
        """
        # Convert to Path object
        research_path = Path(research_directory)
        nova_path = research_path / NOVA_FOLDER
        
        # Gather context from the research folder
        guidelines_path = research_path / ARTICLE_GUIDELINE_FILE
        results_path = nova_path / PERPLEXITY_RESULTS_FILE
        
        article_guidelines = read_file_safe(guidelines_path)
        perplexity_results = read_file_safe(results_path)
        
        # Use LLM to select sources
        selected_ids = await select_sources(
            article_guidelines, perplexity_results, settings.source_selection_model
        )
        
        # Write selected source IDs to file
        sources_selected_path = nova_path / PERPLEXITY_SOURCES_SELECTED_FILE
        sources_selected_path.write_text(",".join(map(str, selected_ids)), encoding="utf-8")
        
        # Extract and save filtered content
        filtered_content = extract_selected_blocks_content(selected_ids, perplexity_results)
        results_selected_path = nova_path / PERPLEXITY_RESULTS_SELECTED_FILE
        results_selected_path.write_text(filtered_content, encoding="utf-8")
        
        return {
            "status": "success",
            "sources_selected_count": len(selected_ids),
            "selected_source_ids": selected_ids,
            "sources_selected_path": str(sources_selected_path.resolve()),
            "results_selected_path": str(results_selected_path.resolve()),
            "message": f"Successfully selected {len(selected_ids)} high-quality sources..."
        }
    ```
    The core of this tool is the `select_sources` function, which uses the `PROMPT_SELECT_SOURCES` prompt to evaluate each source and select the most relevant ones.

### The Source Evaluation Prompt

Here's the prompt used to evaluate the sources:

```python
PROMPT_SELECT_SOURCES = """
You are a research quality evaluator. Your task is to evaluate web sources for an upcoming article
and select only the high-quality, trustworthy sources that are relevant to the article guidelines.

<article_guidelines>
{article_guidelines}
</article_guidelines>

Here are the sources to evaluate:
<sources_to_evaluate>
{sources_data}
</sources_to_evaluate>

**Selection Criteria:**
- ACCEPT sources from trustworthy domains (e.g., .edu, .gov, established news sites,
official documentation, reputable organizations)
- ACCEPT sources with high-quality, relevant content that directly supports the article guidelines
- REJECT sources from obscure, untrustworthy, or potentially biased websites
- REJECT sources with low-quality, irrelevant, or superficial content
- REJECT sources that seem to be marketing materials, advertisements, or self-promotional content

Return your decision as a structured output with:
1. selection_type: "none" if no sources meet the quality standards, "all" if all sources are acceptable,
or "specific" for specific source IDs
2. source_ids: List of selected source IDs
""".strip()
```

This prompt serves as a quality gatekeeper, automatically filtering out unreliable sources. The prompt's structured selection criteria balance domain reputation, content quality, and relevance. It explicitly targets common quality issues like SEO spam, marketing content, and biased sources that often pollute web search results, ensuring only authoritative sources proceed to the next stage.

### Testing the Source Selection Tool

Let's test the source filtering tool to see how it evaluates and selects high-quality sources from our Perplexity results. The tool will analyze each source and provide feedback on which ones meet our quality standards.

1.  We import and call the tool with our research directory.
    ```python
    from research_agent_part_2.mcp_server.src.tools import select_research_sources_to_keep_tool
    
    # Test the source selection tool
    research_folder = "/path/to/research_folder"
    result = await select_research_sources_to_keep_tool(research_directory=research_folder)
    print(result)
    ```
    It outputs:
    ```text
    {'status': 'success', 'sources_selected_count': 12, 'selected_source_ids': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], 'sources_selected_path': '/Users/fabio/Desktop/course-ai-agents/lessons/research_agent_part_2/data/sample_research_folder/.nova/perplexity_sources_selected.md', 'results_selected_path': '/Users/fabio/Desktop/course-ai-agents/lessons/research_agent_part_2/data/sample_research_folder/.nova/perplexity_results_selected.md', 'message': '✅ Selected 12 source(s). IDs written to /Users/fabio/Desktop/course-ai-agents/lessons/research_agent_part_2/data/sample_research_folder/.nova/perplexity_sources_selected.md. Filtered results written to /Users/fabio/Desktop/course-ai-agents/lessons/research_agent_part_2/data/sample_research_folder/.nova/perplexity_results_selected.md.'}
    ```

**Developer Note:** We originally went straight to `research.md` after the loop. Spammy results forced us to add this automated keep step. Later we realized some Perplexity URLs were worth scraping in full; we added a second selector rather than re-running research or editing the guideline mid-flight.

## Select Sources to Scrape in Full

After filtering for quality, we need to identify which sources deserve a full scrape. While Perplexity provides summaries and excerpts, some high-quality sources contain much more valuable content in their full form. The `select_research_sources_to_scrape` tool analyzes the filtered results and strategically chooses the most valuable sources for comprehensive content extraction. This full content will provide the writing agent with richer context, detailed examples, and comprehensive coverage that brief excerpts cannot capture.

### Understanding the Selection Logic

This tool takes filtered Perplexity results and selects the most valuable sources for full scraping. It analyzes the article guidelines, accepted sources, and already-scraped guideline content to avoid duplication. The tool uses an LLM to evaluate sources based on relevance, authority, quality, and uniqueness, then outputs a prioritized list of URLs. The default limit of 5 sources balances comprehensive coverage with processing efficiency and API costs.

1.  The implementation is similar to the previous tool. It gathers context, calls an LLM to select the top sources, and writes the chosen URLs to a file.
    ```python
    async def select_research_sources_to_scrape_tool(research_directory: str, max_sources: int = 5) -> Dict[str, Any]:
        """
        Select up to max_sources priority research sources to scrape in full.
        
        Analyzes the filtered Perplexity results together with the article guidelines and
        the material already scraped from guideline URLs, then chooses up to max_sources diverse,
        authoritative sources whose full content will add most value. The chosen URLs are
        written (one per line) to urls_to_scrape_from_research.md.
        """
        # Gather context from the research folder
        guidelines_path = research_path / ARTICLE_GUIDELINE_FILE
        results_selected_path = nova_path / PERPLEXITY_RESULTS_SELECTED_FILE
        
        article_guidelines = read_file_safe(guidelines_path)
        accepted_sources_data = read_file_safe(results_selected_path)
        scraped_guideline_ctx = load_scraped_guideline_context(nova_path)
        
        # Use LLM to select top sources for scraping
        selected_urls, reasoning = await select_top_sources(
            article_guidelines, accepted_sources_data, scraped_guideline_ctx, max_sources
        )
        
        # Write selected URLs to file
        urls_out_path = nova_path / URLS_TO_SCRAPE_FROM_RESEARCH_FILE
        urls_out_path.write_text("\n".join(selected_urls) + "\n", encoding="utf-8")
        
        return {
            "status": "success",
            "sources_selected": selected_urls,
            "sources_selected_count": len(selected_urls),
            "output_path": str(urls_out_path.resolve()),
            "reasoning": reasoning,
            "message": f"Successfully selected {len(selected_urls)} sources for full scraping..."
        }
    ```
    The core of this tool is the `select_top_sources` function, which uses the `PROMPT_SELECT_TOP_SOURCES` prompt to evaluate each source and select the best ones to scrape.

### The Source Selection Prompt

The tool uses a prompt to choose the most valuable sources:
```python
PROMPT_SELECT_TOP_SOURCES = """
You are assisting with research for an upcoming article.

Your task is to select the most relevant and trustworthy sources from the web search results.
You should consider:
1. **Relevance**: How well each source addresses the article guidelines
2. **Authority**: The credibility and reputation of the source
3. **Quality**: The depth and accuracy of the information provided
4. **Uniqueness**: Sources that provide unique insights not covered by the scraped guideline URLs

Please select the top {top_n} sources that would be most valuable for the article research.

Return your selection with the following structure:
- **selected_urls**: A list of the most valuable URLs to scrape in full, ordered by priority
- **reasoning**: A short explanation summarizing why these specific URLs were chosen
""".strip()
```
This prompt optimizes resource allocation by strategically selecting sources for expensive full-content scraping. The four-dimensional evaluation framework (relevance, authority, quality, uniqueness) ensures maximum research value while avoiding duplication with already-scraped guideline content. The uniqueness criterion is particularly important as it prevents redundant scraping of similar information. The reasoning requirement provides transparency for human oversight and helps identify potential gaps in the selection logic, making the process auditable and improvable.

### Testing the Source Selection Tool

Now let's test the source selection tool to see which URLs it chooses for full content scraping. The tool will analyze our filtered sources and select the most valuable ones based on their potential contribution to the final research.

1.  We call the tool, specifying a `max_sources` limit of 3.
    ```python
    from research_agent_part_2.mcp_server.src.tools import select_research_sources_to_scrape_tool
    
    # Test selecting sources to scrape
    result = await select_research_sources_to_scrape_tool(research_directory=research_folder, max_sources=3)
    print("Selected sources:")
    print(result)
    ```
    It outputs:
    ```text
    Selected sources:
    {'status': 'success', 'urls_selected_count': 3, 'selected_urls': ['https://www.elastic.co/what-is/large-language-models', 'https://arxiv.org/html/2412.01130v2', 'https://www.legitsecurity.com/aspm-knowledge-base/llm-security-risks'], 'selection_reasoning': "These sources were chosen for their direct relevance to the article's themes of understanding why agents need tools, the development of autonomous AI agents, and crucial security considerations. The Elastic.co source provides a comprehensive overview of LLM limitations that tool use addresses. The ArXiv paper offers authoritative insights into the role of function calling in autonomous agent development and action models. The Legit Security source details critical security risks and mitigation strategies associated with external tool-calling, which is a vital aspect not covered in the existing guideline URLs.", 'urls_output_path': '/Users/fabio/Desktop/course-ai-agents/lessons/research_agent_part_2/data/sample_research_folder/.nova/urls_to_scrape_from_research.md', 'message': "✅ Saved 3 URL(s) to scrape to /Users/fabio/Desktop/course-ai-agents/lessons/research_agent_part_2/data/sample_research_folder/.nova/urls_to_scrape_from_research.md.\nReasoning: These sources were chosen for their direct relevance to the article's themes of understanding why agents need tools, the development of autonomous AI agents, and crucial security considerations. The Elastic.co source provides a comprehensive overview of LLM limitations that tool use addresses. The ArXiv paper offers authoritative insights into the role of function calling in autonomous agent development and action models. The Legit Security source details critical security risks and mitigation strategies associated with external tool-calling, which is a vital aspect not covered in the existing guideline URLs."}
    ```

This tool is a practical example of resource allocation optimization. Instead of scraping every URL, which can be costly and time-consuming, we focus our budget on a few high-impact sources that promise unique, in-depth information.

## Scrape Selected Research URLs

The `scrape_research_urls_tool` handles the full content extraction from our selected sources. It works very similarly to the guideline URL scraping tool we saw in lesson 16, using Firecrawl for robust web scraping and an LLM for content cleaning.

1.  We test the scraping tool, which reads the URLs selected in the previous step.
    ```python
    from research_agent_part_2.mcp_server.src.tools import scrape_research_urls_tool
    
    # Test scraping the selected research URLs
    result = await scrape_research_urls_tool(research_directory=research_folder, concurrency_limit=3)
    print("Scraping results:")
    print(result)
    ```
    It outputs:
    ```text
    Scraping results:
    {'status': 'success', 'urls_processed': 3, 'urls_total': 3, 'original_urls_count': 3, 'deduplicated_count': 0, 'files_saved': 3, 'output_directory': '/Users/fabio/Desktop/course-ai-agents/lessons/research_agent_part_2/data/sample_research_folder/.nova/urls_from_research', 'saved_files': ['understanding-large-language-models-a-comprehensive-guide-el.md', 'enhancing-function-calling-capabilities-in-llms-strategies-f.md', 'large-language-model-llm-security-risks-and-best-practices.md'], 'message': "Processed 3 new URLs from urls_to_scrape_from_research.md in '/Users/fabio/Desktop/course-ai-agents/lessons/research_agent_part_2/data/sample_research_folder'. Scraped 3/3 web pages."}
    ```

This tool's goal is to get clean, LLM-ready markdown from the selected URLs. As we covered in Lesson 16, we use Firecrawl because it is purpose-built to convert modern, dynamic web pages into markdown [[3]](https://docs.firecrawl.dev/features/scrape?utm_source=chatgpt.com), [[4]](https://docs.firecrawl.dev/advanced-scraping-guide?utm_source=chatgpt.com). We then run a short LLM pass to clean up any remaining boilerplate. While functionally similar to the `scrape_and_clean_other_urls` tool from our ingestion layer, this tool operates on a different part of the workflow. The main difference is that it reads from `urls_to_scrape_from_research.md` and writes to the `urls_from_research/` folder, whereas the ingestion scraper reads from `guidelines_filenames.json` and writes to `urls_from_guidelines/`.

## Create the Final `research.md` File

The `create_research_file_tool` is the final step of our entire workflow. It takes all the accumulated research data and formats it into a comprehensive, well-organized markdown file that serves as input for the writing agent we'll build in the next part of the course.

### Understanding the Compilation Process

This tool serves as the final orchestrator, combining all research data into a comprehensive markdown file. It takes the research directory as input and collects content from multiple sources: filtered Perplexity results, scraped guideline sources, code repositories, YouTube transcripts, and additional research sources. The tool organizes everything into collapsible sections and outputs a structured `research.md` file with detailed statistics about the compilation process.

1.  The tool reads from all the intermediate files in the `.nova/` directory and assembles the final `research.md` file.
    ```python
    def create_research_file_tool(research_directory: str) -> Dict[str, Any]:
        """
        Generate comprehensive research.md file from all research data.
        
        Combines all research data including filtered Perplexity results, scraped guideline
        sources, and full research sources into a comprehensive research.md file. The file
        is organized into sections with collapsible blocks for easy navigation.
        """
        # Convert to Path object
        article_dir = Path(research_directory)
        nova_dir = article_dir / NOVA_FOLDER
        
        # Collect all research data
        perplexity_results = read_file_safe(nova_dir / PERPLEXITY_RESULTS_SELECTED_FILE)
        
        # Collect scraped sources from guidelines
        scraped_sources = collect_directory_markdowns_with_titles(nova_dir / URLS_FROM_GUIDELINES_FOLDER)
        code_sources = collect_directory_markdowns_with_titles(nova_dir / URLS_FROM_GUIDELINES_CODE_FOLDER)
        youtube_transcripts = collect_directory_markdowns_with_titles(nova_dir / URLS_FROM_GUIDELINES_YOUTUBE_FOLDER)
        
        # Collect full research sources
        additional_sources = collect_directory_markdowns_with_titles(nova_dir / URLS_FROM_RESEARCH_FOLDER)
        
        # Build comprehensive research sections
        research_results_section = build_research_results_section(perplexity_results)
        scraped_sources_section = build_sources_section("Scraped Sources from Guidelines", scraped_sources)
        code_sources_section = build_sources_section("Code Sources from Guidelines", code_sources)
        youtube_section = build_sources_section("YouTube Transcripts from Guidelines", youtube_transcripts)
        additional_section = build_sources_section("Additional Research Sources", additional_sources)
        
        # Combine all sections into final research file
        research_content = combine_research_sections([
            research_results_section,
            scraped_sources_section,
            code_sources_section,
            youtube_section,
            additional_section
        ])
        
        # Write final research file
        research_file_path = article_dir / RESEARCH_MD_FILE
        research_file_path.write_text(research_content, encoding="utf-8")
        
        return {
            "status": "success",
            "markdown_file": str(research_file_path.resolve()),
            "research_results_count": len(extract_perplexity_chunks(perplexity_results)),
            "scraped_sources_count": len(scraped_sources),
            "code_sources_count": len(code_sources),
            "youtube_transcripts_count": len(youtube_transcripts),
            "additional_sources_count": len(additional_sources),
            "message": f"Successfully created comprehensive research file: {research_file_path.name}"
        }
    ```
    The code itself is standard Python for file I/O and string manipulation, so we will not go into a detailed walkthrough. The key is its role in data aggregation and structured formatting.

### The Research File Structure

The final research file `research.md` is organized into collapsible sections for easy navigation. It will look like the following:
```markdown
# Research Results

## Research Results from Web Search
<details>
<summary>Query: [Original Query]</summary>

### Source [1]: [URL]
[Content from source]

### Source [2]: [URL]
[Content from source]
</details>

## Scraped Sources from Guidelines
<details>
<summary>Source: [Filename]</summary>
[Full scraped content]
</details>

## Code Sources from Guidelines
<details>
<summary>Repository: [Repository Name]</summary>
[Repository analysis and code content]
</details>

## YouTube Transcripts from Guidelines
<details>
<summary>Video: [Video Title]</summary>
[Full video transcript]
</details>

## Additional Research Sources
<details>
<summary>Source: [URL]</summary>
[Full scraped research content]
</details>
```
This structure provides comprehensive coverage while remaining navigable for both humans and AI writing agents.

### Testing the Research File Creation

Now let's test the final compilation tool to see how it brings together all our research data into a comprehensive, well-structured file. This represents the final step of our entire research workflow.

1.  We run the tool and inspect a sample of the final `research.md` file.
    ```python
    from research_agent_part_2.mcp_server.src.tools import create_research_file_tool
    
    # Test creating the final research file
    result = create_research_file_tool(research_directory=research_folder)
    print("Research file creation results:")
    print(result)
    
    # Read and display a sample of the generated research file
    with open(result["markdown_file"], "r") as f:
        content = f.read()
        print("\nFirst 1000 characters of the research file:")
        print(content[:1000] + "...")
    ```
    It outputs:
    ```text
    Research file creation results:
    {'status': 'success', 'markdown_file': '/Users/fabio/Desktop/course-ai-agents/lessons/research_agent_part_2/data/sample_research_folder/research.md', 'research_results_count': 3, 'scraped_sources_count': 6, 'code_sources_count': 2, 'youtube_transcripts_count': 1, 'additional_sources_count': 2, 'message': '✅ Generated research markdown file:\n  - research.md'}
    
    First 1000 characters of the research file:
    # Research
    
    ## Research Results
    
    <details>
    <summary>What are the fundamental limitations of large language models that tool use and function calling aim to solve?</summary>
    
    ### Source [1]: https://hatchworks.com/blog/gen-ai/large-language-models-guide/
    
    Query: What are the fundamental limitations of large language models that tool use and function calling aim to solve?
    
    Answer: Large Language Models (LLMs) have several fundamental technical limitations that tool use and function calling aim to solve:
    
    - **Domain Mismatch**: LLMs trained on general datasets struggle with providing accurate or detailed responses in specialized or niche domains, leading to generic or incorrect outputs when specific expertise is required.
    
    - **Word Prediction Issues**: LLMs often fail with less common words or phrases, affecting their ability to generate or translate technical or domain-specific content accurately.
    
    - **Hallucinations**: LLMs sometimes produce highly original but fabricated information. F...
    ```

This final artifact is the culmination of our agent's work, providing a clean, citable, and comprehensive knowledge base for the writing workflow we will build in Lessons 20-23.

## Human-in-the-Loop (HITL) Controls via MCP

As we saw in the previous lesson, it's possible to integrate human feedback into the research agent workflow by simply providing instructions after invoking the MCP prompt. For example, when running the workflow, users can instruct the agent to:

*   Show the source IDs selected by `select_research_sources_to_keep` and ask for approval before proceeding.
*   Display the URLs chosen by `select_research_sources_to_scrape` and allow modifications.
*   Pause after any step for human review and guidance.

This flexibility allows users to maintain control over the research quality while benefiting from the agent's analytical capabilities. Notice that this is possible because of how the MCP prompt is designed and how the inputs/outputs of the MCP tools are structured.

Because our entire workflow is defined in a server-hosted MCP prompt, we can inject these HITL checkpoints without changing any code [[5]](https://openai.github.io/openai-agents-python/mcp/?utm_source=chatgpt.com). The prompt accepts policy tweaks as plain text. This means you can run the agent in a fully autonomous mode or switch to a supervised mode by simply changing the invocation message. For instance, you could add instructions like "Only keep sources from .edu or .gov domains" or "Select exactly 3 URLs to scrape." This is an effective pattern for building controllable and adaptable AI systems [[6]](https://modelcontextprotocol.io/docs/concepts/prompts?utm_source=chatgpt.com).

## Testing the Complete Agent Workflow

Now let's test the complete end-to-end research agent workflow. We'll use the MCP client to run the full workflow and examine the results.

1.  This code starts the MCP client with an in-memory server, allowing us to interact with the agent.
    ```python
    from research_agent_part_2.mcp_client.src.client import main as client_main
    import sys
    
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
    It outputs:
    ```text
     [1m [95m🤔 LLM's Thoughts: [0m
     [35m**Let's Get This Research Started!**

    Okay, so I'm ready to roll. My first step is to lay out this research workflow – gotta make sure we're on the same page and, critically, that I have the right starting point. I need to explain the steps, and then I'll politely ask for that all-important `research_directory`. I'm also going to check if there are any tweaks or modifications you'd like to make to the process.

    Once that's clear, I'll kick things off by calling `extract_guidelines_urls` to grab the URLs and local files listed in `ARTICLE_GUIDELINE_FILE`. That gives me a solid initial pool to work with.

    Then, the heavy lifting begins. I'll launch several parallel processes to handle different types of resources efficiently. I'll call `process_local_files` for local content, `scrape_and_clean_other_urls` for general web pages, `process_github_urls` for those GitHub repositories (always a good source!), and `transcribe_youtube_urls` for any relevant YouTube videos. Parallel processing is key here for speed.

    Next comes the core research loop. We'll run this three times, each time generating new search queries with `generate_next_queries`. Those queries will then be fed into `run_perplexity_research` to pull in the initial research results.

    Now, we filter. I'll use `select_research_sources_to_keep` to identify and keep only the highest-quality sources from the Perplexity results. This is where expertise comes into play – I need to make sure we're focusing on the good stuff.

    Once the good stuff is identified, I'll identify sources for a complete scrape using `select_research_sources_to_scrape`. Then I'll call `scrape_research_urls` to scrape the selected sources.

    Finally, I'll synthesize everything. I'll call `create_research_file` to compile all the research, cleaned content, scraped pages, and initial sources into a comprehensive `research.md` file.

    Now, a critical point: I need to be prepared for potential hiccups. If *any* of the tools run into trouble and successfully process zero items, I'm going to halt the entire process. I'll state which tool failed and the associated error message, and then I'll ask for your guidance on how to proceed. Better safe than sorry – a failed start could compromise the integrity of the entire process! [0m

     [37m💬 LLM Response:  [0mHello! I will help you execute the Nova research agent workflow. Here are the steps involved:

    1.  **Setup**: I will begin by extracting URLs and local file references from your `ARTICLE_GUIDELINE_FILE`.
    2.  **Process Extracted Resources**: I will then process these extracted resources in parallel:
        *   Copying referenced local files to a dedicated folder.
        *   Scraping and cleaning content from other web URLs.
        *   Processing GitHub URLs using gitinge...
    ...
    ```

Once the client is running, you can:
1.  **Start the complete workflow**: Type `/prompt/full_research_instructions_prompt` to load the complete research workflow.
2.  **Provide the research directory**: Write something like `The research folder is /path/to/research_folder. Run the complete workflow from start to finish.` Remember to replace the path with the actual absolute path to your research folder.
3.  **Examine the final output**: Check the generated `research.md` file.
4.  **Terminate the client**: Type `/quit` after the agent completes all steps.

### Quality Audit Checklist
When you test the agent on different article guidelines, use this checklist to audit the quality of the output:
*   Kept sources come from **reputable** domains (.edu, .gov, official docs, established news); answers support the **specific** guideline sections.
*   Deep-scraped content **reduces reliance** on snippet-level summaries and adds unique insights.
*   `research.md` is **navigable** (collapsible sections), **deduplicated** (no repeated content), and **well-cited** (thanks to structured outputs from Lesson 17).
*   Compare **coverage** (do sources span the guideline?), **trust** (domain mix), and **depth** (do deep scrapes add substance?).

## Use the MCP Server in Cursor

Our research agent can also be used directly within Cursor IDE through the MCP protocol. The `mcp_server` folder contains a `.mcp.json.sample` file that shows how to configure Cursor to use our research agent [[7]](https://cursor.com/docs/context/mcp?utm_source=chatgpt.com).

Here's the content of the `.mcp.json.sample` file:
```json
{
  "mcpServers": {
    "research-agent": {
      "transport": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "/Users/fabio/Desktop/course-agents-writing/src/nova/mcp_server",
        "run",
        "-m",
        "src.server",
        "--transport",
        "stdio"
      ]
    }
  }
}
```

To set this up:
1.  In Cursor, click on "Cursor" in the top bar, then "Settings", then "Cursor Settings", then "MCP", and finally on "New MCP Server". Cursor will open a `mcp.json` file.
2.  Update the `mcp.json` file as shown above. `"research-agent"` is the name of our MCP server that you are connecting Cursor to. You could also have other MCP servers defined in the same file [[8]](https://gofastmcp.com/integrations/mcp-json-configuration?utm_source=chatgpt.com).
3.  Save the `mcp.json` file and restart Cursor. Then, make sure that in the "Cursor Settings" page you see the new "research-agent" MCP server and that it's active. If everything is working fine, it should show the amount of MCP tools, prompts and resources available.
4.  Now, you can use the research agent directly within Cursor. Open a new chat in the AI Pane and write `/research-agent` to see the available MCP prompts. You can write `/research-agent/full_research_instructions_prompt` and send it in the chat to start the complete research workflow.

### Quick Troubleshooting & Tips
*   **Paths:** Ensure the `--directory` path in your `mcp.json` is an **absolute path** and points to your `mcp_server` directory.
*   **Python Environment:** `uv` must be available on your system's `PATH`. You can test the server manually by running `uv run -m src.server --transport stdio` from within the `mcp_server` folder.
*   **API Keys:** Confirm that required environment variables like `GOOGLE_API_KEY` and `FIRECRAWL_API_KEY` are accessible to the server process.

### Ideas for Expanding the Research Agent

The research agent we have built provides a solid foundation that can be extended in several meaningful ways to increase its capabilities and sophistication.

**Domain Whitelisting and Blacklisting**: Consider adding fine-grained control over which domains the source selection tool accepts. This would allow researchers to enforce organizational policies such as excluding certain domains known for low-quality content, or restricting results to specific trusted sources. This control could be configured per research project, giving users flexibility in tailoring the agent's behavior to their specific needs and quality standards.

**Fact-Checking and Quote Extraction**: After scraping sources, a dedicated tool could automatically extract direct quotes and verify claims against multiple sources. This would add a layer of quality assurance to your research output, flagging contradictions or unverified claims and helping you build a more reliable evidence base. The tool could also maintain proper attribution for each quote, making it easier to cite sources accurately in your final article.

**Content Deduplication**: As your research grows across multiple sources, you'll inevitably encounter similar or identical paragraphs and concepts. A deduplication tool could intelligently cluster similar content and merge redundant information, creating a more concise and focused research file. This not only reduces file size and improves readability, but also helps identify the most authoritative source for each piece of information and prevents the writing agent from being overwhelmed by repetitive content.

**Cost Reporting and Analytics**: To maintain budget awareness and optimize your research workflow, consider implementing a cost report tool that tracks all API calls and scraping operations. This tool could provide detailed breakdowns of expenses per research project, per source type, and per workflow stage, helping you identify opportunities for optimization and ensuring your research stays within budget constraints.

## Conclusion

In this lesson, you built a production-minded research agent. It filters Perplexity results for trustworthiness and relevance, selects high-value URLs for full scraping, and compiles all findings into a single, well-cited `research.md` file. The file-first design makes the process auditable, while optional HITL gates provide necessary control.

This matters for several reasons. Automated quality control removes SEO spam and low-trust sources. Resource optimization focuses your budget on high-value content that adds unique value. And because the workflow logic lives in a server-hosted prompt, any MCP client can run the same recipe, ensuring interoperability. You now have a complete research pipeline, from ingestion to a final, structured artifact.

With the research agent complete, the next step is to build the writer agent that will consume this `research.md` file. In Lessons 20-23, we will use LangGraph to create a writing workflow with reflection loops and human oversight to turn raw research into a polished, publishable article.

## References

1. Model Context Protocol. (n.d.). Tools. Model Context Protocol. https://modelcontextprotocol.io/docs/concepts/tools?utm_source=chatgpt.com
2. Perplexity. (n.d.). Structured Outputs. Perplexity. https://docs.perplexity.ai/guides/structured-outputs?utm_source=chatgpt.com
3. Firecrawl. (n.d.). Scrape to Markdown. Firecrawl Docs. https://docs.firecrawl.dev/features/scrape?utm_source=chatgpt.com
4. Firecrawl. (n.d.). Advanced Scraping Guide. Firecrawl Docs. https://docs.firecrawl.dev/advanced-scraping-guide?utm_source=chatgpt.com
5. OpenAI. (n.d.). Model context protocol (MCP). OpenAI GitHub Pages. https://openai.github.io/openai-agents-python/mcp/?utm_source=chatgpt.com
6. Model Context Protocol. (n.d.). Prompts. Model Context Protocol. https://modelcontextprotocol.io/docs/concepts/prompts?utm_source=chatgpt.com
7. Cursor. (n.d.). MCP integration. Cursor. https://cursor.com/docs/context/mcp?utm_source=chatgpt.com
8. FastMCP. (n.d.). MCP JSON configuration. FastMCP. https://gofastmcp.com/integrations/mcp-json-configuration?utm_source=chatgpt.com
