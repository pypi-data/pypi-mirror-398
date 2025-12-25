## What We Are Planning to Share

In this lesson we plan to share the first step into building Brown the writing workflow, laying down the foundations of the workflow. To do so, we will go a lot into how to apply good context engineering principles to instruct the LLM into writing professional articles. To get there, we will have to model through Pydantic models multiple domain objects such as multiple writing profiles, few shot examples, and the user inputs such as the article guideline and research. We will learn how to aggregate all these items into a well structured prompts that adheres to good context engineering practices. Also, we will write from scratch the orchestrator-worker pattern used to dynamically generate media items required for the final article.

## Why We Think It’s Valuable

Even if we will focus on writing article, We think that this is an amazing exercise to learn how to properly do context engineering for complex problems that require you to write huge system prompts that follow multiple dimensions. Learning how to guide the LLM reason through huge system prompts is not that straighforward. Thus, in this lesson we want you to show how to do that, while laying down the foundations of Brown the writing workflow.

## Who Is the Intended Audience

Aspiring AI engineers who are learning for the first time about AI agents and workflows. People who transition from other fields, such as data engineering, data science or software engineering and want to learn more about building AI agents and workflows.

⚠️ *EVERYTHING WILL BE WRITTEN RELATIVE TO THE LEVEL AND PERSPECTIVE OF THIS INTENDED AUDIENCE.*

## Theory / Practice Ratio

**15% theory – 85% practice**

## Point of View

The course is created by a team writing for a single reader, also known as the student. Thus, for voice consistency across the course, we will always use 'we,' 'our,' and 'us' to refer to the team that creates the course, and 'you' or 'your' to address the reader. Avoid using the singular 'I’ and don't use 'we' to refer to the student.

## Anchoring the Lesson in the Course

### Details About the Course

This piece is part of a broader course on AI agents and LLM workflows. The course consists of 4 parts, each with multiple lessons. 

Thus, it's essential to always anchor this piece in the broader course, understanding where the reader is in their journey. You will be careful to consider the following:

- To not reintroduce concepts already taught in the previous lesson.
- To be careful when talking about concepts introduced only in future lessons
- To always reference previous and future lessons when discussing topics outside the piece's scope.

### Course Syllabus

In previous lessons of the course, we introduced the following concepts:

**Part 1:**

- **L01 - AI Engineering & Agent Landscape**: Understanding the role, the stack, and why agents matter now
- **L02 - Workflows vs. Agents**: Grasping the crucial difference between predefined logic and LLM-driven autonomy
- **L03 - Context Engineering**: The art of managing information flow to LLMs
- **L04 - Structured Outputs**: Ensuring reliable data extraction from LLM responses
- **L05 - Basic Workflow Ingredients**: Implementing chaining, routing, parallel and the orchestrator-worker patterns
- **L06 - Agent Tools & Function Calling**: Giving your LLM the ability to take action
- **L07 - Planning & Reasoning**: Understanding patterns like ReAct (Reason + Act)
- **L08 - Implementing ReAct**: Building a reasoning agent from scratch
- **L09 - Agent Memory & Knowledge**: Short-term vs. long-term memory (procedural, episodic, semantic)
- **L10 - RAG Deep Dive**: Advanced retrieval techniques for knowledge-augmented agents
- **L11 - Multimodal Processing**: Working with documents, images, and complex data

**Part 2A - Overall Capstone projects Presentation:**

- **L12** — Presenting the capstone projects at a high level
- **L13** — AI framework trade‑offs
- **L14** — Capstone projects system design & cost levers.

**Part 2B - Nova Deep Research Agent:**

- **L15** — Presenting the project structure and design of the Nova deep research agent
- **L16** — MCP foundations (server/client; **tools/resources/prompts**; server‑hosted prompt).
- **L17** — Ingestion layer (guideline URL extraction; local/GitHub/YouTube ingest; Firecrawl scraping; file‑first design).
- **L18** — Research loop (generate queries → **Perplexity** with **structured outputs** → optional HITL between steps).
- **L19** — Testing out the Nova deep research agent

