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
- **Chain-of-Thought (CoT)**: step-by-step reasoning for complex decisions (loan approval)
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
- Key insight: *chunking quality determines everything downstream — it's the foundation*

#### Week 6 — PDF RAG & Score Filtering
- `PyPDFLoader` for real PDF ingestion
- `similarity_search_with_score()` — Chroma returns cosine distance (lower = more similar)
- Fixed threshold: `score < 0.7` vs dynamic: `score - best_score < 0.4`
- Key insight: *not all retrieved chunks are useful — score filtering is essential*

#### Week 7 — HyDE + Hybrid Search
- **HyDE**: generate hypothetical answer → embed it → search
- **BM25** keyword search — catches exact matches vector search misses
- **RRF** (Reciprocal Rank Fusion): `score = Σ 1/(k + rank)` — rank-based merging
- Full hybrid pipeline: vector + HyDE + BM25 → RRF → top-K
- Key insight: *semantic search and keyword search are complementary — combine them*

#### Week 8 — RAG Evaluation
- RAGAS dependency conflicts → built custom LLM-as-judge evaluator
- **4 metrics**: Faithfulness, Answer Relevancy, Context Recall, Context Precision
- Key insight: *"my RAG is good" means nothing without numbers*

#### Week 9 — LLM Capability Boundaries
- Math unreliability → Calculator tool; Temperature behavior; Knowledge cutoff
- Unstructured extraction: meeting notes → structured JSON (LLM's strongest capability)
- Key insight: *know what LLM is bad at, then give it a tool to compensate*

---

### Phase 3 · Prompt Engineering & Applications (Week 10–11)

#### Week 10 — Production Prompt Engineering
- Prompt versioning with `PROMPT_REGISTRY`, rollback-ready
- A/B testing framework: same test dataset across prompt versions
- Two-layer injection defense: keyword regex + length truncation
- Key insight: *never rely on the model to defend itself — sanitize inputs in code*

#### Week 11 — LLM for Data Analysis
- **Text-to-SQL**: natural language → LLM generates SQL → SQLite executes → natural language answer
- **Auto business analysis**: raw query results → LLM generates executive summary with insights
- Key insight: *LLM's real power in data analysis is synthesis and interpretation, not just querying*

---

### Phase 4 · Agent & Multi-Agent Systems (Week 12–14)

#### Week 12 — Agent Design & Tool Calling
- **ReAct loop**: Reason → Act → Observe → repeat until complete
- `@tool` decorator — docstring tells LLM when and how to use the tool
- `create_tool_calling_agent` + `AgentExecutor` with `verbose=True`
- Tools: calculator, word counter, currency converter, web search (DuckDuckGo)
- Key insight: *LLM decides, tools execute — divide responsibilities clearly*

#### Week 13 — LangGraph State Machine
- `StateGraph` with typed `State` dict shared across nodes
- `Annotated[list, operator.add]` — cumulative vs overwrite fields
- Conditional edges: `add_conditional_edges("node", routing_fn)`
- Feedback loop: Writer → Reviewer → (approved? END : Writer)
- Key insight: *`Annotated` with `operator.add` is how you preserve history across nodes*

#### Week 14 — Supervisor Pattern + Human-in-the-loop
- **Supervisor pattern**: one LLM orchestrator routes to specialist worker agents
- `interrupt()` pauses graph; `Command(resume=value)` resumes with human input
- `MemorySaver` persists state across pause/resume
- Critical lesson: **side effects belong OUTSIDE graph nodes** — nodes re-execute on resume

---

### Phase 5 · Fine-tuning (Week 15)

#### Week 15 — Fine-tuning Fundamentals
- Decision framework: Prompt → RAG → Stronger model → Fine-tune (last resort)
- **Knowledge distillation**: strong model generates training data → fine-tune weak model
- LLM's three roles: student (being trained), data generator, evaluator/judge
- Key insight: *fine-tuning changes instincts; prompting gives instructions every time*

---

### Phase 6 · System Design (Week 16)

#### Practiced: Design a RAG Q&A System for 1M Users

**Framework:**
```
1. Clarify Requirements    4. Data Flow
2. Core Entities           5. High-level Design
3. REST API Design         6. Deep Dive  →  7. Trade-offs
```

**Key decisions:**
- Async API pattern (POST → chatId, GET chatId → answer) for 2-3s RAG latency
- JWT in Authorization header — never userId in request body
- Semantic Cache (Redis, 0.95 threshold) → 30% LLM call reduction
- HNSW indexing for ANN — 5% accuracy trade-off for sub-ms vector queries
- Least Connection load balancing over Round Robin for variable-latency RAG
- Eventual consistency for ingestion — availability > strong consistency
- Model routing: Haiku 80% + Opus 20% → ~60% cost reduction

---

### Phase 7 · Capstone Project (Week 17–18)

## Real Estate Copilot 🏠
**AI-powered property intelligence API**

> "Zillow helps you find homes. We help you decide."

### Core Insight
Zestimate's primary error source is missing interior condition data. Real Estate Copilot acts as a **condition intelligence layer on top of any AVM** — collecting renovation history, appliance age, and inspection findings that no public record contains, then using them to produce condition-adjusted price predictions with tighter confidence intervals.

---

### Features Built

#### Feature 1: Property Intelligence Report (Core)
`POST /v1/property/intelligence`

Full analysis pipeline combining three data sources:

**Step 1 — Interior Condition Form**
Structured Pydantic model capturing data absent from all AVM tools:
- Kitchen: renovation year, condition score
- Bathrooms: master bath renovation, condition
- Flooring: type, age, condition
- Roof & Structure: age, condition, foundation issues
- HVAC & Utilities: furnace/AC/water heater age
- Free-text: recent upgrades, seller disclosures

**Step 2 — Inspection Report RAG**
- PDF ingestion → semantic chunking → hybrid retrieval (vector + BM25 + HyDE) → RRF fusion
- Extracts findings with severity (Critical/Major/Minor/Informational) and repair cost estimates
- BUY/NEGOTIATE/AVOID recommendation with confidence score

**Step 3 — Condition-Adjusted Price Prediction**
- Applies condition score as ±% adjustment anchored to AVM base estimate
- Rule-based adjustment prompt: kitchen renovation +2–4%, old roof -1–3%, foundation issues -5–15%
- Phase 2 plan: LightGBM ML model trained on accumulated condition + sale outcome data

**Step 4 — Auto Comparable Sales Matching**
Automatically finds 5 most similar recently sold properties:
- Matching: ZIP code, sqft (±20%), bedrooms, year built (±10yr), last 9 months
- Per-comp fields: listing price, sale price, DOM, HOA, condition score, interior condition
- Explainable price deltas: "+3% kitchen renovation, -1% roof age 8yr, -1.5% no half bath"

**Step 5 — Dual Report Generation (PDF)**
4-section Property Intelligence Report:
- Section 1: Purchase Recommendation + condition + inspection findings + strengths/risks
- Section 2: Price Analysis + financial model (mortgage, ROI for investors)
- Section 3: Top Comparable Sales — full table + interior condition + listing links
- Section 4: Negotiation Strategy + suggested offer range + ready-to-send offer email

Optional agent co-branding via `agent_name` + `agent_license` parameters.

#### Feature 2: Quick Fit Check (Free Tier)
`POST /v1/property/fit-check`

Lightweight screening against user preference profile:
- Budget fit, bedroom/bathroom match, school district rating, commute time, amenities
- Returns fit_score (0–100) + WORTH VISITING / BORDERLINE / SKIP verdict
- No form required — public data only
- Free funnel entry point that converts to full intelligence report

#### Feature 3: Multi-Property Comparison
`POST /v1/property/compare`

User-selected comparison for final purchase decisions:
- Submit 2–5 shortlisted properties
- Each runs full condition scoring pipeline
- Normalized 8-dimension scoring matrix + deal-breaker flags + ranked recommendation

---

### Validation Framework (4 Layers)

```python
Layer 1: Format validation
  price must be numeric/positive
  verdict must be BUY/NEGOTIATE/AVOID

Layer 2: Sanity check
  price deviation > 25% from asking → warning

Layer 3: Logic consistency
  BUY verdict + Critical inspection issues → warning

Layer 4: Condition consistency
  Poor condition score (< 55) + BUY verdict → warning

Output: trust_level = "high" / "medium" / "low"
```

---

### Tech Stack

| Component | Technology |
|-----------|------------|
| LLM | Anthropic Claude (Haiku + Opus) |
| Orchestration | LangGraph Supervisor pattern |
| RAG | Chroma + BM25 + HyDE + RRF fusion |
| Embeddings | all-MiniLM-L6-v2 |
| Data Models | Pydantic |
| PDF Generation | ReportLab |
| API | FastAPI + JWT auth |
| Language | Python 3.9 |

---

### Project Structure

```
real-estate-copilot/
├── app/
│   ├── agents/
│   │   └── property_agent.py          # Main orchestrator + 4-layer validation
│   ├── tools/
│   │   ├── property_tools.py          # Market search, mortgage, ROI, price prediction
│   │   └── comp_tools.py              # Auto comparable sales matching
│   ├── rag/
│   │   └── inspection_rag.py          # PDF RAG pipeline (hybrid retrieval + RRF)
│   ├── models/
│   │   └── property_form.py           # Pydantic interior condition form
│   └── reports/
│       ├── inspection_report_pdf.py   # Standalone inspection report
│       └── property_intelligence_pdf.py  # Full 4-section buyer/investor report
├── test_property_agent.py
├── test_inspection.py
└── test_tools.py
```

### Run

```bash
# Always use PYTHONPATH — not Cursor Run button
PYTHONPATH=. python3 test_property_agent.py
PYTHONPATH=. python3 test_inspection.py
PYTHONPATH=. python3 test_tools.py
```

---

### Known Limitations & Roadmap

```
Current (Phase 1):
  Price prediction:  LLM-based condition adjustment anchored to asking price
  Comp data:         AI-generated for illustrative purposes
  Market data:       LLM-generated estimates

Phase 2 (with real data APIs):
  Integrate Zillow / ATTOM / MLS APIs for real comparable sales
  Real school ratings via GreatSchools API
  Real walk scores and commute time APIs
  LightGBM price model trained on accumulated condition + sale data
  Target price prediction MAE: < 2.5%
```

---

## Core Mental Models

```
1. LLM is stateless
   "memory" = history list you send every time

2. Model is a black box — you control only the input
   Optimize order: Prompt → RAG → Stronger model → Fine-tune

3. Chunking is the foundation of RAG
   Bad chunks → bad retrieval → bad answers

4. LLM decides, tools execute
   Give LLM what it's bad at (math, real-time data) as tools

5. Evaluation turns "feels good" into "is good"
   No number = no improvement direction

6. Side effects belong outside LangGraph nodes
   Nodes re-execute on resume — side effects run twice

7. Security: sanitize in code, not in prompt
   JWT in header, never userId in body

8. Anchoring beats hallucination
   Price prediction: anchor to AVM base + condition adjustment
   Never let LLM generate absolute numbers from scratch
```

---

*Last updated: Week 18 — Property Intelligence Report PDF complete*
