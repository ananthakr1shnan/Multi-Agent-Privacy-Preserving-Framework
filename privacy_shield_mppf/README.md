# Multi-Agent Privacy-Preserving Personalization Framework (MPPF)

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A **Privacy-First AI System** that uses local PII redaction (Microsoft Presidio) and parallel multi-agent orchestration to provide personalized responses without compromising user confidentiality.

Built for **College of Engineering, Trivandrum (CET)** as a demonstration of privacy-preserving AI architecture in multi-agent systems.

---

## 🎯 Core Concept

Current AI systems require users to share sensitive Personal Identifiable Information (PII) to get personalized results. MPPF introduces a **Local Privacy Gateway** that redacts PII locally using Microsoft Presidio before distributing anonymized tasks to multiple specialized AI agents running in parallel.

### Key Innovation

```
User Query → Privacy Shield (Local) → [Parallel Agents] → Aggregator → Final Response
                                      ├─ Productivity
                                      ├─ Ethics  
                                      └─ Creativity
```

**Example:**
- **Input:** "Schedule a meeting with John Doe (john@example.com) at CET tomorrow"
- **Anonymized:** "Schedule a meeting with `<PERSON>` (`<EMAIL>`) at `<ORGANIZATION>` tomorrow"
- **Result:** Personalized scheduling advice without exposing identities to cloud LLMs

---

## 🏗️ Architecture

### System Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Privacy Shield** | Microsoft Presidio | Local PII detection & redaction |
| **Workflow Engine** | Custom DAG | Parallel agent orchestration |
| **LLM Inference** | Groq (Llama 3) | Cloud-based reasoning |
| **Backend API** | FastAPI | Async HTTP + SSE streaming |
| **Frontend** | Bootstrap 5 + jQuery | Mission Control dashboard |
| **Visualization** | Chart.js | Agent contribution metrics |

### Workflow DAG

```
┌─────────────────┐
│  Privacy Shield │ (Root Node - Local)
│   - PII Detection
│   - Anonymization
└────────┬────────┘
         │
    ┌────┴────┬─────────┬──────────┐
    │         │         │          │
┌───▼───┐ ┌──▼───┐ ┌───▼────┐     │
│Produc-│ │Ethics│ │Creative│ (Parallel)
│tivity │ │Agent │ │ Agent  │
└───┬───┘ └──┬───┘ └───┬────┘
    │        │         │
    └────┬───┴─────┬───┘
         │         │
    ┌────▼─────────▼───┐
    │   Aggregator     │ (Sink Node)
    │  - Synthesis
    │  - Weighted merge
    └──────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- GROQ API Key ([Get one here](https://console.groq.com/))

### Installation

```bash
# Clone the repository
cd privacy_shield_mppf

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_lg

# Configure environment
# Edit .env file and add your GROQ_API_KEY
```

### Configuration

Create or edit `.env`:

```env
GROQ_API_KEY=your_actual_groq_api_key_here
HOST=0.0.0.0
PORT=8000
DEBUG=True
GROQ_MODEL=llama3-70b-8192
```

### Run the Application

```bash
# Start the server
python -m app.main

# Or use uvicorn directly
uvicorn app.main:app --reload
```

Navigate to **http://localhost:8000** to access the Mission Control Dashboard.

---

## 💻 Usage

### Web Dashboard

1. **Enter Query**: Type your query in the input panel (try including PII like names, emails)
2. **Submit**: Click "Process Query"
3. **Watch Live Trace**: Monitor real-time workflow execution
4. **View Results**: See anonymized data, agent responses, and contribution weights

### API Endpoints

#### POST `/api/query`

Process a query through the privacy-preserving workflow.

**Request:**
```json
{
  "query": "Schedule a meeting with John Doe at john@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "final_response": "...",
    "agent_contributions": {
      "productivity_agent": 0.5,
      "ethics_agent": 0.25,
      "creativity_agent": 0.25
    },
    "total_processing_time_ms": 1234,
    "privacy_analysis": {
      "redaction_count": 2,
      "entities_found": [...]
    }
  }
}
```

#### GET `/api/stream`

Server-Sent Events (SSE) endpoint for real-time trace updates.

---

## 🧪 Privacy Shield

### Detected Entities

- **PERSON** - Names
- **EMAIL_ADDRESS** - Email addresses
- **PHONE_NUMBER** - Phone numbers
- **LOCATION** - Geographic locations
- **ORGANIZATION** - Company/institution names
- **CREDIT_CARD** - Payment card numbers
- **IP_ADDRESS** - IP addresses
- **DATE_TIME** - Temporal information

### Example

```python
from app.workflow.privacy_node import privacy_shield

