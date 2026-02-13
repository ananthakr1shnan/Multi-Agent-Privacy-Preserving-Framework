# MPPF - Quick Start Guide

## 🚀 For End Users (No Coding Required)

### Option 1: Docker (Recommended)

```bash
# 1. Install Docker Desktop
# Download from: https://www.docker.com/products/docker-desktop

# 2. Clone MPPF
git clone https://github.com/your-org/mppf.git
cd mppf

# 3. Set your API key
echo "GROQ_API_KEY=your_key_here" > .env

# 4. Run
docker-compose up

# 5. Open browser
# Visit: http://localhost:8000
```

**That's it!** Upload PDFs, ask questions, view audit logs.

---

## 💻 For Developers (Python Integration)

### Installation
```bash
pip install requests  # Only dependency needed
```

### Basic Usage
```python
from mppf_sdk import MPPFClient

# Connect to MPPF server
client = MPPFClient("http://localhost:8000")

# Query
result = client.query("What are GDPR requirements?")
print(result.final_response)
```

### Advanced Usage
```python
# Upload documents
client.upload_document("./compliance_guide.pdf")

# Get stats
stats = client.get_knowledge_base_stats()
print(f"Knowledge base has {stats['total_chunks']} chunks")

# View audit logs
logs = client.get_audit_logs(page=1, limit=10)
for log in logs['logs']:
    print(f"{log['timestamp']}: {log['query']}")
```

---

## 🏢 For Organizations (Self-Hosted)

### Prerequisites
- Python 3.9+
- 4GB RAM minimum
- Groq API key ([Get free key](https://console.groq.com))

### Setup
```bash
# 1. Clone repository
git clone https://github.com/your-org/mppf.git
cd mppf

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# 4. Configure
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# 5. Run
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Access
- **Web UI**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 📚 Documentation

### Key Features
- ✅ **Privacy-First**: Local PII redaction (no sensitive data sent to cloud)
- ✅ **Multi-Agent**: 3 specialized AI agents (Productivity, Ethics, Creativity)
- ✅ **RAG System**: ChromaDB vector database for knowledge augmentation
- ✅ **Audit Logs**: Complete query history for compliance
- ✅ **Differential Privacy**: Statistical noise for privacy guarantees

### API Endpoints
- `POST /api/query` - Submit privacy-preserving query
- `POST /api/upload` - Upload PDF/TXT to knowledge base
- `GET /api/knowledge-base` - List documents
- `GET /api/audit-logs` - View query history

Full API docs: http://localhost:8000/docs

---

## 🔐 Security

### Privacy Guarantees
- **Local PII Detection**: Presidio analyzes text locally
- **Cloud Isolation**: Only anonymized text sent to LLM
- **Audit Trail**: Immutable log of all interactions
- **DP Guarantees**: (ε, δ)-differential privacy

### Data Storage
- **Vector DB**: `chroma_db/` directory (persistent)
- **Audit Logs**: `audit.db` SQLite database
- **Knowledge Base**: `knowledge_base/` directory (your documents)

All data stored locally on your infrastructure.

---

## 🎓 Example Use Cases

### Healthcare
```python
# Query with patient data - PII automatically redacted
result = client.query(
    "Patient John Doe (DOB: 01/15/1980) needs medication review"
)
# System redacts name and DOB before processing
```

### Legal
```python
# Upload contracts
client.upload_document("./contract_template.pdf")

# Query with context from documents
result = client.query("What are the indemnification clauses?")
# Retrieves relevant sections from uploaded contracts
```

### Finance
```python
# Query compliance requirements
result = client.query(
    "How should we handle customer credit card data?"
)

# Audit trail for regulatory compliance
audit_id = result.audit_id  # Store for compliance reports
```

---

## 🛠️ Troubleshooting

### Server won't start
```bash
# Check Python version
python --version  # Should be 3.9+

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check logs
tail -f mppf.log
```

### Upload fails
- Check file size (max 10MB)
- Ensure file is PDF or TXT
- Verify disk space in `knowledge_base/`

### Queries slow
- First query loads models (may take 30s)
- Subsequent queries should be ~8-10s
- Check internet connection (for Groq API)

---

## 📞 Support

- **Issues**: https://github.com/your-org/mppf/issues
- **Discussions**: https://github.com/your-org/mppf/discussions
- **Email**: support@your-org.com

---

## 📄 License

MIT License - Free to use, modify, and distribute.

See [LICENSE](LICENSE) file for details.

---

**Built with ❤️ for Privacy-Preserving AI**
