"""
FastAPI Application - Main Entry Point.
Provides REST API and Server-Sent Events (SSE) for real-time trace streaming.
"""
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import json
from datetime import datetime

from app.schemas.models import QueryRequest, FinalResponse, TraceEvent
from app.workflow.engine import workflow_engine
from app.core.config import settings


# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    print(f"🚀 MPPF Server starting on {settings. host}:{settings.port}")
    print(f"📊 Mission Control Dashboard: http://localhost:{settings.port}")
    yield
    print("🛑 MPPF Server shutting down")


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
            yield f"data: {json.dumps({'message': 'Connected to MPPF trace stream', 'timestamp': datetime.now().isoformat()})}\n\n"
            
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
                    yield f"data: {json.dumps({'timestamp': datetime.now().isoformat()})}\n\n"
                    
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
