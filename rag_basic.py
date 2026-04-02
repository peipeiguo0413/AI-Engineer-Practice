from langchain.text_splitter import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import shutil

# Sample company policy document
document = """
# Company Leave Policy

## Annual Leave
Employees are entitled to annual leave after completing one year of service.
Employees with 1-5 years of service receive 10 days of annual leave per year.
Employees with 5-10 years of service receive 15 days of annual leave per year.
Employees with over 10 years of service receive 20 days of annual leave per year.
Annual leave must be requested 3 days in advance and approved by the direct supervisor.

## Sick Leave
Employees may apply for sick leave when ill.
A medical certificate is required for sick leave.
Sick leave exceeding 3 consecutive days requires a certificate from a certified hospital.
Salary during sick leave is paid at 80% of normal rate.
The annual sick leave limit is 30 days.

## Personal Leave
Personal leave must be requested 1 day in advance and approved by the direct supervisor.
No salary is paid during personal leave.
The annual personal leave limit is 10 days.

## Application Process
1. Log in to the HR system and submit a leave application
2. Submit to direct supervisor for approval
3. HR is automatically notified after supervisor approval
4. Confirm return from leave in the system after the leave period ends

## Important Notes
Leaving work without approval is considered absence without leave.
One day of absence results in deduction of 3 days salary.
Consecutive absence of 3 or more days will trigger termination procedures.
"""

shutil.rmtree("./chroma_db", ignore_errors=True)
# Text splitter
# splitter = RecursiveCharacterTextSplitter(
#     chunk_size=300,
#     chunk_overlap=100,
#     separators=["\n\n", "\n", ". ", ", ", ""],
# )

# chunks = splitter.split_text(document)

header_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[("#", "title"), ("##", "section")]
)
md_chunks = header_splitter.split_text(document)
chunks = [f"{doc.metadata}\n{doc.page_content}" for doc in md_chunks]

# print(f"Original length: {len(document)} characters")
# print(f"Split into {len(chunks)} chunks\n")

# for i, chunk in enumerate(chunks):
#     print(f"--- Chunk {i+1} ({len(chunk)} chars) ---")
#     print(chunk)
#     print()

# Initialize embedding model (runs locally, no API key needed)
embeddings = SentenceTransformerEmbeddings(
    model_name="all-MiniLM-L6-v2"
)

# Store chunks in Chroma
vectorstore = Chroma.from_texts(
    texts=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db",  # save to local disk
)

# print(f"Stored {len(chunks)} chunks in Chroma\n")

# Test retrieval
query = "How many days of annual leave do I get?"
results = vectorstore.similarity_search(query, k=3)  # top 3 most relevant chunks

# print(f"Query: {query}\n")
# print("Top 3 relevant chunks:")
# for i, doc in enumerate(results):
#     print(f"\n--- Result {i+1} ---")
#     print(doc.page_content)

# Add to the end of rag_basic.py
test_cases = [
    {
        "query": "How many days of annual leave for someone with 3 years of service?",
        "expected_keyword": "1-5 years"
    },
    {
        "query": "What happens if I skip work without approval?",
        "expected_keyword": "absence without leave"
    },
    {
        "query": "How do I apply for leave?",
        "expected_keyword": "HR system"
    },
    {
        "query": "What is the salary during sick leave?",
        "expected_keyword": "80%"
    },
    {
        "query": "How many days in advance for personal leave?",
        "expected_keyword": "1 day in advance"
    },
]

def evaluate_chunking(vectorstore, test_cases):
    correct = 0
    for case in test_cases:
        results = vectorstore.similarity_search(case["query"], k=2)
        retrieved_text = " ".join([r.page_content for r in results])
        
        hit = case["expected_keyword"].lower() in retrieved_text.lower()
        correct += hit
        status = "PASS" if hit else "FAIL"
        print(f"{status}: {case['query'][:55]}")
        if not hit:
            print(f"       Expected: '{case['expected_keyword']}'")
            print(f"       Got: {retrieved_text[:120]}")
    
    print(f"\nRetrieval accuracy: {correct}/{len(test_cases)} = {correct/len(test_cases):.0%}")

evaluate_chunking(vectorstore, test_cases)

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
    # Step 1: retrieve relevant chunks
    docs = vectorstore.similarity_search(question, k=3)
    context = "\n\n".join([doc.page_content for doc in docs])
    
    # Step 2: generate answer
    answer = chain.invoke({
        "context": context,
        "question": question,
    })
    
    print(f"Q: {question}")
    print(f"A: {answer}\n")

# Test
ask("How many days of annual leave do I get after 3 years?")
ask("What is the process to apply for leave?")
ask("Can I get paid during personal leave?")
ask("What is the weather like today?")  # should say "I don't have that information"