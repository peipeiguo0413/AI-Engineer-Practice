import shutil
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.retrievers import BM25Retriever
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Setup
shutil.rmtree("./chroma_hybrid", ignore_errors=True)

pdf_path = "/Users/peipeiguo/Desktop/AI Agent Learning/user_data/Online Assessments Guide.pdf"
loader = PyPDFLoader(pdf_path)
pages = loader.load()

splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
chunks = splitter.split_documents(pages)

embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_hybrid",
)

# BM25 retriever
bm25_retriever = BM25Retriever.from_documents(chunks)
bm25_retriever.k = 3

llm = ChatAnthropic(model="claude-haiku-4-5")

# HyDE chain
hyde_prompt = ChatPromptTemplate.from_template("""
Write a short passage from an official guide that answers this question.
2-3 sentences only.

Question: {question}
""")
hyde_chain = hyde_prompt | llm | StrOutputParser()

# RRF fusion
def rrf_fusion(results_list, k=60):
    scores = {}
    contents = {}
    
    for results in results_list:
        for rank, doc in enumerate(results):
            key = doc.page_content[:50]  # use content as key
            if key not in scores:
                scores[key] = 0
                contents[key] = doc
            scores[key] += 1 / (k + rank + 1)
    
    # Sort by RRF score
    sorted_keys = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    return [(contents[k], scores[k]) for k in sorted_keys]

# Hybrid search
def hybrid_search(query, top_k=3):
    # 1. Normal vector search
    vector_results = vectorstore.similarity_search(query, k=3)
    
    # 2. HyDE vector search
    hypothetical = hyde_chain.invoke({"question": query})
    hyde_results = vectorstore.similarity_search(hypothetical, k=3)
    
    # 3. BM25 keyword search
    bm25_results = bm25_retriever.invoke(query)
    
    # 4. RRF fusion
    fused = rrf_fusion([vector_results, hyde_results, bm25_results])
    
    return fused[:top_k]

# Answer chain
answer_prompt = ChatPromptTemplate.from_template("""
Answer based only on the context below.
If the answer is not in the context, say "I don't have that information."

Context:
{context}

Question: {question}
""")
answer_chain = answer_prompt | llm | StrOutputParser()

def ask_hybrid(question):
    results = hybrid_search(question)
    
    print(f"Q: {question}")
    print("Top chunks after RRF fusion:")
    for doc, score in results:
        print(f"  rrf={score:.4f} | {doc.page_content[:80]}...")
    
    context = "\n\n".join([doc.page_content for doc, _ in results])
    answer = answer_chain.invoke({"context": context, "question": question})
    print(f"A: {answer}\n")

# Test
ask_hybrid("Can I take a break during the test?")
ask_hybrid("What tool is used for the coding exam?")
ask_hybrid("Is preparation needed for the work style assessment?")
ask_hybrid("What is the pass mark?")