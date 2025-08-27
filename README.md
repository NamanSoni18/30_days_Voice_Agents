# 30 Days of Voice Agents - Challenge Project

An advanced conversational AI voice agent built for the "30 Days of Voice Agents" coding challenge. This FastAPI-powered application provides real-time voice conversations with intelligent web search capabilities, supporting both file upload and live streaming modes.

## 🚀 Features

### Core Functionality
- **🎙️ Speech Recognition**: Real-time and file-based audio transcription using AssemblyAI
- **🧠 AI Conversations**: Intelligent responses powered by Google Gemini AI
- **🔊 Text-to-Speech**: High-quality voice synthesis using Murf AI
- **🔍 Web Search Integration**: Real-time web search using Tavily API for up-to-date information
- **💾 Session Management**: Persistent conversation history with MongoDB
- **⚡ Real-time Processing**: Live audio streaming with instant response generation

### Interaction Modes
- **🎵 Real-time Streaming Mode**: Live microphone input with instant AI responses
- **🌐 WebSocket Communication**: Bidirectional real-time communication
- **📱 Responsive Web Interface**: Modern, mobile-friendly user interface

### Advanced Capabilities
- **🔍 Intelligent Web Search**: AI can search the web for current information
- **💬 Context-Aware Conversations**: Maintains conversation context across sessions
- **🎯 Error Handling**: Comprehensive fallback mechanisms for service failures
- **📊 Real-time Status Updates**: Live connection and processing indicators
- **🔄 Auto-retry Logic**: Robust error recovery and connection management

## 📁 Project Structure

```
├── main.py                                 # FastAPI application with all endpoints and WebSocket handlers
├── requirements.txt                        # Python dependencies
├── voice_agent.log                        # Application logs
├── services/                              # Core service integrations
│   ├── assemblyai_streaming_service.py   # Real-time speech recognition streaming
│   ├── database_service.py               # MongoDB operations and session management
│   ├── llm_service.py                     # Google Gemini AI integration
│   ├── murf_websocket_service.py          # Real-time text-to-speech streaming
│   ├── stt_service.py                     # File-based speech-to-text processing
│   ├── tts_service.py                     # Traditional text-to-speech conversion
│   └── web_search_service.py              # Tavily web search integration
├── models/
│   └── schemas.py                         # Pydantic data models and validation schemas
├── static/
│   ├── app.js                            # Frontend JavaScript with WebSocket handling
│   └── style.css                         # Modern CSS styling
├── templates/
│   └── index.html                        # Main web interface
├── utils/                                # Utility modules
│   ├── constants.py                      # Error messages and application constants
│   ├── json_utils.py                     # JSON processing utilities
│   └── logging_config.py                 # Centralized logging configuration
└── streamed_audio/                       # Storage for streamed audio sessions
    ├── streamed_audio_*.wav              # Saved audio files from streaming
```

## ⚙️ Setup Instructions

### Prerequisites
- **Python 3.7+** (Recommended: Python 3.9+)
- **Modern web browser** with microphone support (Chrome, Firefox, Edge)
- **MongoDB** (optional - application includes in-memory fallback)
- **Stable internet connection** for API services

### 🔑 Required API Keys
Create a `.env` file in the project root with the following configuration:

```env
# AI and Speech Services
GEMINI_API_KEY=your_google_gemini_api_key
ASSEMBLYAI_API_KEY=your_assemblyai_api_key
MURF_API_KEY=your_murf_api_key
MURF_VOICE_ID=en-IN-aarav

# Web Search
TAVILY_API_KEY=your_tavily_api_key

# Database (Optional)
MONGODB_URL=your_mongodb_connection_string
```

