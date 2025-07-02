import asyncio
from datetime import datetime, timedelta
from typing import Optional
import uuid
from venv import logger
from requests import Request
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import create_booking_agent, create_tools
from utils import get_calendar_service, get_calendar_id
from dotenv import load_dotenv



# Load environment variables
load_dotenv()

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
calendar_service = get_calendar_service()
calendar_id = get_calendar_id()

print(f"Using Calendar ID: {calendar_id}")

# Create tools and agent
tools = create_tools(calendar_service, calendar_id)
agent_executor = create_booking_agent(tools)

# Session storage
sessions = {}

# Request model
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None 

# Response model
class ChatResponse(BaseModel):
    response: str
    session_id: str

def get_session(session_id: str):
    """Get or create session state"""
    if session_id not in sessions:
        sessions[session_id] = {
            "history": [],
            "created_at": datetime.now()
        }
    return sessions[session_id]

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # Create new session if none exists
        session_id = request.session_id or str(uuid.uuid4())
        session = get_session(session_id)
        
        # Prepare input with history
        input_with_history = "\n".join(
            session["history"] + [f"User: {request.message}"]
        )
        
        # Run agent
        response = agent_executor.invoke({
            "input": input_with_history,
            "agent_scratchpad": []
        })
        
        # Update session history
        session["history"].append(f"User: {request.message}")
        session["history"].append(f"Assistant: {response['output']}")
        
        # Keep only the last 6 messages (3 exchanges)
        session["history"] = session["history"][-6:]
        
        return ChatResponse(
            response=response['output'],
            session_id=session_id
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "TailorTalk Booking API"}


async def cleanup_sessions():
    """Clean up old sessions"""
    while True:
        now = datetime.now()
        expired_sessions = [sid for sid, session in sessions.items() 
                           if now - session["created_at"] > timedelta(hours=1)]
        for sid in expired_sessions:
            del sessions[sid]
        await asyncio.sleep(3600)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_sessions())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
