from fastapi import FastAPI, Request, UploadFile, File, Path, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.encoders import jsonable_encoder
import os
import uuid
import uvicorn
import json
from datetime import datetime
from dotenv import load_dotenv

from models.schemas import (
    VoiceChatResponse, 
    ChatHistoryResponse, 
    BackendStatusResponse,
    APIKeyConfig,
    ErrorType
)
from services.stt_service import STTService
from services.llm_service import LLMService
from services.tts_service import TTSService
from services.database_service import DatabaseService
from utils.logging_config import setup_logging, get_logger
from utils.constants import get_fallback_message

# Load environment variables
load_dotenv()
setup_logging()
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="30 Days of Voice Agents - FastAPI",
    description="A modern conversational AI voice agent with FastAPI backend",
    version="1.0.0"
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
stt_service: STTService = None
llm_service: LLMService = None
tts_service: TTSService = None
database_service: DatabaseService = None


def initialize_services() -> APIKeyConfig:
    """Initialize all services with API keys"""
    config = APIKeyConfig(
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        assemblyai_api_key=os.getenv("ASSEMBLYAI_API_KEY"),
        murf_api_key=os.getenv("MURF_API_KEY"),
        murf_voice_id=os.getenv("MURF_VOICE_ID", "en-IN-aarav"),
        mongodb_url=os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    )
    
    global stt_service, llm_service, tts_service, database_service
    if config.are_keys_valid:
        stt_service = STTService(config.assemblyai_api_key)
        llm_service = LLMService(config.gemini_api_key)
        tts_service = TTSService(config.murf_api_key, config.murf_voice_id)
        logger.info("✅ All AI services initialized successfully")
    else:
        missing_keys = config.validate_keys()
        logger.error(f"❌ Missing API keys: {missing_keys}")
    database_service = DatabaseService(config.mongodb_url)
    
    return config


