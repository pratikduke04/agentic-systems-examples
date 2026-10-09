# PRD: Local Tesla Financial Report RAG Application

## 1. Product Overview

### 1.1 Product name

**Tesla Financial Report RAG Assistant**

### 1.2 Purpose

Build a lightweight but technically credible Retrieval-Augmented Generation (RAG) proof of concept that allows a user to ask questions about a Tesla financial report PDF and receive answers grounded in the contents of that document.

The application is intended as a **client-facing demonstration / POC**, not as a production enterprise system. The implementation should therefore:

- Remain simple enough to build and run quickly on a local laptop.
- Demonstrate several modern RAG techniques beyond basic vector search.
- Use Python throughout the stack.
- Avoid unnecessary infrastructure and database integrations.
- Provide visible evidence of the RAG pipeline behavior in the UI.
- Be structured cleanly enough that GitHub Copilot can generate the implementation from this PRD.

### 1.3 Primary user experience

A user opens a Streamlit application, enters a natural-language question about the Tesla financial report, and receives a grounded answer.

The application should internally:

1. Classify/route the question.
2. Determine the appropriate RAG pipeline.
3. Check the semantic cache.
4. Optionally perform query expansion.
5. Retrieve relevant chunks.
6. Optionally rerank retrieved chunks.
7. Send the selected context to the LLM.
8. Generate a grounded answer.
9. Return the answer together with useful retrieval metadata.
10. Store the resulting question/answer in the semantic cache for subsequent similar queries.

The UI should make the application look like a real RAG system rather than a plain chatbot. It should expose useful technical metadata such as:

- Selected route.
- Cache hit / cache miss.
- Similar cached question, where applicable.
- Number of chunks retrieved.
- Number of chunks retained after reranking.
- Whether query expansion was used.
- Number of query variants generated.
- Source/page references used for the answer.
- Approximate retrieval/pipeline timing where practical.

---

# 2. Goals

## 2.1 Primary goals

1. Build a working RAG application over a single approximately 130-page Tesla financial report PDF.
2. Use a simple fixed-size chunking strategy.
3. Use a small CPU-friendly embedding model.
4. Use ChromaDB as the vector store.
5. Use LangChain for the RAG implementation.
6. Use Groq as the hosted LLM inference provider.
7. Use the GPT-OSS-20B model through Groq for answer generation.
8. Keep secrets and runtime configuration in a `.env` file.
9. Implement semantic caching with TTL and similarity threshold.
10. Implement limited query expansion with a maximum of three expansions.
11. Implement reranking of retrieved chunks and retain the top three.
12. Implement a lightweight triage/router that selects among three RAG routes.
13. Provide a polished Streamlit interface.
14. Keep the entire application Python-based.
15. Do not introduce an application database.
16. Make the project easy for GitHub Copilot to implement and maintain.

## 2.2 Secondary goals

- Demonstrate that different questions can use different retrieval strategies.
- Demonstrate practical advanced-RAG concepts without excessive infrastructure.
- Make cache behavior visible to the client.
- Preserve source/page metadata throughout the pipeline.
- Make parameters configurable through environment variables.
- Make the architecture modular enough to replace individual components later.

---

# 3. Non-Goals

The following are explicitly outside the scope of this POC:

- Multi-document enterprise ingestion.
- User authentication.
- Authorization / RBAC.
- Production-grade observability platforms.
- Cloud deployment.
- Kubernetes or Docker orchestration unless optionally added later.
- Application SQL/NoSQL database.
- User accounts or conversation persistence.
- Fine-tuning any model.
- Agentic tool use.
- Web search.
- External knowledge retrieval.
- Autonomous research.
- Complex multi-agent workflows.
- OCR-heavy document processing unless the supplied PDF actually requires it.
- Production-grade distributed caching.
- Document version management.
- Enterprise document access control.

The assistant must primarily answer from the supplied Tesla financial report. It should not silently supplement answers with external knowledge.

---

# 4. Target Environment

## 4.1 Hardware

The application must be designed to run locally on:

- CPU-only laptop.
- 32 GB RAM.
- No GPU.
- Local Python environment.

The implementation should avoid unnecessarily large local models.

## 4.2 Technology stack

| Layer | Technology |
|---|---|
| Language | Python |
| Frontend | Streamlit |
| RAG framework | LangChain |
| PDF ingestion | LangChain-compatible PDF loader |
| Chunking | Fixed-size recursive/text chunking |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store | ChromaDB |
| Retrieval | Chroma similarity search |
| Reranking | Small CPU-friendly cross-encoder reranker |
| LLM provider | Groq |
| Generation model | GPT-OSS-20B via Groq |
| Configuration | `.env` / environment variables |
| Application database | None |

### Embedding model rationale

Use `sentence-transformers/all-MiniLM-L6-v2` as the default embedding model.

