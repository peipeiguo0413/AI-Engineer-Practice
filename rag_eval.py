from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_recall,
    context_precision,
)
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import shutil

# ── Setup ──────────────────────────────────────────────
shutil.rmtree("./chroma_ragas", ignore_errors=True)

pdf_path = "/Users/peipeiguo/Desktop/AI Agent Learning/user_data/Online Assessments Guide.pdf"
loader = PyPDFLoader(pdf_path)
pages = loader.load()

splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
chunks = splitter.split_documents(pages)

embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_ragas",
)

llm = ChatAnthropic(model="claude-haiku-4-5")

answer_prompt = ChatPromptTemplate.from_template("""
Answer based only on the context below.
If the answer is not in the context, say "I don't have that information."

Context:
{context}

Question: {question}
""")
answer_chain = answer_prompt | llm | StrOutputParser()

# ── Test dataset ───────────────────────────────────────
# RAGAS needs: question, answer, contexts, ground_truth
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
        "question": "Is preparation needed for the Preferences at Work assessment?",
        "ground_truth": "No preparation is needed. You should answer honestly as the questions are about how you prefer to work."
    },
    {
        "question": "Can I pause the coding assessment once started?",
        "ground_truth": "No, you cannot pause the assessment. Once the timer starts you cannot pause it and must complete it in one sitting."
    },
    {
        "question": "What browsers are recommended for the assessment?",
        "ground_truth": "Chrome, Firefox, Microsoft Edge (Windows only), and Safari (Mac only) are recommended."
    },
]

# ── Run RAG and collect results ────────────────────────
questions, answers, contexts, ground_truths = [], [], [], []

for case in test_cases:
    # Retrieve
    docs = vectorstore.similarity_search(case["question"], k=3)
    context_texts = [doc.page_content for doc in docs]
    
    # Generate
    context_str = "\n\n".join(context_texts)
    answer = answer_chain.invoke({
        "context": context_str,
        "question": case["question"]
    })
    
    questions.append(case["question"])
    answers.append(answer)
    contexts.append(context_texts)
    ground_truths.append(case["ground_truth"])
    
    print(f"Q: {case['question'][:50]}...")
    print(f"A: {answer[:80]}...\n")

# ── RAGAS evaluation ───────────────────────────────────
dataset = Dataset.from_dict({
    "question": questions,
    "answer": answers,
    "contexts": contexts,
    "ground_truth": ground_truths,
})

print("\nRunning RAGAS evaluation...\n")
results = evaluate(
    dataset=dataset,
    metrics=[
        faithfulness,
        answer_relevancy,
        context_recall,
        context_precision,
    ],
)

print(results)