analysis = privacy_shield.analyze_and_redact(
    "Meet Arjun at arjun@cet.ac.in tomorrow"
)

print(analysis.anonymized_text)
# Output: "Meet <PERSON> at <EMAIL> tomorrow"
```

---

## 🤖 Multi-Agent System

### Agent Personas

#### 1. Productivity Agent 💼
- **Focus**: Actionable, direct responses
- **Weight**: 50% (default)
- **Optimized for**: Task completion, efficiency

#### 2. Ethics Agent ⚖️
- **Focus**: Safety, bias detection, ethical concerns
- **Weight**: 25% (default)
- **Optimized for**: Risk assessment, fairness

#### 3. Creativity Agent 🎨
- **Focus**: Diverse perspectives, innovative solutions
- **Weight**: 25% (default)
- **Optimized for**: Out-of-the-box thinking

---

## 📊 Academic Evaluation Metrics

### 1. **Redaction Accuracy**
- Percentage of PII successfully identified and masked
- Target: >95%

### 2. **System Latency**
- Sequential vs Parallel execution comparison
- Expected speedup: ~3x with parallel agents

### 3. **Transparency**
- Real-time trace visibility
- Agent contribution breakdown

### 4. **Privacy Preservation**
- Zero PII leakage to cloud
- Local-first processing guarantee

---

## 📁 Project Structure

```
privacy_shield_mppf/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── core/
│   │   ├── config.py           # Configuration
│   │   └── llm_client.py       # Groq API client
│   ├── workflow/
│   │   ├── engine.py           # DAG orchestration
│   │   ├── privacy_node.py     # Privacy shield
│   │   ├── agent_nodes.py      # Multi-agent logic
│   │   └── aggregator.py       # Response synthesis
│   └── schemas/
│       └── models.py           # Data models
├── static/
│   ├── css/
│   │   ├── dashboard.css       # Dashboard styles
│   │   └── terminal.css        # Terminal styles
│   └── js/
│       ├── dashboard.js        # UI logic
│       └── monitor.js          # SSE handling
├── templates/
│   └── index.html              # Dashboard HTML
├── .env                        # Environment config
├── requirements.txt            # Dependencies
└── README.md                   # This file
```

---

## 🔧 Development

### Running Tests

```bash
# Privacy shield accuracy test
python -m pytest tests/test_privacy.py -v

# Parallel execution benchmark
python scripts/benchmark.py
```

### Adding New Agents

1. Create agent class in `app/workflow/agent_nodes.py`
2. Define system prompt
3. Register in workflow engine DAG
4. Update aggregator weights

---

## 🎓 Academic Context

This project was developed as part of a college project at **College of Engineering, Trivandrum (CET)**, focusing on:

- **AI Privacy** - Local PII redaction
- **Multi-Agent Systems** - Parallel specialized agents
- **Real-Time Orchestration** - DAG workflow execution
- **Explainable AI** - Transparent decision-making

### Key Learning Outcomes

1. Privacy-preserving AI architectures
2. Asynchronous workflow orchestration
3. Multi-agent collaboration patterns
4. Real-time streaming with SSE
5. Full-stack AI application development

---

## 🤝 Contributing

This is an educational project. Contributions, suggestions, and improvements are welcome!

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

- **Microsoft Presidio** - Privacy shield implementation
- **Groq** - Fast LLM inference
- **FastAPI** - Modern Python web framework
- **College of Engineering, Trivandrum** - Academic support

---

## 📞 Contact

For questions or collaboration:
- **Institution**: College of Engineering, Trivandrum (CET)
- **Project Type**: Privacy-First AI System
- **Focus**: Multi-Agent Architecture & Privacy Preservation

---

**Built with ❤️ for Privacy-First AI**
