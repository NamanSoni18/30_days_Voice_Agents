from fastapi import FastAPI, Request, UploadFile, File, Path
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
import os
from typing import Dict, List
import tempfile
from dotenv import load_dotenv
import uvicorn
import assemblyai as aai
from murf import Murf
import google.generativeai as genai
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import uuid
import json

load_dotenv()

# Custom JSON encoder for datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

app = FastAPI(title="30 Days of Voice Agents - FastAPI")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
async def startup_event():
    """Initialize MongoDB connection on startup"""
    await get_mongodb()

mongodb_client = None
db = None
in_memory_chat_store = {}

async def get_mongodb():
    global mongodb_client, db
    if mongodb_client is None:
        try:
            mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
            mongodb_client = AsyncIOMotorClient(mongodb_url)
            db = mongodb_client.voice_agents
            await mongodb_client.admin.command('ping')
            print("✅ Connected to MongoDB successfully")
        except Exception as e:
            print(f"⚠️  MongoDB connection failed: {e}")
            print("💾 Using in-memory storage as fallback")
            mongodb_client = None
            db = None
    return db

async def get_chat_history(session_id: str) -> List[Dict]:
    """Get chat history for a session"""
    db = await get_mongodb()
    if db is not None:
        chat_history = await db.chat_sessions.find_one({"session_id": session_id})
        if chat_history and "messages" in chat_history:
            return chat_history["messages"]
        return []
    else:
        return in_memory_chat_store.get(session_id, [])

async def add_message_to_history(session_id: str, role: str, content: str):
    """Add a message to chat history"""
    db = await get_mongodb()
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now()
    }
    if db is not None:
        await db.chat_sessions.update_one(
            {"session_id": session_id},
            {
                "$push": {"messages": message},
                "$set": {"last_updated": datetime.now()}
            },
            upsert=True
        )
    else:
        if session_id not in in_memory_chat_store:
            in_memory_chat_store[session_id] = []
        in_memory_chat_store[session_id].append(message)


class LLMQueryRequest(BaseModel):
    text: str


def format_chat_history_for_llm(messages: List[Dict]) -> str:
    """Format chat history for inclusion in LLM prompt"""
    if not messages:
        return ""
    
    formatted_history = "\n\nPrevious conversation context:\n"
    for msg in messages[-10:]:
        role = "User" if msg["role"] == "user" else "Assistant"
        formatted_history += f"{role}: {msg['content']}\n"
    
    return formatted_history

