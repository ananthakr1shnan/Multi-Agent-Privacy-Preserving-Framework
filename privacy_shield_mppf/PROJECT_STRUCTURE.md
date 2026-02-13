# MPPF Project Structure

## 📁 Directory Overview

```
privacy_shield_mppf/
├── 📂 app/                          # Main application code
│   ├── core/                        # Core services
│   │   ├── config.py               # Configuration management
│   │   ├── database.py             # Audit log (SQLAlchemy)
│   │   └── ingest.py               # Document ingestion pipeline
│   ├── privacy/                     # Privacy components
│   │   ├── privacy_node.py         # PII redaction (Presidio)
│   │   └── differential_privacy.py # DP noise mechanisms
│   ├── workflow/                    # Workflow orchestration
│   │   ├── engine.py               # Main workflow engine
│   │   ├── retriever_node.py       # ChromaDB integration
│   │   ├── domain_expert_node.py   # Domain classifier (T5)
│   │   ├── agent_nodes.py          # 3 specialized agents
│   │   └── aggregator.py           # Response synthesis
│   ├── schemas/                     # Pydantic models
│   │   └── models.py               # Request/response schemas
│   └── main.py                      # FastAPI application
│
├── 📂 templates/                    # HTML templates
│   ├── index.html                  # Main dashboard
│   ├── knowledge_base.html         # Document manager
│   └── audit_logs.html             # Audit log viewer
│
├── 📂 static/                       # Frontend assets
│   ├── css/
│   │   ├── dashboard.css           # Main styles
│   │   └── terminal.css            # Terminal theme
│   └── js/
│       ├── dashboard.js            # Main UI logic
│       ├── monitor.js              # Real-time monitoring
│       ├── upload.js               # File upload handler
│       ├── kb_manager.js           # KB management
│       └── audit_logs.js           # Log viewer
│
├── 📂 knowledge_base/               # Your documents (PDF/TXT)
│   └── mppf_guide.txt              # Sample document
│
├── 📂 chroma_db/                    # ChromaDB vector database
│   └── [auto-generated]            # Embeddings & metadata
│
├── 📂 best model/                   # Fine-tuned T5 model
│   └── [model files]               # Domain classifier weights
│
├── 📄 audit.db                      # SQLite audit logs
│
├── 📄 mppf_sdk.py                   # Python SDK for developers
├── 📄 example_sdk_usage.py          # SDK usage demo
├── 📄 test_production.py            # Production verification test
│
├── 📄 Dockerfile                    # Container image
├── 📄 docker-compose.yml            # Orchestration config
│
├── 📄 requirements.txt              # Python dependencies
├── 📄 .env                          # Environment variables
│
├── 📄 README.md                     # Project overview
├── 📄 QUICK_START.md                # Quick start guide
├── 📄 PRODUCTION_README.md          # Production deployment
├── 📄 DISTRIBUTION_GUIDE.md         # How to ship as product
├── 📄 HOW_TO_UPDATE_KNOWLEDGE_BASE.md  # Upload guide
└── 📄 DEPLOYMENT.md                 # Cloud deployment

Total: ~40 essential files
```

---

## 🎯 Key Files Explained

### Core Application
| File | Purpose | Priority |
|------|---------|----------|
| `app/main.py` | FastAPI server + API routes | ⭐⭐⭐ |
| `app/workflow/engine.py` | Orchestrates entire workflow | ⭐⭐⭐ |
| `app/privacy/privacy_node.py` | PII redaction (Presidio) | ⭐⭐⭐ |
| `app/workflow/aggregator.py` | Response synthesis (LLM) | ⭐⭐⭐ |

### Knowledge Management
| File | Purpose | Priority |
|------|---------|----------|
| `app/core/ingest.py` | Document processing pipeline | ⭐⭐⭐ |
| `app/workflow/retriever_node.py` | ChromaDB vector search | ⭐⭐⭐ |
| `knowledge_base/` | Your uploaded documents | ⭐⭐⭐ |
| `chroma_db/` | Vector database storage | ⭐⭐⭐ |

