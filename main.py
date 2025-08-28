from fastapi import FastAPI, Request, UploadFile, File, Path, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import uuid
import uvicorn
import json
import asyncio
import re
from datetime import datetime
from dotenv import load_dotenv

from models.schemas import (
    VoiceChatResponse, 
    ChatHistoryResponse, 
    BackendStatusResponse,
    APIKeyConfig,
    ErrorType,
    WebSearchResponse,
    WebSearchResult
)
from services.stt_service import STTService
from services.llm_service import LLMService
from services.tts_service import TTSService
from services.database_service import DatabaseService
from services.assemblyai_streaming_service import AssemblyAIStreamingService
from services.murf_websocket_service import MurfWebSocketService
from services.web_search_service import WebSearchService
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
assemblyai_streaming_service: AssemblyAIStreamingService = None
murf_websocket_service: MurfWebSocketService = None
web_search_service: WebSearchService = None


def initialize_services() -> APIKeyConfig:
    """Initialize all services with API keys - now requires user-provided keys"""
    # Don't load from .env by default - require user to provide keys
    config = APIKeyConfig(
        gemini_api_key="",  # Empty by default
        assemblyai_api_key="",  # Empty by default
        murf_api_key="",  # Empty by default
        murf_voice_id="en-IN-aarav",  # Default voice
        mongodb_url=os.getenv("MONGODB_URL"),  # Database URL still from .env
        tavily_api_key=""  # Empty by default
    )
    
    global stt_service, llm_service, tts_service, database_service, assemblyai_streaming_service, murf_websocket_service, web_search_service
    
    # Only initialize database service - AI services require user keys
    database_service = DatabaseService(config.mongodb_url)
    
    # Set all AI services to None initially
    stt_service = None
    llm_service = None
    tts_service = None
    assemblyai_streaming_service = None
    murf_websocket_service = None
    web_search_service = None
    
    logger.info("🔒 Services initialized in locked mode - user must provide API keys")
    
    return config