**Part 2C - Brown the Writing Workflow:**

- **L20** — Presenting the project structure and design of the Brown writing workflow
- **L21** — Presenting the system design and architecture of Brown the writing workflow
- **🚨 *<<< L22 — Implementing the foundations of Brown the writing workflow (such as applying the orchestrator-worker pattern to generate media items + context engineering to write high-quality articles that follow a specific pattern) >>> CURRENT LESSON - REFERENCE PREVIOUS AND FUTURE LESSONS RELATIVE TO THIS ONE***
- **L23** — Applying the evaluator-optimizer pattern to the Brown writing agent to automatically review and edit the article to automatically force adherence to expected requirements
- **L24** - Expanding Brown the writing agent with multiple editing workflow that let’s you edit the whole article or just a piece of selected text. Everything is exposed as tools through MCP servers to facilitate human in the loop cycles

**Part 2D:**

- Orchestrating both MCP Servers (Nova + Brown) within a single MCP client, automating the whole logic as a unified workflow
- Demo showing how we used Nova + Brown to research and write professional articles or lessons.

**Part 3:**

With both the capstone projects built, this section focuses on the engineering practices required for production:

- AI Evals
- Prompt and system monitoring
- Tracking costs, latency, performance, and other metrics
- Deployment, Scaling to GCP
- Serve the app over the internet
- MCP Security
- CI/CD
- units tests

**Part 4:**

- In this final part of the course, you will build and submit your own advanced LLM agent, applying what you've learned throughout the previous sections. We provide a complete project template repository, enabling you to either extend our agent pipeline or build your own novel solution. Your project will be reviewed to ensure functionality, relevance, and adherence to course guidelines for the awarding of your course certification.

### CURRENT LESSON:

Now we are writing lesson …

## Anchoring the Reader in the Educational Journey

Within the course, we are teaching the reader multiple topics and concepts. Thus, understanding where the reader is in their educational journey is critical for this lesson. You have to use only previously introduced concepts, while being reluctant about using concepts that haven't been introduced yet.

When discussing concepts introduced in previous lessons, avoid reintroducing them to the reader. Especially don't reintroduce the acronyms. Use them as if the reader already knows what they are. 

Avoid using the concepts that will only be introduced in future lessons. Whenever a concept from the current lesson requires references to concepts from future lessons, instead of directly using them, use intuitive analogies or explanations that are more general and easier to understand, as you would explain them to a 7-year-old. For example:

- If the "tools" concept wasn't introduced yet, and you have to talk about tool calling agents, refer to them as "actions".
- If the "routing" concept wasn't introduced yet and you have to talk about it, refer to it as "guiding the workflow between multiple decisions".

The idea is that if you have to use a concept that hasn’t been introduced yet, use real-world analogies that anyone can understand instead of specialized terminology. 

You can use the concepts that haven't been introduced yet only if we explicitly specify them in this guideline. Still, even in that case, as the reader doesn't know how that concept works, you are only allowed to use the term, while keeping the explanation extremely high-level and intuitive, as if you were explaining it to a 7-year-old.

Whenever you use a concept from future lessons, explicitly specify in what lesson it will be explained in more detail. If the lesson number is unclear, specify the part, such as part 3 or 4.

In all use cases, avoid using acronyms that aren't explicitly stated in the guidelines. Rather, use other, more accessible synonyms or descriptions that are easier to understand by non-experts.

## Narrative Flow of the Lesson

- Follow the next narrative flow when writing the end‑to‑end lesson:
- What problem are we learning to solve? Why is it essential to solve it?
- Why other solutions are not working and what's wrong with them.
- At a theoretical level, explain our solution or transformation. Highlight:
    - The theoretical foundations.
    - Why is it better than other solutions?
    - What methods or algorithms can we use?
