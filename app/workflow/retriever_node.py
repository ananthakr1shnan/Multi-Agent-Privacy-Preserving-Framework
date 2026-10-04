"""
Retriever Node - Production Vector Search (ChromaDB).
Uses ChromaDB for persistent, scalable context retrieval.
"""
import chromadb
from chromadb.utils import embedding_functions
import time
from typing import List

# Configuration
CHROMA_DB_DIR = "chroma_db"
COLLECTION_NAME = "mppf_knowledge"

class ContextRetriever:
    """
    Production retriever using ChromaDB.
    """
    
    def __init__(self):
        """
        Initialize the ChromaDB client.
        """
        print(f"📚 Loading Production Retriever (ChromaDB)...")
        try:
            self.client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
            
            # Use sentence-transformers embedding function
            # Must match the one used in ingest.py
            self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
            
            # Get collection
            self.collection = self.client.get_collection(
                name=COLLECTION_NAME,
                embedding_function=self.ef
            )
            
            count = self.collection.count()
            print(f"✅ Retriever loaded with {count} documents in '{COLLECTION_NAME}'.")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not connect to ChromaDB: {e}")
            print("   Did you run 'python -m app.core.ingest'?")
            self.collection = None

    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        """
        Retrieve relevant context for a query.
        
        Args:
            query: The user's query
            top_k: Number of documents to retrieve
            
        Returns:
            List of relevant document strings
        """
        if not self.collection:
            return []
            
        start_time = time.time()
        
        try:
            # Query the collection
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            # Extract documents
            # results['documents'] is a list of lists (one list per query)
            documents = results['documents'][0] if results['documents'] else []
            
            print(f"🔍 Retrieved {len(documents)} docs in {(time.time() - start_time)*1000:.1f}ms")
            return documents
            
        except Exception as e:
            print(f"❌ Error retrieving context: {e}")
            return []

# Global retriever instance
try:
    retriever = ContextRetriever()
except Exception:
    print("Retriever initialization deferred or failed.")
    retriever = None
