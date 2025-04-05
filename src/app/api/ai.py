from fastapi import APIRouter, HTTPException
from services.ai_service import AIService
from typing import Dict, Any

router = APIRouter()
ai_service = AIService()

@router.post("/start")
async def start_openai_conversation() -> Dict[str, str]:
    """Start a new OpenAI conversation and return thread ID"""
    try:
        thread_id = await ai_service.create_openai_conversation()
        return {"threadId": thread_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/message")
async def send_openai_message(data: Dict[str, str]) -> Dict[str, str]:
    """Send a message to OpenAI conversation"""
    try:
        thread_id = data.get("threadId")
        message = data.get("message")
        if not thread_id or not message:
            raise HTTPException(status_code=400, detail="ThreadId and message are required")
        
        response = await ai_service.send_openai_message(thread_id, message)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bedrock/start")
async def start_bedrock_conversation() -> Dict[str, str]:
    """Start a new Bedrock conversation and return session ID"""
    try:
        session_id = await ai_service.create_bedrock_conversation()
        return {"sessionId": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bedrock/message")
async def send_bedrock_message(data: Dict[str, str]) -> Dict[str, str]:
    """Send a message to Bedrock conversation"""
    try:
        session_id = data.get("sessionId")
        message = data.get("message")
        if not session_id or not message:
            raise HTTPException(status_code=400, detail="SessionId and message are required")
        
        response = await ai_service.send_bedrock_message(session_id, message)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 