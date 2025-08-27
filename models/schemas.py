from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ErrorType(str, Enum):
    STT_ERROR = "stt_error"
    LLM_ERROR = "llm_error"
    TTS_ERROR = "tts_error"
    GENERAL_ERROR = "general_error"
    NO_SPEECH = "no_speech"
    API_KEYS_MISSING = "api_keys_missing"
    FILE_ERROR = "file_error"
    TIMEOUT_ERROR = "timeout_error"


class LLMQueryRequest(BaseModel):
    text: str = Field(..., description="Text to be processed by the LLM")


class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the message sender (user or assistant)")
    content: str = Field(..., description="Content of the message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp of the message")


class ChatHistoryResponse(BaseModel):
    success: bool = Field(..., description="Whether the request was successful")
    session_id: str = Field(..., description="Session ID")
    messages: List[ChatMessage] = Field(default_factory=list, description="List of chat messages")
    message_count: int = Field(..., description="Number of messages in the chat history")


class VoiceChatRequest(BaseModel):
    session_id: str = Field(..., description="Session ID for the chat")


class VoiceChatResponse(BaseModel):
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Response message")
    transcription: str = Field(default="", description="Transcribed text from audio")
    llm_response: str = Field(default="", description="Response from the LLM")
    audio_url: Optional[str] = Field(None, description="URL to the generated audio response")
    session_id: Optional[str] = Field(None, description="Session ID")
    error_type: Optional[ErrorType] = Field(None, description="Type of error if any")


class BackendStatusResponse(BaseModel):
    status: str = Field(..., description="Status of the backend")
    services: Dict[str, bool] = Field(..., description="Status of individual services")
    timestamp: str = Field(..., description="Timestamp of the status check")


class SessionStatsResponse(BaseModel):
    success: bool = Field(..., description="Whether the request was successful")
    session_id: str = Field(..., description="Session ID")
    message_count: int = Field(..., description="Total number of messages")
    created_at: Optional[datetime] = Field(None, description="Session creation timestamp")
    last_activity: Optional[datetime] = Field(None, description="Last activity timestamp")
    total_user_messages: int = Field(..., description="Number of user messages")
    total_assistant_messages: int = Field(..., description="Number of assistant messages")


class UserSessionInfo(BaseModel):
    session_id: str = Field(..., description="Session ID")
    created_at: Optional[datetime] = Field(None, description="Session creation timestamp")
    message_count: int = Field(..., description="Total number of messages")
    last_activity: Optional[datetime] = Field(None, description="Last activity timestamp")


class UserSessionsResponse(BaseModel):
    success: bool = Field(..., description="Whether the request was successful")
    sessions: List[UserSessionInfo] = Field(default_factory=list, description="List of user sessions")
    total_sessions: int = Field(..., description="Total number of sessions")


class APIKeyConfig(BaseModel):
    gemini_api_key: Optional[str] = None
    assemblyai_api_key: Optional[str] = None
    murf_api_key: Optional[str] = None
    murf_voice_id: Optional[str] = None
    mongodb_url: Optional[str] = None
    tavily_api_key: Optional[str] = None

    def validate_keys(self) -> List[str]:
        missing_keys = []
        
        if not self.gemini_api_key or self.gemini_api_key == "your_gemini_api_key_here":
            missing_keys.append("GEMINI_API_KEY")
        
        if not self.assemblyai_api_key or self.assemblyai_api_key == "your_assemblyai_api_key_here":
            missing_keys.append("ASSEMBLYAI_API_KEY")
        
        if not self.murf_api_key or self.murf_api_key == "your_murf_api_key_here":
            missing_keys.append("MURF_API_KEY")
        
        return missing_keys

    @property
    def are_keys_valid(self) -> bool:
        return len(self.validate_keys()) == 0


class WebSearchResult(BaseModel):
    title: str = Field(..., description="Title of the search result")
    snippet: str = Field(..., description="Snippet/summary of the search result")
    url: str = Field(..., description="URL of the search result")


class WebSearchResponse(BaseModel):
    success: bool = Field(..., description="Whether the web search was successful")
    query: str = Field(..., description="The search query")
    results: List[WebSearchResult] = Field(default_factory=list, description="List of search results")
    error_message: Optional[str] = Field(None, description="Error message if search failed")
