# How to Update the Knowledge Base

## Quick Guide

### 1️⃣ Add Your Documents
Place PDF or TXT files in the `knowledge_base/` folder:

```bash
d:\multi\privacy_shield_mppf\knowledge_base\
```

**Supported formats:**
- `.pdf` - Research papers, reports, documentation
- `.txt` - Text files, notes, policies

### 2️⃣ Run Ingestion
Open a new terminal and run:

```bash
cd d:\multi\privacy_shield_mppf
.\venv\Scripts\python.exe -m app.core.ingest
```

**What it does:**
- Scans the `knowledge_base/` folder
- Loads all PDFs and TXT files
- Splits text into 500-character chunks (with 50-char overlap)
- Generates embeddings using `sentence-transformers`
- Stores everything in ChromaDB (`chroma_db/` directory)

### 3️⃣ Verify
The ingestion script will show:
```
📄 Loading PDF: knowledge_base\your_file.pdf
✅ Loaded X document pages/files.
✂️ Split into Y semantic chunks.
🎉 Ingestion Complete! Y chunks stored in 'mppf_knowledge'.
```

### 4️⃣ (Optional) Restart Server
If using `--reload` flag, the retriever will automatically detect new documents.

Otherwise, restart:
```bash
Ctrl+C  # Stop server
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

---

## Example Workflow

```bash
# 1. Add a new PDF
copy "C:\Downloads\research_paper.pdf" knowledge_base\

# 2. Run ingestion
.\venv\Scripts\python.exe -m app.core.ingest

# 3. Test it
# Go to http://localhost:8000
# Ask: "What does the research paper say about X?"
```

---

## Current Status

Check what's in your database:

```python
import chromadb
client = chromadb.PersistentClient(path="chroma_db")
collection = client.get_collection("mppf_knowledge")
print(f"Total chunks: {collection.count()}")
```

Currently: **4 chunks** from `mppf_guide.txt`

---

## Tips

✅ **Add multiple files**: Just drop them all in `knowledge_base/` and run ingestion once  
✅ **Update existing**: Re-run ingestion to update (uses upsert)  
✅ **Large PDFs**: Will be automatically chunked for better retrieval  
✅ **Privacy**: All processing is local - no cloud upload

---

**Need help?** Check `app/core/ingest.py` for the ingestion logic.
