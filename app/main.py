"""
FastAPI Application - Main Entry Point.
Provides REST API and Server-Sent Events (SSE) for real-time trace streaming.
"""
from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import json
from datetime import datetime, timezone, timedelta
from app.core.database import IST

def _to_ist(dt: datetime) -> datetime:
    """Convert any datetime to IST. Assumes UTC if no tzinfo is present."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(IST)

from app.schemas.models import QueryRequest, FinalResponse, TraceEvent
from app.workflow.engine import workflow_engine
from app.core.config import settings


# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    print(f"[MPPF] Server starting on {settings.host}:{settings.port}")
    print(f"[MPPF] Dashboard: http://localhost:{settings.port}")
    yield
    print("[MPPF] Server shutting down")


# Initialize FastAPI app
app = FastAPI(
    title="Multi-Agent Privacy-Preserving Framework",
    description="Privacy-first AI system with local PII redaction and multi-agent orchestration",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# Global state for SSE clients
sse_clients = []


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve the Mission Control dashboard"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/knowledge-base", response_class=HTMLResponse)
async def knowledge_base_page(request: Request):
    """Serve the Knowledge Base management page"""
    return templates.TemplateResponse("knowledge_base.html", {"request": request})


@app.get("/audit-logs", response_class=HTMLResponse)
async def audit_logs_page(request: Request):
    """Serve the Audit Logs viewer page"""
    return templates.TemplateResponse("audit_logs.html", {"request": request})



@app.post("/api/query", response_model=FinalResponse)
async def process_query(query_request: QueryRequest):
    """
    Process a user query through the privacy-preserving workflow.
    
    This endpoint executes the complete DAG:
    1. Privacy Shield - Redact PII locally
    2. Parallel Agents - Productivity, Ethics, Creativity
    3. Aggregator - Synthesize final response
    """
    try:
        # Execute workflow
        result = await workflow_engine.execute(
            user_query=query_request.query,
            event_callback=broadcast_trace_event
        )
        
        return FinalResponse(
            success=True,
            result=result
        )
        
    except Exception as e:
        return FinalResponse(
            success=False,
            error=str(e)
        )


@app.get("/api/stream")
async def stream_trace_events(request: Request):
    """
    Server-Sent Events (SSE) endpoint for real-time trace streaming.
    Clients can subscribe to receive live workflow updates.
    """
    async def event_generator():
        """Generate SSE events"""
        # Create a queue for this client
        queue = asyncio.Queue()
        sse_clients.append(queue)
        
        try:
            # Send initial connection event
            yield f"event: connected\n"
            yield f"data: {json.dumps({'message': 'Connected to MPPF trace stream', 'timestamp': _to_ist(datetime.now()).strftime('%Y-%m-%d %H:%M:%S IST')})}\n\n"
            
            # Stream events from the queue
            while True:
                if await request.is_disconnected():
                    break
                
                try:
                    # Wait for new event with timeout
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"event: trace\n"
                    yield f"data: {json.dumps(event, default=str)}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive ping
                    yield f"event: ping\n"
                    yield f"data: {json.dumps({'timestamp': _to_ist(datetime.now()).strftime('%Y-%m-%d %H:%M:%S IST')})}\n\n"
                    
        finally:
            # Remove client on disconnect
            sse_clients.remove(queue)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


async def broadcast_trace_event(event: TraceEvent):
    """
    Broadcast a trace event to all connected SSE clients.
    
    Args:
        event: TraceEvent to broadcast
    """
    event_data = {
        "node_type": event.node_type.value,
        "status": event.status,
        "message": event.message,
        "timestamp": event.timestamp.isoformat(),
        "data": event.data
    }
    
    # Send to all connected clients
    for client_queue in sse_clients:
        try:
            await client_queue.put(event_data)
        except Exception as e:
            print(f"Error broadcasting to client: {e}")




@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a PDF or TXT file to the knowledge base.
    Automatically triggers ingestion.
    """
    import os
    import subprocess
    from pathlib import Path
    
    # Validate file type
    allowed_extensions = {".pdf", ".txt"}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Only {', '.join(allowed_extensions)} are allowed."
        )
    
    # Validate file size (10MB max)
    MAX_SIZE = 10 * 1024 * 1024  # 10MB
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is 10MB."
        )
    
    # Save file to knowledge_base directory
    knowledge_base_dir = Path("knowledge_base")
    knowledge_base_dir.mkdir(exist_ok=True)
    
    # Sanitize filename
    safe_filename = "".join(c for c in file.filename if c.isalnum() or c in "._- ")
    file_path = knowledge_base_dir / safe_filename
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Trigger ingestion asynchronously
    try:
        result = subprocess.run(
            ["python", "-m", "app.core.ingest"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Ingestion failed: {result.stderr}"
            )
        
        # Parse chunk count from output (assumes output contains "X chunks stored")
        import re
        match = re.search(r"(\d+) chunks stored", result.stdout)
        chunk_count = int(match.group(1)) if match else 0
        
        return {
            "success": True,
            "filename": safe_filename,
            "size_bytes": len(content),
            "total_chunks": chunk_count,
            "message": "File uploaded and indexed successfully"
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=500,
            detail="Ingestion timeout. File saved but not indexed yet."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during ingestion: {str(e)}"
        )


@app.get("/api/knowledge-base")
async def list_knowledge_base():
    """List all documents in the knowledge base."""
    import os
    from pathlib import Path
    import chromadb
    
    knowledge_base_dir = Path("knowledge_base")
    
    if not knowledge_base_dir.exists():
        return {"documents": []}
    
    # Get file info
    documents = []
    for file_path in knowledge_base_dir.glob("*"):
        if file_path.suffix.lower() in [".pdf", ".txt"]:
            stat = file_path.stat()
            documents.append({
                "filename": file_path.name,
                "size_bytes": stat.st_size,
                "modified_date": stat.st_mtime,
                "extension": file_path.suffix
            })
    
    return {"documents": documents}


@app.get("/api/knowledge-base/stats")
async def knowledge_base_stats():
    """Get knowledge base statistics from ChromaDB."""
    import chromadb
    
    try:
        client = chromadb.PersistentClient(path="chroma_db")
        collection = client.get_collection("mppf_knowledge")
        
        return {
            "total_chunks": collection.count(),
            "collection_name": "mppf_knowledge",
            "status": "healthy"
        }
    except Exception as e:
        return {
            "total_chunks": 0,
            "collection_name": "mppf_knowledge",
            "status": "error",
            "error": str(e)
        }


@app.delete("/api/knowledge-base/{filename}")
async def delete_document(filename: str):
    """Delete a document from the knowledge base."""
    from pathlib import Path
    import subprocess
    
    knowledge_base_dir = Path("knowledge_base")
    file_path = knowledge_base_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Delete file
    file_path.unlink()
    
    # Re-run ingestion to update ChromaDB
    try:
        subprocess.run(
            ["python", "-m", "app.core.ingest"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        return {
            "success": True,
            "message": f"Deleted {filename} and re-indexed knowledge base"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Deleted {filename} but re-indexing failed: {str(e)}"
        }


@app.get("/api/audit-logs")
async def get_audit_logs(page: int = 1, limit: int = 20):
    """Get paginated audit logs."""
    from app.core.database import SessionLocal, AuditLogTrace
    
    db = SessionLocal()
    try:
        offset = (page - 1) * limit
        
        logs = db.query(AuditLogTrace)\
            .order_by(AuditLogTrace.timestamp.desc())\
            .offset(offset)\
            .limit(limit)\
            .all()
        
        total = db.query(AuditLogTrace).count()
        
        return {
            "logs": [
                {
                    "id": log.id,
                    "timestamp": _to_ist(log.timestamp).strftime("%Y-%m-%d %H:%M:%S IST"),
                    "query": log.user_query_anonymized,
                    "domain": log.domain,
                    "confidence": log.confidence,
                    "redaction_count": log.redaction_count,
                    "processing_time_ms": log.processing_time_ms,
                    "final_response": log.final_response[:100] + "..." if len(log.final_response) > 100 else log.final_response
                }
                for log in logs
            ],
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        }
    finally:
        db.close()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "MPPF",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
