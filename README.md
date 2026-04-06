# LLM Learning Journey
### LLM Application Engineer Track — 26-Week Program

---

## Progress
**Currently on:** Week 18 of 26 — Real Estate Copilot (Capstone Project)

---

## Completed Modules

### Phase 1 · Core Foundations (Week 1–4)

#### Week 1 — Native API & Core Concepts
- Multi-turn conversation CLI with full history management
- Understood LLM statelessness: memory = history list sent on every request
- Token growth visualization: input tokens grow linearly with conversation turns
- Context window truncation: `history[-6:]` with role-pair integrity check
- Structured output with defensive JSON parsing (`json.loads` + regex fallback)
- Learned: AI outputs are never fully reliable — always parse defensively

#### Week 2 — Prompt Engineering
- **Few-shot prompting**: examples embedded in `messages[]` as user/assistant pairs
- **Chain-of-Thought (CoT)**: step-by-step reasoning for complex decisions (loan approval case study)
- **System prompt design**: role definition, behavior constraints, output format control
- **Prompt injection defense**: keyword detection + length limiting as two-layer protection
- **Prompt versioning & A/B testing**: `PROMPT_REGISTRY` pattern for production iteration
- Key insight: *the model is a fixed black box — you can only control the input*

#### Week 3 — LangChain LCEL
- `prompt | model | parser` pipe operator — Unix pipeline metaphor
- `ChatPromptTemplate` with variable substitution
- `MessagesPlaceholder` for injecting conversation history
- `JsonOutputParser` replacing hand-written `parse_json()`
- Key insight: *LangChain wraps what you already built — understanding the raw API first matters*

#### Week 4 — FastAPI Deployment
- FastAPI + Pydantic request/response models
- Multi-user session isolation via `sessions: dict`
- Streaming output with `StreamingResponse` + `astream()`
- JWT auth pattern: userId always in Authorization header, never in request body
- Production note: in-memory sessions → Redis in production

---

### Phase 2 · RAG Systems (Week 5–9)

#### Week 5 — RAG Foundations
- Complete RAG pipeline: document → chunking → embedding → Chroma → retrieval → generation
- `RecursiveCharacterTextSplitter`: `chunk_size`, `chunk_overlap`, separator priority
- `SentenceTransformerEmbeddings` with `all-MiniLM-L6-v2`
- Retrieval evaluation framework: `Recall@K` with keyword matching
- Improved accuracy from **40% → 100%** by optimizing chunking strategy
- Key insight: *chunking quality determines everything downstream — it's the foundation*

#### Week 6 — PDF RAG & Score Filtering
- `PyPDFLoader` for real PDF ingestion
- `similarity_search_with_score()` — Chroma returns cosine distance (lower = more similar)
- Fixed threshold filtering: `score < 0.7`
- Dynamic threshold: `score - best_score < 0.4` (self-adaptive, more robust)
- Tested on Meta Online Assessments Guide PDF
- Key insight: *not all retrieved chunks are useful — score filtering is essential*

#### Week 7 — HyDE + Hybrid Search
- **HyDE** (Hypothetical Document Embedding): generate a hypothetical answer → embed it → search
  - Works when user query style differs from document style
  - Fails when LLM doesn't know the domain (hallucinated hypothetical → wrong direction)
- **BM25** keyword search via `BM25Retriever` — catches exact matches vector search misses
- **RRF** (Reciprocal Rank Fusion): rank-based score merging across search methods
  - Formula: `score = Σ 1/(k + rank)` — handles different score scales without normalization
- Full hybrid pipeline: vector + HyDE + BM25 → RRF → top-K results
- Key insight: *semantic search and keyword search are complementary — combine them*

#### Week 8 — RAG Evaluation
- RAGAS dependency conflicts → built custom evaluator using LLM-as-judge pattern
- **4 evaluation metrics:**
  - `Faithfulness`: are all answer statements grounded in context? (hallucination detector)
  - `Answer Relevancy`: does the answer actually address the question?
  - `Context Recall`: does retrieved context contain everything needed for the answer?
  - `Context Precision`: what proportion of retrieved chunks are actually useful?
- Scores on Meta PDF: Faithfulness 0.98 / Relevancy 0.92 / Recall 0.98 / Precision 0.90
- Key insight: *"my RAG is good" means nothing without numbers — evaluation is what separates engineers from tinkerers*

#### Week 9 — LLM Capability Boundaries
- **Math**: LLM reasoning is correct, but precise arithmetic is unreliable → use Calculator tool
- **Temperature**: `temperature=0` → deterministic output; `temperature>0` → creative variation
  - Production rule: classification/extraction tasks always use `temperature=0`
- **Knowledge cutoff**: LLM correctly refuses questions about events after training cutoff
- **Unstructured extraction**: meeting notes → structured JSON — LLM's strongest capability
- Key insight: *know what LLM is bad at, then give it a tool to compensate*

---

