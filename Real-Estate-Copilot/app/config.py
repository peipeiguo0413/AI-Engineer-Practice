# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CHROMA_DB_PATH = "./data/chroma_db"
UPLOAD_DIR = "./data/uploads"
OUTPUT_DIR = "./outputs"

# LLM models
MODEL_FAST = "claude-haiku-4-5"       # default — fast and cheap
MODEL_SMART = "claude-opus-4-6"       # complex analysis

# RAG settings
CHUNK_SIZE = 300
CHUNK_OVERLAP = 50
TOP_K_RESULTS = 3