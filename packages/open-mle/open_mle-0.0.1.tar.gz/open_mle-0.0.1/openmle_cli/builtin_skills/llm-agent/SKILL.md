---
name: llm-agent
description: Build LLM-powered agents with tool use, RAG pipelines, multi-agent systems, and agentic workflows
---

# LLM Agent Skill

## Description

This skill covers building intelligent agents powered by large language models (LLMs). It includes prompt engineering, tool/function calling, memory systems (short-term and long-term), RAG (Retrieval Augmented Generation) pipelines, multi-agent architectures, and agentic workflows using frameworks like LangChain and LangGraph. Use this skill when building conversational AI, task automation systems, research assistants, code generators, or any application requiring multi-step reasoning and tool use.

LLM agents excel at combining reasoning, planning, and action execution. They can break down complex tasks, use external tools, retrieve relevant information, and maintain context across interactions. This skill emphasizes production-ready implementations with proper error handling, evaluation, and safety measures.

## When to Use

- When building conversational AI or chatbots with tool access
- When implementing RAG systems for question answering over documents
- When creating task automation agents (web scraping, data analysis, coding)
- When designing multi-agent systems with specialized roles
- When user requests prompt engineering or optimization
- When implementing function calling or tool use for LLMs
- When building memory systems for context persistence
- When creating agentic workflows with state management (LangGraph)
- When implementing semantic search with vector databases
- When adding AI capabilities to existing applications

## How to Use

### Step 1: Design Agent Architecture

**Choose appropriate agent pattern:**

**ReAct (Reasoning + Acting):**
- Interleave thought → action → observation steps
- Best for: tool use, multi-step tasks with external APIs
- Example: "I need to search for X, then analyze Y, then summarize"

**Chain-of-Thought (CoT):**
- Step-by-step reasoning before final answer
- Best for: math, logic, complex reasoning without tools
- Prompt: "Let's think step by step..."

**RAG (Retrieval Augmented Generation):**
- Retrieve relevant documents, inject into context, generate answer
- Best for: question answering over knowledge bases, documentation
- Architecture: Query → Retrieve → Rerank → Generate

**Multi-Agent:**
- Multiple specialized agents collaborating
- Best for: complex workflows (research → write → review)
- Patterns: sequential, hierarchical, collaborative

**Plan-and-Execute:**
- Generate plan first, then execute steps
- Best for: complex tasks that benefit from upfront planning

**Select model based on requirements:**
- GPT-4/Claude Opus: complex reasoning, high quality
- GPT-3.5/Claude Sonnet: fast, cost-effective
- Claude Haiku: ultra-fast, batch processing
- Gemini 1.5 Pro: very long context (1M+ tokens)

**Use ml-docs skill to fetch LangChain, LangGraph, Anthropic API documentation.**

### Step 2: Implement Core Components

**Prompt Engineering:**
- Structure: System (role, capabilities) → Context → Task → Format → Examples
- Be specific and clear, avoid ambiguity
- Use delimiters (XML tags, markdown) for structure
- Include few-shot examples (2-5) for complex tasks
- Specify output format (JSON schema, template)
- Add constraints ("Only use provided context", "Cite sources")

**Tool/Function Calling:**
- Define tools with clear descriptions and parameters
- Tool format: name, description, parameter schema (types, required/optional)
- Execution: Agent calls tool → Extract params → Validate → Execute → Return result
- Error handling: Retry on transient failures, return informative errors
- Keep tools atomic and single-purpose

**Memory Systems:**
- **Short-term:** Recent conversation in context window
- **Long-term:** Vector database for semantic search (ChromaDB, Pinecone)
- **Structured:** Key-value store for facts, preferences (Redis, SQLite)
- Manage context: Summarize old messages, prioritize recent/relevant

**Use ml-docs to fetch specific implementation details for tools and frameworks.**

### Step 3: Build RAG Pipeline (if needed)

**For question answering over documents:**

**Ingestion:**
1. Chunk documents (512-1024 tokens, 50-100 overlap)
2. Generate embeddings (sentence-transformers, OpenAI embeddings)
3. Store in vector database with metadata

**Retrieval:**
1. Embed user query
2. Similarity search (cosine similarity, top-k results)
3. Rerank results (cross-encoder or LLM reranking)
4. Inject top-N chunks into prompt

**Generation:**
1. Combine retrieved context + query in prompt
2. Generate answer with citations
3. Validate answer against sources (fact-checking)