### Phase 3 · Prompt Engineering & Applications (Week 10–11)

#### Week 10 — Production Prompt Engineering
- **Prompt versioning**: `PROMPT_REGISTRY` with version, description, template — rollback-ready
- **A/B testing framework**: same test dataset across prompt versions → compare scores
- **Prompt injection defense**: two-layer protection
  - Layer 1: keyword detection via regex (catches `ignore instructions`, `system prompt`, etc.)
  - Layer 2: length truncation (prevents token overflow attacks)
- Stress-tested with malicious inputs: 3/3 injection attempts blocked
- Key insight: *never rely on the model to defend itself — sanitize inputs in code*

#### Week 11 — LLM for Data Analysis
- **Text-to-SQL pipeline**: natural language → LLM generates SQL → SQLite executes → natural language answer
  - Handles JOINs, GROUP BY, WHERE IN automatically
  - Markdown stripping required: AI wraps SQL in code blocks
- **Auto business analysis**: raw query results → LLM generates executive summary with insights
  - Automatically computed percentages and identified risks not explicitly in the data
- Key insight: *LLM's real power in data analysis is synthesis and interpretation, not just querying*

---

### Phase 4 · Agent & Multi-Agent Systems (Week 12–14)

#### Week 12 — Agent Design & Tool Calling
- **ReAct loop**: Reason → Act → Observe → repeat until task complete
- `@tool` decorator with docstring — docstring tells LLM when and how to use the tool
- `create_tool_calling_agent` + `AgentExecutor` with `verbose=True`
- Tools built: calculator, word counter, currency converter, web search (DuckDuckGo)
- Agent behaviors observed:
  - Automatically retries with different search query when first attempt fails
  - Correctly routes math to calculator, current info to web search
  - Multi-step tasks decomposed automatically (USD→EUR→GBP in two calls)
- Fixed the `1234567 * 9876543` error from Week 9: calculator tool gives correct answer
- Key insight: *LLM decides, tools execute — divide responsibilities clearly*

#### Week 13 — LangGraph State Machine
- `StateGraph` with typed `State` dict shared across all nodes
- `Annotated[list, operator.add]` — cumulative fields vs. overwrite fields
- Fixed edges: `add_edge("A", "B")` — always goes A→B
- Conditional edges: `add_conditional_edges("node", routing_fn)` — dynamic routing
- Feedback loop pattern: Writer → Reviewer → (approved? END : Writer) — max 3 iterations
- Key insight: *`Annotated` with `operator.add` is how you preserve history across nodes*

#### Week 14 — Supervisor Pattern + Human-in-the-loop
- **Supervisor pattern**: one LLM orchestrator dynamically routes to specialist worker agents
  - No hardcoded execution order — Supervisor reasons about what to do next
  - Workers always report back to Supervisor before next decision
- **Human-in-the-loop**:
  - `interrupt()` pauses graph execution and surfaces data to the caller
  - `Command(resume=value)` resumes with human input
  - `MemorySaver` persists graph state across pause/resume
  - Critical lesson: side effects (print, send email) belong OUTSIDE the graph, not in nodes
  - Reason: LangGraph re-executes nodes on resume — any side effects in nodes will run twice

---

### Phase 5 · LLM Capabilities & Fine-tuning (Week 15)

#### Week 15 — Fine-tuning Fundamentals
- Fine-tuning vs. Prompt Engineering decision framework:
  ```
  Prompt → RAG → Stronger model → Fine-tuning (last resort)
  ```
- **Two fine-tuning scenarios:**
  1. Quality gap: no existing LLM meets requirements → collect domain data → fine-tune
  2. Cost gap: expensive model works great → use it to generate training data → fine-tune cheap model
- **Knowledge distillation**: strong model (Opus) generates 1000 training examples → fine-tune weak model (Haiku) → Haiku approaches Opus quality at 1/20 the cost
- **LLM's three roles in fine-tuning**: student (being trained), data generator, evaluator/judge
- Stress test proved prompt style constraints fail on complex inputs (6 sentences instead of 2)
- Key insight: *fine-tuning changes the model's instincts; prompting gives it instructions every time*

---

### Phase 6 · System Design (Week 16 — ongoing)

#### Practiced: Design a RAG Q&A System for 1M Users

Full system design walkthrough using the framework:

**Framework:**
```
1. Clarify Requirements (Functional + Non-functional)
2. Core Entities
3. REST API design
4. Data Flow
5. High-level Design
6. Deep Dive (Latency, Cost, Scalability)
7. Trade-offs
```

**Key design decisions made:**
- Async API pattern (POST → chatId, GET chatId → answer) for 2-3s RAG latency
- JWT in Authorization header — never userId in request body (security)
- Semantic Cache (Redis, threshold 0.95) → 30% LLM call reduction, ~$1,500/day savings at scale
- HNSW indexing for ANN search — 5% accuracy trade-off for sub-millisecond vector queries
- Least Connection load balancing — better than Round Robin for variable-latency RAG queries
- Eventual consistency for document ingestion — availability > strong consistency for Q&A
- Intelligent model routing: Haiku (80% of queries) + Opus (20%) → ~60% cost reduction
- Prompt compression → 60% token reduction on context
- Request queue (Kafka) as LLM rate limit buffer