def truncate_text_for_murf(text: str, max_chars: int = 3000) -> str:
    """Truncate text to fit within Murf's character limit while preserving sentence structure."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_sentence_end = max(
        truncated.rfind('.'),
        truncated.rfind('!'),
        truncated.rfind('?')
    )
    
    if last_sentence_end > max_chars * 0.7: 
        return truncated[:last_sentence_end + 1]
    else:
        last_space = truncated.rfind(' ')
        if last_space > 0:
            return truncated[:last_space] + "..."
        else:
            return truncated + "..."


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    session_id = request.query_params.get('session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "session_id": session_id
    })
  
@app.get("/api/backend")
async def get_backend_message():
    return {"message": "🚀 This message is coming from FastAPI backend!", "status": "success"}


@app.get("/agent/chat/{session_id}/history")
async def get_chat_history_endpoint(session_id: str = Path(...)):
    """Get chat history for a session"""
    try:
        chat_history = await get_chat_history(session_id)
        serializable_history = jsonable_encoder(chat_history)
        return {
            "success": True,
            "session_id": session_id,
            "messages": serializable_history,
            "message_count": len(serializable_history)
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to get chat history: {str(e)}",
            "session_id": session_id,
            "messages": [],
            "message_count": 0
        }


@app.post("/agent/chat/{session_id}")
async def chat_with_agent(session_id: str = Path(...), audio: UploadFile = File(...)):
    """Chat endpoint with session-based history storage"""
    try:
        gemini_key = os.getenv("GEMINI_API_KEY")
        assemblyai_key = os.getenv("ASSEMBLYAI_API_KEY")
        murf_key = os.getenv("MURF_API_KEY")
        voice_id = os.getenv("MURF_VOICE_ID", "en-IN-aarav")
        
        if (not gemini_key or gemini_key == "your_gemini_api_key_here" or
            not assemblyai_key or assemblyai_key == "your_assemblyai_api_key_here" or
            not murf_key or murf_key == "your_murf_api_key_here"):
            return {
                "success": False,
                "message": "Required API keys not set. Please set GEMINI_API_KEY, ASSEMBLYAI_API_KEY, and MURF_API_KEY in your environment.",
                "transcription": "",
                "llm_response": "",
                "audio_url": None
            }
        audio_content = await audio.read()
        aai.settings.api_key = assemblyai_key
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_content)
            tmp_path = tmp.name
        try:
            transcriber = aai.Transcriber()
            transcript = transcriber.transcribe(tmp_path)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        
        if transcript.status == aai.TranscriptStatus.error:
            return {
                "success": False,
                "message": f"Transcription failed: {transcript.error}",
                "transcription": "",
                "llm_response": "",
                "audio_url": None
            }
        
        if not transcript.text or transcript.text.strip() == "":
            return {
                "success": False,
                "message": "No speech detected in the audio",
                "transcription": "",
                "llm_response": "",
                "audio_url": None
            }
        
        transcribed_text = transcript.text
        chat_history = await get_chat_history(session_id)
        await add_message_to_history(session_id, "user", transcribed_text)
        history_context = format_chat_history_for_llm(chat_history)
        
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        llm_prompt = f"""Please provide a helpful and well-formatted response to the following user message. 
                        Guidelines:
                        - Keep your response under 3000 characters to ensure it can be converted to speech effectively
                        - Use Markdown formatting when appropriate:
                          - Use **bold** for emphasis
                          - Use `code` for technical terms or code snippets
                          - Use bullet points (-) or numbered lists (1.) when listing items
                          - Use code blocks (```) for longer code examples
                          - Use headers (##) for sections if needed
                          - Use tables when organizing data
                        - Structure your response clearly and logically
                        - Be concise but comprehensive
                        - Consider the conversation history to provide relevant and contextual responses
                        
                        {history_context}
                        
                        Current user message: {transcribed_text}"""
        
        llm_response = model.generate_content(llm_prompt)
        if not llm_response.candidates:
            return {
                "success": False,
                "message": "No response generated from LLM",
                "transcription": transcribed_text,
                "llm_response": "",
                "audio_url": None
            }
        
        response_text = ""
        for part in llm_response.candidates[0].content.parts:
            if hasattr(part, 'text'):
                response_text += part.text
        
        if not response_text.strip():
            return {
                "success": False,
                "message": "No text content in LLM response",
                "transcription": transcribed_text,
                "llm_response": "",
                "audio_url": None
            }
        
        await add_message_to_history(session_id, "assistant", response_text)
        
        murf_text = truncate_text_for_murf(response_text)
        try:
            murf_client = Murf(api_key=murf_key)
            murf_response = murf_client.text_to_speech.generate(
                text=murf_text,
                voice_id=voice_id,
                format="MP3"
            )
            audio_url = murf_response.audio_file
        except Exception as murf_error:
            return {
                "success": False,
                "message": f"Murf API error: {str(murf_error)}",
                "transcription": transcribed_text,
                "llm_response": response_text,
                "audio_url": None
            }
        
        if not audio_url:
            return {
                "success": False,
                "message": "No audio URL returned from Murf API",
                "transcription": transcribed_text,
                "llm_response": response_text,
                "audio_url": None
            }
        
        return {
            "success": True,
            "message": "Voice chat processed successfully",
            "transcription": transcribed_text,
            "llm_response": response_text,
            "audio_url": audio_url,
            "session_id": session_id
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Voice chat processing error: {str(e)}",
            "transcription": "",
            "llm_response": "",
            "audio_url": None
        }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