**Optimization:**
- Chunking strategy: semantic vs fixed size
- Hybrid search: dense + sparse (BM25)
- Query expansion: generate multiple query variations
- Metadata filtering: date, source, category
- Parent-child chunks: retrieve small, return large context

**Use ml-docs to fetch vector database documentation (ChromaDB, FAISS, Pinecone).**

### Step 4: Implement Workflow Logic

**For single-agent systems:**
- Define clear system prompt with role and capabilities
- Implement tool calling loop: think → act → observe → repeat
- Add stopping conditions (max iterations, task complete)
- Error handling: retry on tool failures, fallback to simpler approach

**For multi-agent systems (LangGraph):**
- Define agent roles and responsibilities
- Create state schema (shared data structure)
- Build graph: nodes (agents/functions) + edges (transitions)
- Implement conditional routing based on state
- Add human-in-the-loop approval points if needed

**State management:**
- Pass complete context to each step (agents have no memory between calls)
- Include conversation history, task state, intermediate results
- Use structured state (dataclasses, Pydantic models)

**Use ml-docs to fetch LangGraph documentation for workflow patterns.**

### Step 5: Evaluate and Optimize

**Evaluation metrics:**
- Task success rate: Did agent complete the task?
- Correctness: Is the answer accurate?
- Efficiency: Steps taken, tokens used, time
- Tool usage: Appropriate tool selection
- Safety: No harmful actions, proper error handling

**Evaluation methods:**
- Unit tests for specific capabilities
- Integration tests for end-to-end workflows
- LLM-as-judge: Use stronger model to evaluate outputs
- Human evaluation: For subjective quality

**Optimization:**
- Prompt iteration based on failure analysis
- Add examples for common failure modes
- Tune temperature (0 for deterministic, 0.7+ for creative)
- Implement caching for repeated queries
- Add fallbacks for graceful degradation

**Safety measures:**
- Input validation (prompt injection detection)
- Output filtering (harmful content, PII)
- Action constraints (whitelist allowed tools/APIs)
- Rate limiting and cost controls
- User approval for sensitive actions

## Best Practices

- **Start simple:** Single-agent before multi-agent, few tools before many
- **Clear prompts:** Explicit instructions > implicit assumptions
- **Tool documentation:** Rich descriptions with examples improve tool selection
- **Error handling:** Graceful failures with informative messages
- **Context management:** Summarize long conversations, prioritize relevant info
- **Evaluation early:** Test on diverse examples, identify failure modes
- **Iterative development:** Prompt → Test → Analyze failures → Refine
- **Version prompts:** Track changes, A/B test improvements
- **Monitor production:** Log all interactions, track metrics, collect feedback
- **Human oversight:** Keep humans in loop for high-stakes decisions

## Examples

### Example 1: RAG System for Technical Documentation

**User Request:** "Build a system to answer questions about our internal API documentation (500 pages of markdown files)."

**Approach:**
1. **Design:** RAG architecture with semantic search
2. **Ingestion pipeline:**
   - Read markdown files, extract text
   - Chunk by section (respect headers), 512 tokens with 50 token overlap
   - Generate embeddings with sentence-transformers
   - Store in ChromaDB with metadata (file, section, date)
3. **Retrieval:**
   - Embed user query
   - Retrieve top 5 chunks by similarity
   - Rerank with cross-encoder
   - Take top 3 for context
4. **Generation:**
   - Prompt: "Answer based only on provided context. Cite sources."
   - Include retrieved chunks with source references
   - Generate answer with Claude/GPT
   - Return answer + citations
5. **Optimize:**
   - Query expansion: "What is authentication?" → also search "auth", "login"
   - Metadata filtering: Search only relevant API versions
   - Caching: Store common queries

**Key code pattern:**
```python
from sentence_transformers import SentenceTransformer
import chromadb

# Initialize
embedder = SentenceTransformer('all-MiniLM-L6-v2')
chroma_client = chromadb.Client()
collection = chroma_client.create_collection("api_docs")

# Ingest
chunks = chunk_documents(docs)
embeddings = embedder.encode(chunks)
collection.add(embeddings=embeddings, documents=chunks, ids=[...])

# Retrieve
query_embedding = embedder.encode(query)
results = collection.query(query_embeddings=[query_embedding], n_results=5)

# Generate
context = "\n\n".join(results['documents'])
prompt = f"Context: {context}\n\nQuestion: {query}\n\nAnswer based only on context above."
answer = llm.generate(prompt)
```