It is deliberately selected because the POC is CPU-only and has 32 GB RAM. The model is small enough for practical local execution while providing useful semantic representations for a financial-report RAG demonstration.

The embedding model must be configurable so it can be replaced without changing the rest of the architecture.

### Reranker

Use a small CPU-compatible cross-encoder reranker, with a default such as:

`BAAI/bge-reranker-base`

The reranker must also be configurable.

If CPU latency becomes problematic, the architecture must allow the reranker to be replaced by a smaller model without changing the rest of the pipeline.

---

# 5. High-Level Architecture

```text
                    ┌─────────────────────────────┐
                    │       Tesla PDF Report      │
                    │       ~130 pages            │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │       PDF Document Loader    │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │       Fixed-size Chunker     │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │    MiniLM Embedding Model   │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │          ChromaDB            │
                    │       Local Vector Store     │
                    └─────────────────────────────┘


User
 │
 ▼
┌─────────────────────┐
│   Streamlit UI      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Semantic Cache      │
│ similarity + TTL    │
└──────────┬──────────┘
           │ cache miss
           ▼
┌─────────────────────┐
│ Query Router/Triage │
└──────────┬──────────┘
           │
      ┌────┼───────────────┐
      │    │               │
      ▼    ▼               ▼
   Route 1 Route 2       Route 3
   Direct  Broad         Analytical
   Lookup  / Thematic    / Comparative
      │    │               │
      └────┼───────────────┘
           │
           ▼
┌─────────────────────┐
│ Retrieval            │
│ ChromaDB             │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Optional Query       │
│ Expansion            │
│ max 3 variants       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Candidate Chunks     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Cross-Encoder        │
│ Reranker             │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Top 3 Context Chunks │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ GPT-OSS-20B via      │
│ Groq                  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Answer + Sources +   │
│ Retrieval Metadata   │
└─────────────────────┘
```

---

# 6. Document Ingestion Pipeline

## 6.1 Input

The application will initially operate on one Tesla financial report PDF.

The PDF should be configurable rather than hard-coded into business logic.

Example:

```text
data/tesla_financial_report.pdf
```

## 6.2 Loading

Use a LangChain-compatible PDF loader such as `PyPDFLoader`.

The loader must preserve page metadata wherever possible.

Each resulting document should retain metadata including:

- Source filename.
- Page number.
- Any available document metadata.

## 6.3 Chunking

Use a basic fixed-size chunking approach.

Recommended default:

```text
chunk_size = 1000 characters
chunk_overlap = 150 characters
```

These values must be configurable through environment variables.

Use a standard LangChain recursive character splitter.

The objective is not to create an elaborate semantic chunking system. Simplicity and predictable behavior are preferred for this POC.

## 6.4 Chunk metadata

Every chunk stored in ChromaDB should retain:

```text
source
page
chunk_id
```

Optional metadata may include:

```text
document_name
```

The chunk ID should be deterministic where practical so that the same document can be re-indexed without producing uncontrolled duplicates.

---

# 7. Vector Store

## 7.1 Technology

Use ChromaDB.

The vector store should be local and persistent on disk.

Example:

```text
./chroma_db/
```

## 7.2 Collection

Use a clearly named collection such as:

```text
tesla_financial_report
```

The collection name should be configurable.

## 7.3 Embedding

Default:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Embedding generation should occur during ingestion/indexing.

The application should not regenerate embeddings for every user query unnecessarily.

## 7.4 Indexing behavior

The application should provide a clear initialization/indexing mechanism.

Preferred behavior:

1. Check whether the expected Chroma collection already exists.
2. If it exists and is valid, reuse it.
3. If not, load the PDF.
4. Split the PDF into chunks.
5. Generate embeddings.
6. Store the chunks and metadata in ChromaDB.

The implementation should avoid accidental duplicate ingestion.

---

# 8. Semantic Cache

## 8.1 Purpose

The semantic cache avoids executing the complete RAG pipeline when a user asks the same or a sufficiently similar question within a configurable TTL window.

Example:

User asks:

> What was Tesla's revenue in 2025?

Later the user asks:

> How much revenue did Tesla generate in 2025?

The second question may be considered semantically similar enough to reuse the cached answer.

## 8.2 Important constraint

There is no application database.

Therefore, the semantic cache should be implemented as a lightweight local file-based/in-memory component rather than introducing SQL, Redis, MongoDB, etc.

A practical implementation can use:

- In-memory cache for the current application process.
- Optional lightweight JSON/pickle persistence if desired.
- Embeddings generated using the same MiniLM model.

The default implementation should remain simple.

## 8.3 Cache record

Each cache entry should contain approximately:

```text
cache_id
original_question
answer
question_embedding
created_at
expires_at
route
source_metadata
```

## 8.4 Cache lookup

When a question arrives:

1. Generate an embedding for the user question.
2. Compare it against active cached question embeddings.
3. Ignore expired entries.
4. Calculate cosine similarity.
5. If similarity >= configurable threshold, return the cached answer.
6. Mark the request as `CACHE_HIT`.
7. Otherwise continue to the RAG router and mark it `CACHE_MISS`.

