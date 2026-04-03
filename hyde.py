import shutil
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Setup (reuse from Week 6)
shutil.rmtree("./chroma_hyde", ignore_errors=True)

pdf_path = "/Users/peipeiguo/Desktop/AI Agent Learning/user_data/Online Assessments Guide.pdf"
loader = PyPDFLoader(pdf_path)
pages = loader.load()

splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
chunks = splitter.split_documents(pages)

embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_hyde",
)

llm = ChatAnthropic(model="claude-haiku-4-5")

# Normal retrieval
def normal_search(query, k=3):
    docs = vectorstore.similarity_search(query, k=k)
    return docs

# HyDE retrieval
hyde_prompt = ChatPromptTemplate.from_template("""
Write a short passage that would answer the following question.
Write it as if it's from an official guide document.
Be concise, 2-3 sentences only.

Question: {question}
""")

hyde_chain = hyde_prompt | llm | StrOutputParser()

def hyde_search(query, k=3):
    # Step 1: generate hypothetical answer
    hypothetical_doc = hyde_chain.invoke({"question": query})
    print(f"  Hypothetical doc: {hypothetical_doc[:100]}...")
    
    # Step 2: use hypothetical answer to search
    docs = vectorstore.similarity_search(hypothetical_doc, k=k)
    return docs

# Compare on a tricky query (different wording from the document)
tricky_queries = [
    "Can I take a break during the test?",
    "What tool is used for the coding exam?",
    "Is preparation needed for the work style assessment?",
]

answer_prompt = ChatPromptTemplate.from_template("""
Answer based only on the context. If not in context, say "I don't have that information."

Context: {context}
Question: {question}
""")
answer_chain = answer_prompt | llm | StrOutputParser()

for query in tricky_queries:
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    
    # Normal
    normal_docs = normal_search(query)
    normal_context = "\n".join([d.page_content[:100] for d in normal_docs])
    normal_answer = answer_chain.invoke({"context": normal_context, "question": query})
    print(f"\nNormal RAG: {normal_answer}")
    
    # HyDE
    hyde_docs = hyde_search(query)
    hyde_context = "\n".join([d.page_content[:100] for d in hyde_docs])
    hyde_answer = answer_chain.invoke({"context": hyde_context, "question": query})
    print(f"HyDE RAG:   {hyde_answer}")