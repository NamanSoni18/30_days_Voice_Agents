# 30 Days of Voice Agents - Modern Voice AI Assistant

A sophisticated conversational AI voice agent built for the "30 Days of Voice Agents" coding challenge. This FastAPI-powered application provides real-time voice conversations with multiple AI personas, intelligent web search capabilities, and a modern responsive interface supporting both streaming and traditional interaction modes.

## 🚀 Features

### Core Functionality
- **🎙️ Real-time Speech Recognition**: Live audio streaming with AssemblyAI Universal Streaming
- **🧠 Multi-Persona AI Conversations**: Choose from Developer, Sosuke Aizen, Monkey D. Luffy, or Politician personas powered by Google Gemini
- **🔊 Streaming Text-to-Speech**: High-quality voice synthesis with real-time audio streaming using Murf AI
- **🔍 Intelligent Web Search**: Real-time web search using Tavily API with contextual integration
- **💾 Persistent Session Management**: MongoDB-powered conversation history with session switching
- **⚡ WebSocket Real-time Processing**: Instant audio processing and response generation

### Modern Interface Features
- ** Contemporary UI**: Modern card-based interface with gradient backgrounds and animations
- ** Persona Selection**: Interactive persona switcher with visual indicators
- **💬 Dual Chat Interfaces**: Both modern streaming chat and legacy conversation history
- **📱 Responsive Design**: Mobile-optimized interface that works across all devices
- **🔄 Session Management**: Create new chats, switch between sessions, view conversation history
- **⚙️ Settings Modal**: User-friendly API key configuration with validation

### Advanced Capabilities
- **🔍 Toggle Web Search**: Enable/disable web search functionality per conversation
- **🎵 Streaming Audio Playback**: Real-time audio chunk processing and playback
- **💬 Context-Aware Conversations**: Maintains conversation context across sessions
- **🎯 Comprehensive Error Handling**: Graceful fallbacks for service failures
- **📊 Live Status Updates**: Real-time connection and processing indicators
- **🔄 Auto-retry Logic**: Robust error recovery and connection management

## 📁 Project Structure

```
├── main.py                                 # FastAPI application with WebSocket streaming and all endpoints
├── requirements.txt                        # Python dependencies
├── voice_agent.log                        # Application logs
├── .env                                   # Environment variables (API keys)
├── .env.example                           # Example environment configuration
├── services/                              # Core service integrations
│   ├── assemblyai_streaming_service.py   # Real-time speech recognition streaming
│   ├── database_service.py               # MongoDB operations and session management
│   ├── llm_service.py                     # Google Gemini AI with multi-persona support
│   ├── murf_websocket_service.py          # Real-time text-to-speech streaming
│   ├── stt_service.py                     # Traditional file-based speech-to-text
│   ├── tts_service.py                     # Traditional text-to-speech conversion
│   └── web_search_service.py              # Tavily web search integration
├── models/
│   └── schemas.py                         # Pydantic data models and validation schemas
├── static/
│   ├── app.js                            # Modern frontend JavaScript with WebSocket handling
│   └── style.css                         # Contemporary responsive CSS styling
├── templates/
│   └── index.html                        # Modern web interface with dual chat modes
├── utils/                                # Utility modules
│   ├── constants.py                      # Error messages and application constants
│   └── logging_config.py                 # Centralized logging configuration
└── streamed_audio/                       # Storage for streamed audio sessions
    └── streamed_audio_*.wav              # Saved audio files from streaming sessions
```

## ⚙️ Setup Instructions

### Prerequisites
- **Python 3.7+** (Recommended: Python 3.9+)
- **Modern web browser** with microphone support (Chrome, Firefox, Edge)
- **MongoDB** (optional - application includes in-memory fallback)
- **Stable internet connection** for API services

### 🔑 API Keys Configuration
You have **two options** for configuring API keys:

**🎯 Recommended: In-App Configuration (No .env required)**
- Launch the application and click the ⚙️ Settings button
- Enter your API keys directly in the user-friendly modal
- Keys are stored securely in your browser's localStorage
- Real-time validation ensures your keys are working correctly
- **No environment file setup needed!**



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

# Launch the application (no .env setup required!)
python main.py

# Alternative: Use uvicorn directly
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

**📱 First Time Setup:**
1. Open **http://127.0.0.1:8000** in your browser
2. Click the ⚙️ **Settings** button in the interface
3. Enter your API keys in the modal (see API Key Setup Guide below)
4. Click **Save Settings** - you're ready to chat!

**🔄 No .env file needed** - all configuration is done through the modern web interface!

## 🎭 AI Personas

Choose from four distinct AI personalities for varied conversation experiences:

### 👨‍💻 Developer (Default)
- **Personality**: Professional, logical, and helpful software developer
- **Communication Style**: Clear, structured solutions with technical explanations
- **Best For**: Coding questions, technical discussions, problem-solving

### 👑 Sosuke Aizen (Bleach)
- **Personality**: Calm, confident, and intellectually superior
- **Communication Style**: Composed and slightly manipulative, as if everything is according to plan
- **Best For**: Philosophical discussions, strategic thinking, complex analysis

### ⚓ Monkey D. Luffy (One Piece)
- **Personality**: Boundlessly energetic and optimistic
- **Communication Style**: Simple-minded but determined, with infectious enthusiasm
- **Best For**: Motivation, creativity, fun conversations, adventure planning

### 🏛️ Politician
- **Personality**: Charismatic and diplomatic
- **Communication Style**: Persuasive speeches that inspire and unite people
- **Best For**: Public speaking, diplomatic discussions, motivational content