Recommended initial threshold:

```text
SEMANTIC_CACHE_THRESHOLD=0.90
```

This must be configurable.

Do not assume 0.90 is universally optimal; it is simply the POC default.

## 8.5 TTL

Recommended default:

```text
SEMANTIC_CACHE_TTL_SECONDS=3600
```

The TTL must be configurable.

## 8.6 UI behavior

The UI should clearly display:

```text
Cache: HIT
Similarity: 0.94
Cached question: "What was Tesla's revenue in 2025?"
```

or:

```text
Cache: MISS
```

The actual similarity value should be shown only when a meaningful cache candidate exists.

---

# 9. Query Router / Triage Layer

## 9.1 Purpose

The router is a lightweight classification layer that determines which RAG pipeline should process the question.

The objective is to avoid running the most expensive pipeline for every query.

The router should be deterministic enough for a POC and should use an LLM-based classification prompt rather than a complicated ML classifier.

## 9.2 Three routes

The application must implement exactly three initial routes.

### Route 1 — Direct Fact Lookup

Use for questions that request a specific factual value or a narrowly scoped fact.

Examples:

- What was Tesla's revenue in 2025?
- How many vehicles were delivered?
- What was the operating margin?
- What was the cash balance?
- When did Tesla report X?

Characteristics:

- Narrow retrieval.
- Minimal query expansion.
- Lower latency.
- Fewer chunks.
- Reranking can be skipped or used lightly.

Recommended retrieval:

```text
top_k = 3
rerank = false
query_expansion = false
final_context = 2-3 chunks
```

### Route 2 — Broad / Thematic Question

Use for broader questions requiring multiple pieces of evidence from the report.

Examples:

- Tell me about Tesla's business strategy.
- What are Tesla's major growth drivers?
- Explain Tesla's approach to energy storage.
- What risks does Tesla identify?

Characteristics:

- More retrieval candidates.
- Query expansion enabled.
- Reranking enabled.
- More context.

Recommended retrieval:

```text
base_top_k = 5
query_expansion = true
max_expansions = 3
rerank = true
rerank_top_n = 3
```

### Route 3 — Analytical / Comparative Question

Use for questions requiring synthesis across multiple sections or comparison of concepts, periods, metrics, or factors.

Examples:

- Compare Tesla's 2024 and 2025 financial performance.
- What changed in Tesla's margins and what factors explain those changes?
- How do Tesla's automotive and energy businesses differ?
- What are the main opportunities and risks described in the report?

Characteristics:

- Broadest retrieval.
- Query expansion enabled.
- Reranking strongly emphasized.
- More deliberate synthesis prompt.
- Multiple retrieved evidence groups may be used.

Recommended retrieval:

```text
base_top_k = 5
query_expansion = true
max_expansions = 3
rerank = true
rerank_top_n = 3
multi_query_merge = true
```

The route parameters must remain configurable.

---

# 10. Router Output Contract

The router should return structured output rather than free-form text.

Preferred logical schema:

```json
{
  "route": "direct",
  "reason": "The question asks for a specific financial metric.",
  "confidence": 0.94
}
```

Allowed route values:

```text
direct
thematic
analytical
```

The router should not answer the user's question.

It only determines the appropriate pipeline.

If the router is uncertain, default to the `thematic` route rather than failing.

---

# 11. Query Expansion

## 11.1 Purpose

Query expansion improves retrieval for broader questions by generating alternative formulations of the original question.

Example:

Original:

> What are Tesla's main growth drivers?

Possible expansions:

1. Tesla revenue growth drivers
2. Tesla business expansion strategy
3. factors contributing to Tesla growth

## 11.2 Maximum expansions

Hard limit:

```text
3 expansions
```

Never generate more than three.

## 11.3 Expansion model

Use a lightweight LLM prompt.

For the POC, the existing Groq GPT-OSS-20B model may be used with a tightly constrained prompt if a separate smaller hosted model is not configured.

The model should be instructed to produce short search-oriented queries only.

## 11.4 Expansion rules

The expansion component must:

- Preserve the original intent.
- Avoid introducing facts not present in the question.
- Generate at most three variants.
- Avoid verbose explanations.
- Return only query strings.
- Deduplicate near-identical variants.
- Fall back to the original question if expansion fails.

## 11.5 Retrieval with expansions

For expanded queries:

1. Retrieve candidates for the original query.
2. Retrieve candidates for each expansion.
3. Merge the candidates.
4. Deduplicate chunks by chunk ID.
5. Optionally retain the highest retrieval score for duplicates.
6. Pass the merged candidate set to the reranker.

---

# 12. Retrieval

## 12.1 Basic retrieval

Use Chroma similarity search.

The initial retrieval count must be configurable.

Default:

```text
top_k = 5
```

