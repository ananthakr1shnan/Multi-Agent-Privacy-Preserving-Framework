# Multi-Agent Privacy-Preserving Framework (MPPF)

**A Production-Grade, Research-Level AI Framework with Local Privacy Guarantees**

[![Privacy](https://img.shields.io/badge/Privacy-First-green)](https://github.com)
[![Differential Privacy](https://img.shields.io/badge/DP-Enabled-blue)](https://github.com)
[![GDPR](https://img.shields.io/badge/GDPR-Compliant-orange)](https://github.com)

---

## 🎯 Overview

MPPF is a **multi-agent AI system** that provides intelligent assistance while maintaining **strict privacy guarantees**. It combines:
- **Local PII Redaction** (Microsoft Presidio)
- **Differential Privacy** (IBM DiffPrivLib)
- **Context-Aware Retrieval** (ChromaDB + Sentence Transformers)
- **Persistent Audit Logging** (SQLAlchemy)
- **Multi-Agent Reasoning** (Groq Llama 3 via LangChain)

---

## 🏗️ Architecture

```
User Query → Privacy Shield → Domain Expert → Retriever
                                   ↓              ↓
                            [Productivity, Ethics, Creativity Agents]
                                   ↓
                            Response Aggregator + DP Noise
                                   ↓
                            Final Response + Audit Log
```

### Core Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Privacy Shield** | Presidio + spaCy | Local PII redaction (names, emails, SSN, etc.) |
| **Domain Expert** | T5-LoRA (Fine-tuned) | Domain classification (Medical, Finance, Legal) |
| **Context Retriever** | ChromaDB + Sentence Transformers | RAG-based context augmentation |
| **Agent Pool** | Groq Llama 3 (3x Agents) | Productivity, Ethics, Creativity reasoning |
| **Aggregator** | Llama 3 + Weighted Synthesis | Combines agent outputs with DP noise |
| **Audit Logger** | SQLite + SQLAlchemy | Immutable interaction log |
| **Frontend** | FastAPI + Vanilla JS | Real-time dashboard with trace visualization |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Groq API Key ([Get here](https://console.groq.com))

### Installation

```bash
# 1. Clone repository
git clone <your-repo-url>
cd privacy_shield_mppf

# 2. Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download spaCy model
python -m spacy download en_core_web_sm

# 5. Configure environment
cp .env.example .env
# Add your GROQ_API_KEY to .env
```

### Knowledge Base Setup

```bash
# Place your documents in knowledge_base/
mkdir knowledge_base
# Add .pdf or .txt files to this directory

# Run ingestion
python -m app.core.ingest
```

### Run Application

```bash
uvicorn app.main:app --reload
```

Visit: `http://localhost:8000`

---

## 📖 Usage

### API Endpoint

**POST** `/api/query`

**Request:**
```json
{
  "query": "What are the best practices for data privacy?"
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "final_response": "Based on GDPR and MPPF guidelines...",
    "retrieved_context": ["...", "..."],
    "audit_id": 42,
    "agent_contributions": {
      "productivity_agent": 0.35,
      "ethics_agent": 0.40,
      "creativity_agent": 0.25
    },
    "privacy_analysis": {
      "redaction_count": 2,
      "aggressive_mode_triggered": false
    },
    "dp_metrics": {
      "privacy_guarantee": "ε=1.0",
      "budget_used": 0.05
    }
  }
}
```

---

## 🔐 Privacy Guarantees

### 1. Local PII Redaction
All sensitive data is redacted **before** cloud API calls:
- Names → `<PERSON>`
- Emails → `<EMAIL>`
- Phone Numbers → `<PHONE_NUMBER>`
- Credit Cards → `<CREDIT_CARD>`

### 2. Differential Privacy
Statistical noise is added to the final response using Laplacian mechanism:
- **ε (epsilon) budget**: 1.0 by default
- **Noise scale**: Dynamically adjusted
- **Guarantee**: (ε, δ)-differential privacy

### 3. Audit Trail
Every interaction is logged in `audit.db` with:
- Anonymized query
- Retrieved context
- Agent responses
- Privacy metadata
- Timestamps

---

## 🧪 Testing

### Run Production Tests
```bash
python test_production.py
```

### Run Individual Component Tests
```bash
# Privacy Shield
python test_privacy_pin.py

# Domain Expert
python test_domain_direct.py

# Differential Privacy
python test_differential_privacy.py

# Agent Weights
python test_aggregator_weights.py
```

---

## 📊 Knowledge Base Management

### Adding Documents
```bash
# 1. Add PDFs/TXT to knowledge_base/
cp my_document.pdf knowledge_base/

# 2. Re-run ingestion
python -m app.core.ingest
```

### Viewing Vector Database
```python
import chromadb
client = chromadb.PersistentClient(path="chroma_db")
collection = client.get_collection("mppf_knowledge")
print(f"Total documents: {collection.count()}")
```

---

## 🎓 Research Features

### Domain-Specific Privacy Adaptation
- **High-Sensitivity Domains** (Finance, Medical, Legal):
  - Triggers aggressive PII redaction
  - Boosts Ethics Agent weight to 50%
  - Applies stricter DP noise

### Weighted Multi-Agent Synthesis
Agent weights are calculated based on:
- Domain alignment (e.g., Ethics → Medical)
- Confidence scores
- Response quality

### Explainability
- Every decision is logged
- UI shows real-time trace events
- Audit logs enable post-hoc analysis

---

## 📁 Project Structure

```
privacy_shield_mppf/
├── app/
│   ├── core/
│   │   ├── database.py          # Audit Log (SQLAlchemy)
│   │   └── ingest.py            # Document Ingestion Pipeline
│   ├── privacy/
│   │   ├── privacy_node.py      # PII Redaction (Presidio)
│   │   └── differential_privacy.py  # DP Noise
│   ├── workflow/
│   │   ├── engine.py            # Orchestration Logic
│   │   ├── retriever_node.py    # ChromaDB Integration
│   │   ├── domain_expert_node.py # T5 Domain Classifier
│   │   ├── agent_nodes.py       # 3 Specialized Agents
│   │   └── aggregator.py        # Response Synthesis
│   ├── schemas/
│   │   └── models.py            # Pydantic Models
│   └── main.py                  # FastAPI Application
├── knowledge_base/              # Your Documents
├── chroma_db/                   # Vector Database
├── audit.db                     # Audit Logs
├── static/                      # Frontend Assets
├── templates/                   # HTML Templates
└── requirements.txt
```

---

## 🚢 Deployment

### Environment Variables
```env
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama3-70b-8192
EPSILON_BUDGET=1.0
```

### Docker (Optional)
```bash
docker build -t mppf .
docker run -p 8000:8000 -v ./knowledge_base:/app/knowledge_base mppf
```

### Cloud Deployment
See `DEPLOYMENT.md` for detailed instructions for:
- Render
- AWS
- Azure

---

## 📄 License

MIT License - See `LICENSE` file

---

## 🤝 Contributing

This is a research project. Contributions welcome!

---

## 📚 References

1. [Differential Privacy](https://en.wikipedia.org/wiki/Differential_privacy)
2. [Microsoft Presidio](https://microsoft.github.io/presidio/)
3. [ChromaDB](https://www.trychroma.com/)
4. [GDPR Compliance](https://gdpr.eu/)

---

**Built with ❤️ for Privacy-Preserving AI Research**
