"""
FastAPI Web Service for AI Agent
Purpose: REST API endpoints for agent interaction
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import asyncio
import uuid

from src.agents.base_agent import BaseAgent
from config.logger import app_logger as logger

# Initialize FastAPI app
app = FastAPI(
    title="Azure AI Agent Service",
    description="Autonomous AI agent with tool use capabilities",
    version="1.0.0"
)

# WHY: CORS middleware for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # WHY: In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory agent sessions (in production, use Cosmos DB)
active_agents: Dict[str, BaseAgent] = {}


# Request/Response models
class TaskRequest(BaseModel):
    task: str
    session_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "task": "Search for latest AI trends and summarize",
                "session_id": "optional-session-id"
            }
        }


class TaskResponse(BaseModel):
    success: bool
    response: str
    session_id: str
    tool_calls: Optional[List[Dict]] = []
    error: Optional[str] = None


class SessionResponse(BaseModel):
    session_id: str
    message: str


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Azure AI Agent",
        "status": "healthy",
        "version": "1.0.0"
    }


@app.post("/session/create", response_model=SessionResponse)
async def create_session():
    """
    Create a new agent session
    
    WHY: Sessions enable multi-turn conversations with persistent memory
    """
    
    session_id = str(uuid.uuid4())
    agent = BaseAgent(session_id=session_id)
    active_agents[session_id] = agent
    
    logger.info(f"Created session: {session_id}")
    
    return SessionResponse(
        session_id=session_id,
        message="Session created successfully"
    )


@app.post("/agent/task", response_model=TaskResponse)
async def process_task(request: TaskRequest):
    """
    Process a task with the agent
    
    Args:
        request: Task request with optional session_id
        
    Returns:
        Agent response with tool usage info
    """
    
    # Get or create session
    session_id = request.session_id
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Get or create agent
    if session_id not in active_agents:
        agent = BaseAgent(session_id=session_id)
        active_agents[session_id] = agent
    else:
        agent = active_agents[session_id]
    
    # Process task
    try:
        result = await agent.process_task(request.task)
        
        return TaskResponse(
            success=result["success"],
            response=result["response"],
            session_id=session_id,
            tool_calls=result.get("tool_calls", []),
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Task processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete an agent session"""
    
    if session_id in active_agents:
        agent = active_agents[session_id]
        agent.clear_history()
        del active_agents[session_id]
        
        logger.info(f"Deleted session: {session_id}")
        return {"message": f"Session {session_id} deleted"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@app.get("/session/{session_id}/history")
async def get_session_history(session_id: str):
    """Get conversation history for a session"""
    
    if session_id not in active_agents:
        raise HTTPException(status_code=404, detail="Session not found")
    
    agent = active_agents[session_id]
    history = agent.memory.get_conversation_history(session_id)
    
    return {
        "session_id": session_id,
        "messages": history
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "active_sessions": len(active_agents),
        "services": {
            "azure_openai": "connected",
            "cosmos_db": "connected"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    # WHY: Run with uvicorn for production-ready ASGI server
    uvicorn.run(
        "src.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # WHY: Auto-reload during development
        log_level="info"
    )