- Provide simple examples or diagrams where useful.
- Go deeper into the advanced theory.
- Provide a more complex example supporting the advanced theory.
- Connect our solution to the bigger field of AI Engineering. Add course next steps.

---

## Lesson Outline

1. Introduction
2. The Writing Workflow Architecture
3. Modeling our Domain Entities as Context for LLMs
4. Understanding the Secret Sauce of Writing Professional Articles: The Writing Profiles
5. Unifying LLM Calls
6. Generating Media Items Using the Orchestrator-Worker Pattern
7. The Anatomy of a Prompt
8. Understanding the ArticleWriter Node
9. Conext Engineering Introspection
10. Running the Writing Workflow
11. Conclusion


## Section  1 - Introduction

- **Quick reference to what we've learned in previous lessons:**  One sentence on what we’ve learnt in previous lessons, with a focus on lessons 20 and 21 as they are part of teaching the Brown capstone project
- **Transition to what we'll learn in this lesson:** After presenting what we learned in the past, make a transition to what we will learn in this lesson. Take the core ideas of the lesson from the `What We Are Planning to Share` section and highlight the importance and existence of the lesson based on the `Why We Think It’s Valuable` section.

- **Transition:** Enumerate what we are going to learn in this lesson with bullet points. Focus on outcomes of this lesson. Don’t blindly list the outline.

- **Section length:** 250 words

## Section 2 - The Writing Workflow Architecture

- High-level overview of how the writing workflow works
    1. First step is to load all the necessary context into memory, such as the article guideline, research, few-shot-examples, and writing profiles. Quickly explain what each does.
    2. Next step is to generate all the required media items using the orchestrator-worker pattern through the MediaGeneratorOrchestrator class + all it's available tools such as the MermaidDiagramGenerator tool
    3. The final step is to pass everything as context into the ArticleWriter which will output the article
    4. Generate a mermaid diagram with the 3 steps
- Explain that in this lesson, we will explain how to implement these 3 steps, hands-on!

- **Transition:** Let's start with going through all the entities, how we model them, and what's their role. 

- **Section length:** 300 words (without the code, URL, or mermaid diagram’s code)

## Section 3 - Modeling our Domain Entities as Context for LLMs

- Start with a note that based on our project structure and design lesson these are the entities classes, which are part (the cornerstone) of the domain layer, that’s sits at the bottom and contains orthogonal components that will be used all over the applications.
- Next, we want an on-depth section over the entities and their relationship to the context. To do so, we will load each component into memory from `inputs/examples/course_lessons`, `inputs/profiles` and `inputs/tests/01_sample_small` directories, which we will use an example within this lesson and assume they exist on disk. To do so, we will follow the code from the provided notebook as follows:
    1. Set the input directories as constants
    2. Explain the `ContextMixin` entity
        1. Follow the steps from the Notebook: Explain the code
        2. Explain why this interface it’s so important to make transitions between Python objects from software v1.0 to LLM context in software v3.0. Like this we force each entity to implement a method that makes this translation. take more ideas from the Notebook example
    3. Explain the `ArticleGuideline` entity - Follow the steps from the Notebook:
        - Explain the code
        - Load an example
        - Show the raw example
        - Show the example after calling `to_context()`
    4. Explain the `Research` entity - Follow the steps from the Notebook:
        - Explain the code
        - Load an example
        - Show the raw example
        - Show the example after calling `to_context()`
    5. Explain the `ArticleExamples` entity - Follow the steps from the Notebook 
        1. Follow the steps from the Notebook:
            - Explain the code
            - Load an example
            - Show the raw example
            - Show the example after calling `to_context()`
        2. Then continue with a note on explaining how the few-shot-examples are actually your on-demand "training set” and they are one of the most powerful way to configure how the output should look like. They should contain diverse examples. In our use case, we can consider as an example the whole article for the overall structure, but as the articles are long also each section is an example, as each one can be diverse containing text, mermaid diagram code, PYthon code, examples, images, etc.