For the direct route, the router may override this to 3.

## 12.2 Retrieval result

Each retrieved result should contain:

```text
chunk_text
similarity_score
source
page
chunk_id
```

## 12.3 Deduplication

When multiple expanded queries retrieve the same chunk, deduplicate by `chunk_id`.

Do not send duplicate chunks to the LLM.

---

# 13. Reranking

## 13.1 Purpose

The reranker improves the ordering of candidate chunks after vector retrieval.

Vector similarity is used for initial candidate generation; a cross-encoder reranker then scores each candidate against the user's query.

## 13.2 Default model

Use a small CPU-compatible cross-encoder, with:

```text
BAAI/bge-reranker-base
```

as the default.

The model should be configurable.

## 13.3 Reranking flow

```text
User Query
    ↓
Vector Retrieval
    ↓
Candidate Chunks
    ↓
Cross Encoder
    ↓
Reranked Chunks
    ↓
Top 3
```

## 13.4 Final context

The default final context size is:

```text
3 chunks
```

The final number must be configurable.

## 13.5 Route behavior

- Direct route: reranking disabled by default.
- Thematic route: reranking enabled.
- Analytical route: reranking enabled.

---

# 14. Generation Layer

## 14.1 Provider

Use Groq for LLM inference.

The API key must be read from `.env`.

Example:

```text
GROQ_API_KEY=your_key_here
```

Never hard-code credentials.

## 14.2 Model

Use:

```text
GPT-OSS-20B
```

through Groq.

Make the model name configurable because provider-side model identifiers can change.

Example:

```text
GROQ_MODEL=openai/gpt-oss-20b
```

The exact identifier should be configurable rather than hard-coded throughout the source code.

## 14.3 Generation principles

The generation prompt must enforce grounded answering.

The model must:

- Use the supplied context as the primary source of truth.
- Avoid inventing facts.
- Clearly state when the report does not contain enough information.
- Avoid using unsupported external knowledge.
- Cite source pages when available.
- Distinguish facts from interpretation.
- Provide concise but useful answers.

## 14.4 Hallucination control

If the retrieved context does not contain sufficient evidence, the assistant should respond with a statement such as:

> I could not find sufficient information in the Tesla financial report to answer that reliably.

It must not fabricate an answer to satisfy the user.

---

# 15. Prompt Architecture

Prompts should be kept in a dedicated prompt module or prompt directory rather than being scattered throughout the application.

Recommended prompt files:

```text
prompts/
├── router_prompt.txt
├── expansion_prompt.txt
├── direct_answer_prompt.txt
├── thematic_answer_prompt.txt
└── analytical_answer_prompt.txt
```

## 15.1 Direct answer prompt

Focus on:

- Exact fact extraction.
- Minimal context.
- Concise answer.
- Source citation.

## 15.2 Thematic answer prompt

Focus on:

- Synthesizing multiple relevant passages.
- Identifying themes.
- Providing evidence from the report.
- Avoiding unsupported generalizations.

## 15.3 Analytical answer prompt

Focus on:

- Cross-section synthesis.
- Comparisons.
- Changes over time.
- Evidence-based reasoning.
- Explicitly separating report facts from analytical interpretation.

---

# 16. Source Attribution

Every generated answer should preserve source information.

A preferred response structure is:

```text
Answer

[Generated answer]

Sources
- Tesla Financial Report, page 42
- Tesla Financial Report, page 57
- Tesla Financial Report, page 81
```

Page numbers should come from the PDF metadata.

Do not invent page numbers.

Where the PDF loader uses zero-based page numbering internally, normalize it to human-readable one-based page numbers in the UI.

---

# 17. Streamlit Frontend

## 17.1 Overall objective

Create a visually polished but simple Streamlit application.

It should look like a client-ready POC rather than a developer-only interface.

## 17.2 Suggested layout

### Header

```text
Tesla Financial Report
RAG Intelligence Assistant
```

Short subtitle:

```text
Ask questions grounded in the Tesla financial report.
```

### Main area

Large question input:

```text
Ask a question about the Tesla financial report...
```

Button:

```text
Ask
```

### Example questions

Display 4–6 clickable example questions.

Examples:

- What was Tesla's revenue?
- What were Tesla's major growth drivers?
- What risks does Tesla identify?
- Compare Tesla's financial performance across years.
- Explain Tesla's energy business strategy.

### Answer panel

Display:

- Answer.
- Sources.
- Route used.

### Retrieval diagnostics

Use an expandable section such as:

```text
RAG Pipeline Details
```

Show:

```text
Route: Thematic
Cache: MISS
Query expansion: YES
Expanded queries: 3
Initial chunks: 5
Reranking: YES
Final chunks: 3
```

### Cache information

When a cache hit occurs:

```text
Semantic Cache HIT
Similarity: 0.93
Previous question:
"What were Tesla's revenue growth drivers?"
```

When there is no hit:

