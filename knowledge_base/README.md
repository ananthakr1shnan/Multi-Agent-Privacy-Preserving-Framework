# Knowledge Base Directory

This directory is where you place your custom documents for the RAG (Retrieval-Augmented Generation) system.

## How to Use

1. **Add Your Documents**: Place `.pdf` or `.txt` files in this directory
2. **Run Ingestion**: Execute the following command to index your documents:
   ```bash
   python -m app.core.ingest
   ```
3. **Start the Server**: The retriever will now use your custom knowledge base

## Supported Formats
- PDF files (`.pdf`)
- Text files (`.txt`)

## Example
```bash
knowledge_base/
├── company_policies.pdf
├── product_documentation.txt
└── gdpr_guidelines.pdf
```

After adding files, run:
```bash
python -m app.core.ingest
```

The system will chunk your documents and store vector embeddings in `chroma_db/`.
