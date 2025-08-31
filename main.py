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
import tempfile
from datetime import datetime
from dotenv import load_dotenv

from models.schemas import (
    ChatHistoryResponse, 
    BackendStatusResponse,
    APIKeyConfig,
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


# Load environment variables
load_dotenv()
setup_logging()
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="VoxMate - AI Voice Agent",
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
    
    logger.info("[LOCKED] Services initialized in locked mode - user must provide API keys")
    
    return config


@app.on_event("startup")
async def startup_event():
    logger.info("[START] Starting Voice Agent application...")
    
    # Clean up old temporary audio files from previous sessions
    cleanup_old_temp_audio_files()
    
    config = initialize_services()
    if database_service:
        try:
            db_connected = await database_service.connect()
            if db_connected:
                logger.info("[SUCCESS] Database service connected successfully")
            else:
                logger.warning("[WARNING] Database service running in fallback mode")
        except Exception as e:
            logger.error(f"[ERROR] Database service initialization error: {e}")
    else:
        logger.error("[ERROR] Database service not initialized")
    
    # Start background safety cleanup task
    async def periodic_safety_cleanup():
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                await safety_reset_stuck_sessions()
            except Exception as e:
                logger.error(f"Error in periodic safety cleanup: {e}")
    
    asyncio.create_task(periodic_safety_cleanup())
    logger.info("[SAFETY] Started background safety cleanup task")
    
    logger.info("[SUCCESS] Application startup completed")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("[STOP] Shutting down Voice Agent application...")
    
    if database_service:
        await database_service.close()
    
    # Disconnect from Murf WebSocket on shutdown
    if murf_websocket_service and murf_websocket_service.is_connected:
        await murf_websocket_service.disconnect()
    
    logger.info("[SUCCESS] Application shutdown completed")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the welcome page"""
    return templates.TemplateResponse("welcome.html", {"request": request})


@app.get("/chat", response_class=HTMLResponse)
async def chat(request: Request):
    """Serve the main chat application page"""
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
        success_count = 0
        total_services = 0

        # Reinitialize with user keys
        if user_keys.gemini_api_key:
            total_services += 1
            try:
                llm_service = LLMService(user_keys.gemini_api_key)
                logger.info("[SUCCESS] LLM service reinitialized with user key")
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to reinitialize LLM service: {str(e)}")

        if user_keys.assemblyai_api_key:
            total_services += 1
            try:
                stt_service = STTService(user_keys.assemblyai_api_key)
                assemblyai_streaming_service = AssemblyAIStreamingService(user_keys.assemblyai_api_key)
                logger.info("[SUCCESS] STT and streaming services reinitialized with user key")
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to reinitialize STT/Streaming services: {str(e)}")

        if user_keys.murf_api_key:
            total_services += 1
            try:
                voice_id = user_keys.murf_voice_id or "en-IN-aarav"
                tts_service = TTSService(user_keys.murf_api_key, voice_id)
                murf_websocket_service = MurfWebSocketService(user_keys.murf_api_key, voice_id)
                # Note: Timeout configuration is handled internally by MurfWebSocketService
                logger.info("[SUCCESS] TTS and WebSocket services reinitialized with user key")
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to reinitialize TTS/WebSocket services: {str(e)}")

        if user_keys.tavily_api_key:
            total_services += 1
            try:
                web_search_service = WebSearchService(user_keys.tavily_api_key)
                logger.info("[SUCCESS] Web search service reinitialized with user key")
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to reinitialize Web search service: {str(e)}")

        logger.info(f"Service reinitialization: {success_count}/{total_services} services successful")
        return success_count > 0  # Return True if at least one service was successfully reinitialized

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
# Track last processed transcript per session for duplicate detection
session_last_transcript = {}
# Track last processing time per session
session_last_time = {}
# Track last processed persona per session
session_last_persona = {}
# Track active TTS tasks for cancellation
active_tts_tasks = {}
# Track session responses for fallback TTS (prevent reusing previous responses)
session_responses = {}
# Track session query queues for processing multiple queries
session_queues = {}
# Track currently processing query text per session (for duplicate detection)
session_current_query = {}
# Track response playback status to ensure one response per query (RULE 1)
session_response_played = {}
# Track response buffer clearing status to prevent replay (RULE 1)
session_buffer_cleared = {}
# Track TTS completion to prevent double processing (RULE 1)
session_tts_completed = {}
# Track unique response IDs to prevent any possibility of replay
session_response_ids = {}
# Track active TTS processing to prevent concurrent starts (RULE 1)
session_tts_active = {}

def normalize_query_text(text: str) -> str:
    """
    Normalize query text for duplicate detection
    Removes case, punctuation, and extra spacing differences
    """
    if not text:
        return ""
    
    # Convert to lowercase and remove punctuation
    normalized = re.sub(r'[^\w\s]', ' ', text.lower())
    # Normalize whitespace (multiple spaces become single space, trim)
    normalized = ' '.join(normalized.split())
    return normalized

def log_session_state(session_id: str, event: str):
    """
    Log session state for rule compliance tracking
    """
    processing = session_processing.get(session_id, False)
    queue_length = len(session_queues.get(session_id, []))
    response_played = session_response_played.get(session_id, False)
    buffer_cleared = session_buffer_cleared.get(session_id, False)
    current_query = session_current_query.get(session_id, "None")
    
    logger.info(f"🔍 RULE COMPLIANCE [{event}] Session {session_id}: processing={processing}, queue={queue_length}, played={response_played}, cleared={buffer_cleared}, query='{current_query}'")

def is_duplicate_query(session_id: str, query_text: str) -> bool:
    """
    Check if query is duplicate against:
    1. Currently processing query
    2. All queries in the session queue
    3. Recently processed queries (within session)
    4. Response already played check (RULE 1 protection)
    
    Returns True if duplicate found, False if unique
    """
    normalized_query = normalize_query_text(query_text)
    
    if not normalized_query:
        return True  # Empty queries are always duplicates
    
    # RULE 1: STRICT REPLAY PREVENTION - Check if response already played for this query 
    current_query = session_current_query.get(session_id)
    if current_query and normalize_query_text(current_query) == normalized_query:
        # If it's the same query and response is already played, it's a duplicate
        if session_response_played.get(session_id, False) or session_tts_completed.get(session_id, False):
            logger.info(f"🚫 RULE 1: Duplicate detected - response already played for query: '{query_text}'")
            return True
        logger.info(f"🚫 Duplicate detected - matches currently processing query: '{query_text}'")
        return True
    
    # Check against all queued queries
    if session_id in session_queues:
        for queued_item in session_queues[session_id]:
            queued_text = queued_item.get('text', '')
            if normalize_query_text(queued_text) == normalized_query:
                logger.info(f"🚫 Duplicate detected - matches queued query: '{query_text}'")
                return True
    
    # Check against recently processed (last transcript) - reduced time window for stricter control
    last_transcript = session_last_transcript.get(session_id, '')
    if last_transcript and normalize_query_text(last_transcript) == normalized_query:
        current_time = datetime.now().timestamp()
        last_time = session_last_time.get(session_id, 0)
        time_since_last = current_time - last_time
        
        # RULE 1: Reduced time window for stricter duplicate prevention (15 seconds instead of 30)
        if time_since_last < 15:
            logger.info(f"🚫 RULE 1: Duplicate detected - matches recent processed query: '{query_text}' (time: {time_since_last:.1f}s)")
            return True
    
    logger.info(f"✅ Unique query detected: '{query_text}'")
    return False

async def safety_reset_stuck_sessions():
    """Safety mechanism to reset sessions that might be stuck in processing state"""
    global session_processing, session_last_time
    
    current_time = datetime.now().timestamp()
    stuck_sessions = []
    
    for session_id, is_processing in session_processing.items():
        if is_processing:
            # Check if session has been processing for more than 30 seconds
            last_time = session_last_time.get(session_id, current_time)
            time_stuck = current_time - last_time
            
            if time_stuck > 30:  # 30 seconds timeout
                stuck_sessions.append(session_id)
                logger.warning(f"🚨 Session {session_id} appears stuck in processing state for {time_stuck:.1f}s - force resetting")
    
    # Reset stuck sessions
    for session_id in stuck_sessions:
        session_processing[session_id] = False
        
        # RULE 4: Clear currently processing query tracking for stuck sessions
        if session_id in session_current_query:
            del session_current_query[session_id]
        
        # RULE 1 & 4: Clear response tracking for stuck sessions to prevent replay
        if session_id in session_response_played:
            del session_response_played[session_id]
        if session_id in session_buffer_cleared:
            del session_buffer_cleared[session_id]
        
        logger.info(f"🔓 RULE 4: Force-reset processing flag and state for stuck session {session_id}")
        
        # Log queue status for debugging
        queue_length = len(session_queues.get(session_id, []))
        if queue_length > 0:
            logger.info(f"📋 Session {session_id} has {queue_length} queued items after reset")

async def cleanup_session_context(old_session_id: str, new_session_id: str):
    """Clean up contexts when switching between sessions"""
    global session_contexts, murf_websocket_service
    
    if not murf_websocket_service:
        return
    
    # If switching to a different session, clear the old context
    if old_session_id != new_session_id and old_session_id in session_contexts:
        old_context = session_contexts[old_session_id]
        try:
            logger.info(f"[CLEANUP] Cleaning up context {old_context} for old session {old_session_id}")
            await murf_websocket_service._clear_specific_context(old_context)
            del session_contexts[old_session_id]
        except Exception as e:
            logger.error(f"Error cleaning up context for session {old_session_id}: {str(e)}")


async def process_session_queue(session_id: str, websocket: WebSocket):
    """
    Process any queued queries for a session after the current one completes
    
    STRICT OPERATIONAL RULES COMPLIANCE:
    - RULE 2: FIFO processing with strict sequential order using pop(0)
    - RULE 3: Error handling with proper state reset and queue continuation  
    - RULE 4: Complete state management - ensures processing flag and buffers are properly managed
    - RULE 2: Never leaves queue blocked or stuck, always processes remaining items
    """
    global session_queues, session_processing
    
    # RULE 2: Ensure we only process if session is completely ready for next query
    if session_processing.get(session_id, False):
        logger.info(f"📋 RULE 2: Session {session_id} still processing, skipping queue processing")
        return
    
    if session_id not in session_queues or not session_queues[session_id]:
        logger.info(f"📋 RULE 2: No queued queries for session {session_id}")
        return
    
    # RULE 2: Get the next query from queue (strict FIFO order)
    next_query = session_queues[session_id].pop(0)
    logger.info(f"📋 RULE 2: Processing queued query for session {session_id}: '{next_query['text']}' (Queue length: {len(session_queues[session_id])})")
    
    # RULE 1: CRITICAL CHECK - Ensure this query hasn't been processed recently
    # This prevents duplicate processing if the same query somehow got queued multiple times
    if is_duplicate_query(session_id, next_query['text']):
        logger.warning(f"🚫 RULE 1: SKIPPING QUEUED DUPLICATE for session {session_id}: '{next_query['text']}'")
        # Continue with remaining queue items
        if session_id in session_queues and session_queues[session_id]:
            logger.info(f"🔄 RULE 2: Processing remaining {len(session_queues[session_id])} queued items after skipping duplicate")
            await process_session_queue(session_id, websocket)
        return
    
    try:
        # RULE 2: Process the queued query sequentially (wait for completion)
        # This ensures strict FIFO processing and prevents queue blocking
        await handle_llm_streaming(
            next_query['text'], 
            session_id, 
            websocket, 
            next_query['persona'], 
            web_search_enabled=next_query['web_search_enabled']
        )
        logger.info(f"✅ RULE 2: Completed queued query for session {session_id}")
    except Exception as e:
        logger.error(f"❌ RULE 3: Error processing queued query for session {session_id}: {e}")
        # RULE 3: Clear processing flag on error to prevent session lockup
        session_processing[session_id] = False
        logger.info(f"🔓 RULE 3: Processing flag cleared due to error for session {session_id}")
        
        # RULE 2: Continue processing remaining queue items even if one fails
        if session_id in session_queues and session_queues[session_id]:
            logger.info(f"🔄 RULE 2: Attempting to process remaining {len(session_queues[session_id])} queued items")
            await process_session_queue(session_id, websocket)


def cleanup_old_temp_audio_files():
    """Clean up old temporary audio files that may have been left behind"""
    try:
        temp_dir = tempfile.gettempdir()
        for filename in os.listdir(temp_dir):
            if filename.startswith("voice_agent_") and filename.endswith(".wav"):
                filepath = os.path.join(temp_dir, filename)
                try:
                    # Check if file is older than 1 hour
                    file_age = datetime.now().timestamp() - os.path.getmtime(filepath)
                    if file_age > 3600:  # 1 hour in seconds
                        os.unlink(filepath)
                        logger.info(f"[CLEANUP] Cleaned up old temporary audio file: {filename}")
                except Exception as e:
                    logger.warning(f"Failed to clean up old temp file {filename}: {str(e)}")
    except Exception as e:
        logger.warning(f"Failed to clean up temp directory: {str(e)}")


# Global function to handle LLM streaming (moved outside WebSocket handler to prevent duplicates)
async def handle_llm_streaming(user_message: str, session_id: str, websocket: WebSocket, persona: str = "developer", force_processing: bool = False, web_search_enabled: bool = False):
    """
    Handle LLM streaming response and send to Murf WebSocket for TTS
    
    STRICT SINGLE PLAYBACK RULES:
    1. SINGLE PLAYBACK GUARANTEE: Each query spoken exactly once, buffer cleared immediately after
    2. BUFFER & STATE RESET: Complete state reset before processing new query
    3. TTS HANDLING: Single fallback attempt, then buffer clear regardless of outcome
    4. QUERY LIFECYCLE: Complete lifecycle tracking with guaranteed cleanup
    5. USER EXPERIENCE: One fresh answer per query, zero duplicates or echoes
    """
    
    global session_processing, session_persona_changed, session_contexts, session_last_transcript, session_last_time, session_last_persona, session_current_query, session_response_played, session_buffer_cleared, session_response_ids, session_tts_completed
    
    logger.info(f"[TARGET] Starting LLM streaming for session {session_id}: '{user_message}' with persona: {persona}, web_search: {web_search_enabled}")
    
    # RULE 1: Check for duplicates before processing
    if is_duplicate_query(session_id, user_message):
        logger.info(f"🚫 DUPLICATE QUERY REJECTED for session {session_id}: '{user_message}'")
        return
    
    # RULE 2: COMPLETE BUFFER & STATE RESET before processing new query
    unique_response_id = f"{session_id}_{datetime.now().timestamp()}_{hash(user_message)}"
    session_response_played[session_id] = False
    session_buffer_cleared[session_id] = False
    session_tts_completed[session_id] = False
    session_tts_active[session_id] = False
    session_response_ids[session_id] = unique_response_id
    
    # RULE 2: Ensure response buffer is completely clear before starting
    if session_id in session_responses:
        logger.info(f"🧹 RULE 2: Force clearing previous response buffer for session {session_id}")
        del session_responses[session_id]
    session_responses[session_id] = ""  # Initialize fresh buffer
    
    # Track currently processing query for duplicate detection
    session_current_query[session_id] = user_message
    
    logger.info(f"✅ RULE 2: Complete state reset completed for session {session_id}, response_id: {unique_response_id}")
    session_current_query[session_id] = user_message
    
    log_session_state(session_id, "STATE_INITIALIZED")
    
    # Check if we're already generating LLM response for this session
    if session_id not in session_locks:
        session_locks[session_id] = asyncio.Lock()
    
    # CANCEL ANY ACTIVE TTS TASKS FOR THIS SESSION BEFORE STARTING NEW ONE
    if session_id in active_tts_tasks and not active_tts_tasks[session_id].done():
        logger.info(f"[CANCEL] Cancelling active TTS task for session {session_id} before starting new query")
        try:
            active_tts_tasks[session_id].cancel()
            await active_tts_tasks[session_id]
        except asyncio.CancelledError:
            logger.info(f"[CANCEL] Previous TTS task cancelled successfully for session {session_id}")
        except Exception as e:
            logger.warning(f"[CANCEL] Error cancelling previous TTS task: {e}")
        finally:
            if session_id in active_tts_tasks:
                del active_tts_tasks[session_id]

        # Send audio stop message to client to stop any playing audio
        audio_stop_message = {
            "type": "audio_stop",
            "message": "Stopping previous audio for new query",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }
        await manager.send_personal_message(json.dumps(audio_stop_message), websocket)
    
    # Skip processing flag check if force_processing is True (for persona changes)
    if not force_processing:
        # Check for persona changes that might override processing flag
        persona_change_detected = session_persona_changed.get(session_id, False)
        if persona_change_detected:
            logger.info(f"[PERSONA] Persona change detected for session {session_id}, allowing processing despite active session")
            session_persona_changed[session_id] = False  # Reset the flag
            force_processing = True
        else:
            # Additional check for processing flag
            current_processing_flag = session_processing.get(session_id, False)
            logger.info(f"[CHECK] Processing flag check for session {session_id}: {current_processing_flag}, force_processing: {force_processing}")
            if current_processing_flag:
                logger.info(f"[INFO] Session {session_id} is already processing, but allowing new request: '{user_message}'")
                # Don't return - allow the request to proceed, let duplicate detection handle conflicts

            # Use a non-blocking check - if LLM is busy, still allow but log
            if session_locks[session_id].locked():
                logger.info(f"[INFO] Session {session_id} LLM is currently busy, but allowing new request: '{user_message}'")
    
    if force_processing:
        logger.info(f"🔄 Force processing enabled for session {session_id} - persona change detected")
        # For force processing, we still respect the lock but allow processing flag override
        if session_processing.get(session_id, False):
            logger.info(f"⏳ Force processing will wait for current request to complete for session {session_id}")
    
    # Set processing flag
    session_processing[session_id] = True
    logger.info(f"🔒 Set processing flag for session {session_id}: '{user_message}'")
    logger.info(f"📊 Processing flags after setting: {session_processing}")
    
    log_session_state(session_id, "PROCESSING_STARTED")
    
    # Initialize variables at function scope
    accumulated_response = ""
    audio_chunk_count = 0
    total_audio_size = 0
    
    # RULE 1: Ensure response buffer is completely clear before starting
    if session_id in session_responses:
        logger.info(f"🧹 RULE 1: Clearing previous response buffer for session {session_id}")
        del session_responses[session_id]
    session_responses[session_id] = ""  # Initialize fresh buffer
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
        
        # Simple duplicate detection - only check exact matches within 2 seconds
        # Get last processed transcript from session storage
        last_processed_transcript = session_last_transcript.get(session_id, "")
        last_processing_time = session_last_time.get(session_id, 0)
        
        # Get current time
        current_time = datetime.now().timestamp()
        time_since_last = current_time - last_processing_time
        
        # Clean the current message for comparison
        normalized_current = user_message.lower().strip('.,!?;: ')
        clean_current = re.sub(r'[^\w\s]', ' ', normalized_current)
        clean_current = ' '.join(clean_current.split())  # Normalize whitespace
        
        # Clean the last message for comparison
        normalized_last = last_processed_transcript.lower().strip('.,!?;: ')
        clean_last = ''
        if normalized_last:
            clean_last = re.sub(r'[^\w\s]', ' ', normalized_last)
            clean_last = ' '.join(clean_last.split())  # Normalize whitespace
        
        # Simple exact duplicate check
        is_exact_duplicate = (
            clean_current == clean_last and 
            time_since_last < 2.0  # 2 seconds for exact matches
        )
        
        logger.info(f"[SUCCESS] Duplicate check: '{clean_current}' vs '{clean_last}' - not duplicate, time: {time_since_last:.1f}s")
        
        # If this is a duplicate, clear the processing flag and return
        if is_exact_duplicate:
            logger.info(f"🚫 Exact duplicate detected, clearing processing flag for session {session_id}")
            session_processing[session_id] = False
            return
        
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
                    
                    logger.info(f"[SUCCESS] Web search completed, found {len(search_results)} results")
                    
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
        
        # Update session tracking variables for duplicate detection
        current_time = datetime.now().timestamp()
        session_last_transcript[session_id] = user_message
        session_last_time[session_id] = current_time
        session_last_persona[session_id] = persona
        logger.info(f"📝 Updated session tracking for {session_id}: transcript='{user_message[:50]}...', persona='{persona}'")
        
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
                        
                        # Store current response in session tracking for fallback TTS
                        session_responses[session_id] = accumulated_response
                        
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
                            logger.info(f"[SUCCESS] Assistant response saved to database immediately after LLM completion")
                            
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
        # RULE 1: CRITICAL CHECK - Prevent TTS if already active, played, or completed
        if (session_tts_active.get(session_id, False) or
            session_response_played.get(session_id, False) or 
            session_buffer_cleared.get(session_id, False) or 
            session_tts_completed.get(session_id, False)):
            logger.warning(f"🚫 RULE 1: PREVENTING TTS REPLAY - TTS already processed for session {session_id}")
            logger.info(f"    - TTS active: {session_tts_active.get(session_id, False)}")
            logger.info(f"    - Response played: {session_response_played.get(session_id, False)}")
            logger.info(f"    - Buffer cleared: {session_buffer_cleared.get(session_id, False)}")
            logger.info(f"    - TTS completed: {session_tts_completed.get(session_id, False)}")
            # Still need to complete the lifecycle properly
            session_processing[session_id] = False
            if session_id in session_current_query:
                del session_current_query[session_id]
            await process_session_queue(session_id, websocket)
            return
        
        # RULE 1: Mark TTS as active to prevent concurrent processing
        session_tts_active[session_id] = True
        
        # Ensure Murf WebSocket is connected (reuse existing connection if available)
        try:
            # RULE 1: FINAL CHECK - Mark TTS as starting to prevent any duplicate processing
            if session_tts_completed.get(session_id, False):
                logger.warning(f"🚫 RULE 1: TTS already completed for session {session_id}, skipping")
                session_processing[session_id] = False
                await process_session_queue(session_id, websocket)
                return
                
            logger.info(f"🔊 RULE 1: Starting TTS for session {session_id}, response_id: {session_response_ids.get(session_id, 'unknown')}")
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
                    timeout_count = 0
                    max_timeouts = 2  # Reduced from 3 to 2 for faster failure detection
                    
                    try:
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
                                
                                # RULE 1: Check if this is the final chunk - mark as played exactly once
                                if audio_response["is_final"]:
                                    session_response_played[session_id] = True
                                    session_tts_completed[session_id] = True
                                    logger.info(f"🎵 RULE 1: TTS playback completed for session {session_id}, response_id: {session_response_ids.get(session_id, 'unknown')}")
                                    
                                    # RULE 1: IMMEDIATE buffer clear after final chunk
                                    if session_id in session_responses:
                                        logger.info(f"🧹 RULE 1: Immediate buffer clear after final TTS chunk for session {session_id}")
                                        del session_responses[session_id]
                                        session_buffer_cleared[session_id] = True
                                    break
                            
                            elif audio_response["type"] == "timeout":
                                timeout_count += 1
                                logger.warning(f"TTS timeout {timeout_count}/{max_timeouts} for session {session_id}")
                                
                                if timeout_count >= max_timeouts:
                                    logger.error(f"Too many TTS timeouts ({timeout_count}) for session {session_id}")
                                    raise Exception(f"TTS streaming failed after {max_timeouts} timeouts")
                                
                                # Send timeout status to client
                                timeout_status = {
                                    "type": "tts_timeout_warning",
                                    "timeout_count": timeout_count,
                                    "max_timeouts": max_timeouts,
                                    "timestamp": audio_response["timestamp"]
                                }
                                await manager.send_personal_message(json.dumps(timeout_status), websocket)
                            
                            elif audio_response["type"] == "status":
                                # Send status updates to client
                                status_message = {
                                    "type": "tts_status",
                                    "data": audio_response["data"],
                                    "timestamp": audio_response["timestamp"]
                                }
                                await manager.send_personal_message(json.dumps(status_message), websocket)
                            
                            elif audio_response["type"] == "error":
                                logger.error(f"TTS error for session {session_id}: {audio_response['error']}")
                                raise Exception(f"TTS service error: {audio_response['error']}")
                    
                    except Exception as e:
                        logger.error(f"TTS processing error for session {session_id}: {str(e)}")
                        raise
                
                # Create and track TTS task
                tts_task = asyncio.create_task(process_tts())
                active_tts_tasks[session_id] = tts_task

                try:
                    await asyncio.wait_for(tts_task, timeout=45.0)  # Reduced to 45 seconds for better responsiveness
                finally:
                    # Clean up the task reference
                    if session_id in active_tts_tasks:
                        del active_tts_tasks[session_id]

            except asyncio.TimeoutError:
                logger.error(f"TTS streaming timed out after 45s for session {session_id}")

                # Cancel any ongoing TTS task for this session
                if session_id in active_tts_tasks:
                    logger.info(f"[CANCEL] Cancelling ongoing TTS task for session {session_id}")
                    active_tts_tasks[session_id].cancel()
                    try:
                        await active_tts_tasks[session_id]
                    except asyncio.CancelledError:
                        logger.info(f"[CANCEL] TTS task cancelled successfully for session {session_id}")
                    del active_tts_tasks[session_id]

                # Send timeout notification to client
                timeout_message = {
                    "type": "tts_timeout",
                    "message": "TTS streaming timed out, attempting fallback...",
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                }
                await manager.send_personal_message(json.dumps(timeout_message), websocket)

                # Don't clear processing flag immediately - wait for fallback to complete
                # This prevents new transcripts from being processed while fallback is running
                logger.warning(f"[CLEANUP] TTS timeout - keeping processing flag set during fallback for session {session_id}")

                # RULE 3: Single fallback attempt with strict buffer validation
                try:
                    # RULE 3: Prevent any replay - check if already played or buffer already cleared
                    current_response = session_responses.get(session_id, "").strip()
                    already_played = session_response_played.get(session_id, False)
                    already_cleared = session_buffer_cleared.get(session_id, False)
                    
                    if already_played or already_cleared:
                        logger.warning(f"🚫 RULE 1: Skipping fallback - response already played or cleared for session {session_id}")
                        raise Exception("Response already played - preventing replay per RULE 1")
                    
                    if tts_service and current_response:
                        logger.info(f"RULE 3: Single fallback TTS attempt for session {session_id}, response_id: {session_response_ids.get(session_id, 'unknown')}")
                        logger.info(f"Current response length: {len(current_response)} chars")
                        logger.info(f"Response preview: {current_response[:100]}...")
                        
                        fallback_audio_url = await tts_service.generate_speech(
                            current_response, 
                            format="MP3"
                        )
                        
                        if fallback_audio_url:
                            fallback_message = {
                                "type": "tts_fallback_audio",
                                "audio_url": fallback_audio_url,
                                "message": "Using fallback audio generation due to WebSocket timeout",
                                "response_id": session_response_ids.get(session_id, 'unknown'),
                                "timestamp": datetime.now().isoformat()
                            }
                            await manager.send_personal_message(json.dumps(fallback_message), websocket)
                            logger.info(f"[SUCCESS] RULE 3: Fallback audio generated and sent for session {session_id}")
                            
                            # RULE 1: Mark as played exactly once after fallback success
                            session_response_played[session_id] = True
                            session_tts_completed[session_id] = True
                            
                            # RULE 1: IMMEDIATE buffer clear after fallback playback
                            if session_id in session_responses:
                                logger.info(f"🧹 RULE 1: Immediate buffer clear after fallback playback for session {session_id}")
                                del session_responses[session_id]
                                session_buffer_cleared[session_id] = True
                        else:
                            raise Exception("Fallback TTS generation failed")
                    else:
                        if not current_response:
                            raise Exception("No current response available for fallback TTS")
                        else:
                            raise Exception("TTS service not available")

                    # RULE 2: Clear processing flag after successful fallback
                    logger.info(f"RULE 2: Clearing processing flag after successful fallback for session {session_id}")
                    session_processing[session_id] = False
                    
                    # RULE 4: Process any queued queries immediately after fallback success
                    await process_session_queue(session_id, websocket)

                except Exception as fallback_error:
                    logger.error(f"❌ RULE 3: Fallback TTS failed: {fallback_error}")
                    
                    # RULE 5: When uncertain, skip replaying and clear state
                    timeout_message = {
                        "type": "tts_streaming_timeout",
                        "message": "TTS streaming timed out - continuing without audio. Ready for next query.",
                        "timestamp": datetime.now().isoformat()
                    }
                    await manager.send_personal_message(json.dumps(timeout_message), websocket)

                    # RULE 3: Always clear processing flag and buffers on TTS failure
                    session_processing[session_id] = False
                    logger.info(f"🔓 RULE 3: Processing flag cleared after TTS timeout for session {session_id}")
                    
                    # RULE 1: Force clear response buffer to prevent any possibility of replay
                    if session_id in session_responses:
                        logger.info(f"🧹 RULE 1: Force clearing response buffer after TTS failure for session {session_id}")
                        del session_responses[session_id]
                    session_buffer_cleared[session_id] = True
                    session_response_played[session_id] = True  # Mark as completed to prevent retry
                    
                    # RULE 4: Always process queue even if TTS completely failed
                    await process_session_queue(session_id, websocket)
                    
                    # Send session reset notification even on failure
                    reset_message = {
                        "type": "session_reset",
                        "message": "Session ready for next query (TTS failed but system is responsive)",
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat()
                    }
                    await manager.send_personal_message(json.dumps(reset_message), websocket)
        except Exception as e:
            logger.error(f"Error with Murf WebSocket streaming: {str(e)}")
            
            # Try fallback TTS immediately when streaming fails
            try:
                # RULE 3: Use session-specific response but ensure no replay from previous queries
                current_response = session_responses.get(session_id, "").strip()
                if tts_service and current_response and not session_response_played.get(session_id, False):
                    logger.info(f"RULE 3: TTS streaming failed, attempting fallback TTS generation for session {session_id}...")
                    logger.info(f"Current response length: {len(current_response)} chars")
                    logger.info(f"Response preview: {current_response[:100]}...")
                    fallback_audio_url = await tts_service.generate_speech(
                        current_response, 
                        format="MP3"
                    )
                    
                    if fallback_audio_url:
                        fallback_message = {
                            "type": "tts_fallback_audio",
                            "audio_url": fallback_audio_url,
                            "message": "TTS streaming failed, using fallback audio generation",
                            "timestamp": datetime.now().isoformat()
                        }
                        await manager.send_personal_message(json.dumps(fallback_message), websocket)
                        logger.info("[SUCCESS] RULE 3: Fallback audio generated successfully after streaming failure")
                        
                        # RULE 1: Mark as played exactly once after fallback success
                        session_response_played[session_id] = True
                    else:
                        raise Exception("Fallback TTS also failed")
                else:
                    if not current_response:
                        raise Exception("No current response available for fallback TTS")
                    elif session_response_played.get(session_id, False):
                        raise Exception("Response already played - preventing replay per RULE 1")
                    else:
                        raise Exception("TTS service not available")
                    
            except Exception as fallback_error:
                logger.error(f"RULE 3: Fallback TTS also failed: {fallback_error}")
                error_message = {
                    "type": "tts_streaming_error",
                    "message": f"Both streaming and fallback TTS failed: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
                await manager.send_personal_message(json.dumps(error_message), websocket)
                
                # RULE 3: Clear processing flag and buffers even on total failure
                session_processing[session_id] = False
                
                # RULE 1: Clear response buffer even on total failure to prevent replay
                if session_id in session_responses:
                    logger.info(f"🧹 RULE 1: Clearing response buffer after total TTS failure for session {session_id}")
                    del session_responses[session_id]
                    session_buffer_cleared[session_id] = True
                
                # RULE 2: Process queue even on total failure
                await process_session_queue(session_id, websocket)
        
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
            "session_id": session_id,
            "response_id": session_response_ids.get(session_id, 'unknown'),
            "session_ready": True,
            "timestamp": datetime.now().isoformat()
        }
        await manager.send_personal_message(json.dumps(complete_message), websocket)
        
        # RULE 1: GUARANTEED BUFFER CLEARING - even if already cleared during TTS
        if session_id in session_responses and not session_buffer_cleared.get(session_id, False):
            logger.info(f"🧹 RULE 1: Final buffer clear after completion for session {session_id}")
            del session_responses[session_id]
            session_buffer_cleared[session_id] = True
        
        # RULE 2: Complete state reset for next query
        session_processing[session_id] = False
        
        # RULE 4: Clear all query-specific tracking
        if session_id in session_current_query:
            del session_current_query[session_id]
        
        # RULE 2: Reset state variables for next query
        session_response_played[session_id] = False
        session_buffer_cleared[session_id] = False
        session_tts_completed[session_id] = False
        session_tts_active[session_id] = False
        if session_id in session_response_ids:
            del session_response_ids[session_id]
        
        logger.info(f"🔓 RULE 2: Complete state reset for session {session_id} - ready for next request")
        
        log_session_state(session_id, "PROCESSING_COMPLETED")
        
        # RULE 2: Process any queued queries immediately (FIFO)
        await process_session_queue(session_id, websocket)
        
        # Send explicit session reset notification to UI
        reset_message = {
            "type": "session_reset",
            "message": "Session ready for next query",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }
        await manager.send_personal_message(json.dumps(reset_message), websocket)
        
        logger.info(f"[SUCCESS] RULE COMPLIANCE: LLM streaming and TTS completed for session {session_id}. State cleared, session reset and ready for next request.")
        
    except Exception as e:
        logger.error(f"Error in LLM streaming: {str(e)}")
        error_message = {
            "type": "llm_streaming_error",
            "message": f"Error generating LLM response: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
        await manager.send_personal_message(json.dumps(error_message), websocket)
        
        # RULE 3: Clear processing flag and process queue even on LLM error
        session_processing[session_id] = False
        
        # RULE 4: Clear currently processing query tracking on error
        if session_id in session_current_query:
            del session_current_query[session_id]
        
        # RULE 1: Clear response buffer even on LLM error to prevent replay
        if session_id in session_responses:
            logger.info(f"🧹 RULE 1: Clearing response buffer after LLM error for session {session_id}")
            del session_responses[session_id]
            session_buffer_cleared[session_id] = True
        
        # RULE 4: Reset playback tracking on error
        session_response_played[session_id] = False
        session_buffer_cleared[session_id] = False
        
        # RULE 2: Process queue even on LLM error 
        await process_session_queue(session_id, websocket)
    
    finally:
        # Comprehensive cleanup to ensure smooth operation
        try:
            # 1. Cancel any active TTS tasks for this session
            if session_id in active_tts_tasks and not active_tts_tasks[session_id].done():
                logger.info(f"[CLEANUP] Cancelling active TTS task for session {session_id}")
                try:
                    active_tts_tasks[session_id].cancel()
                    await active_tts_tasks[session_id]
                except asyncio.CancelledError:
                    logger.info(f"[CLEANUP] TTS task cancelled successfully for session {session_id}")
                except Exception as e:
                    logger.warning(f"[CLEANUP] Error cancelling TTS task: {e}")
                finally:
                    if session_id in active_tts_tasks:
                        del active_tts_tasks[session_id]

            # 2. Clear the Murf WebSocket context immediately after each response
            if murf_websocket_service:
                current_context = murf_websocket_service.get_current_context_id()
                if current_context:
                    logger.info(f"[CLEANUP] Clearing Murf context {current_context} for session {session_id}")
                    try:
                        await murf_websocket_service._clear_specific_context(current_context)
                        logger.info(f"[CLEANUP] Successfully cleared context {current_context}")
                    except Exception as e:
                        logger.warning(f"[CLEANUP] Error clearing context {current_context}: {e}")
                        # Force clear from internal tracking
                        murf_websocket_service.active_contexts.discard(current_context)
                        murf_websocket_service.current_context_id = None

            # 3. Clean up session tracking data (processing flag already cleared)
            # Note: Processing flag is cleared immediately after TTS completion for responsiveness
            
            # Clear any duplicate detection data to ensure fresh start
            if session_id in session_last_transcript:
                del session_last_transcript[session_id]
            if session_id in session_last_time:
                del session_last_time[session_id]
            if session_id in session_last_persona:
                del session_last_persona[session_id]
            if session_id in session_persona_changed:
                del session_persona_changed[session_id]
            if session_id in session_contexts:
                del session_contexts[session_id]
            if session_id in session_responses:
                del session_responses[session_id]
            if session_id in session_queues:
                del session_queues[session_id]
            # RULE 4: Clear currently processing query tracking  
            if session_id in session_current_query:
                del session_current_query[session_id]
            # RULE 1 & 2: Clear ALL response playback and buffer tracking
            if session_id in session_response_played:
                del session_response_played[session_id]
            if session_id in session_buffer_cleared:
                del session_buffer_cleared[session_id]
            if session_id in session_tts_completed:
                del session_tts_completed[session_id]
            if session_id in session_tts_active:
                del session_tts_active[session_id]
            if session_id in session_response_ids:
                del session_response_ids[session_id]
                del session_response_played[session_id]
            if session_id in session_buffer_cleared:
                del session_buffer_cleared[session_id]
            if session_id in session_response_ids:
                del session_response_ids[session_id]
            if session_id in session_tts_completed:
                del session_tts_completed[session_id]

            logger.info(f"🔓 RULE 2: Session {session_id} cleanup completed with all state variables cleared")
            logger.info(f"📊 Current processing flags: {session_processing}")

        except Exception as cleanup_error:
            logger.error(f"❌ Error during cleanup for session {session_id}: {cleanup_error}")
            # RULE 3: Force clear critical flags to prevent session lockup
            session_processing[session_id] = False
            if session_id in active_tts_tasks:
                del active_tts_tasks[session_id]
            if session_id in session_queues:
                del session_queues[session_id]
            if session_id in session_current_query:
                del session_current_query[session_id]
            # RULE 1 & 4: Force clear response tracking on cleanup error
            if session_id in session_response_played:
                del session_response_played[session_id]
            if session_id in session_buffer_cleared:
                del session_buffer_cleared[session_id]
            if session_id in session_tts_completed:
                del session_tts_completed[session_id]
            if session_id in session_tts_active:
                del session_tts_active[session_id]
            if session_id in session_response_ids:
                del session_response_ids[session_id]


@app.post("/cleanup/temp-audio")
async def cleanup_temp_audio():
    """Manual cleanup endpoint for temporary audio files"""
    try:
        cleanup_old_temp_audio_files()
        return {"success": True, "message": "Temporary audio files cleaned up successfully"}
    except Exception as e:
        logger.error(f"Failed to cleanup temp audio files: {str(e)}")
        return {"success": False, "message": f"Failed to cleanup: {str(e)}"}


@app.get("/debug/websocket-status")
async def get_websocket_status():
    """Debug endpoint to check WebSocket connection status"""
    try:
        status = {
            "murf_websocket": {
                "connected": murf_websocket_service.is_connected if murf_websocket_service else False,
                "current_context": murf_websocket_service.get_current_context_id() if murf_websocket_service else None,
                "active_contexts": list(murf_websocket_service.active_contexts) if murf_websocket_service else []
            },
            "assemblyai_streaming": {
                "connected": assemblyai_streaming_service.is_connected() if assemblyai_streaming_service else False
            }
        }
        return {"success": True, "status": status}
    except Exception as e:
        logger.error(f"Failed to get WebSocket status: {str(e)}")
        return {"success": False, "message": f"Failed to get status: {str(e)}"}


@app.post("/debug/test-tts")
async def test_tts(request: Request):
    """Debug endpoint to test TTS functionality"""
    try:
        data = await request.json()
        text = data.get("text", "Hello! This is a test of the TTS system.")
        
        if not murf_websocket_service:
            return {"success": False, "message": "Murf WebSocket service not available"}
        
        # Test WebSocket connection
        await murf_websocket_service.ensure_connected()
        
        # Create a simple text stream
        async def simple_text_stream():
            yield text
        
        # Test TTS streaming
        audio_chunks = []
        async for audio_response in murf_websocket_service.stream_text_to_audio(simple_text_stream()):
            if audio_response.get("type") == "audio_chunk":
                audio_chunks.append({
                    "chunk_number": audio_response.get("chunk_number"),
                    "chunk_size": audio_response.get("chunk_size"),
                    "is_final": audio_response.get("is_final")
                })
        
        return {
            "success": True, 
            "message": f"TTS test completed", 
            "audio_chunks_received": len(audio_chunks),
            "chunks_info": audio_chunks
        }
        
    except Exception as e:
        logger.error(f"TTS test failed: {str(e)}")
        return {"success": False, "message": f"TTS test failed: {str(e)}"}


@app.websocket("/ws/audio-stream")
async def audio_stream_websocket(websocket: WebSocket):
    await manager.connect(websocket)
    
    # Try to get session_id from query parameters first
    query_params = dict(websocket.query_params)
    session_id = query_params.get('session_id')
    
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Use temporary file instead of saving to streamed_audio folder
    temp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{session_id}.wav", prefix="voice_agent_")
    audio_filepath = temp_audio_file.name
    audio_filename = os.path.basename(audio_filepath)
    temp_audio_file.close()  # Close the file handle so we can open it for writing
    is_websocket_active = True
    last_processed_transcript = ""  # Track last processed transcript to prevent duplicates
    last_processing_time = datetime.now().timestamp()  # Initialize to current time to avoid huge time differences
    last_processed_persona = ""  # Track persona of last processed transcript
    current_persona = "developer"  # Default persona
    
    async def transcription_callback(transcript_data):
        nonlocal last_processed_transcript, last_processing_time, last_processed_persona
        try:
            if is_websocket_active and manager.is_connected(websocket):
                await manager.send_personal_message(json.dumps(transcript_data), websocket)

                # Only process final transcripts
                if transcript_data.get("type") == "final_transcript":
                    final_text = transcript_data.get('text', '').strip()

                    # Skip if too short
                    if len(final_text.strip()) < 3:
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

                    # RULE 1: COMPREHENSIVE DUPLICATE DETECTION
                    # Check against: currently processing + queue + recent history
                    if is_duplicate_query(session_id, final_text):
                        logger.info(f"🚫 DUPLICATE QUERY REJECTED in transcript: '{final_text}'")
                        return

                    # Also check if the session is currently processing
                    is_currently_processing = session_processing.get(session_id, False)
                    
                    # Initialize queue for this session if it doesn't exist
                    if session_id not in session_queues:
                        session_queues[session_id] = []
                    
                    if is_currently_processing:
                        # RULE 2: Add to FIFO queue (only if not duplicate)
                        queue_item = {
                            'text': final_text,
                            'persona': current_persona,
                            'web_search_enabled': session_web_search.get(session_id, False),
                            'timestamp': datetime.now().timestamp()
                        }
                        session_queues[session_id].append(queue_item)
                        queue_length = len(session_queues[session_id])
                        logger.info(f"📋 UNIQUE query added to queue for session {session_id}: '{final_text}' (Queue length: {queue_length})")
                        
                        # Send queue status to client
                        queue_message = {
                            "type": "query_queued",
                            "message": f"Query added to queue (position {queue_length})",
                            "query": final_text,
                            "queue_position": queue_length,
                            "session_id": session_id,
                            "timestamp": datetime.now().isoformat()
                        }
                        await manager.send_personal_message(json.dumps(queue_message), websocket)
                        return

                    # Process immediately if system is ready
                    current_time = datetime.now().timestamp()
                    time_since_last = current_time - last_processing_time
                    logger.info(f"📝 Processing transcript immediately: '{final_text}' (time since last: {time_since_last:.1f}s)")

                    # Get web search enabled status
                    web_search_enabled = session_web_search.get(session_id, False)

                    # RULE 3: Always answer the most recent unique query clearly and directly
                    await handle_llm_streaming(final_text, session_id, websocket, current_persona, web_search_enabled=web_search_enabled)

                    # RULE 4: Update tracking variables after successful processing
                    last_processed_transcript = final_text
                    last_processing_time = current_time
                    last_processed_persona = current_persona

                    # Also update global session tracking for consistency
                    session_last_transcript[session_id] = final_text
                    session_last_time[session_id] = current_time
                    session_last_persona[session_id] = current_persona

        except Exception as e:
            logger.error(f"Error in transcription callback: {str(e)}")

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
                                        # Note: Keep using the same temporary file for this session
                                        # as it's still the same audio stream, just with updated session ID
                                    
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
                                            logger.info(f"[SUCCESS] AssemblyAI streaming reinitialized for session {session_id}")
                                        except Exception as streaming_error:
                                            logger.error(f"Failed to reinitialize streaming: {streaming_error}")
                                    
                                    if success:
                                        logger.info(f"[SUCCESS] Services reinitialized with user API keys for session {session_id}")
                                        response = {
                                            "type": "api_keys_updated",
                                            "success": True,
                                            "message": "API keys updated successfully",
                                            "streaming_ready": assemblyai_streaming_service is not None,
                                            "timestamp": datetime.now().isoformat()
                                        }
                                    else:
                                        logger.error(f"[ERROR] Failed to reinitialize services with user API keys for session {session_id}")
                                        response = {
                                            "type": "api_keys_updated",
                                            "success": False,
                                            "message": "Failed to update API keys",
                                            "streaming_ready": False,
                                            "timestamp": datetime.now().isoformat()
                                        }
                                    
                                    await manager.send_personal_message(json.dumps(response), websocket)
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

        # Cancel any active TTS tasks for this session
        try:
            if session_id in active_tts_tasks:
                logger.info(f"[CLEANUP] Cancelling active TTS task for session {session_id}")
                active_tts_tasks[session_id].cancel()
                try:
                    await active_tts_tasks[session_id]
                except asyncio.CancelledError:
                    logger.info(f"[CLEANUP] TTS task cancelled successfully for session {session_id}")
                del active_tts_tasks[session_id]
        except Exception as e:
            logger.error(f"Error cancelling TTS task: {e}")

        # Clear processing flag
        try:
            if session_id in session_processing:
                session_processing[session_id] = False
                logger.info(f"[CLEANUP] Cleared processing flag for session {session_id}")
            # Clear session queue on disconnect
            if session_id in session_queues:
                del session_queues[session_id]
                logger.info(f"[CLEANUP] Cleared session queue for session {session_id}")
        except Exception as e:
            logger.error(f"Error clearing processing flag: {e}")

        if assemblyai_streaming_service:
            await assemblyai_streaming_service.stop_streaming_transcription()

        # Clean up temporary audio file
        try:
            if os.path.exists(audio_filepath):
                os.unlink(audio_filepath)
                logger.info(f"[CLEANUP] Cleaned up temporary audio file: {audio_filename}")
        except Exception as e:
            logger.warning(f"Failed to clean up temporary audio file {audio_filename}: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