```text
Semantic Cache MISS
```

---

# 18. UI Design Requirements

The UI should:

- Be clean.
- Have clear hierarchy.
- Avoid excessive technical clutter.
- Use cards/metrics where useful.
- Make the advanced RAG behavior visible without overwhelming the user.
- Provide a clear distinction between answer and diagnostics.
- Show source pages.
- Display a loading state during processing.
- Handle errors gracefully.

Do not build a complicated custom JavaScript frontend.

Streamlit is the only frontend framework required.

---

# 19. Application State

Use Streamlit session state only for UI/session behavior such as:

- Current question.
- Current answer.
- Recent questions.
- Current diagnostics.
- UI state.

Do not use Streamlit session state as the only source of truth for document indexing.

---

# 20. Recent Questions

The UI should optionally show a small list of recent questions in the current session.

Example:

```text
Recent questions

1. What was Tesla's revenue in 2025?
2. What are Tesla's major growth drivers?
3. Compare automotive and energy businesses.
```

Clicking a previous question may rerun it or populate the input field, depending on the simplest reliable Streamlit implementation.

---

# 21. Error Handling

The application must handle at least:

### Missing PDF

Display:

```text
Tesla financial report not found.
Please place the PDF in the configured data directory.
```

### Missing API key

Display:

```text
GROQ_API_KEY is not configured.
Please add it to the .env file.
```

Never display the actual API key.

### LLM failure

Display a user-friendly error.

### Embedding failure

Display a clear indexing/retrieval error.

### Chroma failure

Display a vector-store initialization error.

### Empty question

Do not execute the RAG pipeline.

### No relevant context

Return a grounded "insufficient information" response.

---

# 22. Configuration

All configurable parameters should be placed in `.env`.

Suggested `.env.example`:

```env
# Application
APP_TITLE=Tesla Financial Report RAG Assistant
DEBUG=false

# Document
PDF_PATH=data/tesla_financial_report.pdf

# Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Chroma
CHROMA_PERSIST_DIRECTORY=./chroma_db
CHROMA_COLLECTION=tesla_financial_report

# Chunking
CHUNK_SIZE=1000
CHUNK_OVERLAP=150

# Groq
GROQ_API_KEY=
GROQ_MODEL=openai/gpt-oss-20b
GROQ_TEMPERATURE=0.1
GROQ_MAX_TOKENS=1200

# Retrieval
DEFAULT_TOP_K=5
DIRECT_TOP_K=3
FINAL_CONTEXT_CHUNKS=3

# Reranking
RERANKER_MODEL=BAAI/bge-reranker-base
RERANK_TOP_N=3

# Query expansion
ENABLE_QUERY_EXPANSION=true
MAX_QUERY_EXPANSIONS=3

# Semantic cache
ENABLE_SEMANTIC_CACHE=true
SEMANTIC_CACHE_THRESHOLD=0.90
SEMANTIC_CACHE_TTL_SECONDS=3600

# Router
ROUTER_CONFIDENCE_THRESHOLD=0.60
```

The actual `.env` file must be excluded from Git.

The repository should contain `.env.example`.

---

# 23. Suggested Project Structure

GitHub Copilot should generate a clean modular structure similar to:

```text
tesla-rag/
│
├── app.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
├── PRD.md
│
├── data/
│   └── tesla_financial_report.pdf
│
├── chroma_db/
│
├── src/
│   ├── __init__.py
│   │
│   ├── config.py
│   │
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── loader.py
│   │   ├── chunker.py
│   │   └── indexer.py
│   │
│   ├── embeddings/
│   │   ├── __init__.py
│   │   └── embedding_model.py
│   │
│   ├── vectorstore/
│   │   ├── __init__.py
│   │   └── chroma_store.py
│   │
│   ├── cache/
│   │   ├── __init__.py
│   │   └── semantic_cache.py
│   │
│   ├── routing/
│   │   ├── __init__.py
│   │   └── query_router.py
│   │
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── retriever.py
│   │   ├── query_expander.py
│   │   └── reranker.py
│   │
│   ├── generation/
│   │   ├── __init__.py
│   │   ├── groq_client.py
│   │   └── answer_generator.py
│   │
│   ├── pipelines/
│   │   ├── __init__.py
│   │   ├── direct_pipeline.py
│   │   ├── thematic_pipeline.py
│   │   ├── analytical_pipeline.py
│   │   └── pipeline_orchestrator.py
│   │
│   ├── prompts/
│   │   ├── router_prompt.txt
│   │   ├── expansion_prompt.txt
│   │   ├── direct_answer_prompt.txt
│   │   ├── thematic_answer_prompt.txt
│   │   └── analytical_answer_prompt.txt
│   │
│   └── models/
│       └── schemas.py
│
└── tests/
    ├── test_chunking.py
    ├── test_cache.py
    ├── test_router.py
    ├── test_retrieval.py
    └── test_pipelines.py
```

