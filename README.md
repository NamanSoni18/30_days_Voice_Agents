# 30 Days of Voice Agents - VoxMate - Modern Voice AI Assistant 

A sophisticated conversational AI voice agent built for the "30 Days of Voice Agents" coding challenge. This FastAPI-powered application provides real-time voice conversations with multiple AI personas, intelligent web search capabilities, and a modern responsive interface supporting both streaming and traditional interaction modes.

## 🚀 Features

### Core Functionality
- **🎙️ Real-time Speech Recognition**: Live audio streaming with AssemblyAI Universal Streaming
- **🧠 Multi-Persona AI Conversations**: Choose from Developer, Sosuke Aizen, Monkey D. Luffy, or Politician personas powered by Google Gemini
- **🔊 Streaming Text-to-Speech**: High-quality voice synthesis with real-time audio streaming using Murf AI
- **🔍 Intelligent Web Search**: Real-time web search using Tavily API with contextual integration
- **💾 Persistent Session Management**: MongoDB-powered conversation history with session switching
- **⚡ WebSocket Real-time Processing**: Instant audio processing and response generation

### Advanced AI Capabilities
- **🎭 Dynamic Persona Switching**: Real-time persona changes during conversations
- **🔄 Context-Aware Conversations**: Maintains conversation context across sessions
- **🧠 Intelligent Duplicate Detection**: Prevents processing of repeated audio inputs
- **⚡ Concurrent Processing Management**: Handles multiple simultaneous requests efficiently
- **🔄 Auto-retry Logic**: Robust error recovery and connection management
- **📊 Live Processing Status**: Real-time feedback on audio processing and AI generation

### Modern Interface Features
- **🎨 Contemporary UI**: Modern card-based interface with gradient backgrounds and animations
- **👤 Persona Selection**: Interactive persona switcher with visual indicators
- **💬 Dual Chat Interfaces**: Both modern streaming chat and legacy conversation history
- **📱 Responsive Design**: Mobile-optimized interface that works across all devices
- **🔄 Session Management**: Create new chats, switch between sessions, view conversation history
- **⚙️ Settings Modal**: User-friendly API key configuration with validation

### Technical Excellence
- **🔊 Audio Chunk Processing**: Real-time audio chunk handling with base64 encoding
- **🎵 Streaming Audio Playback**: Real-time audio chunk processing and playback
- **💾 Automatic Audio Cleanup**: Smart temporary file management and cleanup
- **🔐 Secure API Key Management**: In-browser storage with validation
- **📊 Comprehensive Logging**: Detailed logging with configurable levels
- **🛡️ Comprehensive Error Handling**: Graceful fallbacks for service failures
- **🔄 Fallback TTS Mechanisms**: Multiple TTS strategies for reliability
- **⚡ Performance Optimization**: Efficient WebSocket connection reuse and context management

## 📁 Project Structure

```
├── main.py                                 # FastAPI application with WebSocket streaming and all endpoints
├── requirements.txt                        # Python dependencies with specific versions
├── voice_agent.log                        # Application logs with configurable logging levels
├── .env                                   # Environment variables (API keys - optional)
├── .env.example                           # Example environment configuration
├── services/                              # Core service integrations
│   ├── assemblyai_streaming_service.py   # Real-time speech recognition streaming
│   ├── database_service.py               # MongoDB operations and session management
│   ├── llm_service.py                     # Google Gemini AI with multi-persona support
│   ├── murf_websocket_service.py          # Real-time text-to-speech streaming with fallbacks
│   ├── stt_service.py                     # Traditional file-based speech-to-text
│   ├── tts_service.py                     # Traditional text-to-speech conversion
│   └── web_search_service.py              # Tavily web search integration with result formatting
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
4. **Persona-Based AI Response** → Selected persona generates contextual responses
5. **Optional Web Search** → If enabled, Tavily API provides current web information
6. **Streaming TTS** → Murf WebSocket streams high-quality audio response in real-time
7. **Live Audio Playback** → Audio chunks play as they arrive for seamless experience
8. **Instant Storage** → Complete conversation immediately persisted to MongoDB
9. **UI Updates** → Real-time status updates and conversation display

### 🎨 Modern Interface Features
1. **Dual Chat Modes** → Modern streaming chat + legacy conversation history view
2. **Persona Selection** → Visual persona switcher with animated transitions
3. **Session Management** → Create new chats, switch between existing sessions
4. **Web Search Toggle** → Enable/disable web search per conversation
5. **Settings Modal** → Comprehensive API key configuration interface
6. **Responsive Design** → Mobile-optimized interface that adapts to all screen sizes

### 🔍 Intelligent Web Search Integration
- **Contextual Queries**: AI determines when current information is needed
- **Real-time Results**: Tavily API provides up-to-date web information
- **Enhanced Responses**: AI incorporates search results into persona-appropriate responses
- **Source Attribution**: Search results properly cited and referenced
- **Toggle Control**: Users can enable/disable web search functionality per conversation

## 🛠️ Technology Stack

### Backend
- **FastAPI**: High-performance async web framework
- **WebSockets**: Real-time bidirectional communication
- **Uvicorn**: ASGI server for production deployment
- **Pydantic**: Data validation and serialization
- **Motor**: Async MongoDB driver for database operations

### AI & ML Services
- **Google Gemini 1.5 Flash**: Advanced LLM for conversational AI
- **AssemblyAI**: Real-time speech recognition and transcription
- **Murf AI**: High-quality text-to-speech synthesis
- **Tavily**: Intelligent web search and content discovery

### Frontend
- **Vanilla JavaScript**: Modern ES6+ with async/await
- **HTML5 Web Audio API**: Real-time audio capture and playback
- **CSS3**: Responsive design with modern styling
- **Marked.js**: Markdown parsing and rendering
- **Highlight.js**: Code syntax highlighting

### Database & Storage
- **MongoDB**: Document-based database for session management
- **In-memory Fallback**: Graceful degradation when MongoDB unavailable
- **Temporary File System**: Efficient audio file management

### Development & Deployment
- **Python 3.7+**: Core programming language
- **Docker Ready**: Containerized deployment support
- **Environment Configuration**: Flexible API key management
- **Comprehensive Logging**: Structured logging with multiple levels

## 🏗️ System Architecture

### Real-time Audio Pipeline
1. **Audio Capture**: Browser captures microphone input via Web Audio API
2. **Streaming Transmission**: Audio chunks sent via WebSocket to backend
3. **Speech Recognition**: AssemblyAI processes audio in real-time
4. **AI Processing**: Google Gemini generates contextual responses
5. **Text-to-Speech**: Murf AI converts responses to natural speech
6. **Audio Streaming**: Real-time audio playback with base64 encoding

### WebSocket Communication Flow
```
Browser ↔ FastAPI WebSocket ↔ AssemblyAI Streaming
    ↕                    ↕
Audio Input        Speech Recognition
    ↕                    ↕
Real-time Display  ↔ Murf WebSocket TTS
    ↕                    ↕
UI Updates         Audio Output Streaming
```

### Session Management
- **Unique Session IDs**: Each conversation gets a UUID for tracking
- **Context Preservation**: Conversation history maintained across sessions
- **Persona Persistence**: AI personality settings saved per session
- **Web Search State**: Search preferences maintained per conversation
- **Automatic Cleanup**: Old sessions and temporary files cleaned up

### Error Handling & Resilience
- **Graceful Fallbacks**: Multiple TTS strategies for reliability
- **Connection Recovery**: Automatic reconnection for WebSocket failures
- **Service Degradation**: App continues functioning with partial service failures
- **User Feedback**: Real-time status updates and error notifications

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