- **Transition:** Now, let's move on to the writing profiles. As they are extremely important, we dedicated a whole seciton to them.

- **Section length:** 500 words (without the code, URL, or mermaid diagram’s code)

## Section 4 - Understanding the Secret Sauce of Writing Professional Articles: The Writing Profiles

- In-depth walkthrough over the writing profiles. These profiles will be passed to the writing agent. Thus, it's critical to understand how they work.
- Explain the python implementation of the profiles entities - Follow the steps from the Notebook:
    - Explain the code
    - Load an example
    - Show the raw examples
    - Show the examples after calling `to_context()`
- Specify which are used in general for guiding the LLM to write professional content and which are targeted for specific use cases such as articles and voice. These two can be leverage to further customize the workflow on your liking, such as switching from writing articles to writing LinkedIn posts or video transcripts and swithcing from the Paul Iusztin voice to your's voice or another popular character such as Richard Feynmann.
- Next, explain the role of each profile in-depth, which are the key to the writing workflow. These profiles will be passed to the writing agent. Thus, it's critical to understand how they work. Explain how each works:
    1. Mechaniscs Profile (General to any content type):
        - Make a 2 sentences summary of it's role based on the content of the mechaniscs profile that can be found within the <research> marked as part of `inputs/profiles/mechanics_profile.md`
        - Copy paste, highlight and output some key parts of the file as such:
            - Active vs. passive voice usage
            - Point of View
            - Punctuation preferences
        - Add a link to `inputs/profiles/mechanics_profile.md` for the reader to read the whole file
    2. Structure Profile (General to any content type):
        - Make a 2 sentences summary of it's role based on the content of the mechaniscs profile that can be found within the <research> marked as part of `inputs/profiles/structure_profile.md`
        - Copy paste, highlight and output some key parts of the file as such:
            - Sentence and paragraph length patterns
            - Sections Sub-Heading Formatting
            - Formatting Media
            - Formatting Code
        - Add a link to `inputs/profiles/structure_profile.md` for the reader to read the whole file
    3. Terminology Profile (General to any content type):
        - Make a 2 sentences summary of it's role based on the content of the mechaniscs profile that can be found within the <research> marked as part of `inputs/profiles/terminology_profile.md`
        - Copy paste, highlight and output some key parts of the file as such:
            - Word Choice Patterns
            - Descriptive Language Patterns
            - AI Slop Banned Expressions List
        - Add a link to `inputs/profiles/terminology_profile.md` for the reader to read the whole file
    4. Tonality Profile (General to any content type):
        - Make a 2 sentences summary of it's role based on the content of the mechaniscs profile that can be found within the <research> marked as part of `inputs/profiles/tonality_profile.md`
        - Copy paste, highlight and output some key parts of the file as such:
            - Primary voice characteristics
            - Formality level
            - On-Brand Tones (Desired)
            - Off-Brand Tones (Undesired)
        - Add a link to `inputs/profiles/tonality_profile.md` for the reader to read the whole file
    5. Article Profile (Specific to articles):
        - Make a 2 sentences summary of it's role based on the content of the mechaniscs profile that can be found within the <research> marked as part of `inputs/profiles/article_profile.md`
        - Copy paste, highlight and output some key parts of the file as such:
            - General Article Structure
            - Introduction, Section, Conclusion Guidelines
            - Narrative Flow of the Article
            - Referencing Ideas Between Sections
            - References
        - Add a link to `inputs/profiles/article_profile.md` for the reader to read the whole file
    6. Character Profiles (Specific to a given voice): Used to inject a particular voice, either yours, such as Paul Iusztin or from another popular character such as Richard Feynmann 
        - Make a 2 sentences summary of it's role based on the content of the mechaniscs profile that can be found within the <research> marked as part of `inputs/profiles/character_profiles/paul_iusztin.md`
        - Copy paste, highlight and output some key parts of the file as such:
            - About Paul Iusztin
            - Similar Personas
            - Style
        - Add a link to `inputs/profiles/character_profiles/paul_iusztin.md` for the reader to read the whole file

