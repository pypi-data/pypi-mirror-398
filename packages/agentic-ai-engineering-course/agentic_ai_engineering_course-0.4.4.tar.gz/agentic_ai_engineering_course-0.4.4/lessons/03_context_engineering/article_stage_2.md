# TITLE NOT AVAILABLE
### SUBTITLE NOT AVAILABLE

## When prompt engineering breaks

AI applications have evolved rapidly. In 2022, we had simple chatbots for question-answering. By 2023, Retrieval-Augmented Generation (RAG) systems connected Large Language Models (LLMs) to domain-specific knowledge. 2024 brought us tool-using agents that could perform actions. Now, we are building memory-enabled agents that remember past interactions and build relationships over time (more on memory in Lesson 9).

In our last lesson, we explored how to choose between AI agents and LLM workflows when designing a system. As these applications grow more complex, prompt engineering, a practice that once served us well, is showing its limits. It optimizes single LLM calls, but fails when managing systems with memory, actions, and long interaction histories. The sheer volume of information an agent might need—past conversations, user data, documents, and action descriptions—has grown exponentially. Simply stuffing all this into a prompt is not a viable strategy. This is where context engineering comes in. It is the discipline of orchestrating this entire information ecosystem to ensure the LLM gets exactly what it needs, when it needs it. This skill is becoming a core foundation for AI engineering, much like fine-tuning.

## The Problem: Context Decay and Overload

Prompt engineering, while effective for simple tasks, is designed for single, stateless interactions. It treats each call to a Large Language Model (LLM) as a new, isolated event. This approach breaks down in stateful applications where context must be preserved and managed across multiple turns.

As a conversation or task progresses, the context grows. Without a strategy to manage this growth, the LLM’s performance degrades. This is context decay: the model gets confused by the noise of an ever-expanding history. It starts to lose track of original instructions or key information.

Even with large context windows, a physical limit exists for what you can include. Every token adds to the cost and latency of an LLM call. Simply putting everything into the context creates a slow, expensive, and unreliable system. We will explore these concepts in more detail in upcoming lessons, including memory in Lesson 9 and Retrieval-Augmented Generation (RAG) in Lesson 10.

On a recent project, we learned this the hard way. We were working with a model that supported a two-million-token context window, so we thought, "What could go wrong?" We stuffed everything in: our research, guidelines, examples, and user history. The result was an LLM workflow that took 30 minutes to run and produced low-quality outputs.

This is where context engineering becomes essential. It shifts the focus from crafting static prompts to building dynamic systems that manage information flow. As AI engineers, your job is to select only the most critical pieces of context for each LLM call. This makes your applications accurate, fast, and cost-effective.

## Understanding Context Engineering

## Understanding context engineering

Context engineering is about finding the best way to arrange information from your memory into the context passed to a Large Language Model (LLM). It is an optimization problem. You retrieve the right parts from your short-term and long-term memory to solve a specific task without overwhelming the model. For example, when you ask a cooking agent for a recipe, you do not give it the entire cookbook. Instead, you retrieve the specific recipe, along with personal context like allergies or taste preferences. This precise selection ensures the model receives only the essential information, making its responses more accurate, faster, and more cost-effective.

