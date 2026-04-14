import shutil
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.retrievers import BM25Retriever
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.config import (
    CHROMA_DB_PATH, MODEL_FAST, MODEL_SMART,
    CHUNK_SIZE, CHUNK_OVERLAP, TOP_K_RESULTS
)
import json, re

# ── Embedding model (shared across modules) ────────────
embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

llm_fast  = ChatAnthropic(model=MODEL_FAST,  temperature=0, max_tokens=1024)
llm_smart = ChatAnthropic(model=MODEL_SMART, temperature=0, max_tokens=2048)

# ── Load and chunk PDF ─────────────────────────────────
def load_inspection_report(pdf_path: str) -> list:
    loader = PyPDFLoader(pdf_path)
    pages  = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = splitter.split_documents(pages)
    print(f"  Loaded {len(pages)} pages → {len(chunks)} chunks")
    return chunks

# ── Build hybrid retriever ─────────────────────────────
def build_retriever(chunks: list, collection_name: str):
    # Vector store
    db_path = f"{CHROMA_DB_PATH}/{collection_name}"
    shutil.rmtree(db_path, ignore_errors=True)

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=db_path,
    )

    # BM25 for keyword matching
    bm25 = BM25Retriever.from_documents(chunks)
    bm25.k = TOP_K_RESULTS

    return vectorstore, bm25

# ── RRF fusion ─────────────────────────────────────────
def rrf_search(query: str, vectorstore, bm25, k: int = 3) -> list:
    vector_results = vectorstore.similarity_search(query, k=k)
    bm25_results   = bm25.invoke(query)

    scores   = {}
    contents = {}
    for results in [vector_results, bm25_results]:
        for rank, doc in enumerate(results):
            key = doc.page_content[:80]
            if key not in scores:
                scores[key]   = 0
                contents[key] = doc
            scores[key] += 1 / (60 + rank + 1)

    sorted_keys = sorted(scores, key=lambda x: scores[x], reverse=True)
    return [contents[k] for k in sorted_keys[:k]]

# ── Parse JSON safely ──────────────────────────────────
def parse_json(raw: str) -> dict:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"error": "Failed to parse response", "raw": raw[:200]}

# ── Main analysis function ─────────────────────────────
# =============================================================================
# TODO (Phase 1.5): 10-Year Cost Projection per Inspection Finding
# Location: add to analyze_inspection_report() output
# Purpose: transform repair costs from one-time to lifetime perspective
# Implementation:
#   For each finding, estimate:
#   - immediate_cost: current repair estimate (already have this)
#   - year_5_risk: probability issue escalates if not fixed
#   - year_10_projected_cost: if ignored, what will it cost in 10 years
#   - recommended_action: fix now / monitor / budget for replacement
#   Example output per finding:
#   {
#     "issue": "Heat exchanger not fully inspectable",
#     "severity": "Major",
#     "immediate_cost": {"low": 200, "high": 500},
#     "year_10_projected_cost": {"low": 3000, "high": 6000},
#     "year_5_risk": "high — full HVAC replacement likely within 5-7 years",
#     "recoended_action": "Budget $4,000-$6,000 for HVAC replacement"
#   }
#   Summary: total_10yr_low, total_10yr_high
#   "This property may require $12,000-$28,000 in repairs over the next 10 years"
# =============================================================================

def analyze_inspection_report(pdf_path: str) -> dict:
    print(f"\nAnalyzing: {pdf_path}")

    # Step 1: Load and index
    chunks    = load_inspection_report(pdf_path)
    vectorstore, bm25 = build_retriever(chunks, "inspection")

    # Step 2: Extract all findings
    findings_prompt = ChatPromptTemplate.from_template("""
You are a professional home inspector analyst.
Analyze the following inspection report excerpts and extract ALL findings.

Context:
{context}

Return a JSON object only:
{{
  "findings": [
    {{
      "category": "Roof/Electrical/Plumbing/HVAC/Structural/Other",
      "issue": "brief description of the issue",
      "severity": "Critical/Major/Minor/Informational",
      "estimated_repair_cost_usd": {{"low": 0, "high": 0}},
      "recommendation": "what should be done"
    }}
  ]
}}

Severity guide:
- Critical: safety hazard or major structural issue, must fix before purchase
- Major: significant defect, negotiate repair or price reduction
- Minor: maintenance item, low urgency
- Informational: noted for awareness, no action required
""")

    # Search for issues across key categories
    queries = [
        "safety hazards defects problems issues",
        "roof damage water leaks moisture",
        "electrical wiring panel issues",
        "plumbing pipes water heater",
        "HVAC heating cooling system",
        "structural foundation walls",
    ]

    all_chunks = []
    for query in queries:
        results = rrf_search(query, vectorstore, bm25, k=2)
        all_chunks.extend(results)

    # Deduplicate
    seen    = set()
    unique  = []
    for doc in all_chunks:
        key = doc.page_content[:60]
        if key not in seen:
            seen.add(key)
            unique.append(doc)

    context = "\n\n".join([d.page_content for d in unique])

    findings_chain = findings_prompt | llm_smart | StrOutputParser()
    findings_raw   = findings_chain.invoke({"context": context})
    findings_data  = parse_json(findings_raw)

    # Step 3: Generate recommendation
    recommend_prompt = ChatPromptTemplate.from_template("""
Based on these inspection findings, provide a purchase recommendation.

Findings:
{findings}

Return JSON only:
{{
  "recommendation": "BUY/NEGOTIATE/AVOID",
  "confidence": 0.0-1.0,
  "summary": "2-3 sentence plain-language summary for a home buyer",
  "total_estimated_repair_cost": {{"low": 0, "high": 0}},
  "critical_issues_count": 0,
  "major_issues_count": 0,
  "key_concerns": ["top 3 concerns"]
}}
""")

    recommend_chain = recommend_prompt | llm_smart | StrOutputParser()
    recommend_raw   = recommend_chain.invoke({
        "findings": json.dumps(findings_data, indent=2)
    })
    recommend_data  = parse_json(recommend_raw)

    # Step 4: Combine results
    return {
        "pdf_path":       pdf_path,
        "chunks_analyzed": len(unique),
        **findings_data,
        **recommend_data,
    }