- **Section length:** 650 words (without the code, URL, or mermaid diagram’s code)

## Section 5 - Unifying LLM Calls

- **Transition:** The last step before digging into the implementation of the actual workflow is to understand how we implemented a unified layer to call LLMs.

- Explain how we model the `models` . Before starting to dig into the nodes and run the writing workflow, Make a paranthesis where we explain the `models` dir and how we actually call the models. Explain the code from models/config and models/get_model. 
    1. Start by explaining the `get_model` function
    2. Next move on to the `ModelConfig`, `SupportedModels` and `DEFAULT_MODEL_CONFIGS` structures
    3. Explain that we will use these methods to instantiate and configure models everywhere within the codebase and that the ModelConfig allows us to configure different models at each node from the workflow
    4. show the example + the output from the example Notebook

- **Section length:** 400 words (without the code, URL, or mermaid diagram’s code)

## Section 6 - Generating Media Items Using the Orchestrator-Worker Pattern

- **Transition:** Finally, let's dig into the actual workflow which is composed of two main nodes, one powered by the orchestartor-worker pattern to generate media items and the last one used to write the actual article. 

- Add another note highlighing that even the nodes are still part of the domain layer, as each node makes sense on it’s own and contains domain logic. Each node is a self-contained piece of business logic, which is orthogonal, and can be composed as lego blocks into specific workflows. Hence, we will use these nodes, into all our specific workflows, such as the generating or editing workflows. 
- In this section, we will start by explaining the `MediaGeneratorOrchestrator` node which uses the orchestartor-worker pattern and in the next section explain the article wrtier node.
- We will explain the orchestartor-worker pattern following closely the code from the Notebook as follows:
    1. First, we have to explain the Node, Toolkit and ToolCall interfaces as base abstractions shared across all our nodes
    2. Explain the MediaGeneratorOrchestrator class following step-by-step the logic from the Notebook
    3. Now we actually need to hook some workers as tools, thus explain the ToolNode interface as explain in the Notebook
    4. Explain the MermaidDiagramGenerator class as explain in the Notebook
    5. Walk people through the hands-on example presented in the Notebook showing how we use these classes and the output
    6. Talk about how we model multimodal inputs using the text from the example Notebook

- **Transition:** Before presenting the article writer node, let's have a quick recap on how the anatomy of a prompt looks like. As the article writer has a huge system prompt, this will be important to understand how we designed it.

- **Section length:** 600 words (without the code, URL, or mermaid diagram’s code)

## Section 7 - The Anatomy of a Prompt

- Write 2 paragraps on the anatomy of a prompt based on Antrophic's facts loaded within the <research>. Based on the prompt structure go over the key elements:
    1. Task context
    2. Tone context
    3. Background data
    4. Detailed task descriptio and rules
    5. Examples
    6. Conversation history
    7. Immediate task description or request
    8. Thinking step by step
    9. Output formatting
    10. Prefilled response (if any)
- Attach an image from the research from Antrophic's anatomy of a prompt facts
- Highlight how these fields are either directly or indirectly reflected into the system prompt. For example the output formatting can be handled by the API provided  as we've seen in the structured output lesson

- **Transition:**Finally, let's move to the article writer node that combines everything we learned so far into the final article piece.

- **Section length:** 400 words (without the code, URL, or mermaid diagram’s code)

## Section 8 - Understanding the ArticleWriter Node

- Explain the `ArticleWriter` class - Follow closely the steps from the Notebook for the following parts of the class:
        1. The class + the init method 
        2. The ainvoke method (completely ignore the logic related to self.reviews, ArticleReviews, SelectedTextReviews - focus only on the logic for one-shot article generation, without reviews)
