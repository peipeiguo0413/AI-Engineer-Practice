import shutil
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Clean up old database
shutil.rmtree("./chroma_pdf", ignore_errors=True)

# Step 1: Load PDF
loader = PyPDFLoader("/Users/peipeiguo/Desktop/AI Agent Learning/user_data/Online Assessments Guide.pdf")
pages = loader.load()
print(f"Loaded {len(pages)} pages")

# Step 2: Split into chunks
splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=50,
)
chunks = splitter.split_documents(pages)
print(f"Split into {len(chunks)} chunks")

# Step 3: Store in Chroma
embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_pdf",
)
print(f"Stored in Chroma\n")

# Step 4: RAG chain
llm = ChatAnthropic(model="claude-haiku-4-5")
prompt = ChatPromptTemplate.from_template("""
Answer the question based only on the following context.
If the answer is not in the context, say "I don't have that information."

Context:
{context}

Question: {question}
""")
chain = prompt | llm | StrOutputParser()

def ask(question):
    docs = vectorstore.similarity_search(question, k=3)
    context = "\n\n".join([doc.page_content for doc in docs])
    answer = chain.invoke({"context": context, "question": question})
    print(f"Q: {question}")
    print(f"A: {answer}\n")

# Test with real questions about the PDF
ask("How long is the online coding assessment?")
ask("What browsers are recommended for the assessment?")
ask("Can I use ChatGPT during the coding assessment?")
ask("How many questions are in the Preferences @ Work assessment?")
ask("What is the pass mark for the assessment?")  # not in the doc

def ask_with_sources(question):
    docs = vectorstore.similarity_search(question, k=3)
    
    print(f"Q: {question}")
    print("Retrieved chunks:")
    for i, doc in enumerate(docs):
        print(f"  [{i+1}] Page {doc.metadata.get('page', '?')}: {doc.page_content[:80]}...")
    
    context = "\n\n".join([doc.page_content for doc in docs])
    answer = chain.invoke({"context": context, "question": question})
    print(f"A: {answer}\n")

ask_with_sources("How long is the online coding assessment?")

def ask_filtered(question, threshold=0.7):
    docs_with_scores = vectorstore.similarity_search_with_score(question, k=3)
    
    # Filter by score threshold
    filtered = [(doc, score) for doc, score in docs_with_scores if score < threshold]
    
    print(f"Q: {question}")
    print(f"Chunks after filtering (threshold={threshold}):")
    
    if not filtered:
        print("  No relevant chunks found!")
        print("A: I don't have that information.\n")
        return
    
    for doc, score in filtered:
        print(f"  score={score:.3f} | {doc.page_content[:80]}...")
    
    context = "\n\n".join([doc.page_content for doc, _ in filtered])
    answer = chain.invoke({"context": context, "question": question})
    print(f"A: {answer}\n")

ask_filtered("How long is the online coding assessment?")
ask_filtered("How many questions in Preferences @ Work?")
ask_filtered("What is the pass mark?")  # should find nothing

def ask_smart(question, k=4, relative_threshold=0.4):
    docs_with_scores = vectorstore.similarity_search_with_score(question, k=k)
    
    if not docs_with_scores:
        print(f"Q: {question}\nA: I don't have that information.\n")
        return
    
    # Best score as baseline
    best_score = docs_with_scores[0][1]
    
    # Keep chunks within relative_threshold of the best score
    filtered = [
        (doc, score) for doc, score in docs_with_scores
        if score - best_score < relative_threshold
    ]
    
    print(f"Q: {question}")
    print(f"Best score: {best_score:.3f} | Kept {len(filtered)}/{len(docs_with_scores)} chunks")
    for doc, score in filtered:
        print(f"  score={score:.3f} | {doc.page_content[:80]}...")
    
    context = "\n\n".join([doc.page_content for doc, _ in filtered])
    answer = chain.invoke({"context": context, "question": question})
    print(f"A: {answer}\n")

ask_smart("How long is the online coding assessment?")
ask_smart("How many questions in Preferences @ Work?")
ask_smart("What is the pass mark?")
ask_smart("Can I pause the coding assessment?")


