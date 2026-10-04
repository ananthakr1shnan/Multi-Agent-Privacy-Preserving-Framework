# Multi-Agent Privacy-Preserving Framework

MPPF is a Python application for testing privacy-aware, multi-agent workflows. It accepts a query, removes detected personally identifiable information locally, optionally retrieves context from a document collection, and sends the anonymized request through a sequence of specialist agents before producing a final response.

The project is intended for research, evaluation, and internal prototyping. It is not a security certification, a compliance product, or a substitute for a formal privacy review.

## What it includes

- Local PII detection and anonymization using Microsoft Presidio and spaCy.
- A domain-classification step backed by the model files in `best model/`.
- Creativity, productivity, and ethics agents coordinated by an aggregator.
- Retrieval-augmented generation using ChromaDB and uploaded PDF or TXT files.
- Optional web search during the workflow.
- Differential-privacy metrics exposed as part of the workflow result.
- SQLite audit records containing anonymized query data and processing metadata.
- A FastAPI web application, browser dashboard, REST API, and Python client.
- Server-Sent Events for displaying workflow progress in the dashboard.

## How a query is processed

```text
User query
    |
    v
Local privacy shield (PII detection and anonymization)
    |
    +--> Domain analysis
    +--> Knowledge-base retrieval
    |
    v
Creativity -> Productivity -> Ethics review
    |
    v
Aggregator and response generation
    |
    v
Audit record and API response
```

The cloud model provider receives the anonymized workflow input. Operators should still review the implementation, provider settings, logs, and deployment environment before using the system with sensitive data. Local anonymization can miss information, and the application currently has no authentication or tenant isolation.

## Requirements

- Python 3.9 or newer
- A Groq API key
- At least 4 GB of available memory for the NLP and embedding dependencies

The default configuration uses several Groq-hosted models. Model names, retry behavior, and search limits can be changed through environment variables; see `app/core/config.py` for the available settings.

## Run locally

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate

# On Windows, use: .venv\\Scripts\\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

Set the required API key in the environment:

```bash
export GROQ_API_KEY="your-groq-api-key"
```

Then start the development server:

```bash
uvicorn app.main:app --reload
```

Open `http://localhost:8000` for the dashboard. The interactive API documentation is available at `http://localhost:8000/docs`.

The application creates or updates `audit.db` and the persistent ChromaDB data under `chroma_db/`. Uploaded source documents are stored under `knowledge_base/`.

## Docker

The repository includes a Dockerfile and a Compose configuration. Export `GROQ_API_KEY`, then run:

```bash
export GROQ_API_KEY="your-groq-api-key"
docker compose up --build
```

The Compose setup persists the knowledge base, ChromaDB data, and audit database through local volumes. Review the configuration before exposing the service outside a trusted network; authentication and production hardening are not included.

## Using the API

Submit a query:

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What is differential privacy?"}'
```

Upload a PDF or TXT document. Uploads are limited to 10 MB and are indexed automatically:

```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@document.pdf"
```

Other useful endpoints include:

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Service health check |
| `GET /api/stream` | Workflow trace stream using Server-Sent Events |
| `GET /api/knowledge-base` | List indexed source files |
| `GET /api/knowledge-base/stats` | Get the ChromaDB collection count |
| `DELETE /api/knowledge-base/{filename}` | Remove a source file and re-index |
| `GET /api/audit-logs?page=1&limit=20` | Read paginated audit records |

## Python client

`mppf_sdk.py` provides a small client for queries, document management, health checks, and audit logs.

```python
from mppf_sdk import MPPFClient

client = MPPFClient("http://localhost:8000")
result = client.query("What is the role of the ethics agent?")

print(result.final_response)
print(f"Redactions: {result.privacy_analysis.redaction_count}")
print(f"Audit ID: {result.audit_id}")
```

See [example_sdk_usage.py](example_sdk_usage.py) for a complete example.

## Privacy and audit notes

The privacy layer reports detected entities and replaces them before the workflow continues. The response also exposes redaction details and differential-privacy metrics when those metrics are produced by the workflow.

Audit entries are stored in SQLite and include anonymized query text, domain information, redaction counts, processing time, and a shortened final response. These records still require operational protection: the application does not encrypt the database, restrict access, or provide automatic retention controls.

The presence of a differential-privacy metric in a response should not be interpreted as a blanket mathematical guarantee for the entire application. Review `app/privacy/differential_privacy.py` and the workflow configuration before relying on those values.

## Repository guide

| Path | Description |
| --- | --- |
| `app/main.py` | FastAPI application and HTTP endpoints |
| `app/privacy/` | PII and differential-privacy components |
| `app/workflow/` | Agent nodes, retrieval, orchestration, and aggregation |
| `app/core/` | Configuration, ingestion, database, and model client code |
| `static/` and `templates/` | Dashboard assets and HTML templates |
| `knowledge_base/` | Included project notes and sample knowledge material |
| `mppf_sdk.py` | Python API client |
| `test_production.py` | End-to-end production-path test script |
| `benchmark.py` | Benchmark runner |

The `knowledge_base/` directory contains notes explaining the project's DAG, differential privacy, and PII detection design.

## Testing

Start the application and provide a valid `GROQ_API_KEY`, then run:

```bash
python test_production.py
```

For the SDK example:

```bash
python example_sdk_usage.py
```

These scripts exercise live application paths and may call the configured model provider. They are not a substitute for isolated unit tests, adversarial privacy testing, or a deployment security review.

## Contributing

Changes should include a focused description of the behavior being changed and a test or reproducible check where practical. Please avoid committing API keys, generated databases, private documents, or model artifacts that are not necessary for the change.

## License and status

No license file is currently included in the repository. Add and review a license before distributing MPPF as a third-party package.

This project is under active development. Interfaces, model defaults, and workflow behavior may change.