The exact folder structure may be simplified if GitHub Copilot determines a materially cleaner equivalent. However, responsibilities must remain modular.

---

# 24. Core Data Models

Use typed Python structures, preferably Pydantic models or dataclasses, for important pipeline outputs.

## 24.1 RetrievedChunk

```text
chunk_id
text
source
page
retrieval_score
rerank_score
```

## 24.2 RouterDecision

```text
route
reason
confidence
```

## 24.3 CacheResult

```text
hit
similarity
cached_question
answer
created_at
expires_at
```

## 24.4 PipelineResult

```text
answer
route
cache_hit
cache_similarity
expanded_queries
retrieved_chunks
reranked_chunks
sources
latency_ms
```

---

# 25. End-to-End Request Flow

The application should follow this logical sequence:

```text
1. User enters question
       ↓
2. Validate question
       ↓
3. Semantic cache lookup
       ↓
   ┌───────────────┐
   │ Cache hit?    │
   └───────┬───────┘
       YES │ NO
           │
           ▼
 Return cached answer
           │
           │
           └───────────────────────────────┐
                                           │
                                           ▼
                                4. Query Router
                                           │
                           ┌───────────────┼───────────────┐
                           ▼               ▼               ▼
                        Direct         Thematic        Analytical
                           │               │               │
                           ▼               ▼               ▼
                       Retrieve        Expand          Expand
                           │             queries         queries
                           │               │               │
                           │               ▼               ▼
                           │            Retrieve        Retrieve
                           │               │               │
                           │               ▼               ▼
                           │           Rerank          Rerank
                           │               │               │
                           ▼               ▼               ▼
                       Context         Top 3           Top 3
                           │               │               │
                           └───────────────┼───────────────┘
                                           ▼
                                  5. LLM Generation
                                           ↓
                                  6. Source extraction
                                           ↓
                                  7. Store cache entry
                                           ↓
                                  8. Return PipelineResult
                                           ↓
                                  9. Render Streamlit UI
```

---

# 26. Detailed Route Specifications

## 26.1 Direct Route

### Objective

Answer narrowly scoped factual questions efficiently.

### Steps

1. Receive user question.
2. Retrieve top 3 chunks from Chroma.
3. Do not perform query expansion.
4. Do not perform reranking by default.
5. Construct direct-answer prompt.
6. Call GPT-OSS-20B through Groq.
7. Return answer and source pages.
8. Cache result.

### Performance objective

This route should be the lowest-latency route.

---

## 26.2 Thematic Route

### Objective

Answer broad questions requiring synthesis.

### Steps

1. Receive user question.
2. Generate up to three query expansions.
3. Retrieve candidates for original + expanded queries.
4. Merge and deduplicate chunks.
5. Rerank candidates.
6. Retain top 3 chunks.
7. Construct thematic-answer prompt.
8. Call GPT-OSS-20B through Groq.
9. Return answer and sources.
10. Cache result.

---

## 26.3 Analytical Route

### Objective

Answer questions requiring comparison, synthesis, or reasoning across multiple pieces of evidence.

### Steps

1. Receive user question.
2. Generate up to three query expansions.
3. Retrieve candidates for original + expanded queries.
4. Merge and deduplicate.
5. Rerank candidates.
6. Retain top 3 final chunks.
7. Use an analytical generation prompt.
8. Ask the model to explicitly ground conclusions in the supplied evidence.
9. Call GPT-OSS-20B through Groq.
10. Return answer and source pages.
11. Cache result.

---

# 27. Router Prompt Requirements

The router prompt must instruct the LLM to classify the question into exactly one of:

```text
direct
thematic
analytical
```

Definitions:

### direct

A narrowly scoped question requesting a specific fact, value, date, metric, or statement.

### thematic

A broad question asking for explanation, overview, themes, strategy, risks, drivers, or a topic spanning several passages.

### analytical

A question requiring comparison, change analysis, relationships between factors, or synthesis across multiple financial/business dimensions.

The router must return structured JSON.

Example:

```json
{
  "route": "analytical",
  "reason": "The user asks to compare performance across periods and explain the changes.",
  "confidence": 0.91
}
```

If parsing fails, default to:

```text
thematic
```

---

# 28. Generation Guardrails

The answer-generation prompts must include the following principles:

1. Answer only using the supplied document context.
2. Do not fabricate numbers.
3. Do not invent page numbers.
4. If evidence is insufficient, say so.
5. Do not pretend that an inference is explicitly stated in the report.
6. When making an inference, label it as an interpretation.
7. Keep financial figures exact when they appear in the source.
8. Prefer concise structured answers.
9. Include source pages.
10. Do not mention internal implementation details unless the UI asks for them.

---

# 29. Observability for the POC

A full observability platform is not required.

The application should nevertheless capture basic per-request metrics:

```text
request_id
timestamp
route
cache_hit
cache_similarity
query_expansion_count
initial_retrieval_count
reranking_enabled
final_context_count
latency_ms
```