@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting Voice Agent application...")
    
    config = initialize_services()
    if database_service:
        try:
            db_connected = await database_service.connect()
            if db_connected:
                logger.info("✅ Database service connected successfully")
            else:
                logger.warning("⚠️ Database service running in fallback mode")
        except Exception as e:
            logger.error(f"❌ Database service initialization error: {e}")
    else:
        logger.error("❌ Database service not initialized")
    
    logger.info("✅ Application startup completed")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("🛑 Shutting down Voice Agent application...")
    
    if database_service:
        await database_service.close()
    
    # Disconnect from Murf WebSocket on shutdown
    if murf_websocket_service and murf_websocket_service.is_connected:
        await murf_websocket_service.disconnect()
    
    logger.info("✅ Application shutdown completed")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main application page"""
    session_id = request.query_params.get('session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "session_id": session_id
    })


@app.get("/api/backend", response_model=BackendStatusResponse)
async def get_backend_status():
    """Get backend status"""
    try:
        db_connected = database_service.is_connected() if database_service else False
        db_test_result = await database_service.test_connection() if database_service else False
        
        return BackendStatusResponse(
            status="healthy",
            services={
                "stt": stt_service is not None,
                "llm": llm_service is not None,
                "tts": tts_service is not None,
                "database": database_service is not None,
                "database_connected": db_connected,
                "database_test": db_test_result,
                "assemblyai_streaming": assemblyai_streaming_service is not None,
                "murf_websocket": murf_websocket_service is not None,
                "web_search": web_search_service is not None and web_search_service.is_configured()
            },
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Error getting backend status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")



@app.get("/api/sessions")
async def get_all_sessions():
    """Get all chat sessions"""
    try:
        sessions = await database_service.get_all_sessions()
        return {
            "success": True,
            "sessions": sessions,
            "total_count": len(sessions)
        }
    except Exception as e:
        logger.error(f"Error getting all sessions: {str(e)}")
        return {
            "success": False,
            "sessions": [],
            "total_count": 0,
            "error": str(e)
        }


@app.get("/agent/chat/{session_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history_endpoint(session_id: str = Path(..., description="Session ID")):
    """Get chat history for a session"""
    try:
        chat_history = await database_service.get_chat_history(session_id)
        return ChatHistoryResponse(
            success=True,
            session_id=session_id,
            messages=chat_history,
            message_count=len(chat_history)
        )
    except Exception as e:
        logger.error(f"Error getting chat history for session {session_id}: {str(e)}")
        return ChatHistoryResponse(
            success=False,
            session_id=session_id,
            messages=[],
            message_count=0
        )



@app.delete("/agent/chat/{session_id}/history")
async def clear_session_history(session_id: str = Path(..., description="Session ID")):
    """Clear chat history for a specific session"""
    try:
        success = await database_service.clear_session_history(session_id)
        if success:
            logger.info(f"Chat history cleared for session: {session_id}")
            return {"success": True, "message": f"Chat history cleared for session {session_id}"}
        else:
            return {"success": False, "message": f"Failed to clear chat history for session {session_id}"}
    except Exception as e:
        logger.error(f"Error clearing session history for {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/web-search", response_model=WebSearchResponse)
async def search_web_endpoint(request: Request):
    """Search the web using Tavily API"""
    try:
        body = await request.json()
        query = body.get("query", "")
        
        if not query.strip():
            return WebSearchResponse(
                success=False,
                query=query,
                results=[],
                error_message="Search query cannot be empty"
            )
        
        if not web_search_service or not web_search_service.is_configured():
            return WebSearchResponse(
                success=False,
                query=query,
                results=[],
                error_message="Web search service is not available. Please check Tavily API key."
            )
        
        # Perform web search
        search_results = await web_search_service.search_web(query, max_results=3)
        
        # Convert to response format
        web_results = [
            WebSearchResult(
                title=result["title"],
                snippet=result["snippet"],
                url=result["url"]
            )
            for result in search_results
        ]
        
        return WebSearchResponse(
            success=True,
            query=query,
            results=web_results
        )
        
    except Exception as e:
        logger.error(f"Web search error: {str(e)}")
        return WebSearchResponse(
            success=False,
            query=body.get("query", "") if 'body' in locals() else "",
            results=[],
            error_message=str(e)
        )


# @app.post("/agent/chat/{session_id}", response_model=VoiceChatResponse)
# async def chat_with_agent(
#     session_id: str = Path(..., description="Session ID"),
#     audio: UploadFile = File(..., description="Audio file for voice input")
# ):
#     """Chat with the voice agent using audio input"""
#     transcribed_text = ""
#     response_text = ""
#     audio_url = None
#     temp_audio_path = None
    
#     try:
#         # Validate services availability
#         config = initialize_services()
#         if not config.are_keys_valid:
#             missing_keys = config.validate_keys()
#             error_message = get_fallback_message(ErrorType.API_KEYS_MISSING)
#             fallback_audio = await tts_service.generate_fallback_audio(error_message) if tts_service else None
#             return VoiceChatResponse(
#                 success=False,
#                 message=error_message,
#                 transcription="",
#                 llm_response=error_message,
#                 audio_url=fallback_audio,
#                 session_id=session_id,
#                 error_type=ErrorType.API_KEYS_MISSING
#             )
        
#         # Process audio file
#         audio_content = await audio.read()
#         temp_audio_path = f"temp_audio_{session_id}_{uuid.uuid4().hex}.wav"
        
#         with open(temp_audio_path, "wb") as temp_file:
#             temp_file.write(audio_content)
        
#         # Transcribe audio
#         transcribed_text = await stt_service.transcribe_audio(temp_audio_path)
        
#         # Generate LLM response with chat history
#         if not database_service:
#             chat_history = []
#             user_save_success = False
#             assistant_save_success = False
#         else:
#             chat_history = await database_service.get_chat_history(session_id)
            
#             # Save user message to chat history
#             user_save_success = await database_service.add_message_to_history(session_id, "user", transcribed_text)
        
#         response_text = await llm_service.generate_response(transcribed_text, chat_history)
        
#         if database_service:
#             # Save assistant response to chat history
#             assistant_save_success = await database_service.add_message_to_history(session_id, "assistant", response_text)
        
#         # Generate TTS audio
#         audio_url = await tts_service.generate_audio(response_text, session_id)
        
#         return VoiceChatResponse(
#             success=True,
#             message="Voice chat processed successfully",
#             transcription=transcribed_text,
#             llm_response=response_text,
#             audio_url=audio_url,
#             session_id=session_id
#         )
        
#     except Exception as e:
#         logger.error(f"Error in chat_with_agent for session {session_id}: {str(e)}")
        
#         # Generate appropriate error response based on the stage where error occurred
#         if not transcribed_text:
#             error_type = ErrorType.STT_ERROR
#             error_message = get_fallback_message(ErrorType.STT_ERROR)
#         elif not response_text:
#             error_type = ErrorType.LLM_ERROR
#             error_message = get_fallback_message(ErrorType.LLM_ERROR)
#         elif not audio_url:
#             error_type = ErrorType.TTS_ERROR
#             error_message = get_fallback_message(ErrorType.TTS_ERROR)
#         else:
#             error_type = ErrorType.GENERAL_ERROR
#             error_message = get_fallback_message(ErrorType.GENERAL_ERROR)
        
#         fallback_audio = await tts_service.generate_fallback_audio(error_message) if tts_service else None
        
#         return VoiceChatResponse(
#             success=False,
#             message=error_message,
#             transcription=transcribed_text,
#             llm_response=response_text or error_message,
#             audio_url=fallback_audio,
#             session_id=session_id,
#             error_type=error_type
#         )
    
#     finally:
#         # Clean up temporary file
#         if temp_audio_path and os.path.exists(temp_audio_path):
#             try:
#                 os.remove(temp_audio_path)
#             except Exception as e:
#                 logger.warning(f"Failed to delete temp file {temp_audio_path}: {str(e)}")


@app.post("/api/validate-keys")
async def validate_api_keys(keys: APIKeyConfig):
    """Validate user provided API keys"""
    try:
        validation_results = {}
        
        # Test Gemini API key
        if keys.gemini_api_key:
            try:
                test_llm = LLMService(keys.gemini_api_key)
                test_response = await test_llm.get_response("test", "developer", web_search_enabled=False)
                validation_results["gemini"] = {"valid": True, "message": "Valid"}
            except Exception as e:
                validation_results["gemini"] = {"valid": False, "message": f"Invalid: {str(e)[:100]}"}
        else:
            validation_results["gemini"] = {"valid": False, "message": "API key required"}
        
        # Test AssemblyAI API key
        if keys.assemblyai_api_key:
            try:
                test_stt = STTService(keys.assemblyai_api_key)
                # Simple validation - just check if the key format is correct
                validation_results["assemblyai"] = {"valid": True, "message": "Valid"}
            except Exception as e:
                validation_results["assemblyai"] = {"valid": False, "message": f"Invalid: {str(e)[:100]}"}
        else:
            validation_results["assemblyai"] = {"valid": False, "message": "API key required"}
        
        # Test MURF API key
        if keys.murf_api_key:
            try:
                test_tts = TTSService(keys.murf_api_key, keys.murf_voice_id or "en-IN-aarav")
                validation_results["murf"] = {"valid": True, "message": "Valid"}
            except Exception as e:
                validation_results["murf"] = {"valid": False, "message": f"Invalid: {str(e)[:100]}"}
        else:
            validation_results["murf"] = {"valid": False, "message": "API key required"}
        
        # Test Tavily API key (optional)
        if keys.tavily_api_key:
            try:
                test_search = WebSearchService(keys.tavily_api_key)
                validation_results["tavily"] = {"valid": True, "message": "Valid"}
            except Exception as e:
                validation_results["tavily"] = {"valid": False, "message": f"Invalid: {str(e)[:100]}"}
        else:
            validation_results["tavily"] = {"valid": True, "message": "Optional - not provided"}
        
        return {
            "success": True,
            "validation_results": validation_results,
            "all_valid": all(result["valid"] for key, result in validation_results.items() if key != "tavily")
        }
        
    except Exception as e:
        logger.error(f"API key validation error: {str(e)}")
        return {
            "success": False,
            "error": f"Validation failed: {str(e)}",
            "validation_results": {},
            "all_valid": False
        }


def reinitialize_services_with_user_keys(user_keys: APIKeyConfig):
    """Reinitialize services with user-provided API keys"""
    global stt_service, llm_service, tts_service, assemblyai_streaming_service, murf_websocket_service, web_search_service
    
    try:
        # Reinitialize with user keys
        if user_keys.gemini_api_key:
            llm_service = LLMService(user_keys.gemini_api_key)
            logger.info("✅ LLM service reinitialized with user key")
        
        if user_keys.assemblyai_api_key:
            stt_service = STTService(user_keys.assemblyai_api_key)
            assemblyai_streaming_service = AssemblyAIStreamingService(user_keys.assemblyai_api_key)
            logger.info("✅ STT and streaming services reinitialized with user key")
        
        if user_keys.murf_api_key:
            voice_id = user_keys.murf_voice_id or "en-IN-aarav"
            tts_service = TTSService(user_keys.murf_api_key, voice_id)
            murf_websocket_service = MurfWebSocketService(user_keys.murf_api_key, voice_id)
            logger.info("✅ TTS and WebSocket services reinitialized with user key")
        
        if user_keys.tavily_api_key:
            web_search_service = WebSearchService(user_keys.tavily_api_key)
            logger.info("✅ Web search service reinitialized with user key")
        
        return True
        
    except Exception as e:
        logger.error(f"Service reinitialization error: {str(e)}")
        return False


        
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    def is_connected(self, websocket: WebSocket) -> bool:
        """Check if a WebSocket is still in active connections"""
        return websocket in self.active_connections

    async def send_personal_message(self, message: str, websocket: WebSocket):
        if self.is_connected(websocket):
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error sending personal message: {e}")
                # Remove from active connections immediately on send error
                if websocket in self.active_connections:
                    self.active_connections.remove(websocket)
        else:
            logger.debug("Attempted to send message to disconnected WebSocket")

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                self.disconnect(connection)


manager = ConnectionManager()

# Global locks to prevent concurrent LLM streaming for the same session
session_locks = {}
# Track which sessions are currently processing to prevent overlaps
session_processing = {}
# Track if persona changed during processing to allow force processing
session_persona_changed = {}
# Track session to context mapping for cleanup
session_contexts = {}
# Track web search enabled status per session
session_web_search = {}

async def cleanup_session_context(old_session_id: str, new_session_id: str):
    """Clean up contexts when switching between sessions"""
    global session_contexts, murf_websocket_service
    
    if not murf_websocket_service:
        return
    
    # If switching to a different session, clear the old context
    if old_session_id != new_session_id and old_session_id in session_contexts:
        old_context = session_contexts[old_session_id]
        try:
            logger.info(f"🧹 Cleaning up context {old_context} for old session {old_session_id}")
            await murf_websocket_service._clear_specific_context(old_context)
            del session_contexts[old_session_id]
        except Exception as e:
            logger.error(f"Error cleaning up context for session {old_session_id}: {str(e)}")


# Global function to handle LLM streaming (moved outside WebSocket handler to prevent duplicates)
async def handle_llm_streaming(user_message: str, session_id: str, websocket: WebSocket, persona: str = "developer", force_processing: bool = False, web_search_enabled: bool = False):
    """Handle LLM streaming response and send to Murf WebSocket for TTS"""
    
    global session_processing, session_persona_changed, session_contexts
    
    logger.info(f"🎯 Starting LLM streaming for session {session_id}: '{user_message}' with persona: {persona}, web_search: {web_search_enabled}")
    
    # Check if we're already generating LLM response for this session
    if session_id not in session_locks:
        session_locks[session_id] = asyncio.Lock()
    
    # Skip processing flag check if force_processing is True (for persona changes)
    if not force_processing:
        # Check for persona changes that might override processing flag
        persona_change_detected = session_persona_changed.get(session_id, False)
        if persona_change_detected:
            logger.info(f"🎭 Persona change detected for session {session_id}, allowing processing despite active session")
            session_persona_changed[session_id] = False  # Reset the flag
            force_processing = True
        else:
            # Additional check for processing flag
            if session_processing.get(session_id, False):
                logger.warning(f"⚠️ Session {session_id} is already processing a request, skipping: '{user_message}' (processing flag: {session_processing.get(session_id)})")
                return
            
            # Use a non-blocking check - if LLM is busy, skip this request  
            if session_locks[session_id].locked():
                logger.warning(f"⚠️ Session {session_id} LLM is currently generating response, skipping: '{user_message}' (lock: {session_locks[session_id].locked()})")
                return
    
    if force_processing:
        logger.info(f"🔄 Force processing enabled for session {session_id} - persona change detected")
        # For force processing, we still respect the lock but allow processing flag override
        if session_processing.get(session_id, False):
            logger.info(f"⏳ Force processing will wait for current request to complete for session {session_id}")
    
    # Set processing flag
    session_processing[session_id] = True
    logger.info(f"🔒 Set processing flag for session {session_id}: '{user_message}'")
    
    # Initialize variables at function scope
    accumulated_response = ""
    audio_chunk_count = 0
    total_audio_size = 0
    web_search_results = None
    
    try:
        # Get chat history
        try:
            if not database_service:
                chat_history = []
            else:
                chat_history = await database_service.get_chat_history(session_id)
                # Save user message to chat history
                save_success = await database_service.add_message_to_history(session_id, "user", user_message)
        except Exception as e:
            logger.error(f"Chat history error: {str(e)}")
            chat_history = []
        
        # Initialize web search results
        web_search_results = None
        search_results = None  # Store actual search results for sources
        
        # Perform web search if enabled
        if web_search_enabled and web_search_service and web_search_service.is_configured():
            try:
                logger.info(f"🔍 Performing web search for: '{user_message}'")
                
                # Send web search status to client
                search_status_message = {
                    "type": "web_search_start",
                    "message": f"Searching the web for: {user_message}",
                    "query": user_message,
                    "timestamp": datetime.now().isoformat()
                }
                await manager.send_personal_message(json.dumps(search_status_message), websocket)
                
                search_results = await web_search_service.search_web(user_message, max_results=3)
                
                if search_results:
                    # Always format results with URLs for LLM context
                    web_search_results = web_search_service.format_search_results_for_llm(
                        search_results, 
                        show_urls=True  # Always show URLs to LLM
                    )
                    
                    logger.info(f"✅ Web search completed, found {len(search_results)} results")
                    
                    # Send web search results to client
                    search_complete_message = {
                        "type": "web_search_complete",
                        "message": f"Found {len(search_results)} web results",
                        "results": search_results,
                        "include_urls": True,  # Always include URLs now
                        "timestamp": datetime.now().isoformat()
                    }
                    await manager.send_personal_message(json.dumps(search_complete_message), websocket)
                else:
                    logger.warning(f"⚠️ No web search results found for: '{user_message}'")
                    web_search_results = None
                    
            except Exception as e:
                logger.error(f"❌ Web search error: {str(e)}")
                web_search_results = None
                search_error_message = {
                    "type": "web_search_error",
                    "message": f"Web search failed: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
                await manager.send_personal_message(json.dumps(search_error_message), websocket)
        else:
            logger.info(f"🔍 Web search disabled or not configured for this query")
            web_search_results = None
        
        # Send LLM streaming start notification
        start_message = {
            "type": "llm_streaming_start",
            "message": "LLM is generating response...",
            "user_message": user_message,
            "web_search_enabled": web_search_enabled,
            "timestamp": datetime.now().isoformat()
        }
        await manager.send_personal_message(json.dumps(start_message), websocket)
        
        # Only lock during LLM generation phase - not during TTS
        async with session_locks[session_id]:
            logger.info(f"🔒 Generating LLM response for session {session_id}: '{user_message}'")
            
            # Create async generator that yields chunks and saves to DB when complete
            async def llm_text_stream_with_save():
                nonlocal accumulated_response
                chunk_count = 0
                
                # Stream LLM response and collect chunks
                async for chunk in llm_service.generate_streaming_response(user_message, chat_history, persona, web_search_results):
                    if chunk:
                        chunk_count += 1
                        accumulated_response += chunk
                        
                        # Send chunk to client immediately
                        chunk_message = {
                            "type": "llm_streaming_chunk",
                            "chunk": chunk,
                            "accumulated_length": len(accumulated_response),
                            "timestamp": datetime.now().isoformat()
                        }
                        await manager.send_personal_message(json.dumps(chunk_message), websocket)
                        
                        # Yield chunk for TTS processing
                        yield chunk
                
                # LLM streaming is complete - save to database immediately
                if accumulated_response.strip():
                    try:
                        if database_service:
                            save_success = await database_service.add_message_to_history(session_id, "assistant", accumulated_response)
                            logger.info(f"✅ Assistant response saved to database immediately after LLM completion")
                            
                            # Send notification that response is saved
                            save_notification = {
                                "type": "response_saved",
                                "message": "Assistant response saved to database",
                                "response_length": len(accumulated_response),
                                "timestamp": datetime.now().isoformat()
                            }
                            await manager.send_personal_message(json.dumps(save_notification), websocket)
                    except Exception as e:
                        logger.error(f"Failed to save assistant response to database immediately: {str(e)}")
                else:
                    logger.error(f"❌ Empty accumulated response for: '{user_message}'")
                    raise Exception("Empty response from LLM stream")
            
            # Generate the text stream but don't start TTS yet
            text_generator = llm_text_stream_with_save()
            
            logger.info(f"🔓 LLM generation completed for session {session_id}, starting TTS phase (unlocked)")
        
        # TTS phase - no longer locked, other requests can be processed
        # Ensure Murf WebSocket is connected (reuse existing connection if available)
        try:
            await murf_websocket_service.ensure_connected()
            
            # Send LLM stream to Murf and receive base64 audio
            tts_start_message = {
                "type": "tts_streaming_start", 
                "message": "Starting TTS streaming with Murf WebSocket...",
                "timestamp": datetime.now().isoformat()
            }
            await manager.send_personal_message(json.dumps(tts_start_message), websocket)
            
            # Stream LLM text to Murf and get base64 audio back with timeout
            try:
                # Use asyncio.wait_for for better compatibility
                async def process_tts():
                    nonlocal audio_chunk_count, total_audio_size
                    # Pass session_id to ensure unique context per session
                    async for audio_response in murf_websocket_service.stream_text_to_audio(text_generator, session_id):
                        if audio_response["type"] == "audio_chunk":
                            audio_chunk_count += 1
                            total_audio_size += audio_response["chunk_size"]
                            
                            # Send audio data to client
                            audio_message = {
                                "type": "tts_audio_chunk",
                                "audio_base64": audio_response["audio_base64"],
                                "chunk_number": audio_response["chunk_number"],
                                "chunk_size": audio_response["chunk_size"],
                                "total_size": audio_response["total_size"],
                                "is_final": audio_response["is_final"],
                                "timestamp": audio_response["timestamp"]
                            }
                            await manager.send_personal_message(json.dumps(audio_message), websocket)
                            
                            # Check if this is the final chunk
                            if audio_response["is_final"]:
                                break
                        
                        elif audio_response["type"] == "status":
                            # Send status updates to client
                            status_message = {
                                "type": "tts_status",
                                "data": audio_response["data"],
                                "timestamp": audio_response["timestamp"]
                            }
                            await manager.send_personal_message(json.dumps(status_message), websocket)
                
                await asyncio.wait_for(process_tts(), timeout=30.0)
                
            except asyncio.TimeoutError:
                logger.error(f"TTS streaming timed out for session {session_id}")
                timeout_message = {
                    "type": "tts_streaming_timeout",
                    "message": "TTS streaming timed out - continuing without audio",
                    "timestamp": datetime.now().isoformat()
                }
                await manager.send_personal_message(json.dumps(timeout_message), websocket)
        except Exception as e:
            logger.error(f"Error with Murf WebSocket streaming: {str(e)}")
            error_message = {
                "type": "tts_streaming_error",
                "message": f"Error with Murf WebSocket: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
            await manager.send_personal_message(json.dumps(error_message), websocket)
        
        finally:
            # Don't disconnect from Murf WebSocket - keep it alive for next request
            # The connection will be reused for better performance
            pass
        
        # Send completion notification
        complete_message = {
            "type": "llm_streaming_complete",
            "message": "LLM response and TTS streaming completed",
            "complete_response": accumulated_response,
            "total_length": len(accumulated_response),
            "audio_chunks_received": audio_chunk_count,
            "total_audio_size": total_audio_size,
            "session_id": session_id,  # Include session_id in response
            "timestamp": datetime.now().isoformat()
        }
        await manager.send_personal_message(json.dumps(complete_message), websocket)
        
        logger.info(f"✅ LLM streaming and TTS completed for session {session_id}. Ready for next request.")
        
    except Exception as e:
        logger.error(f"Error in LLM streaming: {str(e)}")
        error_message = {
            "type": "llm_streaming_error",
            "message": f"Error generating LLM response: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
        await manager.send_personal_message(json.dumps(error_message), websocket)
    
    finally:
        # Track the current context for this session
        if murf_websocket_service:
            current_context = murf_websocket_service.get_current_context_id()
            if current_context:
                session_contexts[session_id] = current_context
                logger.info(f"🔗 Tracked context {current_context} for session {session_id}")
        
        # Always clear the processing flag
        logger.info(f"🧹 About to clear processing flag for session {session_id}")
        session_processing[session_id] = False
        logger.info(f"🔓 Cleared processing flag for session {session_id}")
        logger.info(f"📊 Current processing flags: {session_processing}")


@app.websocket("/ws/audio-stream")
async def audio_stream_websocket(websocket: WebSocket):
    await manager.connect(websocket)
    
    # Try to get session_id from query parameters first
    query_params = dict(websocket.query_params)
    session_id = query_params.get('session_id')
    
    if not session_id:
        session_id = str(uuid.uuid4())
    
    audio_filename = f"streamed_audio_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
    audio_filepath = os.path.join("streamed_audio", audio_filename)
    os.makedirs("streamed_audio", exist_ok=True)
    is_websocket_active = True
    last_processed_transcript = ""  # Track last processed transcript to prevent duplicates
    last_processing_time = 0  # Track when we last processed a transcript
    last_processed_persona = ""  # Track persona of last processed transcript
    current_persona = "developer"  # Default persona
    
    async def transcription_callback(transcript_data):
        nonlocal last_processed_transcript, last_processing_time, last_processed_persona
        try:
            if is_websocket_active and manager.is_connected(websocket):
                await manager.send_personal_message(json.dumps(transcript_data), websocket)
                # Only show final transcriptions and trigger LLM streaming
                if transcript_data.get("type") == "final_transcript":
                    final_text = transcript_data.get('text', '').strip()
                    
                    # Check if we have valid text
                    if not final_text or len(final_text.strip()) < 3:
                        logger.info(f"Skipping short transcript: '{final_text}'")
                        return
                    
                    # CHECK FOR API KEYS BEFORE PROCESSING
                    if not llm_service or not assemblyai_streaming_service or not murf_websocket_service:
                        logger.warning("🔒 API keys not configured - cannot process transcript")
                        error_message = {
                            "type": "api_keys_required",
                            "message": "Please configure your API keys in settings before using the voice agent",
                            "transcript": final_text,
                            "timestamp": datetime.now().isoformat()
                        }
                        await manager.send_personal_message(json.dumps(error_message), websocket)
                        return
                    
                    # Smart duplicate detection - catch variations of the same question
                    normalized_current = final_text.lower().strip('.,!?;: ')
                    normalized_last = last_processed_transcript.lower().strip('.,!?;: ')
                    
                    # Get current time
                    current_time = datetime.now().timestamp()
                    time_since_last = current_time - last_processing_time
                    
                    # Remove all punctuation and normalize spaces for better comparison
                    clean_current = re.sub(r'[^\w\s]', ' ', normalized_current)
                    clean_current = ' '.join(clean_current.split())  # Normalize whitespace
                    
                    clean_last = ''
                    if normalized_last:
                        clean_last = re.sub(r'[^\w\s]', ' ', normalized_last)
                        clean_last = ' '.join(clean_last.split())  # Normalize whitespace
                    
                    # Check for exact duplicates after cleaning - BUT allow if persona changed
                    persona_changed = (current_persona != last_processed_persona)
                    
                    # Set the persona change flag for this session if persona changed
                    if persona_changed:
                        session_persona_changed[session_id] = True
                        logger.info(f"🎭 Persona changed from '{last_processed_persona}' to '{current_persona}' - setting force processing flag")
                    
                    is_exact_duplicate = (
                        clean_current == clean_last and 
                        time_since_last < 5.0 and  # Further increased time window for exact matches
                        current_persona == last_processed_persona  # Only consider duplicate if same persona
                    )
                    
                    # Check for very similar questions (same meaning, different punctuation/capitalization)
                    is_similar_duplicate = False
                    if not is_exact_duplicate and clean_last and time_since_last < 8.0 and current_persona == last_processed_persona:  # Only check if same persona
                        # Calculate word-level similarity
                        current_words = set(clean_current.split())
                        last_words = set(clean_last.split())
                        if len(current_words) > 0 and len(last_words) > 0:
                            # Use Jaccard similarity for better comparison
                            similarity = len(current_words & last_words) / len(current_words | last_words)
                            # More aggressive similarity threshold - if 60%+ similar, consider it a duplicate
                            is_similar_duplicate = similarity >= 0.6 and time_since_last < 5.0
                            
                            # Additional check: if one is a subset of the other with high overlap
                            if not is_similar_duplicate:
                                min_words = min(len(current_words), len(last_words))
                                overlap_ratio = len(current_words & last_words) / min_words if min_words > 0 else 0
                                is_similar_duplicate = overlap_ratio >= 0.75 and time_since_last < 4.0  # More aggressive
                            
                            # Extra check for very short queries (like "who is X")
                            if not is_similar_duplicate and len(current_words) <= 4 and len(last_words) <= 4:
                                # For short queries, be even more aggressive
                                is_similar_duplicate = similarity >= 0.5 and time_since_last < 6.0
                    
                    is_duplicate = is_exact_duplicate or is_similar_duplicate
                    
                    # Log for debugging
                    if persona_changed:
                        logger.info(f"🎭 Persona changed from '{last_processed_persona}' to '{current_persona}' - allowing potential duplicate")
                    
                    if is_similar_duplicate:
                        similarity_info = f"words: {len(set(clean_current.split()) & set(clean_last.split()))}/{len(set(clean_current.split()) | set(clean_last.split()))}"
                        jaccard_sim = len(set(clean_current.split()) & set(clean_last.split())) / len(set(clean_current.split()) | set(clean_last.split())) if len(set(clean_current.split()) | set(clean_last.split())) > 0 else 0
                        logger.info(f"✋ Similar duplicate detected: '{clean_current}' vs '{clean_last}' - {similarity_info} (sim: {jaccard_sim:.2f}), time: {time_since_last:.1f}s")
                    elif is_exact_duplicate:
                        logger.info(f"✋ Exact duplicate detected: '{clean_current}' vs '{clean_last}' - time: {time_since_last:.1f}s")
                    else:
                        logger.info(f"✅ Duplicate check: '{clean_current}' vs '{clean_last}' - not duplicate, time: {time_since_last:.1f}s")
                    
                    # More flexible processing conditions
                    should_process = (
                        final_text and 
                        len(normalized_current) >= 3 and  # Minimum 3 characters
                        not is_duplicate and  # Use the comprehensive duplicate check (now persona-aware)
                        llm_service
                    )
                    
                    if should_process:
                        logger.info(f"Processing transcript: '{final_text}' (time since last: {time_since_last:.1f}s)")
                        last_processed_transcript = final_text
                        last_processing_time = current_time
                        last_processed_persona = current_persona  # Save the persona
                        
                        # Get web search enabled status from frontend (if available)
                        web_search_enabled = session_web_search.get(session_id, False)
                        
                        await handle_llm_streaming(final_text, session_id, websocket, current_persona, web_search_enabled=web_search_enabled)
                    else:
                        logger.info(f"Skipping transcript: '{final_text}' - duplicate: {is_duplicate}, persona_changed: {persona_changed}, time_since_last: {time_since_last:.1f}s")
                        
        except Exception as e:
            logger.error(f"Error sending transcription: {e}")

    try:
        if assemblyai_streaming_service:
            assemblyai_streaming_service.set_transcription_callback(transcription_callback)
            async def safe_websocket_callback(msg):
                if is_websocket_active and manager.is_connected(websocket):
                    return await manager.send_personal_message(json.dumps(msg), websocket)
                return None
            
            await assemblyai_streaming_service.start_streaming_transcription(
                websocket_callback=safe_websocket_callback
            )
        
        welcome_message = {
            "type": "audio_stream_ready",
            "message": "Audio streaming endpoint ready with AssemblyAI transcription. Send binary audio data.",
            "session_id": session_id,
            "audio_filename": audio_filename,
            "transcription_enabled": assemblyai_streaming_service is not None,
            "timestamp": datetime.now().isoformat()
        }
        await manager.send_personal_message(json.dumps(welcome_message), websocket)
        
        with open(audio_filepath, "wb") as audio_file:
            chunk_count = 0
            total_bytes = 0
            
            while True:
                try:
                    message = await websocket.receive()
                    
                    if "text" in message:
                        text_data = message["text"]
                        
                        # Try to parse as JSON first (for session_id and persona_update messages)
                        try:
                            command_data = json.loads(text_data)
                            if isinstance(command_data, dict):
                                command_type = command_data.get("type")
                                
                                if command_type == "session_id":
                                    # Update session_id if provided from frontend
                                    new_session_id = command_data.get("session_id")
                                    if new_session_id and new_session_id != session_id:
                                        logger.info(f"Updating session_id from {session_id} to {new_session_id}")
                                        old_session_id = session_id
                                        session_id = new_session_id
                                        # Clean up context for the old session
                                        await cleanup_session_context(old_session_id, new_session_id)
                                        # Update audio filename with new session ID
                                        audio_filename = f"streamed_audio_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
                                        audio_filepath = os.path.join("streamed_audio", audio_filename)
                                    
                                    # Update persona if provided from frontend
                                    new_persona = command_data.get("persona")
                                    if new_persona and new_persona != current_persona:
                                        logger.info(f"Updating persona from {current_persona} to {new_persona}")
                                        current_persona = new_persona
                                    
                                    # Update web search state if provided from frontend
                                    web_search_state = command_data.get("web_search_enabled")
                                    if web_search_state is not None:
                                        session_web_search[session_id] = web_search_state
                                        logger.info(f"🔍 Initial web search state set to: {web_search_state} for session {session_id}")
                                    
                                    continue
                                
                                elif command_type == "persona_update":
                                    # Handle real-time persona updates
                                    new_persona = command_data.get("persona")
                                    if new_persona and new_persona != current_persona:
                                        logger.info(f"Real-time persona update from {current_persona} to {new_persona}")
                                        current_persona = new_persona
                                        
                                        # Send confirmation back to client
                                        persona_response = {
                                            "type": "persona_updated",
                                            "persona": current_persona,
                                            "message": f"Persona updated to {current_persona}",
                                            "timestamp": datetime.now().isoformat()
                                        }
                                        await manager.send_personal_message(json.dumps(persona_response), websocket)
                                    continue
                                
                                elif command_type == "web_search_update":
                                    # Handle web search state updates
                                    web_search_enabled = command_data.get("web_search_enabled", False)
                                    session_web_search[session_id] = web_search_enabled
                                    logger.info(f"🔍 Web search {'enabled' if web_search_enabled else 'disabled'} for session {session_id}")
                                    
                                    # Send confirmation back to client
                                    web_search_response = {
                                        "type": "web_search_updated",
                                        "enabled": web_search_enabled,
                                        "message": f"Web search {'enabled' if web_search_enabled else 'disabled'}",
                                        "timestamp": datetime.now().isoformat()
                                    }
                                    await manager.send_personal_message(json.dumps(web_search_response), websocket)
                                    continue
                                
                                elif command_type == "web_search_toggle":
                                    # Handle web search toggle
                                    web_search_enabled = command_data.get("enabled", False)
                                    session_web_search[session_id] = web_search_enabled
                                    logger.info(f"Web search {'enabled' if web_search_enabled else 'disabled'} for session {session_id}")
                                    
                                    # Send confirmation back to client
                                    web_search_response = {
                                        "type": "web_search_toggled",
                                        "enabled": web_search_enabled,
                                        "message": f"Web search {'enabled' if web_search_enabled else 'disabled'}",
                                        "timestamp": datetime.now().isoformat()
                                    }
                                    await manager.send_personal_message(json.dumps(web_search_response), websocket)
                                    continue
                                
                                elif command_type == "api_keys_update":
                                    # Handle API keys update from frontend
                                    api_keys_data = command_data.get("api_keys", {})
                                    
                                    # Create APIKeyConfig from user data
                                    user_config = APIKeyConfig(
                                        gemini_api_key=api_keys_data.get("gemini_api_key", ""),
                                        assemblyai_api_key=api_keys_data.get("assemblyai_api_key", ""),
                                        murf_api_key=api_keys_data.get("murf_api_key", ""),
                                        murf_voice_id=api_keys_data.get("murf_voice_id", "en-IN-aarav"),
                                        tavily_api_key=api_keys_data.get("tavily_api_key", "")
                                    )
                                    
                                    # Reinitialize services with user keys
                                    success = reinitialize_services_with_user_keys(user_config)
                                    
                                    if success and assemblyai_streaming_service:
                                        # Reinitialize the streaming service with the new callback
                                        try:
                                            await assemblyai_streaming_service.stop_streaming_transcription()
                                            assemblyai_streaming_service.set_transcription_callback(transcription_callback)
                                            
                                            async def safe_websocket_callback(msg):
                                                if is_websocket_active and manager.is_connected(websocket):
                                                    return await manager.send_personal_message(json.dumps(msg), websocket)
                                                return None
                                            
                                            await assemblyai_streaming_service.start_streaming_transcription(
                                                websocket_callback=safe_websocket_callback
                                            )
                                            logger.info(f"✅ AssemblyAI streaming reinitialized for session {session_id}")
                                        except Exception as streaming_error:
                                            logger.error(f"Failed to reinitialize streaming: {streaming_error}")
                                    
                                    if success:
                                        logger.info(f"✅ Services reinitialized with user API keys for session {session_id}")
                                        response = {
                                            "type": "api_keys_updated",
                                            "success": True,
                                            "message": "API keys updated successfully",
                                            "streaming_ready": assemblyai_streaming_service is not None,
                                            "timestamp": datetime.now().isoformat()
                                        }
                                    else:
                                        logger.error(f"❌ Failed to reinitialize services with user API keys for session {session_id}")
                                        response = {
                                            "type": "api_keys_updated",
                                            "success": False,
                                            "message": "Failed to update API keys",
                                            "streaming_ready": False,
                                            "timestamp": datetime.now().isoformat()
                                        }
                                    
                                    await manager.send_personal_message(json.dumps(response), websocket)
                                    continue# Handle API keys update from user
                                    try:
                                        api_keys_data = command_data.get("api_keys", {})
                                        user_keys = APIKeyConfig(
                                            gemini_api_key=api_keys_data.get("gemini_api_key", ""),
                                            assemblyai_api_key=api_keys_data.get("assemblyai_api_key", ""),
                                            murf_api_key=api_keys_data.get("murf_api_key", ""),
                                            murf_voice_id=api_keys_data.get("murf_voice_id", "en-IN-aarav"),
                                            tavily_api_key=api_keys_data.get("tavily_api_key", ""),
                                            mongodb_url=os.getenv("MONGODB_URL")  # Keep using env for MongoDB
                                        )
                                        
                                        # Reinitialize services with user keys
                                        success = reinitialize_services_with_user_keys(user_keys)
                                        
                                        if success:
                                            logger.info("✅ Services reinitialized with user-provided API keys")
                                            response_message = "API keys updated successfully"
                                        else:
                                            logger.warning("⚠️ Some services failed to reinitialize with user keys")
                                            response_message = "API keys updated with some warnings"
                                        
                                        # Send confirmation back to client
                                        api_keys_response = {
                                            "type": "api_keys_updated",
                                            "success": success,
                                            "message": response_message,
                                            "timestamp": datetime.now().isoformat()
                                        }
                                        await manager.send_personal_message(json.dumps(api_keys_response), websocket)
                                        
                                    except Exception as e:
                                        logger.error(f"API keys update error: {str(e)}")
                                        error_response = {
                                            "type": "api_keys_error",
                                            "success": False,
                                            "message": f"Failed to update API keys: {str(e)}",
                                            "timestamp": datetime.now().isoformat()
                                        }
                                        await manager.send_personal_message(json.dumps(error_response), websocket)
                                    continue
                        except json.JSONDecodeError:
                            # Not JSON, treat as regular command
                            pass
                        
                        command = text_data
                        
                        if command == "start_streaming":
                            response = {
                                "type": "command_response",
                                "message": "Ready to receive audio chunks with real-time transcription",
                                "status": "streaming_ready"
                            }
                            await manager.send_personal_message(json.dumps(response), websocket)
                            
                        elif command == "stop_streaming":
                            response = {
                                "type": "command_response",
                                "message": "Stopping audio stream",
                                "status": "streaming_stopped"
                            }
                            await manager.send_personal_message(json.dumps(response), websocket)
                            
                            if assemblyai_streaming_service:
                                async def safe_stop_callback(msg):
                                    if manager.is_connected(websocket):
                                        return await manager.send_personal_message(json.dumps(msg), websocket)
                                    return None
                            break
                    
                    elif "bytes" in message:
                        audio_chunk = message["bytes"]
                        chunk_count += 1
                        total_bytes += len(audio_chunk)
                        
                        # Write to file
                        audio_file.write(audio_chunk)
                        
                        # Send to AssemblyAI for transcription if available
                        if assemblyai_streaming_service and is_websocket_active:
                            await assemblyai_streaming_service.send_audio_chunk(audio_chunk)
                        
                        # Send chunk confirmation to client
                        if chunk_count % 10 == 0:  # Send every 10th chunk to avoid spam
                            chunk_response = {
                                "type": "audio_chunk_received",
                                "chunk_number": chunk_count,
                                "total_bytes": total_bytes,
                                "timestamp": datetime.now().isoformat()
                            }
                            await manager.send_personal_message(json.dumps(chunk_response), websocket)
                
                except WebSocketDisconnect:
                    logger.info("WebSocket disconnected during audio streaming")
                    break
                except Exception as e:
                    logger.error(f"Error processing audio chunk: {e}")
                    break
        
        # Only send final response if WebSocket is still connected
        if manager.is_connected(websocket):
            final_response = {
                "type": "audio_stream_complete",
                "message": f"Audio stream completed. Total chunks: {chunk_count}, Total bytes: {total_bytes}",
                "session_id": session_id,
                "audio_filename": audio_filename,
                "total_chunks": chunk_count,
                "total_bytes": total_bytes,
                "timestamp": datetime.now().isoformat()
            }
            await manager.send_personal_message(json.dumps(final_response), websocket)
        
    except WebSocketDisconnect:
        is_websocket_active = False
        manager.disconnect(websocket)
    except Exception as e:
        is_websocket_active = False
        logger.error(f"Audio streaming WebSocket error: {e}")
        manager.disconnect(websocket)
    finally:
        is_websocket_active = False
        if assemblyai_streaming_service:
            await assemblyai_streaming_service.stop_streaming_transcription()


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
