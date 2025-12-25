# AI Agents Need Memory to Thrive
### Unlock personalized AI with long-term memory

## Introduction: Why Agents Need a Memory in the first place

In the previous lessons, we've covered the engineering fundamentals for building agents, from structured outputs and tools to reasoning patterns like ReAct. You now have the core components to make a Large Language Model (LLM) act. But a piece is still missing. Modern LLMs are incredibly knowledgeable, yet their knowledge is frozen at the time of their training. They are unable to learn from new interactions by updating their own weights, a problem known as the challenge of continual learning.

An LLM without memory is like a brilliant intern with severe amnesia. It can answer complex questions and perform tasks, but it forgets who you are and what you discussed the moment the conversation ends. Imagine telling an AI companion you are vegetarian and avoid dairy. In a new session, when you ask for dinner ideas, a system without persistent memory might suggest chicken alfredo, completely forgetting your dietary needs. To build agents that offer personalized and adaptive experiences, we need to engineer a solution for this fundamental limitation.

The primary tool we have for this is the context window, which acts as a form of short-term or "working" memory. By feeding past interactions back to the model, we can give it the illusion of continuity. However, relying solely on the context window is not a scalable solution. It has a finite size, making it impossible to hold long conversation histories. Stuffing it with too much information is also expensive, as you pay for every token you send. Furthermore, it introduces noise; LLMs can get distracted by irrelevant information, and research shows they often struggle to recall details buried in the middle of a long context [[1]](https://www.meibel.ai/post/understanding-the-impact-of-increasing-llm-context-windows).

The engineering landscape for AI agents is constantly changing. Just a couple of years ago, with context windows limited to 8,000 or 16,000 tokens, aggressive compression of memory was a necessity. Early efforts to build personal AI companions, for instance, quickly hit these limits, forcing engineers to develop complex memory systems that heavily relied on summarization and extraction to fit relevant information into the tight context window. Today, models with million-token context windows are becoming common, shifting the engineering challenge from pure compression to more intelligent filtering of a larger, in-context history [[2]](https://storage.googleapis.com/deepmind-media/gemini/gemini_v2_5_report.pdf). However, even with these massive context windows, the need for a persistent, long-term memory system remains. This is where external memory tools come in, providing a practical, stateful layer that allows an agent to "learn" and adapt over time, acting as a crucial workaround for the LLM's inherent inability to continually update its weights.

To understand how to build agents that remember, we first need a useful way to think about memory. We can borrow from biology and cognitive science to understand how memory works in humans and apply it to agents.

## The Layers of Memory: Internal, Short-Term, and Long-Term

To build effective memory systems, we borrow concepts from cognitive science, giving us a clear mental model for how an agent stores and accesses information. We think of an agent's memory as having three distinct layers [[3]](https://connectai.blog/agents-memory), [[4]](https://www.marktechpost.com/2025/03/30/understanding-ai-agent-memory-building-blocks-for-intelligent-systems/).

### Internal Knowledge
Internal Knowledge is the static, pre-trained information baked into the LLM's weights. This provides its vast, general understanding of the world, from facts to linguistic patterns. While powerful, it is read-only; we cannot update it with new user-specific information without fine-tuning. This fixed knowledge is a current limitation, as models cannot update their weights from experience [[5]](https://www.ibm.com/think/topics/ai-agent-memory).

### Short-Term Memory
Short-Term Memory is the agent's active working memory—the LLM's context window. Volatile and limited, it is the only space where information becomes actionable. For the LLM to reason about data, we must load it into this short-term context [[5]](https://www.ibm.com/think/topics/ai-agent-memory).

### Long-Term Memory
Long-Term Memory is an external, persistent storage system, like a database, where the agent saves information across conversations. We store user preferences, past interactions, and learned skills, giving the agent continuity and a sense of history [[6]](https://decodingml.substack.com/p/memory-the-secret-sauce-of-ai-agents).

The real value comes from the dynamic interplay between these layers. We pull information from Long-Term Memory into Short-Term Memory for relevant context. This retrieval process, often part of a larger retrieval pipeline, is core to making an agent context-aware and intelligent. Internal knowledge provides general intelligence, short-term memory handles immediate tasks, and long-term memory offers context and personalization. No single layer performs all three functions effectively.
```mermaid
graph TD
    subgraph Agent Memory Architecture
        A[Long-Term Memory <br/> (External Database)]
        B[Short-Term Memory <br/> (Context Window)]
        C[Internal Knowledge <br/> (LLM Weights)]

        A -- Retrieval --> B
        B -- Actionable Context --> C
    end
```
Figure 1: The hierarchical layers of an AI agent's memory, showing the flow of information from long-term storage into the actionable short-term context window.

To better think about long-term memory, we can further borrow from biology and cognitive science to understand how memory works in humans and apply it to agents.

## Long-Term Memory: Semantic, Episodic, and Procedural

To build a truly capable agent, we need to be more specific about what we store in its long-term memory. Again, we can borrow from cognitive science to categorize long-term memory into three distinct types: semantic, episodic, and procedural. Each type serves a different purpose and is important for different agent behaviors.

### Semantic Memory (Facts & Knowledge)
Semantic memory is the agent's personal encyclopedia. It serves as a repository for discrete, timeless facts about the world, specific domains, or, most importantly, the user. This is where the agent stores extracted concepts and relationships, such as user preferences or key entities. These facts can be individual, independent statements like "User is a vegetarian" or "User has a dog named George". Alternatively, they can be attached to an entity, such as a person, place, or object, like `{"food restrictions": "User is a vegetarian"}`. What you decide to store and how you structure this memory depends heavily on the agent's specific use case.

The primary role of semantic memory is to provide the agent with a reliable source of truth. For an enterprise agent, this might involve storing internal company documents, technical manuals, or an entire product catalog, allowing it to answer questions on proprietary topics. For a personal assistant, semantic memory forms the foundation of a user profile, recalling specific information like preferences, relationships, or hard constraints. This structured knowledge allows the agent to provide personalized and accurate responses without sifting through noisy conversation histories, retrieving relevant and important information as needed.

### Episodic Memory (Experiences & History)
Episodic memory is the agent's personal diary. It functions as a chronological log of its experiences, specifically the interactions it has had with a user. Unlike the timeless facts in semantic memory, episodic memories focus on "what happened and when," adding a crucial element of time to the stored information. For instance, instead of merely knowing a user is frustrated with their brother, an episodic memory might record: "On Tuesday, the user expressed frustration that their brother, Mark, always forgets their birthday, and I provided an empathetic response."

This temporal context allows the agent to recall past events, understand the narrative of a relationship, and interact with more nuance and empathy. For example, an agent could say, "As you expressed last week, I know the topic of your brother's birthday can be sensitive..." if the subject arises again. With the time element, the agent can also answer questions like "What happened on June 8th?" Depending on the use case, these episodic memories can group important events, facts, or insights that occurred over a day, a single conversation, or a week. There is no one-size-fits-all solution; the optimal time scale depends on the product's needs.

### Procedural Memory (Skills & How-To)
Procedural memory is the agent's muscle memory. It represents the collection of skills, workflows, and routines an agent knows how to execute. This "how-to" knowledge dictates its ability to perform multi-step tasks and agents often encode it as functions, tools, or predefined sequences of actions. For example, an agent might have a stored procedure called `MonthlyReportIntent`. When a user requests a monthly update, the agent does not need to reason from scratch. Instead, it retrieves and executes the stored procedure, which defines a clear series of steps: 1) Query the sales database for the last 30 days, 2) Summarize the key findings, and 3) Ask the user for their preferred output format.

This makes the agent's behavior on common, multi-step tasks highly reliable, efficient, and consistent. By encoding successful workflows, procedural memory allows an agent to improve its task completion efficiency over time, reducing errors and ensuring complex jobs are executed consistently every time.

Now that we have an idea of what to save, and the benefits of specific types of memories, how should they be saved or stored? What are the three approaches we can experiment with?

## Storing Memories: Pros and Cons of Different Approaches

How an agent stores its memories is an important architectural decision. This choice impacts performance, complexity, and the ability to scale your product. No single solution fits all needs; the ideal approach depends entirely on your product's use case. Let's explore the trade-offs of three primary methods: storing memories as raw strings, as structured entities like JSON, and within a knowledge graph.

### Storing memories as raw strings
This simple method stores conversational turns or documents as plain text. We typically index them in a vector database for semantic search.
*   **Pros:** This method is easy and fast to implement, requiring little engineering effort. It preserves the full nuance of the original interaction, including emotional tone and subtle linguistic cues that structured formats might lose [[7]](https://www.geeksforgeeks.org/artificial-intelligence/ai-agent-memory/), [[8]](https://dev.to/foxgem/ai-agent-memory-a-comparative-analysis-of-langgraph-crewai-and-autogen-31dp).
*   **Cons:** Retrieval can be imprecise. A query might pull text that is semantically similar but contextually incorrect. A key challenge is updating information. If a user states, "My brother is now a doctor, not a lawyer," the new fact is simply another string in the log, creating a potential contradiction with older entries [[9]](https://diamantai.substack.com/p/memory-optimization-strategies-in). This approach also struggles with temporal reasoning and state changes. It cannot easily distinguish between "Barry *was* the CEO" and "Claude *is* the CEO" because the relationship is not explicitly defined, and the memory lacks the element of time [[7]](https://www.geeksforgeeks.org/artificial-intelligence/ai-agent-memory/), [[9]](https://diamantai.substack.com/p/memory-optimization-strategies-in).

### Storing Memories as Entities (JSON-like Structures)
This approach shifts from unstructured text to structured data. We often use an LLM to extract information and store it in a format like JSON.
*   **Pros:** We organize information into key-value pairs (e.g., `"brother": {"job": "Software Engineer"}`), which allows for precise, field-level queries and easy updates. This method is well-suited for managing semantic memory, such as user profiles and preferences [[10]](https://www.arxiv.org/pdf/2506.06326).
*   **Cons:** This method requires more upfront engineering to design a data schema. A rigid schema might fail to capture information that does not fit its structure. We can let an LLM dynamically add new entities, new fields, or change the structure of the schema, but then updating these memories becomes more complex, with an increased risk of saving duplicated information. The extraction process can also strip away the rich nuance of the original conversation. For example, the factual memory `"user_likes": ["cats"]` conveys less meaning than the original statement, "Petting my cat is the best part of my day." [[7]](https://www.geeksforgeeks.org/artificial-intelligence/ai-agent-memory/).

### Storing Memories in a Knowledge Graph
A knowledge graph offers the most advanced approach. It structures memories as a network of nodes (entities) and edges (relationships).
*   **Pros:** Its core strength lies in explicitly representing complex relationships (e.g., `(User) -> [HAS_BROTHER] -> (Mark)`). This allows for complex, context-aware queries that simple vector search cannot handle. It also allows you to audit the agent's reasoning, as you can trace the exact path that led to an answer [[11]](https://writer.com/engineering/vector-database-vs-graph-database/), [[12]](https://neo4j.com/blog/genai/knowledge-graph-vs-vectordb-for-retrieval-augmented-generation/). Knowledge graphs can also model context and time as explicit properties of a relationship (e.g., `User -[RECOMMENDED_ON_DATE: "2025-10-25"]-> Restaurant`), providing more accurate and grounded retrieval than vector search alone [[12]](https://neo4j.com/blog/genai/knowledge-graph-vs-vectordb-for-retrieval-augmented-generation/).
*   **Cons:** This approach introduces the highest complexity and cost. It requires substantial investment in data modeling, schema design, and maintenance. For many simpler use cases, a graph database adds unnecessary overhead [[13]](https://www.useparagon.com/blog/vector-database-vs-knowledge-graphs-for-rag), [[14]](https://www.elastic.co/blog/vector-database-vs-graph-database/). While powerful, graph traversals for complex queries can be slower than a simple vector lookup, which might impact real-time performance if not carefully optimized [[13]](https://www.useparagon.com/blog/vector-database-vs-knowledge-graphs-for-rag).

💡 **Tip:** Let your product's core needs guide your choice of memory storage. Start with the simplest architecture that delivers value, and evolve it as your agent's demands grow more complex.
```mermaid
graph TD
    subgraph Memory Storage Approaches
        direction LR
        A[Raw Strings]
        B[Structured Entities (JSON)]
        C[Knowledge Graph]

        subgraph "Simplicity vs. Complexity"
            direction LR
            Simplicity -- Increases --> Complexity
        end
        
        A -- "More Structured" --> B
        B -- "More Relational" --> C

        subgraph "Pros & Cons"
            direction TB
            A_Pros["✅ Simple <br> ✅ Preserves Nuance"]
            A_Cons["❌ Imprecise <br> ❌ Hard to Update"]
            B_Pros["✅ Structured <br> ✅ Easy to Update"]
            B_Cons["❌ Loses Nuance <br> ❌ Schema Rigidity"]
            C_Pros["✅ Rich Relationships <br> ✅ Context-Aware"]
            C_Cons["❌ High Complexity <br> ❌ Slower Queries"]
        end

        A --- A_Pros & A_Cons
        B --- B_Pros & B_Cons
        C --- C_Pros & C_Cons
    end
```
Figure 2: A comparison of the three primary approaches to storing agent memories, highlighting the trade-offs between simplicity, structure, and relational complexity.

Now that we know what to save and how to store the memories, let's provide some code examples, using available "memory" tools, like `mem0`.

## Memory implementations with code examples

Now that you understand the types of memories and how they can be stored, let's look at some practical code examples. We use `mem0`, an open-source library designed to help manage agent memory. While we cover Retrieval-Augmented Generation (RAG) in detail in the next lesson, remember that high-quality retrieval depends on high-quality memory creation. Here, we focus on that first step: how memories are formed. For these examples, we use the simple "raw strings" storage approach to focus on the distinct creation process for each memory category.

First, set up `mem0`. It provides a unified interface for adding and searching memories, handling the underlying embedding models and vector stores for you. We configure it to use Google's Gemini for both embeddings and LLM tasks, with a local ChromaDB instance for storage.
```python
from mem0 import Memory
import os

MEM0_CONFIG = {
    # Use Google's text-embedding-004 (768-dim) for embeddings
    "embedder": {
        "provider": "gemini",
        "config": {
            "model": "text-embedding-004",
            "embedding_dims": 768,
            "api_key": os.getenv("GOOGLE_API_KEY"),
        },
    },
    # Use ChromaDB as a local, in-notebook vector store (ephemeral, in-memory)
    "vector_store": {
        "provider": "chroma",
        "config": {
            "collection_name": "lesson9_memories",
        },
    },
    "llm": {
        "provider": "gemini",
        "config": {
            "model": "gemini-1.5-flash",
            "api_key": os.getenv("GOOGLE_API_KEY"),
        },
    },
}

memory = Memory.from_config(MEM0_CONFIG)
MEM_USER_ID = "lesson9_notebook_student"
memory.delete_all(user_id=MEM_USER_ID)
print("✅ Mem0 ready (Gemini embeddings + in-memory Chroma).")
```
It outputs:
```
✅ Mem0 ready (Gemini embeddings + in-memory Chroma).
```

### Semantic Memory: Extracting Facts
We create semantic memory through an extraction pipeline. An LLM processes unstructured text to pull out discrete, atomic facts. This turns messy conversational data into a clean, queryable knowledge base.

For a personal assistant, a prompt might look like this:
```
Extract persistent facts and strong preferences as short bullet points.
- Keep each fact atomic and context-independent.
- Notice nuance and subtle details.
- 3–6 bullets max.

Text:
{My brother Mark is a software engineer, but his real passion is painting. He gifted me a painting a few years ago. It's really beautiful.}
```
The resulting memories would be stored as individual strings: "Mark is the user's brother.", "Mark is a software engineer.", "Mark's real passion is painting.", and "The user has a beautiful painting from Mark."

Here's how we add these facts using our `mem0` setup:
```python
facts: list[str] = [
    "User prefers vegetarian meals.",
    "User has a dog named George.",
    "User is allergic to gluten.",
    "User's brother is named Mark and is a software engineer.",
]
for f in facts:
    memory.add(f, user_id=MEM_USER_ID, metadata={"category": "semantic"}, infer=False)

# Search for a specific fact
results = memory.search("brother job", user_id=MEM_USER_ID, limit=1)
print(results['results'][0]['memory'])
```
It outputs:
```
User's brother is named Mark and is a software engineer.
```
When retrieving semantic memory, `mem0.search` uses semantic search to find the most contextually relevant fact. For example, a query like "brother job" will find the stored memory "User's brother is named Mark and is a software engineer" because of their semantic similarity. More advanced retrieval methods, such as hybrid search, combine keyword filtering with semantic relevance, and we will explore these in the next lesson.

### Episodic Memory: The Log of Events
Episodic memory functions as a chronological log. We create it by summarizing interactions over a period, like a day or a single conversation, and storing the summary with a timestamp. This captures the "what" and "when" of an interaction. These memories can be stored as raw conversation text or as summaries extracted by an LLM. When stored raw, the memory is the event itself, requiring no extraction prompt. However, for summarized memories, an LLM processes the conversation to extract key insights, facts, or events, which are then saved with a timestamp.

Let's take a short dialogue and create an episodic memory from it. We use the LLM to summarize it, then store that summary.
```python
dialogue = [
    {"role": "user", "content": "I'm stressed about my project deadline on Friday."},
    {"role": "assistant", "content": "I’m here to help—what’s the blocker?"},
    {"role": "user", "content": "Mainly testing. I also prefer working at night."},
    {"role": "assistant", "content": "Okay, we can split testing into two sessions."},
]

# Using mem0's built-in summarization (infer=True)
memory.add(dialogue, user_id=MEM_USER_ID, metadata={"category": "episodic"}, infer=True)

# Retrieve the episode
results = memory.search("deadline stress", user_id=MEM_USER_ID, limit=1, metadata={"category": "episodic"})
print(f"- [created_at={results['results'][0].get('created_at')}] {results['results'][0]['memory']}")
```
It outputs:
```
- [created_at=2025-08-25T17:26:28.260452-07:00] The user is stressed about a project deadline on Friday, with testing being the main issue. They prefer working at night, and a solution was proposed to split the testing into two sessions.
```
The summary captures the essence of the interaction, creating a memory of that specific event. Retrieval from episodic memory often blends temporal and semantic queries. You can filter by a date range, for example, to ask "What did we talk about yesterday?" or use semantic search to find conversations contextually similar to your current query, then re-rank the results by recency.

### Procedural Memory: Defining and Learning Skills
We create procedural memory in two ways: a developer defines it, or an agent learns it from user instructions. A developer can explicitly code a tool or function, like `book_flight()`, that an agent can trigger during a conversation. More advanced agents can learn new procedures dynamically from user interactions. When a user provides explicit steps for a task, the agent can save this sequence as a new, callable procedure for future use.

Let's teach our agent a procedure called "monthly_report".
```python
def learn_procedure(name: str, steps: list[str]) -> str:
    body = "Procedure: " + name + "\nSteps:\n" + "\n".join(f"{i + 1}. {s}" for i, s in enumerate(steps))
    memory.add(body, user_id=MEM_USER_ID, metadata={"category": "procedure", "procedure_name": name}, infer=False)
    return f"Learned procedure: {name}"

# Teach the agent the skill
learn_procedure(
    "monthly_report",
    [
        "Query sales DB for the last 30 days.",
        "Summarize top 5 insights.",
        "Ask user whether to email or display.",
    ],
)

# Retrieve the procedure by name
results = memory.search("monthly_report", user_id=MEM_USER_ID, limit=1, metadata={"category": "procedure"})
print(results['results'][0]['memory'])
```
It outputs:
```
Procedure: monthly_report
Steps:
1. Query sales DB for the last 30 days.
2. Summarize top 5 insights.
3. Ask user whether to email or display.
```
Now, when a user asks for a monthly report, the agent can retrieve these steps and execute them, demonstrating its learned skill. Retrieval for procedural memory is an intent-matching and function-calling process. The agent receives descriptions of all available procedures, both built-in and user-taught. It then compares the user's current request against these descriptions. If the user says, "Let's find a summer cabin again," the agent recognizes the semantic similarity to its learned `find_summer_cabin` procedure and executes it, showing a form of learning and adaptation.

While these code examples show the mechanics of creating different memory types, building a production-ready system involves more than just calling an API. Let's look at the hard-won lessons from deploying these systems in the real world.

## Real-World Lessons: Challenges and Best Practices

The architectural patterns we have discussed provide a solid foundation, but moving from a prototype to a production-ready system requires navigating complex trade-offs that are constantly reshaped by rapid technological advances. Here are three key lessons you learn from building and scaling agent memory systems.

### Re-evaluating compression
The trade-off between compressing information and preserving its raw detail has fundamentally shifted. Just two years ago, with small context windows of 8k or 16k tokens, you had to be aggressive with compression. You distilled every interaction into concise summaries or facts to fit within tight constraints. This process was necessary, but it often lost the nuance and emotional subtext of a conversation [[15]](https://www.youtube.com/watch?v=7AmhgMAJIT4&list=PLDV8PPvY5K8VlygSJcp3__mhToZMBoiX&index=112).

Today's models, with million-token context windows, change how you approach this [[2]](https://storage.googleapis.com/deepmind-media/gemini/gemini_v2_5_report.pdf). The best practice is now to use less compression. The raw conversational history is the ultimate source of truth. A semantic fact like "User has a dog" is less valuable than the episodic memory "User mentioned that walking their dog is the best part of their day." The latter contains rich context that is vital for a truly personalized agent.

To implement this, design your system to work with the most complete version of history that is economically and technically feasible. Use extraction and summarization to create efficient indexes for retrieval, but always treat the raw log as the ground truth. As context windows expand, your pipeline may need to do less *retrieving* and more intelligent *filtering* of a large, in-context history [[16]](https://arxiv.org/html/2406.06110v1).

### Designing for the Product
There is no "perfect" memory architecture. Semantic, episodic, and procedural memory are powerful concepts, but they are a toolkit, not a mandatory blueprint. The most common failure is over-engineering a complex system for a product that does not need it. You might feel tempted to build a system that handles all memory types from day one. This often leads to unnecessary complexity, higher maintenance costs, and slower performance.

To avoid this, start from first principles by defining the core function of your agent. The product's goal should dictate the memory architecture, not the other way around [[17]](https://www.speakeasy.com/mcp/ai-agents/architecture-patterns), [[18]](https://www.youtube.com/watch?v=W2HVdB4Jbjs). For a Q&A bot over internal documents, a simple knowledge base is enough. For a personal companion, rich episodic memory that captures the narrative of your relationship is key. For a task automation agent, procedural memory is the priority.

### The Human Factor: Avoiding Cognitive Overhead
Memory exists to make the agent smarter, not to give the user a new job. A common issue is exposing the internal workings of the memory system, thinking it improves transparency. In practice, it often creates a difficult user experience. Early memory implementations often allowed users to view, edit, and delete the facts an agent stored about them. While well-intentioned, this creates considerable cognitive overhead [[19]](https://www.letta.com/blog/agent-memory).

You should not ask users to "garden their agent's memories." This breaks the illusion of a capable assistant and turns the interaction into a data-entry task. Memory management must be an autonomous function of the agent [[20]](https://arxiv.org/html/2506.06326), [[21]](https://www.vincirufus.com/posts/memory-based-agent-learning/). The agent should learn from corrections within the natural flow of conversation (e.g., "Actually, my brother's name is Mark, not Mike"). It is the agent's responsibility, not the user's, to periodically review, consolidate, and resolve conflicting information in its memory [[22]](https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/memory-management-for-ai-agents/4406359).

## Conclusion

Memory is a core component for transforming a simple chatbot into a truly personalized and adaptive agent. By giving agents the ability to remember past interactions, user preferences, and learned skills, we enable them to build context, maintain continuity, and "learn" over time. The frameworks and techniques we have discussed, from the different layers and types of memory to the trade-offs in storage, provide an essential and practical toolkit for any AI engineer looking to build robust agentic applications.

It is important to remember that these external memory systems are, for now, a clever engineering workaround for the fundamental inability of current LLMs to achieve true continual learning. They are a temporary but highly effective solution that works today, bridging a critical gap in LLM capabilities. As the underlying models evolve, potentially incorporating more native learning mechanisms, so too will our approaches to memory management.

We have focused on how to create and categorize memories. The next logical step is to understand how to efficiently retrieve the right memory at the right time. That is the subject of our next lesson, Lesson 10, which will be a deep dive into Retrieval-Augmented Generation (RAG). From there, we will continue our journey by building, monitoring, and evaluating complete agentic systems, equipping you with the knowledge to deploy, maintain, and continually improve sophisticated AI agents in real-world scenarios, moving ever closer to production-ready AI.

## References

- [1] [Understanding the Impact of Increasing LLM Context Windows](https://www.meibel.ai/post/understanding-the-impact-of-increasing-llm-context-windows)
- [2] [Gemini 2.5 Pro Technical Report](https://storage.googleapis.com/deepmind-media/gemini/gemini_v2_5_report.pdf)
- [3] [Agents memory](https://connectai.blog/agents-memory)
- [4] [Understanding AI Agent Memory: Building Blocks for Intelligent Systems](https://www.marktechpost.com/2025/03/30/understanding-ai-agent-memory-building-blocks-for-intelligent-systems/)
- [5] [What is AI agent memory?](https://www.ibm.com/think/topics/ai-agent-memory)
- [6] [Memory: The secret sauce of AI agents](https://decodingml.substack.com/p/memory-the-secret-sauce-of-ai-agents)
- [7] [AI Agent Memory](https://www.geeksforgeeks.org/artificial-intelligence/ai-agent-memory/)
- [8] [AI Agent Memory: A Comparative Analysis of LangGraph, CrewAI, and AutoGen](https://dev.to/foxgem/ai-agent-memory-a-comparative-analysis-of-langgraph-crewai-and-autogen-31dp)
- [9] [Memory Optimization Strategies in AI Agents](https://diamantai.substack.com/p/memory-optimization-strategies-in)
- [10] [MemoryOS: A Novel Memory Management System for AI Agents](https://www.arxiv.org/pdf/2506.06326)
- [11] [Vector database vs. graph database: What’s the difference?](https://writer.com/engineering/vector-database-vs-graph-database/)
- [12] [Knowledge Graph vs Vector Database for Retrieval-Augmented Generation](https://neo4j.com/blog/genai/knowledge-graph-vs-vectordb-for-retrieval-augmented-generation/)
- [13] [Vector Database vs Knowledge Graphs for RAG](https://www.useparagon.com/blog/vector-database-vs-knowledge-graphs-for-rag)
- [14] [Vector database vs. graph database](https://www.elastic.co/blog/vector-database-vs-graph-database)
- [15] [What is the perfect memory architecture?](https://www.youtube.com/watch?v=7AmhgMAJIT4&list=PLDV8PPvY5K8VlygSJcp3__mhToZMBoiX&index=112)
- [16] [Recurrent Context Compression: Efficiently Expanding the Context Window of LLM](https://arxiv.org/html/2406.06110v1)
- [17] [AI Agents: Architecture & Patterns](https://www.speakeasy.com/mcp/ai-agents/architecture-patterns)
- [18] [AI Agent Memory Management: A Deep Dive](https://www.youtube.com/watch?v=W2HVdB4Jbjs)
- [19] [Agent Memory](https://www.letta.com/blog/agent-memory)
- [20] [MemoryOS: A Novel Memory Management System for AI Agents](https://arxiv.org/html/2506.06326)
- [21] [Introducing Memento: A Memory-Based Learning Framework for AI Agents](https://www.vincirufus.com/posts/memory-based-agent-learning/)
- [22] [Memory management for AI agents](https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/memory-management-for-ai-agents/4406359)