import os
import json
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import re

llm = ChatAnthropic(model="claude-haiku-4-5")

# ── Faithfulness evaluator ─────────────────────────────
faithfulness_prompt = ChatPromptTemplate.from_template("""
You are evaluating whether an answer is faithful to the given context.

Context: {context}
Answer: {answer}

Break the answer into individual statements.
For each statement, check if it can be supported by the context.
Return JSON only:
{{"score": 0.0-1.0, "reason": "brief explanation"}}
""")

# ── Answer Relevancy evaluator ─────────────────────────
relevancy_prompt = ChatPromptTemplate.from_template("""
You are evaluating whether an answer is relevant to the question.

Question: {question}
Answer: {answer}

Score how well the answer addresses the question.
Return JSON only:
{{"score": 0.0-1.0, "reason": "brief explanation"}}
""")

# ── Context Recall evaluator ───────────────────────────
recall_prompt = ChatPromptTemplate.from_template("""
You are evaluating whether the context contains enough information to answer the question.

Question: {question}
Context: {context}
Ground truth: {ground_truth}

Check if all key information in the ground truth can be found in the context.
Return JSON only:
{{"score": 0.0-1.0, "reason": "brief explanation"}}
""")

# ── Context Precision evaluator ────────────────────────
precision_prompt = ChatPromptTemplate.from_template("""
You are evaluating whether the retrieved context is relevant to the question.

Question: {question}
Context: {context}

Check what proportion of the context is actually useful for answering the question.
Return JSON only:
{{"score": 0.0-1.0, "reason": "brief explanation"}}
""")

def parse_json(raw):
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        score = re.search(r'"score"\s*:\s*([\d.]+)', cleaned)
        reason = re.search(r'"reason"\s*:\s*"(.+?)"', cleaned, re.DOTALL)
        return {
            "score": float(score.group(1)) if score else 0.0,
            "reason": reason.group(1) if reason else "parse failed"
        }

eval_chain = StrOutputParser()

def evaluate_single(question, answer, contexts, ground_truth):
    context_str = "\n\n".join(contexts)
    
    results = {}
    
    # Faithfulness
    r = llm.invoke(faithfulness_prompt.format_messages(
        context=context_str, answer=answer))
    results["faithfulness"] = parse_json(r.content)
    
    # Answer Relevancy
    r = llm.invoke(relevancy_prompt.format_messages(
        question=question, answer=answer))
    results["answer_relevancy"] = parse_json(r.content)
    
    # Context Recall
    r = llm.invoke(recall_prompt.format_messages(
        question=question, context=context_str, ground_truth=ground_truth))
    results["context_recall"] = parse_json(r.content)
    
    # Context Precision
    r = llm.invoke(precision_prompt.format_messages(
        question=question, context=context_str))
    results["context_precision"] = parse_json(r.content)
    
    return results

# ── Test cases ─────────────────────────────────────────
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_core.prompts import ChatPromptTemplate as CT
import shutil

shutil.rmtree("./chroma_eval", ignore_errors=True)
pdf_path = "/Users/peipeiguo/Desktop/AI Agent Learning/user_data/Online Assessments Guide.pdf"
pages = PyPDFLoader(pdf_path).load()
chunks = RecursiveCharacterTextSplitter(
    chunk_size=300, chunk_overlap=50).split_documents(pages)
embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Chroma.from_documents(
    documents=chunks, embedding=embeddings,
    persist_directory="./chroma_eval")

answer_prompt = CT.from_template("""
Answer based only on the context below.
If not in context, say "I don't have that information."
Context: {context}
Question: {question}
""")
answer_llm = ChatAnthropic(model="claude-haiku-4-5")
answer_chain = answer_prompt | answer_llm | StrOutputParser()

test_cases = [
    {
        "question": "How long is the online coding assessment?",
        "ground_truth": "The online coding assessment is 90 minutes long."
    },
    {
        "question": "What tool is used for the coding exam?",
        "ground_truth": "CodeSignal is the platform used for the coding assessment."
    },
    {
        "question": "Can I pause the coding assessment once started?",
        "ground_truth": "No, you cannot pause it. Must complete in one sitting."
    },
]

# ── Run evaluation ─────────────────────────────────────
all_scores = {
    "faithfulness": [],
    "answer_relevancy": [],
    "context_recall": [],
    "context_precision": [],
}

for case in test_cases:
    docs = vectorstore.similarity_search(case["question"], k=3)
    context_texts = [doc.page_content for doc in docs]
    context_str = "\n\n".join(context_texts)
    
    answer = answer_chain.invoke({
        "context": context_str,
        "question": case["question"]
    })
    
    print(f"\nQ: {case['question']}")
    print(f"A: {answer[:80]}...")
    
    scores = evaluate_single(
        case["question"], answer,
        context_texts, case["ground_truth"]
    )
    
    for metric, result in scores.items():
        all_scores[metric].append(result["score"])
        print(f"  {metric}: {result['score']:.2f} — {result['reason']}")

# ── Final scores ───────────────────────────────────────
print("\n" + "="*50)
print("FINAL SCORES")
print("="*50)
for metric, scores in all_scores.items():
    avg = sum(scores) / len(scores)
    print(f"{metric:25s}: {avg:.2f}")