@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting Voice Agent application...")
    
    config = initialize_services()
    if database_service:
        await database_service.connect()
    
    logger.info("✅ Application startup completed")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("🛑 Shutting down Voice Agent application...")
    
    if database_service:
        await database_service.close()
    
    logger.info("✅ Application shutdown completed")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main application page"""
    session_id = request.query_params.get('session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
    
    logger.info(f"Serving home page for session: {session_id}")
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "session_id": session_id
    })


@app.get("/api/backend", response_model=BackendStatusResponse)
async def get_backend_status():
    """Get backend status"""
    return BackendStatusResponse(
        message="🚀 This message is coming from FastAPI backend!",
        status="success"
    )


@app.get("/agent/chat/{session_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history_endpoint(session_id: str = Path(..., description="Session ID")):
    """Get chat history for a session"""
    try:
        if not database_service:
            raise HTTPException(status_code=500, detail="Database service not available")
        
        chat_history = await database_service.get_chat_history(session_id)
        serializable_history = jsonable_encoder(chat_history)
        
        logger.info(f"Retrieved {len(serializable_history)} messages for session {session_id}")
        
        return ChatHistoryResponse(
            success=True,
            session_id=session_id,
            messages=serializable_history,
            message_count=len(serializable_history)
        )
    except Exception as e:
        logger.error(f"Failed to get chat history: {str(e)}")
        return ChatHistoryResponse(
            success=False,
            session_id=session_id,
            messages=[],
            message_count=0
        )


@app.get("/api/streamed-audio")
async def list_streamed_audio():
    """Get list of all streamed audio files"""
    try:
        audio_dir = "streamed_audio"
        if not os.path.exists(audio_dir):
            return {
                "success": True,
                "message": "No streamed audio directory found",
                "files": [],
                "total_files": 0
            }
        
        audio_files = []
        for filename in os.listdir(audio_dir):
            if filename.endswith('.wav'):
                filepath = os.path.join(audio_dir, filename)
                file_stats = os.stat(filepath)
                audio_files.append({
                    "filename": filename,
                    "size_bytes": file_stats.st_size,
                    "created_at": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(file_stats.st_mtime).isoformat()
                })
        
        # Sort by creation time (newest first)
        audio_files.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "success": True,
            "message": f"Found {len(audio_files)} streamed audio files",
            "files": audio_files,
            "total_files": len(audio_files),
            "total_size_bytes": sum(f["size_bytes"] for f in audio_files)
        }
        
    except Exception as e:
        logger.error(f"Error listing streamed audio files: {e}")
        return {
            "success": False,
            "message": f"Error listing files: {str(e)}",
            "files": [],
            "total_files": 0
        }


@app.post("/agent/chat/{session_id}", response_model=VoiceChatResponse)
async def chat_with_agent(
    session_id: str = Path(..., description="Session ID"),
    audio: UploadFile = File(..., description="Audio file for voice input")
):
    transcribed_text = ""
    response_text = ""
    
    try:
        logger.info(f"Processing voice chat for session: {session_id}")
        
        if not all([stt_service, llm_service, tts_service, database_service]):
            logger.error("Services not properly initialized")
            fallback_audio = None
            if tts_service:
                fallback_audio = await tts_service.generate_fallback_audio(
                    get_fallback_message(ErrorType.API_KEYS_MISSING)
                )
            
            return VoiceChatResponse(
                success=False,
                message=get_fallback_message(ErrorType.API_KEYS_MISSING),
                transcription="",
                llm_response=get_fallback_message(ErrorType.API_KEYS_MISSING),
                audio_url=fallback_audio,
                error_type=ErrorType.API_KEYS_MISSING
            )
        try:
            audio_content = await audio.read()
            if not audio_content:
                raise ValueError("Empty audio file received")
        except Exception as e:
            logger.error(f"Audio file processing error: {str(e)}")
            fallback_audio = await tts_service.generate_fallback_audio(
                get_fallback_message(ErrorType.FILE_ERROR)
            )
            return VoiceChatResponse(
                success=False,
                message=get_fallback_message(ErrorType.FILE_ERROR),
                transcription="",
                llm_response=get_fallback_message(ErrorType.FILE_ERROR),
                audio_url=fallback_audio,
                error_type=ErrorType.FILE_ERROR
            )
        try:
            transcribed_text = await stt_service.transcribe_audio(audio_content)
            if not transcribed_text:
                fallback_audio = await tts_service.generate_fallback_audio(
                    get_fallback_message(ErrorType.NO_SPEECH)
                )
                return VoiceChatResponse(
                    success=False,
                    message=get_fallback_message(ErrorType.NO_SPEECH),
                    transcription="",
                    llm_response=get_fallback_message(ErrorType.NO_SPEECH),
                    audio_url=fallback_audio,
                    error_type=ErrorType.NO_SPEECH
                )
        except Exception as e:
            logger.error(f"STT error: {str(e)}")
            fallback_audio = await tts_service.generate_fallback_audio(
                get_fallback_message(ErrorType.STT_ERROR)
            )
            return VoiceChatResponse(
                success=False,
                message=get_fallback_message(ErrorType.STT_ERROR),
                transcription="",
                llm_response=get_fallback_message(ErrorType.STT_ERROR),
                audio_url=fallback_audio,
                error_type=ErrorType.STT_ERROR
            )
        try:
            chat_history = await database_service.get_chat_history(session_id)
            await database_service.add_message_to_history(session_id, "user", transcribed_text)
        except Exception as e:
            logger.error(f"Chat history error: {str(e)}")
            chat_history = []  # Continue with empty history
        try:
            response_text = await llm_service.generate_response(transcribed_text, chat_history)
        except Exception as e:
            logger.error(f"LLM error: {str(e)}")
            fallback_audio = await tts_service.generate_fallback_audio(
                get_fallback_message(ErrorType.LLM_ERROR)
            )
            return VoiceChatResponse(
                success=False,
                message=get_fallback_message(ErrorType.LLM_ERROR),
                transcription=transcribed_text,
                llm_response=get_fallback_message(ErrorType.LLM_ERROR),
                audio_url=fallback_audio,
                error_type=ErrorType.LLM_ERROR
            )
        try:
            await database_service.add_message_to_history(session_id, "assistant", response_text)
        except Exception as e:
            logger.error(f"Failed to save assistant response to history: {str(e)}")
        try:
            audio_url = await tts_service.generate_speech(response_text)
            if not audio_url:
                raise Exception("No audio URL returned from TTS service")
        except Exception as e:
            logger.error(f"TTS error: {str(e)}")
            fallback_audio = await tts_service.generate_fallback_audio(
                get_fallback_message(ErrorType.TTS_ERROR)
            )
            return VoiceChatResponse(
                success=False,
                message=get_fallback_message(ErrorType.TTS_ERROR),
                transcription=transcribed_text,
                llm_response=response_text,
                audio_url=fallback_audio,
                error_type=ErrorType.TTS_ERROR
            )
        logger.info(f"Voice chat completed successfully for session: {session_id}")
        return VoiceChatResponse(
            success=True,
            message="Voice chat processed successfully",
            transcription=transcribed_text,
            llm_response=response_text,
            audio_url=audio_url,
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in chat_with_agent: {str(e)}")
        fallback_audio = None
        if tts_service:
            fallback_audio = await tts_service.generate_fallback_audio(
                get_fallback_message(ErrorType.GENERAL_ERROR)
            )
        
        return VoiceChatResponse(
            success=False,
            message=get_fallback_message(ErrorType.GENERAL_ERROR),
            transcription=transcribed_text,
            llm_response=get_fallback_message(ErrorType.GENERAL_ERROR),
            audio_url=fallback_audio,
            error_type=ErrorType.GENERAL_ERROR
        )
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
manager = ConnectionManager()


@app.websocket("/ws/audio-stream")
async def audio_stream_websocket(websocket: WebSocket):
    await manager.connect(websocket)
    session_id = str(uuid.uuid4())
    audio_filename = f"streamed_audio_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
    audio_filepath = os.path.join("streamed_audio", audio_filename)
    os.makedirs("streamed_audio", exist_ok=True)
    
    try:
        welcome_message = {
            "type": "audio_stream_ready",
            "message": "Audio streaming endpoint ready. Send binary audio data.",
            "session_id": session_id,
            "audio_filename": audio_filename,
            "timestamp": datetime.now().isoformat()
        }
        await manager.send_personal_message(json.dumps(welcome_message), websocket)
        logger.info(f"Audio streaming session started: {session_id}")
        
        with open(audio_filepath, "wb") as audio_file:
            chunk_count = 0
            total_bytes = 0
            
            while True:
                try:
                    message = await websocket.receive()
                    
                    if "text" in message:
                        command = message["text"]
                        logger.info(f"Received command: {command}")
                        
                        if command == "start_streaming":
                            response = {
                                "type": "command_response",
                                "message": "Ready to receive audio chunks",
                                "status": "streaming_ready"
                            }
                            await manager.send_personal_message(json.dumps(response), websocket)
                            
                        elif command == "stop_streaming":
                            response = {
                                "type": "command_response", 
                                "message": f"Audio streaming completed. Saved {chunk_count} chunks ({total_bytes} bytes) to {audio_filename}",
                                "status": "streaming_completed",
                                "chunk_count": chunk_count,
                                "total_bytes": total_bytes,
                                "audio_filename": audio_filename
                            }
                            await manager.send_personal_message(json.dumps(response), websocket)
                            logger.info(f"Audio streaming completed: {audio_filename} ({total_bytes} bytes)")
                            break
                            
                    elif "bytes" in message:
                        # Handle binary audio data
                        audio_chunk = message["bytes"]
                        chunk_size = len(audio_chunk)
                        
                        # Write audio chunk to file
                        audio_file.write(audio_chunk)
                        audio_file.flush()
                        
                        chunk_count += 1
                        total_bytes += chunk_size
                        
                        logger.info(f"Received audio chunk {chunk_count}: {chunk_size} bytes")
                        ack_response = {
                            "type": "chunk_ack",
                            "chunk_number": chunk_count,
                            "chunk_size": chunk_size,
                            "total_bytes": total_bytes,
                            "timestamp": datetime.now().isoformat()
                        }
                        await manager.send_personal_message(json.dumps(ack_response), websocket)
                        
                except Exception as e:
                    logger.error(f"Error processing audio stream: {e}")
                    error_response = {
                        "type": "error",
                        "message": f"Error processing audio data: {str(e)}"
                    }
                    await manager.send_personal_message(json.dumps(error_response), websocket)
                    break
                    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"Audio streaming WebSocket disconnected for session: {session_id}")
    except Exception as e:
        logger.error(f"Audio streaming WebSocket error: {e}")
        manager.disconnect(websocket)
    finally:
        logger.info(f"Audio streaming session ended: {session_id}")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received WebSocket message: {data}")
            response = {
                "type": "echo",
                "original_message": data,
                "echo_message": f"Echo: {data}",
                "timestamp": datetime.now().isoformat(),
                "connection_id": id(websocket),
                "total_connections": len(manager.active_connections)
            }
            await manager.send_personal_message(json.dumps(response), websocket)
            logger.info(f"Sent echo response back to client")
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