These metrics can be held in application/session memory for the POC.

No external telemetry platform is required.

---

# 30. Logging

Use Python's standard `logging` module.

Logging levels:

- INFO: major pipeline stages.
- WARNING: recoverable problems.
- ERROR: failures.

Do not log:

- API keys.
- Secrets.
- Sensitive user information unnecessarily.

---

# 31. Testing Requirements

The implementation should include basic automated tests.

## 31.1 Chunking test

Verify:

- Chunk size is respected within expected splitter behavior.
- Overlap is configured.
- Metadata is retained.

## 31.2 Cache test

Verify:

- Cache miss works.
- Cache hit works.
- Similarity threshold works.
- Expired entries are ignored.
- TTL works.

## 31.3 Router test

Test representative examples for all three routes.

Examples:

```text
"What was Tesla's revenue?"
→ direct
```

```text
"What are Tesla's major growth drivers?"
→ thematic
```

```text
"Compare Tesla's margins across the reported years and explain the change."
→ analytical
```

Tests should focus on valid route output rather than requiring an exact LLM explanation.

## 31.4 Retrieval test

Verify that Chroma returns:

- Text.
- Chunk ID.
- Source.
- Page.

## 31.5 Reranking test

Verify:

- Candidate chunks are scored.
- Results are sorted.
- Top N is returned.

## 31.6 Pipeline tests

At least one test per route should validate the orchestration logic using mocked LLM/vector-store dependencies.

---

# 32. Security Requirements

1. Never commit `.env`.
2. Never hard-code the Groq API key.
3. Include `.env` in `.gitignore`.
4. Include `.env.example`.
5. Never display secrets in Streamlit.
6. Do not expose the Chroma persistence directory as a public download.
7. Validate uploaded/configured file paths if upload functionality is later added.

---

# 33. Dependency Requirements

The implementation should use current stable versions compatible with the local Python environment.

Expected core dependencies include:

```text
streamlit
langchain
langchain-community
langchain-chroma
chromadb
sentence-transformers
pypdf
groq
langchain-groq
python-dotenv
pydantic
torch
transformers
```

The implementation should avoid adding dependencies unless they are necessary.

The exact dependency versions should be pinned after implementation/testing rather than blindly using unpinned latest versions.

---

# 34. Startup Behavior

When the application starts:

1. Load configuration.
2. Validate required configuration.
3. Initialize embedding model.
4. Initialize ChromaDB.
5. Check whether the document has already been indexed.
6. If necessary, perform indexing.
7. Initialize reranker lazily or at startup depending on performance.
8. Initialize Groq client.
9. Launch Streamlit UI.

Heavy models should preferably be cached using Streamlit's resource caching mechanisms so they are not repeatedly loaded on every interaction.

Use appropriate `st.cache_resource` / `st.cache_data` patterns.

---

# 35. Performance Requirements

Because this is a CPU-only demonstration:

- Do not repeatedly reload embedding/reranking models.
- Cache model instances.
- Avoid unnecessarily large retrieval candidate sets.
- Limit query expansion to three variants.
- Limit final context to three chunks.
- Avoid reranking on direct fact queries by default.
- Avoid regenerating document embeddings after the vector store is initialized.

The goal is not benchmark-grade latency. The goal is a responsive local demo.

---

# 36. Reproducibility

The project should include:

```text
README.md
.env.example
requirements.txt
```

README should explain:

1. Python version.
2. Installation.
3. Environment setup.
4. Where to put the PDF.
5. How to initialize the index.
6. How to run Streamlit.
7. How to configure Groq.
8. How the three routes work.
9. How semantic caching works.
10. How to reset the Chroma index.

Example startup:

```bash
pip install -r requirements.txt
```

Then:

```bash
streamlit run app.py
```

---

# 37. Acceptance Criteria

The POC is considered complete when all of the following are true.

## Document

- [ ] The Tesla PDF can be loaded.
- [ ] Approximately 130 pages can be processed.
- [ ] Fixed-size chunks are created.
- [ ] Page metadata is retained.

## Embeddings

- [ ] MiniLM embeddings run locally on CPU.
- [ ] Embeddings are persisted through ChromaDB.

## Vector database

- [ ] ChromaDB stores the document chunks.
- [ ] Re-running the application does not blindly duplicate the index.

## Semantic cache

- [ ] Cache miss is detected.
- [ ] Cache hit is detected for sufficiently similar questions.
- [ ] TTL is respected.
- [ ] Similarity threshold is configurable.
- [ ] Cache status is visible in UI.

## Query expansion

- [ ] Expansion can generate alternative queries.
- [ ] Maximum of three expansions is enforced.
- [ ] Expansion is used only on appropriate routes.
- [ ] Expanded retrieval results are merged and deduplicated.

## Reranking