### 🔧 API Key Setup Guide
1. **Google Gemini API**: Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **AssemblyAI**: Sign up at [AssemblyAI](https://www.assemblyai.com/)
3. **Murf AI**: Register at [Murf](https://murf.ai/)
4. **Tavily Search**: Get API key from [Tavily](https://tavily.com/)
5. **MongoDB**: Use [MongoDB Atlas](https://cloud.mongodb.com/) for cloud database

### 🚀 Installation & Launch

```bash
# Clone the repository
git clone <repository-url>
cd "30 Days of Voice Agents"

# Install Python dependencies
pip install -r requirements.txt

# Create environment file
# Copy the .env template above and add your API keys

# Launch the application
python main.py
```

The application will be available at: **http://127.0.0.1:8000**

## 🛠️ API Endpoints

### 🌐 Web Interface
- `GET /` - Main application interface with voice interaction

### 💬 Voice Chat API
- `GET /agent/chat/{session_id}/history` - Retrieve conversation history
- `DELETE /agent/chat/{session_id}/history` - Clear session conversation history

### 🔍 Web Search API  
- `POST /agent/search` - Perform web search queries
- Returns real-time search results for AI context enhancement

### 🔌 WebSocket Endpoints
- `ws://localhost:8000/ws/audio-stream` - Real-time audio streaming and processing

### 🔧 System API
- `GET /api/backend` - Backend health check and service status

## 🔄 How It Works

### 📁 File Upload Mode
1. **Audio Upload** → User selects and uploads an audio file
2. **Speech Recognition** → AssemblyAI transcribes the audio to text
3. **Web Search** → If needed, AI searches for current information using Tavily
4. **AI Processing** → Google Gemini generates intelligent response
5. **Text-to-Speech** → Murf AI converts response to natural speech
6. **Storage** → Complete conversation saved to MongoDB
7. **Response** → Audio and text response returned to user

### 🎵 Real-time Streaming Mode
1. **WebSocket Connection** → Browser establishes real-time connection
2. **Live Audio Capture** → Microphone streams audio directly to server
3. **Real-time Transcription** → AssemblyAI processes audio chunks instantly
4. **Contextual AI Response** → Gemini generates responses with web search context
5. **Streaming TTS** → Murf WebSocket streams audio response in real-time
6. **Live Playback** → Audio chunks play as they arrive
7. **Instant Storage** → Conversation immediately persisted to database

### 🔍 Intelligent Web Search Integration
- **Contextual Queries**: AI determines when web search is needed
- **Real-time Results**: Tavily API provides current web information
- **Enhanced Responses**: AI incorporates search results into conversational responses
- **Source Attribution**: Search results properly cited in responses

## ⚙️ Technical Configuration

### 🎵 Audio Settings
- **Sample Rate**: 16kHz (optimized for speech recognition)
- **Format**: PCM (Pulse Code Modulation)
- **Channels**: Mono (single channel)
- **Chunk Size**: 4096 samples for optimal streaming
- **Supported Formats**: WAV, MP3, M4A, FLAC

### 🗄️ Database Schema
```python
Session Document:
{
    "_id": "unique_session_id",
    "messages": [
        {
            "role": "user|assistant",
            "content": "message_content",
            "timestamp": "ISO_datetime",
            "audio_file": "optional_audio_path"
        }
    ],
    "created_at": "ISO_datetime",
    "last_activity": "ISO_datetime"
}
```

### 🔧 Environment Configuration
```python
# Required API Keys
GEMINI_API_KEY          # Google AI language model
ASSEMBLYAI_API_KEY      # Speech recognition service  
MURF_API_KEY           # Text-to-speech synthesis
TAVILY_API_KEY         # Web search functionality
MONGODB_URL            # Database connection (fallback: in-memory)
MURF_VOICE_ID          # Voice selection (default: en-IN-aarav)
```

### 🛡️ Error Handling & Resilience
- **Service Fallbacks**: Graceful degradation when external APIs fail
- **Connection Retry**: Automatic retry logic for transient failures  
- **Comprehensive Logging**: Detailed logs in `voice_agent.log`
- **User-Friendly Messages**: Clear error communication to users
- **Session Recovery**: Maintains state across connection interruptions

## 🔧 Troubleshooting

### 🎤 Common Issues & Solutions

#### **Microphone Not Working**
- ✅ Check browser permissions (click 🔒 lock icon in address bar)
- ✅ Verify system microphone settings and default device
- ✅ Test with other applications to confirm microphone functionality
- ✅ Try different browsers (Chrome/Edge recommended)

#### **API Connection Errors**
- ✅ Verify all API keys are correctly set in `.env` file
- ✅ Check API key validity and account limits
- ✅ Ensure stable internet connection

#### **Audio Playback Issues**
- ✅ Check browser Web Audio API support
- ✅ Verify system audio output settings
- ✅ Clear browser cache and cookies
- ✅ Test with different audio formats

#### **Connection & Performance**
- ✅ Ensure all required services are accessible
- ✅ Check firewall and antivirus settings
- ✅ Monitor network latency for real-time features
- ✅ Restart application if persistent issues occur

**Log Categories:**
- 🚀 **Service initialization** and configuration status
- 🔌 **WebSocket connection** events and lifecycle
- 📞 **API call** success/failure with response times
- 🎵 **Audio processing** metrics and performance data
- 🗄️ **Database operations** and session management
- ❌ **Error tracking** with stack traces and context

### 🏥 Health Checks
Monitor application health via the status endpoint:
```bash
curl http://127.0.0.1:8000/api/backend
```

Expected healthy response:
```json
{
    "status": "healthy",
    "services": {
        "stt": "connected",
        "llm": "connected", 
        "tts": "connected",
        "database": "connected",
        "web_search": "connected"
    },
    "version": "1.0.0"
}
```

---

## 🎯 30 Days Voice Agents Challenge

This project was built as part of the **30 Days of Voice Agents** coding challenge, demonstrating:

- ✨ **Real-time voice interaction** with sub-second latency
- 🔍 **Intelligent web search** integration for current information
- 🎨 **Modern web interface** with responsive design
- 🔄 **Robust error handling** and service resilience
- 📊 **Comprehensive logging** and monitoring capabilities
- 🚀 **Production-ready architecture** with scalable design

### 🏆 Key Achievements
- **Multi-modal AI interaction** (voice, text, web search)
- **Real-time streaming** with WebSocket implementation
- **Modular architecture** for easy service integration
- **Enterprise-grade error handling** and logging
- **Mobile-responsive interface** for cross-platform usage

---

**Built with ❤️ for the Voice Agents Community**

## 🧰 Dependencies & Technology Stack

### 🔧 Backend Dependencies
```txt
fastapi==0.104.1              # Modern web framework
uvicorn[standard]==0.24.0     # ASGI server with auto-reload
websockets==12.0              # Real-time WebSocket communication
jinja2==3.1.2                 # Template engine
python-multipart==0.0.6       # File upload handling
python-dotenv==1.0.0          # Environment variable management
requests==2.31.0              # HTTP client library
```

### 🤖 AI & Voice Services
```txt
google-generativeai==0.3.2    # Google Gemini AI integration
assemblyai==0.43.1            # Speech recognition API
murf==2.0.0                   # Text-to-speech synthesis
tavily-python==0.3.3          # Web search API client
```

### 🗄️ Database & Storage
```txt
pymongo==4.6.0                # MongoDB synchronous driver
motor==3.3.2                  # MongoDB asynchronous driver
```

### 🌐 Frontend Technologies
- **Vanilla JavaScript** - No framework dependencies for maximum compatibility
- **Web Audio API** - Real-time audio processing and streaming
- **WebSocket API** - Bidirectional real-time communication
- **CSS Grid & Flexbox** - Modern responsive layout
- **Progressive Web App** features for mobile optimization

## 🚀 Development & Deployment

### 🔧 Development Mode
```bash
# Run with auto-reload for development
python main.py

# The server automatically restarts on code changes
# Access at: http://127.0.0.1:8000
```

### 📁 Project Architecture
- **Modular Services**: All integrations are swappable and independent
- **Async/Await**: Full asynchronous processing for optimal performance
- **Type Safety**: Pydantic models for data validation and serialization
- **Logging**: Centralized logging with configurable levels
- **Error Recovery**: Comprehensive error handling with user feedback

### 🧪 Testing & Quality
- **Service Isolation**: Each service can be tested independently
- **Mock Support**: Easy mocking of external API dependencies
- **Logging Integration**: Detailed logging for debugging and monitoring
- **Performance Monitoring**: Built-in metrics for response times and errors