### Privacy & Compliance
| File | Purpose | Priority |
|------|---------|----------|
| `app/privacy/differential_privacy.py` | DP noise mechanisms | ⭐⭐ |
| `app/core/database.py` | Audit logging | ⭐⭐⭐ |
| `audit.db` | SQLite audit database | ⭐⭐⭐ |

### Frontend
| File | Purpose | Priority |
|------|---------|----------|
| `templates/index.html` | Main dashboard UI | ⭐⭐⭐ |
| `static/js/dashboard.js` | Core UI logic | ⭐⭐⭐ |
| `static/js/upload.js` | File upload handler | ⭐⭐ |

### Deployment
| File | Purpose | Priority |
|------|---------|----------|
| `Dockerfile` | Container image definition | ⭐⭐⭐ |
| `docker-compose.yml` | Easy deployment | ⭐⭐⭐ |
| `requirements.txt` | Python dependencies | ⭐⭐⭐ |

### SDK & Examples
| File | Purpose | Priority |
|------|---------|----------|
| `mppf_sdk.py` | Python client library | ⭐⭐ |
| `example_sdk_usage.py` | SDK demo script | ⭐⭐ |
| `test_production.py` | Verification test | ⭐⭐ |

---

## 🚀 Quick Commands

### Run Server
```bash
uvicorn app.main:app --reload
```

### Test System
```bash
python test_production.py
```

### Test SDK
```bash
python example_sdk_usage.py
```

### Ingest Documents
```bash
python -m app.core.ingest
```

### Docker Deployment
```bash
docker-compose up
```

---

## 📦 What's Inside Each Directory

### `app/` - Application Logic
- **Core**: Database, config, ingestion
- **Privacy**: PII detection, DP noise
- **Workflow**: Orchestration, agents, retrieval
- **Schemas**: Pydantic models

### `templates/` - Web UI
- Main dashboard
- Knowledge base manager
- Audit log viewer

### `static/` - Frontend Assets
- CSS styles
- JavaScript modules
- UI components

### `knowledge_base/` - Your Data
- Upload PDFs here
- Or use web upload
- Auto-ingested to ChromaDB

### `chroma_db/` - Vector Database
- Embeddings
- Metadata
- Auto-managed

---

## 🗑️ Removed Files (Cleanup)

The following test files were removed to keep the project clean:
- ❌ `test_api.py`
- ❌ `test_aggregator_weights.py`
- ❌ `test_api_simple.py`
- ❌ `test_privacy_pin.py`
- ❌ `test_domain_direct.py`
- ❌ `test_adaptive_privacy.py`
- ❌ `test_differential_privacy.py`
- ❌ `quick_test.py`
- ❌ `verify_workflow.py`
- ❌ `check_response.py`
- ❌ `demo_sdk.py`
- ❌ `test_output.txt`
- ❌ `test_results.txt`

**Kept**: `test_production.py` (comprehensive E2E test)

---

## 📊 File Count Summary

| Category | Count |
|----------|-------|
| **Python Files** | 20+ |
| **HTML Templates** | 3 |
| **JavaScript Modules** | 5 |
| **CSS Files** | 2 |
| **Documentation** | 6 |
| **Config Files** | 4 |
| **Total Essential Files** | ~40 |

---

## 🎯 What You Need to Touch

### As a User
- **Upload docs**: Use web UI or add to `knowledge_base/`
- **Query**: Visit `http://localhost:8000`
- **Config**: Edit `.env` for API keys

### As a Developer
- **Add features**: Modify files in `app/`
- **Change UI**: Edit `templates/` and `static/`
- **Add tests**: Add to `test_production.py`

### As Ops
- **Deploy**: Use `Dockerfile` or `docker-compose.yml`
- **Monitor**: Check `audit.db`
- **Scale**: See `DEPLOYMENT.md`

---

**Clean, organized, and production-ready!** ✨