- [ ] Retrieved candidates can be reranked.
- [ ] Top three chunks are retained by default.
- [ ] Reranking can be disabled for direct queries.

## Router

- [ ] Three routes exist.
- [ ] Direct factual questions use the direct route.
- [ ] Broad questions use the thematic route.
- [ ] Comparative/analytical questions use the analytical route.
- [ ] Router output is structured.
- [ ] Router failures have a safe fallback.

## LLM

- [ ] Groq is used.
- [ ] GPT-OSS-20B is configurable.
- [ ] API key comes from `.env`.
- [ ] Grounded prompts are implemented.
- [ ] Insufficient evidence is handled explicitly.

## UI

- [ ] Streamlit application runs.
- [ ] User can submit questions.
- [ ] Answers are displayed clearly.
- [ ] Sources are displayed.
- [ ] Route is displayed.
- [ ] Cache hit/miss is displayed.
- [ ] Retrieval/reranking metadata is available.
- [ ] Example questions are provided.
- [ ] Errors are presented cleanly.

---

# 38. Example User Scenarios

## Scenario 1 — Direct factual lookup

User:

> What was Tesla's total revenue?

Expected:

```text
Route: Direct
Cache: Miss
Retrieved chunks: 3
Reranking: No
Answer: [grounded answer]
Sources: [page references]
```

## Scenario 2 — Repeated question

User:

> What was Tesla's total revenue?

Then:

> How much total revenue did Tesla report?

Expected:

```text
Route: Cached
Cache: Hit
Similarity: >= configured threshold
```

The second request should not execute the full RAG pipeline.

## Scenario 3 — Broad question

User:

> Tell me about Tesla's growth strategy.

Expected:

```text
Route: Thematic
Query expansion: Yes
Expansions: <= 3
Initial retrieval: 5+
Reranking: Yes
Final context: 3
```

## Scenario 4 — Analytical question

User:

> Compare Tesla's financial performance across the reported years and explain the major changes.

Expected:

```text
Route: Analytical
Query expansion: Yes
Reranking: Yes
Final context: 3
Analytical generation prompt
Sources displayed
```

---

# 39. Important Implementation Principles for GitHub Copilot

GitHub Copilot should implement the system incrementally and modularly.

### Principle 1 — Keep components loosely coupled

The following components should have clear interfaces:

```text
DocumentLoader
Chunker
EmbeddingProvider
VectorStore
SemanticCache
QueryRouter
QueryExpander
Retriever
Reranker
LLMClient
AnswerGenerator
PipelineOrchestrator
```

### Principle 2 — Avoid unnecessary abstraction

This is a POC.

Do not create an enterprise-scale framework or dozens of unnecessary classes.

Prefer simple, readable Python modules.

### Principle 3 — Configuration-driven behavior

Do not hard-code:

- Model names.
- API keys.
- Chunk size.
- Chunk overlap.
- Retrieval count.
- Cache threshold.
- Cache TTL.
- Reranker model.
- Expansion count.

### Principle 4 — Preserve metadata

Page/source metadata must survive:

```text
PDF
→ chunk
→ embedding
→ retrieval
→ reranking
→ generation
→ UI
```

### Principle 5 — Make the pipeline observable

Every request should produce enough metadata to understand which route was used and what retrieval operations occurred.

### Principle 6 — Fail gracefully

One failed optional component should not crash the entire application where a sensible fallback exists.

---

# 40. Future Extension Points

The architecture should make these future additions possible without redesigning the entire application:

- Multiple PDF documents.
- Multiple document collections.
- Hybrid BM25 + vector retrieval.
- Advanced metadata filtering.
- Parent-child retrieval.
- Multi-vector retrieval.
- Persistent semantic cache.
- Redis cache.
- Production observability.
- Authentication.
- Cloud deployment.
- Streaming responses.
- Conversation memory.
- Evaluation framework.
- RAGAS-style evaluation.
- Citation verification.
- Document upload UI.

These are explicitly future extensions and should **not** be implemented in the initial POC unless required to make the core application work.

---

# 41. Final Product Definition

The finished application should demonstrate the following story to a client:

> A user asks a question about a Tesla financial report. The application first checks whether a semantically similar question has already been answered. If not, it intelligently routes the question to an appropriate RAG strategy. Broader questions can be expanded into multiple search queries, retrieved evidence can be reranked, and the final answer is generated from the most relevant sections of the report. The UI exposes the route, cache behavior, retrieval process, and source pages so the client can see that the answer is grounded in the document.

The application should remain intentionally lightweight:

```text
Python
├── Streamlit
├── LangChain
├── MiniLM
├── ChromaDB
├── Cross-Encoder Reranker
└── Groq GPT-OSS-20B
```

No application database is required.

No GPU is required.

No external web search is required.

No agent framework is required.

No unnecessary infrastructure should be introduced.

The primary success criterion is a polished, understandable, technically credible RAG POC that can be implemented locally and demonstrated quickly to a client.