- When explaining the `system_prompt_template` of the `ArticleWriter` class we want to dig deeper that what we have in the Notebook. Still, you will completely ignore the system prompts related to reviews, such as article_reviews_prompt_template and selected_text_reviews_prompt_template and focus ONLY on the `system_prompt_template`. When explaining it you will:
    - Apply the learning from the `The Anatomy of a Prompt` section to this system prompt
    - When applying the learnings from `The Anatomy of a Prompt` you will divide the system prompt into multiple groups based and explain each group individually. On how to format this, you can use the exact formatting as we do with normal code.

- **Section length:** 600 words (without the code, URL, or mermaid diagram’s code)

Here is the FULL content of the `system_prompt_template` variable:
<system_prompt_template>
```python
class ArticleWriter(Node):
    system_prompt_template = """
You are Brown, a professional human writer specialized in writing technical, educative and informational articles
about AI. 

Your task is to write a high-quality article, while providing you the following context:
- **article guideline:** the user intent describing how the article should look like. Specific to this particular article.
- **research:** the factual data used to support the ideas from the article guideline. Specific to this particular article.
- **article profile:** rules specific to writing articles. Generic for all articles.
- **character profile:** the character you will emporsonate while writing. Generic for all content.
- **structure profile:** Structure rules guiding the final output format. Generic for all content.
- **mechanics profile:** Mechanics rules guiding the writing process. Generic for all content.
- **terminology profile:** Terminology rules guiding word choice and phrasing. Generic for all content.
- **tonality profile:** Tonality rules guiding the writing style. Generic for all content.

Each of these will be carefully considered to guide your writing process. You will never ignore or deviate from these rules. These
rules are your north star, your bible, the only reality you know and operate on. They are the only truth you have.

## Character Profile

To make the writing more personable, you will emporsonate the following character profile. The character profile 
will anchor your identity and specify things such as your:
- **personal details:** name, age, location, etc.
- **working details:** company, job title, etc.
- **artistic preferences:** it's niche, core content pillars, style, tone, voice, etc.

What to avoid using the character profile for:
- explicitly mentioning the character profile in the article, such as "I'm Paul Iusztin, founder of Decoding AI." Use
it only to impersonate the character and make the writing more personable. For example if you are "Paul Iusztin",
you will never say all the time "I'm Paul Iusztin, founder of Decoding AI." as people already know who you are.
- using the character profile to generate article sections, such as "Okay, I'm Paul Iusztin, founder of Decoding AI. 
Let's cut through the hype and talk real engineering for AI agents." Use the character profile only to adapt the
writing style and introduce references to the character. Nothing more.

Here is the character profile:
{character_profile}

## Research

When using factual data to write the article, anchor your results exclusively in information from the given 
<research> or <article_guideline> tags. Avoid, at all costs, using factual information from your internal knowledge.

The <research> will contain most of the factual data to write the article. But the user might add additional information
within the <article_guideline>. 

Thus, always prioritize the factual data from the <article_guideline> over the <research>.

Here is the research you will use as factual data for writing the article:
{research}

## Article Examples

Here is a set of article examples you will use to understand how to write the article:
{article_examples}

## Tonality Profile

Here is the tonality profile, describing the tone, voice and style of the writing:
{tonality_profile}

## Terminology Profile

Here is the terminology profile, describing how to choose the right words and phrases:§
to the target audience:
{terminology_profile}

## Mechanics Profile

Here is the mechanics profile, describing how the sentences and words should be written:
{mechanics_profile}

## Structure Profile

Here is the structure profile, describing general rules on how to structure text, such as the sections, paragraphs, lists,
code blocks, or media items:
{structure_profile}

## Media Items

Within the <article_guideline>, the user requested to include all types of media items, such as tables, diagrams, images, etc. Some of the 
media items will be present inside the <research> or <article_guideline> tags as links. But often, we will have to generate the 
media items ourselves.

Thus, here is the list of media items that we already generated before writing the article that should be included as they are:
{media_items}

The list contains the <location> of each media item to know where to place it within the article. The location is the section title, 
inferred from the <article_guideline> outline. Based on the <location>, locate the generated media item within the <article_guideline>, 
and use it as is when writing the article.

Replace the media item requirements from the <article_guideline> with the generated media item and it's caption. We always
want to group a media item with it's caption.

## Article Profile

Here is the article profile, describing particularities on how the end-to-end article should look like:
{article_profile}

## Article Guideline: 

Here is the article guideline, representing the user intent, describing how the actual article should look like:
{article_guideline}

You will always start understand what to write by reading the <article_guideline>.

As the <article_guideline> represents the user intent, it will always have priority over anything else. If any information
contradicts between the <article_guideline> and other rules, you will always pick the one from the <article_guideline>.

Avoid using the whole <research> when writing the article. Extract from the <research> only what is useful to respect the 
user intent from the <article_guideline>. Still, always anchor your content based on the facts from the <research> or <article_guideline>.

Always priotize the facts directly passed by the user in the <article_guideline> over the facts from the <research>. Avoid at all costs 
to use your internal knowledge when writing the article.

The <article_guideline> will ALWAYS contain:
- all the sections of the article expected to be wrriten, in the correct order
- a level of detail for each section, describing what each section should contain. Depending on how much detail you have in a
particular section of the <article_guideline>, you will use more or less information from the <research> tags to write the section.

The <article_guideline> can ALSO contain:
- length constraints for each section, such as the number of characters, words or reading time. If present, you will respect them.
- important (golden) references as URLs or titles present in the <research> tags. If present, always prioritize them over anything else 
from the <research>.
- information about anchoring the article into a series such as a course or a book. Extremely important when the article is part of 
something bigger and we have to anchor the article into the learning journey of the reader. For example, when introducing concepts
in previous articles that we don't want to reintroduce into the current one.
- concrete information about writing the article. If present, you will ALWAYS priotize the instructions from the <article_guideline> 
over any other instructions.

## Article Outline

Internnaly, based on the <article_guideline>, before starting to write the article, you will plan an article outline, 
as a short summary of the article, describing what each section contains and in what order.

Here are the rules you will use to generate the article outline:
- The user's <article_guideline> always has priority! If the user already provides an article outline or a list of sections, 
you will use them instead of generating a new one.
- If the section titles are already provided in the <article_guideline>, you will use them as is, with 0 modifications.
- Extract the core ideas from the <article_guideline> and lay them down into sections.
- Your internal description of each section will be verbose enough for you to understand what each section contains.
- Ultimately, the CORE scope of the article outline is to have an internal process that verifies that each section is anchored into the
<article_guideline>, <research> and all the other profiles.
- Before starting writing the final article, verify that the flow of ideas between the sections, from top to bottom, 
is coherent and natural.

## Chain of Thought

1. Plan the article outline
2. Write the article following the article outline and all the other constraints.
3. Check if all the constraints are respected. Edit the article if not.
4. Return ONLY the final version of the article.

With that in mind, based on the <article_guideline>, you will write an in-depth and high-quality article following all 
the <research>, guidelines and profiles.
"""
```
</system_prompt_template>