Andrej Karpathy explains that LLMs are like a new kind of operating system where the model is the CPU and its context window is the RAM [[36]](https://addyo.substack.com/p/context-engineering-bringing-engineering). Just as an operating system manages what fits into your computer’s limited RAM, context engineering manages what information occupies the model’s limited context window.

Prompt engineering is not dead. It is a subset of context engineering. You still write effective prompts. But you also design a system that feeds the right context into those prompts. This means understanding not just *how* to phrase a task, but *what* information the model needs to perform optimally.

| Dimension | Prompt Engineering | Context Engineering |
|-----------|-------------------|---------------------|
| Scope | Single interaction optimization | Entire information ecosystem |
| State Management | Stateless function | Stateful due to memory |
| Focus | How to phrase tasks | What information to provide |
Table 1: A comparison of prompt engineering and context engineering.

Context engineering is the new fine-tuning. Fine-tuning has its place, but it is expensive, time-consuming, and inflexible. Data changes constantly, making fine-tuning a last resort [[41]](https://www.tabnine.com/blog/your-ai-doesnt-need-more-training-it-needs-context/). For most enterprise use cases, you get better results faster and more cheaply with context engineering [[43]](https://www.tribe.ai/applied-ai/fine-tuning-vs-prompt-engineering). It allows for rapid iteration and adaptation to evolving data without altering the core model, a key advantage in dynamic environments. This approach avoids the computational resources and specialized expertise required for retraining, offering a more agile path to reliable AI applications.

When you start a new AI project, your decision-making process for guiding the Large Language Model (LLM) looks like this:```mermaid
graph TD
    prompt_eng_decision{\"Prompt Engineering?\"}
    context_eng_decision{\"Context Engineering?\"}
    fine_tune_dataset_decision{\"Can fine-tuning dataset be created?\"}
    stop_prompt[\"Stop\"]
    stop_context[\"Stop\"]
    fine_tune_stop[\"Fine-tune and Stop\"]
    reframing[\"Suggest reframing the problem\"]

    prompt_eng_decision -->|\"Yes\"| stop_prompt
    prompt_eng_decision -->|\"No\"| context_eng_decision
    context_eng_decision -->|\"Yes\"| stop_context
    context_eng_decision -->|\"No\"| fine_tune_dataset_decision
    fine_tune_dataset_decision -->|\"Yes\"| fine_tune_stop
    fine_tune_dataset_decision -->|\"No\"| reframing
```
Figure 1: A decision-making workflow for choosing between prompt engineering, context engineering, and fine-tuning.

For instance, if you build an agent to process internal Slack messages, you do not need to fine-tune a model on your company’s communication style. It is more effective to use a powerful reasoning model. Engineer the context to retrieve specific messages and enable actions like creating tasks or drafting emails. This avoids the overhead of fine-tuning for specific communication nuances. Throughout this course, we show you how to solve most industry problems using context engineering.

## What makes up the context

To master context engineering, you first need to understand what "context" actually is. It is everything the Large Language Model (LLM) sees in a single turn. We dynamically assemble it from various memory components before passing it to the model.

We will walk through the high-level workflow. A user input triggers the system to pull relevant information from both long-term and short-term memory. This information assembles into the final context, inserts into a prompt template, and sends to the LLM. The LLM’s answer then updates the memory, and the cycle repeats (more on memory in Lesson 9).```mermaid
graph TD
    A[User Input] --> B{Long-Term Memory};
    B --> C{Short-Term Working Memory};
    C --> D[Context Assembly];
    D --> E[Prompt Template];
    E --> F[Prompt];
    F --> G((LLM Call));
    G --> H[Answer];
    H --> C;
    subgraph Memory Update
        H --> I{Update Short-Term Memory};
        I --> J{Update Long-Term Memory};
    end
```
Figure 2: The high-level workflow of how context is assembled and used in an AI system.

These components group into two main categories. We explain them intuitively for now, as we have not formally introduced these concepts yet.

### Short-term working memory
Short-term working memory is the state of the agent for the current task or conversation. It is volatile and changes with each interaction. This memory helps the agent maintain a coherent dialogue and make immediate decisions. It includes:
*   **User input:** The most recent query or command from the user. This is the immediate focus for the LLM.
*   **Message history:** The log of the current conversation. This allows the LLM to understand the flow and previous turns, ensuring continuity.
*   **Agent's internal thoughts:** The reasoning steps the agent takes to decide on its next action. These thoughts guide the agent's problem-solving process.
*   **Action calls and outputs:** The results from any actions the agent has performed. These provide real-time feedback from external systems, informing the agent's next steps.

### Long-term memory
Long-term memory is more persistent and stores information across sessions. This allows the AI system to remember things beyond a single conversation, building a deeper understanding over time. We divide it into three types, drawing parallels from human memory [[16]](https://arxiv.org/html/2504.15965v1):
*   **Procedural memory:** This is knowledge encoded directly in the system's design. It includes the system prompt, which sets the agent's overall behavior, the definitions of available actions, which tell the agent what it can do, and schemas for structured outputs (more on structured outputs in Lesson 4), which guide the format of its responses. Think of this as the agent's built-in skills or instincts.
*   **Episodic memory:** This is memory of specific past experiences, like user preferences or previous interactions. It helps the agent personalize its responses by recalling individual user histories. We typically store this in vector or graph databases, allowing for efficient retrieval of relevant past events.
*   **Semantic memory:** This is the agent’s general knowledge base. It can be internal, like company documents stored in a vector database, or external, accessed via the internet through API calls or web scraping (more on RAG in Lesson 10). This memory provides the factual information and general understanding the agent needs to answer questions and perform tasks.
![A Venn diagram showing that Context Engineering encompasses RAG, Prompt Engineering, State/History, Memory, and Structured Outputs.](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-03-own-your-context-window.md)

Figure 3: Context engineering encompasses a variety of techniques and information sources. (Media from [[2]](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-03-own-your-context-window.md))

If this seems like a lot, bear with us. We will cover all these concepts in-depth in future lessons, including structured outputs (Lesson 4), actions (Lesson 6), memory (Lesson 9), and RAG (Lesson 10).

The key takeaway is that these components are not static. We dynamically re-compute them for every single interaction. For each conversation turn or new task, the short-term memory grows or the long-term memory can change. Context engineering involves knowing how to select the right pieces from this vast memory pool to construct the most effective prompt for the task at hand.

## Challenges in Context Engineering

Now that we understand context engineering, let's look at the core challenges when implementing it in AI agents and Large Language Model (LLM) workflow solutions. All these challenges revolve around a single question: "How can I keep my context as small as possible while providing enough information to the LLM?"

Here are four common issues that come up when building AI applications:

1.  **The context window challenge:** Every AI model has a limited context window. This is the maximum amount of information, measured in tokens, it can process simultaneously. Think of it like your computer's RAM. If your machine has only 32GB of RAM, that is all it can process at one time. While context windows are getting larger, they are not infinite, and treating them as such leads to other problems.

2.  **Information overload:** Just because you can fit a lot of information into the context does not mean you should. Too much context reduces the performance of the LLM by confusing it. This is known as the "lost-in-the-middle" or "needle in the haystack" problem. LLMs are well-known for mostly remembering what is at the top and bottom of the context window. Processing what is in the middle is always a lottery. Performance often drops long before the physical context limit is reached [[55]](https://www.unite.ai/why-large-language-models-forget-the-middle-uncovering-ais-hidden-blind-spot/), [[8]](https://openreview.net/forum?id=5sB6cSblDR).

3.  **Context drift:** This occurs when conflicting views of truth accumulate in the memory over time [[28]](https://viso.ai/deep-learning/concept-drift-vs-data-drift/). For example, you might have conflicting statements about the same concept, such as "My cat is white" and "My cat is black." This is not quantum physics or the Schrödinger Cat experiment, but it confuses the LLM and prevents it from knowing what to pick. Without a mechanism to resolve these conflicts, the LLM becomes confused, and its responses become unreliable [[31]](https://erikjlarson.substack.com/p/context-drift-and-the-illusion-of).

4.  **Tool confusion:** This problem arises in two main ways. First, adding too many actions to an AI agent or workflow can confuse the LLM about the best action for the job. This often happens with over 100 actions [[38]](https://support.talkdesk.com/hc/en-us/articles/39096730105115--Preview-AI-Agent-Platform-Best-Practices). We will learn more about patterns like the orchestrator-worker in Lesson 5. Secondly, tool confusion can appear when action descriptions are poorly written or have unclear separations. If descriptions are not clearly separated or overlap, it is a recipe for disaster. Even a human would not know what to pick in that case [[49]](https://www.forrester.com/blogs/the-state-of-ai-agents-lots-of-potential-and-confusion/).

## Context Optimization Strategies

At the beginning, most AI applications were chatbots over single knowledge bases. But for most AI applications today, this is no longer the case. Modern AI solutions require access to multiple knowledge bases and actions, and manage complex histories. Context engineering is all about managing this complexity while staying within the desired performance, latency, and cost requirements.

Here are four of the most popular context engineering strategies used across the industry:

### Selecting the right context

Retrieving the right information from memory to form the context for a given task is important. A common mistake when building AI products is providing everything into the context at once. Often, the reasoning is that if they work with models that can handle up to 2 million input tokens, the model can handle all that input. But as mentioned in the previous section, due to the "lost-in-the-middle" problem this often results in poor performance. It also translates to increased latency and costs.

To solve this, consider these approaches:
*   Use structured outputs: Define clear schemas for what the LLM should return. This allows you to pass only the necessary, structured information to downstream steps, rather than a verbose natural language response. We will cover this in detail in Lesson 4.
*   Use Retrieval-Augmented Generation (RAG): Instead of providing entire documents, use RAG to fetch only the specific chunks of text needed to answer a user's question. This is a core topic we will explore in Lesson 10.
*   Reduce the number of available actions: Rather than giving an agent access to every available action, use a RAG-based approach to dynamically select a small, relevant subset of actions for each task. Studies show that limiting the selection to under 30 actions can triple action selection accuracy [[45]](https://productschool.com/blog/artificial-intelligence/ai-agents-product-managers).
*   Rank time-sensitive data: For time-sensitive information, rank it by date and filter out anything no longer relevant.
*   Repeat core instructions: For the most important instructions, repeat them across the prompt, at both the start and the end. This leverages the model's tendency to pay more attention to the context edges, ensuring core directives are not lost [[56]](https://promptmetheus.com/resources/llm-knowledge-base/lost-in-the-middle-effect).```mermaid
graph TD
    subgraph "Context Selection"
        A[Memory] --> B{Information Retrieval};
        B -->|RAG| C[Relevant Facts];
        B -->|Tool Selection| D[Relevant Tools];
        B -->|History Ranking| E[Relevant History];
        C --> F[Optimized Context];
        D --> F;
        E --> F;
    end
```
Figure 4: A workflow for selecting the right context from various memory sources.

### Context compression

As the message history grows in the short-term working memory, you have to carefully manage past interactions to keep your context window in check. You cannot just drop past conversation turns, as the LLM still needs to remember what happened. Thus, we need ways to compress key facts from the past while shrinking the short-term memory.

We can do that through:
*   Create summaries of past interactions using an LLM: This replaces a long, detailed history with a concise overview.
*   Move user preferences to long-term memory: Transfer user preferences from working memory to long-term episodic memory (more on episodic memory in Lesson 9). This keeps the working context clean while ensuring preferences are remembered for future sessions.
*   Deduplicate to avoid repetition: This helps remove redundant information from the context.```mermaid
graph TD
    subgraph "Context Compression"
        A[Long Message History] -- LLM Call --> B(Summarize);
        B --> C[Compressed History];
        A -- LLM Call --> D(Extract Preferences);
        D --> E[Long-Term Episodic Memory];
    end
```
Figure 5: Compressing context by summarizing history and extracting preferences to long-term memory.

### Isolating context

Another powerful strategy is to isolate context by splitting information across multiple agents or LLM workflows. Instead of one agent with a massive, cluttered context window, you can have a team of agents, each with a smaller, focused context.

We often implement this using an orchestrator-worker pattern, where a central orchestrator agent breaks down a problem and assigns sub-tasks to specialized worker agents (more on the orchestrator-worker pattern in Lesson 5) [[12]](https://www.confluent.io/blog/event-driven-multi-agent-systems/). Each worker operates in its own isolated context, improving focus and allowing for parallel processing.```mermaid
graph TD
    A[User Request] --> B(Orchestrator Agent);
    B --> C{Worker Agent 1<br>(Context A)};
    B --> D{Worker Agent 2<br>(Context B)};
    B --> E{Worker Agent 3<br>(Context C)};
    C --> F[Results];
    D --> F;
    E --> F;
```
Figure 6: The orchestrator-worker pattern isolates context across multiple specialized agents.

### Format optimization

Finally, the way you format the context matters. Models are sensitive to structure. Using clear delimiters can improve performance.
*   Use XML tags: Wrap different pieces of context in XML-like tags (e.g., `<user_query>`, `<documents>`). This helps the model distinguish between different types of information [[5]](https://milvus.io/ai-quick-reference/what-modifications-might-be-needed-to-the-llms-input-formatting-or-architecture-to-best-take-advantage-of-retrieved-documents-for-example-adding-special-tokens-or-segments-to-separate-context).
*   Prefer YAML over JSON: When providing structured data as input, YAML is often more token-efficient than JSON, which helps save space in your context window.

💡 A final note: Always understand what is passed to the LLM. Seeing exactly what occupies your context window at every step is key to mastering context engineering for your LLM applications.

## Here is an example

We connect the theories and strategies discussed earlier with concrete examples. Context engineering is fundamental for many advanced AI applications that need to manage memory and maintain state across interactions.

Consider several real-world scenarios where keeping context in memory across multiple conversation turns or user sessions is essential:
*   **Healthcare:** An AI assistant accesses a patient's medical history (episodic memory), current symptoms (working memory), and the latest medical literature (semantic memory) to provide personalized diagnostic support [[52]](https://www.akira.ai/blog/context-engineering).
*   **Financial Services:** AI systems integrate with enterprise tools like Customer Relationship Management (CRM) systems and calendars, combining real-time market data and client portfolio information to generate tailored financial advice [[50]](https://66degrees.com/building-a-business-case-for-ai-in-financial-services/).
*   **Project Management:** AI systems access enterprise infrastructure such as Customer Relationship Management (CRM) systems, Slack, Zoom, Calendars, and task managers to automatically understand project requirements, then add and update project tasks.
*   **Content Creator Assistant:** An AI agent uses your research, past content, personality traits, and lesson guidelines to understand what and how to create a given piece of content.

Let's walk through a specific query to see context engineering in action. A user asks their healthcare assistant: `I have a headache. What can I do to stop it? I would prefer not to take any medicine.`

Before the AI attempts to answer, a context engineering system performs several steps:
1.  It retrieves the user's patient history, known allergies, and lifestyle habits from episodic memory.
2.  It queries a medical database for non-pharmacological headache remedies, retrieving relevant information from semantic memory.
3.  It uses various actions to assemble the key units of information from both memory types into the final context (we will discuss actions in more detail in Lesson 6).
4.  It formats this information into a structured prompt and calls the Large Language Model (LLM).
5.  Finally, it presents a personalized, context-aware answer to the user.

Here is a simplified Python example showing how you might structure the prompt for the LLM, using XML tags to format the different context elements. We use XML to differentiate pieces from the context, which helps with clarity and order.

1.  First, we define the user's query:```python
user_query = "I have a headache. What can I do to stop it? I would prefer not to take any medicine."
```

2.  Next, we define the patient's history, which would typically be retrieved from episodic memory, such as a vector database:```python
patient_history = """
- Patient: John Doe, 45M
- Known Conditions: Mild hypertension
- Allergies: None
- Preferences: Avoids medication unless necessary. Prefers natural remedies.
- Habits: Reports high stress from work, drinks 3-4 cups of coffee daily.
"""
```

3.  Then, we include relevant medical literature, which would be retrieved from semantic memory, perhaps through Retrieval-Augmented Generation (RAG) from a medical database:```python
medical_literature = """
- Article 1: Dehydration is a common cause of tension headaches. Rehydration can alleviate symptoms within 30 minutes to three hours.
- Article 2: Applying a cold compress to the forehead and temples can constrict blood vessels and reduce inflammation, helping to relieve migraine pain.
- Article 3: Caffeine withdrawal can trigger headaches. For individuals who consume caffeine regularly, a small amount may alleviate a withdrawal headache.
- Article 4: Stress-relief techniques such as deep breathing, meditation, or a short walk can be effective for tension headaches.
"""
```

4.  Finally, we assemble the complete prompt, combining the system instructions, patient history, medical literature, and user query into a structured format:```python
prompt = f"""
<system_prompt>
You are a helpful AI medical assistant. Your role is to provide safe, helpful, and personalized health advice based on the provided context. Do not give advice outside of the provided context. Prioritize non-medicinal options as per user preference.
</system_prompt>

<patient_history>
{patient_history}
</patient_history>

<medical_literature>
{medical_literature}
</medical_literature>

<user_query>
{user_query}
</user_query>

<instructions>
Based on all the information above, provide a step-by-step plan for the user to relieve their headache. Structure your response clearly.
</instructions>
"""
```

5.  Printing the assembled prompt shows the final input sent to the LLM:```python
print(prompt)
```
It outputs:```
<system_prompt>
You are a helpful AI medical assistant. Your role is to provide safe, helpful, and personalized health advice based on the provided context. Do not give advice outside of the provided context. Prioritize non-medicinal options as per user preference.
</system_prompt>

<patient_history>
- Patient: John Doe, 45M
- Known Conditions: Mild hypertension
- Allergies: None
- Preferences: Avoids medication unless necessary. Prefers natural remedies.
- Habits: Reports high stress from work, drinks 3-4 cups of coffee daily.
</patient_history>

<medical_literature>
- Article 1: Dehydration is a common cause of tension headaches. Rehydration can alleviate symptoms within 30 minutes to three hours.
- Article 2: Applying a cold compress to the forehead and temples can constrict blood vessels and reduce inflammation, helping to relieve migraine pain.
- Article 3: Caffeine withdrawal can trigger headaches. For individuals who consume caffeine regularly, a small amount may alleviate a withdrawal headache.
- Article 4: Stress-relief techniques such as deep breathing, meditation, or a short walk can be effective for tension headaches.
</medical_literature>

<user_query>
I have a headache. What can I do to stop it? I would prefer not to take any medicine.
</user_query>

<instructions>
Based on all the information above, provide a step-by-step plan for the user to relieve their headache. Structure your response clearly.
</instructions>
```

To build such a system, you need a robust tech stack. Here is a potential stack we recommend and will use throughout this course:
*   **LLM:** Gemini as a multimodal, reasoning, and cost-effective LLM API provider (we will cover multimodal LLMs in Lesson 11).
*   **Orchestration:** LangGraph for defining stateful, agentic workflows.
*   **Databases:** PostgreSQL, MongoDB, Redis, Qdrant, and Neo4j as databases. Often, it is effective to keep it simple, as you can achieve much with only PostgreSQL or MongoDB.
*   **Observability:** Opik or LangSmith for observability, including evaluation and monitoring (we will explore evaluations in future lessons).

## Conclusion

Context engineering is more of an art than a science. It is about developing the intuition to craft effective prompts, select the right information from memory, and arrange context for optimal results. This discipline helps you determine the minimal yet essential information an LLM needs to perform at its best.

This discipline cannot be learned in isolation. It is a complex yet beautiful field that combines:
1.  **AI Engineering:** LLM workflows, RAG, and AI Agents. This includes implementing evaluation pipelines (more on evaluations in future lessons).
2.  **Software Engineering (SWE):** Aggregating all context elements into scalable and maintainable code. This involves designing scalable architectures and wrapping agents as APIs.
3.  **Data Engineering:** Building data pipelines to feed information into the long-term memory.
4.  **Operations (Ops):** Deploying your agents on the right infrastructure to ensure they are reproducible, maintainable, observable, and scalable. This also means automating processes and writing Continuous Integration/Continuous Delivery (CI/CD) pipelines.

Our goal is to teach you how to master these skills. In the world of AI, we should all think in systems rather than isolated components. We will show you how to build production-ready AI applications.

To transition from this lesson, we will next explore structured outputs in Lesson 4. Later in the course, we will delve into actions (Lesson 6), memory (Lesson 9), and RAG (Lesson 10).

## References

- [2] https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-03-own-your-context-window.md
- [5] https://milvus.io/ai-quick-reference/what-modifications-might-be-needed-to-the-llms-input-formatting-or-architecture-to-best-take-advantage-of-retrieved-documents-for-example-adding-special-tokens-or-segments-to-separate-context
- [8] https://openreview.net/forum?id=5sB6cSblDR
- [12] https://www.confluent.io/blog/event-driven-multi-agent-systems/
- [16] https://arxiv.org/html/2504.15965v1
- [28] https://viso.ai/deep-learning/concept-drift-vs-data-drift/
- [31] https://erikjlarson.substack.com/p/context-drift-and-the-illusion-of
- [35] https://www.llamaindex.ai/blog/context-engineering-what-it-is-and-techniques-to-consider
- [36] https://addyo.substack.com/p/context-engineering-bringing-engineering
- [38] https://support.talkdesk.com/hc/en-us/articles/39096730105115--Preview-AI-Agent-Platform-Best-Practices
- [41] https://www.tabnine.com/blog/your-ai-doesnt-need-more-training-it-needs-context/
- [43] https://www.tribe.ai/applied-ai/fine-tuning-vs-prompt-engineering
- [45] https://productschool.com/blog/artificial-intelligence/ai-agents-product-managers
- [49] https://www.forrester.com/blogs/the-state-of-ai-agents-lots-of-potential-and-confusion/
- [50] https://66degrees.com/building-a-business-case-for-ai-in-financial-services/
- [52] https://www.akira.ai/blog/context-engineering
- [55] https://www.unite.ai/why-large-language-models-forget-the-middle-uncovering-ais-hidden-blind-spot/
- [56] https://promptmetheus.com/resources/llm-knowledge-base/lost-in-the-middle-effect