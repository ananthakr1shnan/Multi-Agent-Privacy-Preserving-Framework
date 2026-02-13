"""
Document Ingestion Pipeline for MPPF.
Loads PDFs and Text files, chunks them, and stores embeddings in ChromaDB.
"""
import os
import glob
from typing import List
import chromadb
from chromadb.utils import embedding_functions
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import shutil

# Configuration
KNOWLEDGE_BASE_DIR = "knowledge_base"
CHROMA_DB_DIR = "chroma_db"
COLLECTION_NAME = "mppf_knowledge"

def ensure_directories():
    """Create necessary directories if they don't exist."""
    if not os.path.exists(KNOWLEDGE_BASE_DIR):
        os.makedirs(KNOWLEDGE_BASE_DIR)
        print(f"📁 Created directory: {KNOWLEDGE_BASE_DIR}")
        print(f"👉 Please place your .pdf or .txt files in '{KNOWLEDGE_BASE_DIR}'")

def load_documents() -> List:
    """Load all PDF and TXT files from the knowledge base directory."""
    documents = []
    
    # Load PDFs
    pdf_files = glob.glob(os.path.join(KNOWLEDGE_BASE_DIR, "*.pdf"))
    for pdf_path in pdf_files:
        try:
            print(f"📄 Loading PDF: {pdf_path}")
            loader = PyPDFLoader(pdf_path)
            documents.extend(loader.load())
        except Exception as e:
            print(f"❌ Error loading {pdf_path}: {e}")

    # Load Text files
    txt_files = glob.glob(os.path.join(KNOWLEDGE_BASE_DIR, "*.txt"))
    for txt_path in txt_files:
        try:
            print(f"📄 Loading Text: {txt_path}")
            loader = TextLoader(txt_path, encoding='utf-8')
            documents.extend(loader.load())
        except Exception as e:
            print(f"❌ Error loading {txt_path}: {e}")
            
    return documents

def ingest_documents():
    """Main ingestion function."""
    ensure_directories()
    
    print("🚀 Starting Document Ingestion...")
    
    # 1. Load Documents
    raw_docs = load_documents()
    if not raw_docs:
        print("⚠️ No documents found. Please add files to 'knowledge_base/' and run again.")
        return

    print(f"✅ Loaded {len(raw_docs)} document pages/files.")

    # 2. Split Text (Chunking)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.split_documents(raw_docs)
    print(f"✂️ Split into {len(chunks)} semantic chunks.")

    # 3. Store in ChromaDB
    print(f"💾 Storing in ChromaDB ({CHROMA_DB_DIR})...")
    
    # Initialize Client
    client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    
    # Use sentence-transformers embedding function
    # This matches the model we used in the lightweight version for consistency
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    
    # Get or Create Collection
    # meaningful_name helps with debugging
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef
    )
    
    # Prepare data for insertion
    ids = [f"doc_{i}" for i in range(len(chunks))]
    documents = [chunk.page_content for chunk in chunks]
    metadatas = [chunk.metadata for chunk in chunks]
    
    # Upsert (Insert or Update)
    # Using batches of 100 to be safe
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch_end = min(i + batch_size, len(chunks))
        print(f"   Writing batch {i} to {batch_end}...")
        collection.upsert(
            ids=ids[i:batch_end],
            documents=documents[i:batch_end],
            metadatas=metadatas[i:batch_end]
        )
        
    print(f"🎉 Ingestion Complete! {len(chunks)} chunks stored in '{COLLECTION_NAME}'.")

if __name__ == "__main__":
    ingest_documents()
