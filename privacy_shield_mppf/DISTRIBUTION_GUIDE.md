# MPPF Product Distribution Guide

## How to Ship & Use MPPF as a Framework

MPPF can be distributed and used in **3 primary ways**:

---

## 1️⃣ **As a Hosted Service** (SaaS)

Deploy MPPF on a server and provide API access to users.

### Deployment Options

#### Option A: Docker Deployment (Recommended)
```bash
# Users download and run:
docker pull your-registry/mppf:latest
docker run -p 8000:8000 \
  -v ./knowledge_base:/app/knowledge_base \
  -v ./chroma_db:/app/chroma_db \
  -e GROQ_API_KEY=your_key \
  mppf:latest
```

#### Option B: Cloud Hosting
- **Render**: Deploy via `render.yaml` (already included)
- **AWS**: EC2 + ECS
- **Azure**: App Service
- **Google Cloud**: Cloud Run

### User Access
Users access via:
- **Web UI**: `https://your-domain.com`
- **REST API**: `https://your-domain.com/api/query`

---

## 2️⃣ **As a Python SDK** (Library)

Users install MPPF as a package and integrate it into their own applications.

### Installation
```bash
pip install mppf-framework  # (After publishing to PyPI)
```

### Usage Example
```python
from mppf import PrivacyPreservingAgent

# Initialize
agent = PrivacyPreservingAgent(
    groq_api_key="your_key",
    knowledge_base_path="./my_docs"
)

# Query
result = agent.query("What is GDPR compliance?")

print(result.final_response)
print(f"Privacy: {result.privacy_analysis.redaction_count} redactions")
print(f"Audit ID: {result.audit_id}")
```

---

## 3️⃣ **As a Self-Hosted Application** (On-Premise)

Organizations download and run MPPF on their own infrastructure.

### For Enterprise Users
```bash
# Clone repository
git clone https://github.com/your-org/mppf.git
cd mppf

# Install
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Configure
cp .env.example .env
# Edit .env with API keys

# Run
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 📦 Package Distribution Strategies

### Strategy 1: PyPI Package (Python Developers)

**What to ship**:
- Core library (`mppf/` package)
- CLI tool
- Documentation

**Structure**:
```
mppf/
├── setup.py
├── pyproject.toml
├── README.md
├── mppf/
│   ├── __init__.py
│   ├── agent.py          # Main SDK
│   ├── privacy/
│   ├── workflow/
│   └── core/
└── examples/
    ├── basic_usage.py
    └── advanced_integration.py