**Use ml-docs to fetch ChromaDB and sentence-transformers documentation.**

### Example 2: Task Automation Agent with Tools

**User Request:** "Create an agent that can search the web, read articles, and summarize findings on a given topic."

**Approach:**
1. **Design:** ReAct agent with tools (web_search, fetch_url, summarize)
2. **Define tools:**
   - `web_search(query: str)`: Returns top 10 search results
   - `fetch_url(url: str)`: Fetches and extracts text from webpage
   - `summarize(text: str)`: Generates concise summary
3. **System prompt:**
   ```
   You are a research assistant. Break down research tasks into steps:
   1. Search for information using web_search
   2. Read relevant articles using fetch_url
   3. Synthesize findings into summary
   
   Available tools: web_search, fetch_url, summarize
   Think step-by-step and use tools as needed.
   ```
4. **Execution loop:**
   - Agent thinks: "I need to search for X"
   - Agent calls: web_search("topic")
   - Agent observes: Gets search results
   - Agent thinks: "I'll read the top 3 articles"
   - Agent calls: fetch_url for each URL
   - Agent observes: Gets article text
   - Agent calls: summarize(combined_text)
   - Agent responds: Final summary
5. **Error handling:**
   - If fetch_url fails (404, timeout), skip and try next URL
   - If all URLs fail, search with different query
   - Max 10 iterations to prevent infinite loops

**Key considerations:**
- Clear tool descriptions help agent choose correctly
- Return structured results from tools (not just raw HTML)
- Add rate limiting to prevent API abuse
- Log all tool calls for debugging

### Example 3: Multi-Agent System with LangGraph

**User Request:** "Build a system where one agent researches a topic, another writes a blog post, and a third reviews it."

**Approach:**
1. **Design:** Sequential multi-agent workflow
2. **Define agents:**
   - Researcher: Uses web_search and fetch_url to gather info
   - Writer: Takes research, writes blog post
   - Reviewer: Critiques post, suggests improvements
3. **State schema:**
   ```python
   class BlogState(TypedDict):
       topic: str
       research: str
       draft: str
       feedback: str
       final_post: str
       iteration: int
   ```
4. **Build LangGraph workflow:**
   - Nodes: research_node, write_node, review_node, revise_node
   - Edges: research → write → review → conditional(good enough? → done, else → revise → write)
   - Conditional: If feedback is positive, end; else, iterate (max 3 times)
5. **Implementation:**
   - Each node receives state, performs action, returns updated state
   - Researcher populates `research` field
   - Writer uses `research` to create `draft`
   - Reviewer analyzes `draft`, provides `feedback`
   - Loop until quality threshold met or max iterations

**Key code pattern:**
```python
from langgraph.graph import StateGraph

workflow = StateGraph(BlogState)

# Add nodes
workflow.add_node("research", research_agent)
workflow.add_node("write", writer_agent)
workflow.add_node("review", reviewer_agent)

# Add edges
workflow.add_edge("research", "write")
workflow.add_edge("write", "review")
workflow.add_conditional_edges(
    "review",
    lambda state: "end" if state["feedback"].startswith("Approved") else "write",
    {"end": END, "write": "write"}
)

workflow.set_entry_point("research")
app = workflow.compile()
result = app.invoke({"topic": "AI Safety"})
```

**Use ml-docs to fetch LangGraph documentation for advanced patterns.**

## Notes

- **Context window limits:** Even with long context (100K+ tokens), performance degrades. Summarize or prioritize important information
- **Cost management:** LLM API calls add up. Cache responses, use smaller models for subtasks, batch requests when possible
- **Prompt injection:** Users may try to manipulate agent. Validate inputs, use system prompts that are hard to override
- **Hallucination:** LLMs may invent information. Always validate critical facts, use RAG with citations
- **Latency:** Multiple LLM calls are slow. Consider parallel tool calls, streaming responses, or async processing
- **Testing:** Unit test individual components, integration test workflows, adversarial test with edge cases
- **Monitoring:** Track success rates, token usage, latency, user feedback in production
- **Model selection:** Use appropriate model for task complexity. Don't use GPT-4 when GPT-3.5 suffices
- **Use ml-docs skill:** Fetch LangChain, LangGraph, Anthropic, OpenAI documentation for specific implementations
- **Integration with other skills:** May use embeddings from deep-learning, receives evaluation from evaluation skill, deploys via mlops-production