## Section 8 - Conext Engineering Introspection

- **Transition:** As a wrap-up section, we want to quickly add a few sentences on The trade-off between isolating context (v1) + adding everything everything into a one-shot (v2). There has to be balance between "specialized LLM calls" and more generic ones. 
    1. Inspired from the transition of Brown's v1 architecture to it's v2 architecture (as we've seen in Lesson 21): As you start having more "specialized LLM calls or agents" you start having more LLM calls + your context get's fragmented. Thus, you have to find the right balance to avoid high latency, costs and overcomplicating the solution
    2. You can also leverage ideas from the <research> to expand on this topic.
- Conclusion from our learnings:
    - Always start simple, as close to one shot LLM calls.
    - Add specialized LLM calls / Agents only when the performance start's to degrade.
    - Never start the other way around: from specialized to simple!
    - Still, how can you trully measure performance more than just vibe checks? Based on AI Evals, which we will learn in Part 3.

- **Transition:** Now, before wrapping up, let's run the whole workflow end-to-end on a more complex example.

- **Section length:** 200 words (without the code, URL, or mermaid diagram’s code)

## Section 9 - Running the Writing Workflow

- Final section showing how to run the whole thing, by brining in all the logic from previous sections and using the `inputs/tests/02_sample_medium` directory as an example. Show the example from the Notebook step-by-step with the code blocks and outputs.
    - Step 1: Load all the context
    - Step 2: Generate media items
    - Step 3: Write the article
    (Show all the code + output!)
- Provide some final notes related to code design as follows:
    1. Note at the end how we had to glue all our domain components to actually generate an end-to-end article. here is where the application layer kicks in. It doesn’t contain a lot of core logic, but just glues together orthogonal components from the domain layer. 
    2. Also, note how infrastructure elements such as the file loaders, renderers or the models do not pollute the domain objects or the overall application logic, but are just injected into them through composition. Which means, we can easily abstract away the application logic through interfaces and swap them with different implementations, such as using S3 Loaders/Renderers instead of local disk ones.

- **Section length:** 250 words (without the code, URL, or mermaid diagram’s code)

## Section 10 - Conclusion
(Connect our solution to the bigger field of AI Engineering. Add course next steps.)

- One sentence conclusion remembering people why this is important based on the `Why We Think It’s Valuable` section.
- What we've learnt:
        1. context engineering: how to properly do context engineering and combine multiple dimensions of your business logic into a system prompt that your LLM can properly reason on 
        2. How we defined our interfaces through the ContextMixin, Node, Toolkit, etc. interfaces for modularity, flexibility, composability, while still not being overly rigid and complex
        3. how to implement from scratch the orchestrator-worker pattern for generating media items
        4. how we merged everythign together into our ArticleWriter node
- Ideas on how you can further extend this code:
        1. Add image and video generation support within the Orchestrator-Worker layer
        2. Reduce costs and latency
            1. Cache constant inputs between LLM calls, such as the research and profiles, to avoid recomputing them
            2. Compress the research relative to the article guideline
        3. Extend the writer to other media formats such as social media posts, email newsletter articles, technical documentation or video transcripts
        4. Add different character profiles along our Paul Iusztin one
- To transition from this lesson to the next, specify what we will learn in future lessons. Mention in a more detailed sentence what we will learn in the next lesson, which is Lesson 23 (in the next lesson we will learn how to automate reviewing and editing with the evaluator-optimizer pattern and how to glue everything together into a LangGraph workflow). Then, very slightly what we will learn in Lesson 24, such as adding the human in the loop by implementing the editing workflows and exposing them as an MCP server.

- Section length: 250 words

## Lesson Code

Links to code that will be used to support the lesson. Always prioritize this code over every other piece of code found in the sources:

1. [Notebook](https://github.com/towardsai/agentic-ai-engineering-course/blob/dev/lessons/22_foundations_writing_workflow/notebook.ipynb)


## Golden Sources

1. [Prompting 101 | Code w/ Claude](https://www.youtube.com/watch?v=ysPbXH0LpIE)
2. [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
3. [Anthropic just revealed their internal prompt engineering template - here's how to 10x your Claude results](https://www.reddit.com/r/PromptEngineering/comments/1n08dpp/anthropic_just_revealed_their_internal_prompt/)
4. [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)

## Documentation
4. [LangChain Models](https://reference.langchain.com/python/langchain/models/)