---

## Capstone Project

### Real Estate Copilot 🏠
**AI-powered property intelligence API platform**

**Status:** In development (Week 17–18)

**Tech stack:**
- LLM: Anthropic Claude (Haiku + Opus)
- Orchestration: LangGraph Supervisor pattern
- RAG: Chroma + BM25 + HyDE + RRF fusion
- API: FastAPI + JWT auth
- Evaluation: Custom 4-metric framework
- Observability: Langfuse

**Features:**
1. Inspection Report Analysis (RAG + PDF)
2. Property Intelligence (search + financial modeling)
3. Multi-Property Comparison
4. PDF Report Generation (buyer / investor / agent formats)
5. Personalized Property Matching + Subscription Alerts
6. *(Phase 2)* Seller AI Toolkit

---

## Key Metrics Achieved

| Achievement | Result |
|-------------|--------|
| RAG retrieval accuracy | 40% → 100% |
| Prompt injection defense | 3/3 attacks blocked |
| RAG evaluation scores | Faithfulness 0.98, Relevancy 0.92 |
| System design | Full RAG system design for 1M DAU |
| Capstone proposal | 11-section product proposal (PDF) |

---

## Core Mental Models

```
1. LLM is stateless — "memory" = history list you send every time

2. Model is a black box — you control only the input
   Optimize: Prompt → RAG → Stronger model → Fine-tune

3. Chunking is the foundation of RAG
   Bad chunks → bad embeddings → bad scores → bad answers

4. LLM decides, tools execute
   Give LLM what it's bad at (math, real-time data) as tools

5. Evaluation turns "feels good" into "is good"
   No number = no improvement direction

6. Side effects belong outside LangGraph nodes
   Nodes re-execute on resume — anything with side effects runs twice

7. Security: sanitize inputs in code, never rely on the model
   JWT in header, never userId in body
   Injection defense in code, not in prompt
```

---

## Tech Stack

| Category | Tools |
|----------|-------|
| LLM | Anthropic Claude (Opus, Sonnet, Haiku) |
| Frameworks | LangChain, LangGraph, FastAPI |
| Vector DB | Chroma |
| Retrieval | BM25, HyDE, RRF fusion |
| Evaluation | Custom RAGAS-style evaluator |
| Search | DuckDuckGo Search |
| Database | SQLite (dev), PostgreSQL (prod) |
| Cache | Redis (semantic cache) |
| IDE | Cursor |
| Language | Python 3.9 |

---

## Repository Structure

```
llm-learning/
├── Week1_native_api/
│   ├── chat.py                  # Multi-turn conversation CLI
│   └── sentiment.py             # Structured output with defensive parsing
├── Week2_prompt_engineering/
│   ├── few_shot.py              # Few-shot customer service classifier
│   ├── cot.py                   # Chain-of-Thought loan approval
│   └── system_prompt.py         # Role + boundary control
├── Week3_langchain/
│   ├── lcel_basic.py            # Pipe operator, prompt templates
│   └── prompt_manager.py        # Versioning + A/B testing + injection defense
├── Week4_fastapi/
│   └── main.py                  # FastAPI + streaming + session management
├── Week5_rag_basic/
│   └── rag_basic.py             # Complete RAG pipeline + chunking evaluation
├── Week6_pdf_rag/
│   └── rag_pdf.py               # PDF ingestion + score-based filtering
├── Week7_hybrid_search/
│   └── hybrid_rag.py            # HyDE + BM25 + RRF fusion
├── Week8_evaluation/
│   └── rag_eval_manual.py       # Custom 4-metric RAG evaluator
├── Week9_llm_limits/
│   └── llm_limits.py            # Capability boundary experiments
├── Week10_prompt_engineering/
│   └── prompt_manager.py        # Production prompt management
├── Week11_data_analysis/
│   └── text_to_sql.py           # Text-to-SQL + auto report generation
├── Week12_agents/
│   └── agent_basic.py           # ReAct agent with 4 tools
├── Week13_langgraph/
│   └── langgraph_basic.py       # State machine + conditional edges
├── Week14_multiagent/
│   ├── supervisor.py            # Supervisor pattern
│   └── human_in_loop.py         # interrupt/resume with MemorySaver
├── Week15_finetuning/
│   └── finetune_demo.py         # Prompt boundary stress test
└── real-estate-copilot/         # Capstone project
    ├── app/
    │   ├── agents/
    │   ├── tools/
    │   ├── rag/
    │   ├── api/
    │   └── config.py
    └── main.py
```

---

*Last updated: Week 18 — Real Estate Copilot development started*