## 🛠️ API Endpoints

### 🌐 Web Interface
- `GET /` - Modern web application with dual-interface design

### 💬 Session & Chat Management
- `GET /api/sessions` - Get all conversation sessions
- `GET /agent/chat/{session_id}/history` - Retrieve specific session conversation history
- `DELETE /agent/chat/{session_id}/history` - Clear session conversation history

### 🔍 Web Search API  
- `POST /api/web-search` - Perform intelligent web search queries
- Returns contextual search results for AI enhancement

### 🔌 Real-time Communication
- `ws://localhost:8000/ws/audio-stream` - WebSocket for real-time audio streaming and processing

### 🔧 System & Configuration
- `GET /api/backend` - Backend health check and service status
- `POST /api/validate-keys` - Validate user-provided API keys

## 🔄 How It Works

### 🎵 Real-time Streaming Mode (Primary)
1. **WebSocket Connection** → Browser establishes secure real-time connection
2. **Live Audio Capture** → Microphone streams audio directly to server via WebSocket
3. **Real-time Transcription** → AssemblyAI Universal Streaming processes audio chunks instantly
4. **Persona-Based AI Response** → Selected persona (Developer/Aizen/Luffy/Politician) generates contextual responses
5. **Optional Web Search** → If enabled, Tavily API provides current web information
6. **Streaming TTS** → Murf WebSocket streams high-quality audio response in real-time
7. **Live Audio Playback** → Audio chunks play as they arrive for seamless experience
8. **Instant Storage** → Complete conversation immediately persisted to MongoDB
9. **UI Updates** → Real-time status updates and conversation display

### � Modern Interface Features
1. **Dual Chat Modes** → Modern streaming chat + legacy conversation history view
2. **Persona Selection** → Visual persona switcher with animated transitions
3. **Session Management** → Create new chats, switch between existing sessions
4. **Web Search Toggle** → Enable/disable web search per conversation
5. **Settings Modal** → User-friendly API key configuration with real-time validation
6. **Responsive Design** → Mobile-optimized interface that adapts to all screen sizes

### 🔍 Intelligent Web Search Integration
- **Contextual Queries**: AI determines when current information is needed
- **Real-time Results**: Tavily API provides up-to-date web information
- **Enhanced Responses**: AI incorporates search results into persona-appropriate responses
- **Source Attribution**: Search results properly cited and referenced
- **Toggle Control**: Users can enable/disable web search functionality per conversation

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

### 🎵 Audio File Management
- **Temporary Storage**: Audio files are now stored in the system's temporary directory
- **Automatic Cleanup**: Files are automatically removed after playback completion
- **Session Cleanup**: Temporary files are cleaned when switching sessions or closing the app
- **Manual Cleanup**: Use `cleanup_console_logs.ps1` script for manual cleanup
- **No Persistent Storage**: Audio files no longer accumulate in the `streamed_audio` folder
- **Memory Efficient**: Reduced disk usage with automatic temporary file management

### 🛡️ Error Handling & Resilience
- **Service Fallbacks**: Graceful degradation when external APIs fail
- **Connection Retry**: Automatic retry logic for transient failures  
- **Comprehensive Logging**: Detailed logs in `voice_agent.log`
- **User-Friendly Messages**: Clear error communication through modern UI
- **Session Recovery**: Maintains state across connection interruptions
- **API Key Validation**: Real-time validation of user-provided API keys
- **Fallback Audio**: Text-to-speech fallback messages for error scenarios

## 🎨 Interface Features

### 🖥️ Modern Design Elements
- **Gradient Backgrounds**: Contemporary visual design with animated effects
- **Card-Based Layout**: Clean, organized interface components
- **Responsive Grid**: Adapts seamlessly to desktop, tablet, and mobile
- **Smooth Animations**: Engaging transitions and micro-interactions
- **Real-time Indicators**: Live status updates and connection monitoring

### 🎛️ User Controls
- **Microphone Button**: Large, accessible voice activation control
- **Persona Selector**: Visual dropdown with character icons and descriptions
- **Web Search Toggle**: Easy enable/disable for web search functionality
- **New Chat Button**: Quick session creation and management
- **Settings Modal**: Comprehensive API key configuration interface
- **Session History**: Browse and switch between conversation sessions

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

### 🚀 Development & Deployment

### 🔧 Development Mode
```bash
# Run with auto-reload for development
python main.py

# Alternative: Use uvicorn directly with custom settings
uvicorn main:app --host 127.0.0.1 --port 8000 --reload --log-level info

# The server automatically restarts on code changes
# Access at: http://127.0.0.1:8000
```

### 📁 Project Architecture
- **Modular Services**: All AI integrations are swappable and independent
- **Async/Await**: Full asynchronous processing for optimal performance
- **Type Safety**: Pydantic models for comprehensive data validation
- **Clean Code**: Organized, production-ready codebase with minimal technical debt
- **Real-time Communication**: WebSocket-based streaming for instant interactions
- **Modern Frontend**: Vanilla JavaScript with contemporary UI patterns

### 🎯 Key Features Implemented
- **Multi-Persona AI**: Four distinct AI personalities with unique communication styles
- **Real-time Audio**: WebSocket streaming for instant voice interactions
- **Modern Interface**: Card-based responsive design with smooth animations
- **Session Management**: Persistent conversations with easy session switching
- **Flexible Configuration**: Both environment variables and in-app settings
- **Comprehensive Error Handling**: Robust fallbacks and user feedback