```

**Publishing**:
```bash
python setup.py sdist bdist_wheel
twine upload dist/*
```

---

### Strategy 2: Docker Image (Ops Teams)

**What to ship**:
- Complete application
- Web UI + API
- Pre-configured environment

**Dockerfile** (already created below):
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python -m spacy download en_core_web_sm

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### Strategy 3: GitHub Release (Open Source)

**What to ship**:
- Source code
- Documentation
- Setup scripts
- Example configurations

**Users download**:
```bash
wget https://github.com/your-org/mppf/releases/latest/download/mppf.zip
unzip mppf.zip
cd mppf
./setup.sh  # Automated setup script
```

---

## 🔧 SDK Design (For Python Developers)

Create a simple wrapper SDK that abstracts the complexity.

### `mppf/sdk/__init__.py`
```python
from .client import MPPFClient
from .models import QueryResponse, PrivacyMetrics

__all__ = ["MPPFClient", "QueryResponse", "PrivacyMetrics"]
```

### `mppf/sdk/client.py`
```python
import requests
from typing import Optional
from .models import QueryResponse

class MPPFClient:
    """High-level client for MPPF API."""
    
    def __init__(
        self, 
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None
    ):
        self.base_url = base_url
        self.api_key = api_key
    
    def query(self, text: str) -> QueryResponse:
        """Submit a privacy-preserving query."""
        response = requests.post(
            f"{self.base_url}/api/query",
            json={"query": text},
            headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        )
        response.raise_for_status()
        return QueryResponse(**response.json()["result"])
    
    def upload_document(self, file_path: str) -> dict:
        """Upload a document to the knowledge base."""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{self.base_url}/api/upload", files=files)
            response.raise_for_status()
            return response.json()
    
    def get_audit_logs(self, page: int = 1, limit: int = 20) -> dict:
        """Retrieve audit logs."""
        response = requests.get(
            f"{self.base_url}/api/audit-logs",
            params={"page": page, "limit": limit}
        )
        response.raise_for_status()
        return response.json()
```

---

## 📚 User-Facing Documentation Structure

### For Developers
```
docs/
├── getting-started.md        # Quick start guide
├── api-reference.md          # REST API docs
├── sdk-guide.md              # Python SDK usage
├── examples/
│   ├── basic-query.py
│   ├── document-upload.py
│   └── custom-workflow.py
└── deployment/
    ├── docker.md
    ├── kubernetes.md
    └── cloud-providers.md
```

### For End Users
```
user-guide/
├── introduction.md
├── uploading-documents.md
├── querying-system.md
├── understanding-privacy.md
└── audit-logs.md
```

---

## 🌐 Multi-Tenant Deployment (Enterprise)

For SaaS offerings with multiple organizations:

### Database Schema Updates
```python
# Add organization/tenant support
class Organization(Base):
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    api_key = Column(String, unique=True)

class AuditLogTrace(Base):
    # Existing fields...
    organization_id = Column(Integer, ForeignKey("organizations.id"))
```

### API Key Authentication
```python
from fastapi import Header, HTTPException

async def verify_api_key(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing API key")
    
    api_key = authorization.replace("Bearer ", "")
    # Validate API key against database
    org = get_organization_by_api_key(api_key)
    if not org:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return org

@app.post("/api/query")
async def process_query(
    query_request: QueryRequest,
    organization: Organization = Depends(verify_api_key)
):
    # Process with organization context
    pass
```

---

## 📦 Distribution Checklist

### Before Shipping
- [ ] **Documentation** - Complete API docs, SDK guide, examples
- [ ] **Tests** - Unit tests, integration tests, E2E tests
- [ ] **Security** - API authentication, rate limiting, input validation
- [ ] **Monitoring** - Logging, metrics, error tracking
- [ ] **Licensing** - Choose license (MIT, Apache 2.0, etc.)
- [ ] **CI/CD** - Automated builds, testing, deployment
- [ ] **Docker Image** - Build and publish to Docker Hub
- [ ] **PyPI Package** - If offering SDK
- [ ] **Demo Site** - Public demo for potential users

### For Open Source
- [ ] **README.md** - Clear installation and usage instructions
- [ ] **CONTRIBUTING.md** - Contribution guidelines
- [ ] **LICENSE** - License file
- [ ] **CHANGELOG.md** - Version history
- [ ] **Issue Templates** - Bug report, feature request
- [ ] **GitHub Actions** - CI/CD workflows

---

## 🚀 Example Use Cases

### Use Case 1: Healthcare Organization
```python
# Healthcare provider integrates MPPF for patient data queries
from mppf import MPPFClient

client = MPPFClient("https://mppf.hospital.com")

# Query with sensitive patient data
result = client.query(
    "Patient John Doe (SSN: 123-45-6789) needs medication review"
)

# PII automatically redacted before cloud processing
# Result contains anonymized response
```

### Use Case 2: Financial Institution
```python
# Bank uses MPPF for compliance-safe AI queries
client = MPPFClient()

# Upload compliance documents
client.upload_document("./policies/gdpr_policy.pdf")
client.upload_document("./regulations/sox_compliance.pdf")

# Query with context from uploaded docs
result = client.query("What are our data retention requirements?")

# Audit log automatically created for compliance
audit_id = result.audit_id
```

### Use Case 3: Research Institution
```bash
# Self-hosted for sensitive research data
docker run -d \
  -p 8000:8000 \
  -v ./research_papers:/app/knowledge_base \
  -v ./chroma_db:/app/chroma_db \
  --name mppf-research \
  mppf:latest

# Access via local network only
# No external API calls for maximum privacy
```

---

## 💡 Monetization Options (If Commercial)

1. **Freemium Model**
   - Free: Community edition (limited queries/month)
   - Paid: Enterprise (unlimited, support, SLA)

2. **Per-Query Pricing**
   - $0.01 per query
   - Volume discounts

3. **Subscription Tiers**
   - Starter: $49/mo (1000 queries)
   - Professional: $199/mo (10,000 queries)
   - Enterprise: Custom pricing

4. **Self-Hosted License**
   - One-time fee for source code
   - Annual support contract

---

## 📄 Sample Licensing Options

### Open Source (MIT License)
- Free to use, modify, distribute
- No warranty
- Best for community adoption

### Dual License
- Open source for individuals/non-commercial
- Commercial license for enterprises
- Example: MySQL, Qt

### Proprietary SaaS
- Closed source
- API access only
- Full control over distribution

---

## 🎯 Summary

**Recommended Distribution Strategy**:
1. **Open Source Core** - GitHub repository (MIT license)
2. **PyPI SDK** - `pip install mppf-framework`
3. **Docker Image** - Docker Hub for easy deployment
4. **Managed Hosting** - SaaS offering for non-technical users
5. **Enterprise Support** - Paid support contracts for large orgs

This gives maximum flexibility: developers can self-host, integrate via SDK, or use your hosted service.
