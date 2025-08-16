# 30 Days of Voice Agents - Modern Conversational AI Voice Agent

A sleek, production-ready conversational AI voice agent built with FastAPI, featuring a modern single-button interface, seamless voice interactions, and robust session-based chat history. Experience natural voice conversations with AI through an intuitive, streamlined interface that automatically handles the entire conversation flow.

## ✨ Features

### 🎙️ **Modern Voice Interface**
- **Single Smart Button**: Unified recording control that dynamically changes between "Start Recording", "Stop Recording", "Processing", and "Ask Another Question" states
- **Intelligent State Management**: Button adapts with visual feedback - microphone icon (🎤) for recording, stop icon (⏹️) when recording, loading icon (⏳) when processing
- **Seamless Audio Experience**: Hidden audio player with automatic playback - responses start immediately without visible controls
- **Visual Recording Feedback**: Animated pulsing button during recording with real-time timer
- **Auto-Continue Flow**: Automatically transitions to next question after audio response completes

### 🤖 **AI-Powered Conversation Engine**
- **Voice-to-Voice Pipeline**: Complete workflow from speech → text → AI processing → natural speech response
- **Context-Aware Responses**: AI remembers conversation history for natural follow-up interactions
- **Advanced Speech Recognition**: Powered by AssemblyAI for accurate transcription
- **Intelligent AI Responses**: Google Gemini 2.5 Flash generates contextual, well-formatted answers
- **Natural Voice Synthesis**: Murf AI creates lifelike speech responses in multiple voices
- **Markdown-Rich Responses**: Full formatting support including code blocks, lists, tables, and syntax highlighting

### 🔄 **Session & Memory Management**
- **Persistent Chat History**: MongoDB-backed conversation storage with session-based organization
- **Session URL Sharing**: Share conversations via URL parameters or continue previous sessions
- **Interactive History Browser**: Expandable chat history with clickable conversation cards
- **Smart Memory Fallback**: Seamless operation with in-memory storage when database is unavailable
- **Auto-Session Generation**: Intelligent session creation and management

### 🛡️ **Production-Ready Error Handling**
- **Comprehensive Fallback System**: Intelligent error detection with spoken error messages via Murf TTS
- **Auto-Recovery Mechanisms**: Smart restart logic for different error scenarios (STT, LLM, TTS, network failures)
- **Error-Specific Responses**: Tailored audio feedback for API failures, empty recordings, network issues
- **Graceful Degradation**: Continues operation even when individual services fail
- **User-Friendly Error Messages**: Clear, emoji-enhanced guidance with specific recovery actions

### 🏗️ **Clean Architecture & Code Quality**
- **Modular Design**: Separated services, models, and utilities for maintainability
- **Pydantic Models**: Type-safe request/response schemas with validation
- **Service Layer**: Isolated third-party integrations (STT, LLM, TTS, Database)
- **Centralized Logging**: Structured logging with file output and console display
- **Error Constants**: Centralized error messages and fallback handling
- **Clean Code**: Removed unused imports, followed Python best practices

### 🔌 **Real-Time Communication (NEW)**
- **WebSocket Support**: Bidirectional real-time communication between client and server
- **Connection Management**: Automatic connection tracking and cleanup
- **Echo Functionality**: Server echoes messages with enhanced metadata
- **Multi-Connection Support**: Handle multiple simultaneous WebSocket connections
- **Extensible Foundation**: Ready for future streaming and real-time features

## 📁 Project Structure

```
30 Days of Voice Agents/
├── main.py                 # FastAPI application entry point with refactored endpoints
├── requirements.txt        # Python dependencies (FastAPI, WebSockets, Murf, AssemblyAI, Gemini, MongoDB)
├── .env                   # Environment variables (API keys and configuration)
├── models/
│   └── schemas.py         # Pydantic models for request/response validation
├── services/
│   ├── stt_service.py     # Speech-to-Text service (AssemblyAI)
│   ├── llm_service.py     # Language Model service (Google Gemini)
│   ├── tts_service.py     # Text-to-Speech service (Murf AI)
│   └── database_service.py # Database operations (MongoDB with fallback)
├── utils/
│   ├── logging_config.py  # Centralized logging configuration
│   ├── constants.py       # Application constants and error messages
│   └── json_utils.py      # JSON utilities and custom encoders
├── templates/
│   └── index.html         # Modern single-page application with smart button interface
├── static/
│   ├── app.js            # Frontend JavaScript with state management and auto-recording
│   └── style.css         # Modern CSS with button animations and responsive design
├── voice_agent.log        # Application log file
└── README.md             # Project documentation
```

## 🔧 How It Works

### Refactored Architecture

The application now follows a **clean, modular architecture** for better maintainability and scalability:

#### **📋 Models Layer** (`models/`)
- **Pydantic Schemas**: Type-safe request/response models with automatic validation
- **Error Enums**: Standardized error type definitions
- **API Configuration**: Centralized API key validation and configuration

#### **🛠️ Services Layer** (`services/`)
- **STT Service**: Encapsulates AssemblyAI speech recognition logic
- **LLM Service**: Handles Google Gemini AI interactions and prompt formatting
- **TTS Service**: Manages Murf AI text-to-speech generation
- **Database Service**: MongoDB operations with automatic in-memory fallback

#### **🔧 Utils Layer** (`utils/`)
- **Logging Configuration**: Centralized logging setup with file and console output
- **Constants**: Error messages and application constants
- **JSON Utilities**: Custom encoders for datetime and other types

#### **🎯 Main Application** (`main.py`)
- **Clean FastAPI App**: Focused on routing and request handling
- **Service Orchestration**: Coordinates between different services
- **Error Handling**: Comprehensive error management with fallback responses

### Modern Voice Agent Workflow
1. **Smart Button Interface**: Single button that adapts to current state:
   - **Ready State**: Shows microphone icon 🎤 with "Start Recording"
   - **Recording State**: Changes to stop icon ⏹️ with "Stop Recording" and pulsing animation
   - **Processing State**: Displays loading icon ⏳ with "Processing..." (disabled)
   - **Completed State**: Returns to microphone icon with "Ask Another Question"

2. **Seamless Audio Flow**: 
   - User clicks the smart button to start/stop recording
   - Real-time visual feedback with animated recording indicator and timer
   - Audio automatically plays in hidden player upon completion
   - Button automatically becomes ready for next question after audio ends

3. **AI Processing Pipeline**:
   - **Speech Recognition**: AssemblyAI converts audio to text with high accuracy
   - **Context Retrieval**: System loads conversation history from MongoDB for contextual responses  
   - **AI Response Generation**: Google Gemini 2.5 Flash creates intelligent, Markdown-formatted replies
   - **Voice Synthesis**: Murf AI generates natural-sounding speech responses
   - **History Storage**: Conversation is automatically saved for future reference

4. **Advanced Error Recovery**:
   - Intelligent error detection with specific recovery strategies
   - Spoken error messages for better user experience
   - Auto-restart mechanisms for certain error types
   - Graceful fallback to alternative storage/processing methods

## 🚀 Quick Start

### Prerequisites
- Python 3.7 or higher
- A Murf AI API key ([Get one here](https://murf.ai))
- An AssemblyAI API key ([Get one here](https://www.assemblyai.com/))
- A Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))
- Modern web browser with microphone support (Chrome, Firefox, Safari, Edge)

### Installation

1. **Clone or download this repository**

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your environment**
   
   Create a `.env` file in the project root:
   ```bash
   MURF_API_KEY=your_actual_murf_api_key_here
   ASSEMBLYAI_API_KEY=your_actual_assemblyai_api_key_here
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   MURF_VOICE_ID=en-IN-aarav
   MONGODB_URL=mongodb://localhost:27017
   ```

4. **Set up MongoDB (Optional)**
   
   **Option A: Local MongoDB Installation**
   - Install MongoDB Community Server from [mongodb.com](https://www.mongodb.com/try/download/community)
   - Start MongoDB service: `mongod` (default: localhost:27017)
   
   **Option B: MongoDB Atlas (Cloud)**
   - Create a free account at [MongoDB Atlas](https://www.mongodb.com/atlas)
   - Create a cluster and get your connection string
   - Replace `MONGODB_URL` in your `.env` file with your Atlas connection string
   
   **Option C: Skip MongoDB**
   - App automatically falls back to in-memory storage if MongoDB is unavailable

5. **Run the application**
   ```bash
   python main.py
   ```

6. **Access the voice agent**
   
   Navigate to: `http://127.0.0.1:8000`
   
   **Important**: Your browser will request microphone permission. Click "Allow" to enable voice recording functionality.

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Main application interface with modern voice agent UI |
| `POST` | `/agent/chat/{session_id}` | Process voice input with session-based conversation history |
| `GET` | `/agent/chat/{session_id}/history` | Retrieve chat history for a specific session |
| `GET` | `/api/backend` | Backend connectivity test endpoint |
| `WebSocket` | `/ws` | Real-time WebSocket connection for bidirectional communication |
| `GET` | `/docs` | Interactive API documentation (Swagger UI) |
| `GET` | `/redoc` | Alternative API documentation (ReDoc) |

## 🔌 WebSocket Support (Day 15)

The application now includes **real-time WebSocket functionality** for bidirectional communication between client and server.

### WebSocket Endpoint

**Endpoint:** `ws://127.0.0.1:8000/ws`

### Features
- ✅ **Real-time Communication**: Instant bidirectional messaging
- ✅ **Connection Management**: Automatic connection tracking and cleanup
- ✅ **Echo Functionality**: Server echoes back messages with enhanced metadata
- ✅ **Connection Monitoring**: Real-time connection count and status
- ✅ **Error Handling**: Graceful disconnect handling with logging

### WebSocket Response Format

When you send a message to the WebSocket endpoint, you'll receive an enhanced echo response:

```json
{
  "type": "echo",
  "original_message": "Hello WebSocket!",
  "echo_message": "Echo: Hello WebSocket!",
  "timestamp": "2025-08-16T10:39:40.123456",
  "connection_id": 123456789,
  "total_connections": 1
}
```

### Testing with Postman

1. **Open Postman** and create a new **WebSocket Request**
2. **Connect to:** `ws://127.0.0.1:8000/ws`
3. **Send test messages:**
   - `"Hello WebSocket!"`
   - `"Testing real-time communication"`
   - `{"message": "JSON test", "type": "test"}`
4. **Observe responses** with timestamps and connection metadata
5. **Test multiple connections** to see connection count changes

### Server Logs
Monitor the terminal for WebSocket activity:
```
INFO - WebSocket connected. Total connections: 1
INFO - Received WebSocket message: Hello WebSocket!
INFO - Sent echo response back to client
INFO - WebSocket disconnected. Total connections: 0
```

### Integration Ready
This WebSocket foundation is ready for future enhancements:
- **Real-time voice streaming** (future implementation)
- **Live conversation updates**
- **Multi-user chat capabilities**
- **Real-time system notifications**

### Primary Chat Agent API (`/agent/chat/{session_id}`)

The main endpoint for session-based voice conversations with persistent history.

**Path Parameter:**
- `session_id`: Unique identifier for the chat session (automatically generated by the UI)

**Request**: Multipart form data with audio file

**Supported Audio Formats:**
- `audio/wav`, `audio/mp3`, `audio/webm`, `audio/ogg`, `audio/m4a`

**Success Response:**
```json
{
  "success": true,
  "message": "Voice chat processed successfully",
  "transcription": "What is artificial intelligence?",
  "llm_response": "**Artificial Intelligence (AI)** is a branch of computer science...",
  "audio_url": "https://murf-audio-url.com/response.mp3",
  "session_id": "session_abc123_1640995200000"
}
```

**Error Response with Fallback Audio:**
```json
{
  "success": false,
  "message": "I'm having trouble understanding your audio right now.",
  "transcription": "",
  "llm_response": "I'm having trouble understanding your audio right now. Please try speaking again clearly into your microphone.",
  "audio_url": "https://murf-fallback-audio-url.com/error_response.mp3",
  "error_type": "stt_error"
}
```

**Error Types & Recovery:**
- `api_keys_missing`: Configuration issues with guidance
- `file_error`: Audio processing problems with auto-restart
- `stt_error`: Speech recognition failures with retry
- `no_speech`: Silent recordings with auto-recovery
- `llm_error`: AI processing issues with fallback
- `tts_error`: Voice generation problems (text still shown)
- `general_error`: Network/connection issues

### Chat History API (`/agent/chat/{session_id}/history`)

Retrieve conversation history for a specific session.

**Success Response:**
```json
{
  "success": true,
  "session_id": "session_abc123_1640995200000",
  "messages": [
    {
      "role": "user",
      "content": "What is artificial intelligence?",
      "timestamp": "2023-12-01T10:30:00Z"
    },
    {
      "role": "assistant", 
      "content": "**Artificial Intelligence (AI)** is a branch of computer science...",
      "timestamp": "2023-12-01T10:30:15Z"
    }
  ],
  "message_count": 2
}
```

### Backend Test API (`/api/backend`)

**Response:**
```json
{
  "message": "🚀 This message is coming from FastAPI backend!",
  "status": "success"
}
```

## 🛠️ Technologies Used

### Backend Architecture
- **[FastAPI](https://fastapi.tiangolo.com/)**: Modern, fast web framework with automatic API documentation
- **[WebSockets](https://websockets.readthedocs.io/)**: Real-time bidirectional communication support
- **[Pydantic](https://pydantic-docs.helpmanual.io/)**: Data validation and settings management with type hints
- **Modular Services**: Clean separation of STT, LLM, TTS, and database operations
- **Centralized Logging**: Structured logging with file output and error tracking

### AI Services Integration  
- **[AssemblyAI](https://www.assemblyai.com/)**: AI-powered speech-to-text transcription service
- **[Google Gemini](https://ai.google.dev/)**: Advanced large language model for text-based AI queries (using Gemini 2.5 Flash)
- **[Murf AI](https://murf.ai)**: Text-to-speech API for natural voice generation (using "en-IN-aarav" voice)

### Data & Infrastructure
- **[MongoDB](https://www.mongodb.com/)**: NoSQL database for persistent chat history storage with Motor async driver
- **[Uvicorn](https://www.uvicorn.org/)**: Lightning-fast ASGI server for production
- **[python-dotenv](https://pypi.org/project/python-dotenv/)**: Environment variable management
- **[Jinja2](https://jinja.palletsprojects.com/)**: Template engine for dynamic HTML rendering

### Frontend
- **HTML5 & CSS3**: Modern web standards with responsive design and Markdown styling
- **Vanilla JavaScript**: Frontend interactivity with advanced audio processing
- **MediaRecorder API**: Browser-native audio recording capabilities
- **Web Audio API**: Real-time audio processing and playback
- **Blob API**: Handling recorded audio data
- **Marked.js**: Markdown parsing and rendering library
- **Highlight.js**: Syntax highlighting for code blocks

## 🎨 Frontend Features

### AI Voice Agent Interface
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **Recording Controls**: Start/Stop recording buttons with visual feedback
- **Real-time Recording Timer**: Shows recording duration (0s, 1s, 2s...)
- **Visual Recording Indicator**: Animated pulsing dot during recording
- **Advanced Loading States**: Step-by-step processing visualization showing:
  - 🎙️ Transcribing audio (converting speech to text)
  - 🔍 Analyzing question (understanding user intent)
  - 🤖 Generating response (creating AI answer)
  - 🎵 Creating speech (converting text to voice)
- **Rich Markdown Rendering**: Full support for formatted AI responses including:
  - Headers and subheaders (# ## ###)
  - **Bold** and *italic* text formatting
  - `Inline code` with syntax highlighting
  - Code blocks with professional syntax highlighting
  - Bullet points and numbered lists
  - Tables with hover effects
  - Blockquotes and horizontal rules
  - Clickable links
- **Audio Playback Controls**: Built-in HTML5 audio players with full controls
- **Transcription Display**: Shows user's original question in clean format
- **Scrollable Content**: Large AI responses with custom scrollbars
- **Error Handling**: User-friendly error messages with visual feedback
- **Microphone Permission Handling**: Clear guidance for granting microphone access
- **Audio Format Support**: Automatic format selection based on browser capabilities

## 📦 Dependencies

This project uses the following Python packages (see [`requirements.txt`](requirements.txt)):

```
fastapi==0.104.1          # Web framework for building APIs
uvicorn[standard]==0.24.0 # ASGI server for FastAPI
jinja2==3.1.2             # Template engine for HTML rendering
python-multipart==0.0.6   # For handling form data and file uploads
python-dotenv==1.0.0      # Environment variable management
murf==2.0.0               # Official Murf AI Python SDK
requests==2.31.0          # HTTP library for API calls
assemblyai==0.17.0        # AssemblyAI Python SDK for transcription
google-generativeai==0.3.2 # Google Gemini AI Python SDK
pymongo==4.6.0            # MongoDB driver for Python
motor==3.3.2              # Async MongoDB driver for FastAPI
```

### 🏗️ Architecture Benefits

The refactored codebase provides several key improvements:

- **🧩 Modularity**: Each service is self-contained and can be easily tested or replaced
- **🔒 Type Safety**: Pydantic models ensure data validation and type checking
- **📝 Maintainability**: Clear separation of concerns makes the code easier to understand and modify
- **🐛 Debugging**: Centralized logging makes it easier to track down issues
- **🚀 Scalability**: Service-based architecture allows for easier scaling and optimization
- **🧪 Testability**: Isolated services can be unit tested independently

## 🔧 Configuration

### Environment Variables

Create a [`.env`](.env) file in the project root with the following variables:

```bash
# Required: Your Murf AI API key
MURF_API_KEY=your_actual_murf_api_key_here

# Required: Your AssemblyAI API key
ASSEMBLYAI_API_KEY=your_actual_assemblyai_api_key_here

# Required: Your Google Gemini API key
GEMINI_API_KEY=your_actual_gemini_api_key_here

# Optional: Murf voice ID (defaults to "en-IN-aarav")
MURF_VOICE_ID=en-IN-aarav
```

### Getting Your API Keys

#### Murf AI API Key
1. Sign up at [Murf.ai](https://murf.ai)
2. Navigate to your account settings or API section
3. Generate or copy your API key
4. Add it to your `.env` file

#### AssemblyAI API Key
1. Sign up at [AssemblyAI.com](https://www.assemblyai.com/)
2. Go to your dashboard
3. Copy your API key
4. Add it to your `.env` file

#### Google Gemini API Key
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Create a new API key
4. Add it to your `.env` file

## 🚀 Development

### Running in Development Mode

The application runs with auto-reload enabled by default, which means it will automatically restart when you make changes to the code:

```bash
python main.py
```

### API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

## 🐛 Troubleshooting & Error Handling

### 🛡️ Built-in Error Recovery Features

This application includes **comprehensive error handling** that automatically manages failures and provides intelligent recovery:

#### **Automatic Error Detection & Recovery**
- **API Key Issues**: Detects missing or invalid API keys and provides fallback audio responses
- **Network Failures**: Handles timeout and connection errors with auto-retry mechanisms  
- **Service Outages**: Gracefully manages when individual AI services (STT/LLM/TTS) are unavailable
- **Audio Processing**: Manages microphone issues, empty recordings, and file format problems
- **MongoDB Fallback**: Automatically switches to in-memory storage when database is unavailable

#### **Error Types & Responses**
1. **🔧 `api_keys_missing`**: Configuration issues with spoken guidance to contact support
2. **🎤 `file_error`**: Audio processing problems with automatic recording restart
3. **🎯 `stt_error`**: Speech transcription failures with retry suggestions
4. **🔇 `no_speech`**: Silent recordings with auto-restart after guidance
5. **🤖 `llm_error`**: AI thinking problems with retry mechanisms
6. **🔊 `tts_error`**: Voice generation issues (text response still provided)
7. **⚠️ `general_error`**: Network/connection problems with auto-recovery

#### **Smart Recovery Mechanisms**
- **Auto-Recording Restart**: Certain errors automatically restart voice recording
- **Fallback Audio**: Every error gets a spoken response via Murf TTS
- **Progressive Retry**: Different retry strategies based on error type
- **Graceful Degradation**: App continues working even when individual services fail

### Common Issues & Solutions

#### API Key Related
1. **"The voice agent is not properly configured"** 🔧
   - **Auto-Handled**: App detects this and provides spoken error message
   - **Manual Fix**: Verify your API keys in the `.env` file
   - **What App Does**: Generates fallback audio response automatically

#### Recording & Audio Issues  
2. **"No speech detected in your audio"** 🔇
   - **Auto-Handled**: App automatically restarts recording after 3 seconds
   - **Manual Fix**: Speak clearly and check microphone
   - **What App Does**: Provides spoken guidance and auto-restarts

3. **"Having trouble understanding your audio"** 🎯  
   - **Auto-Handled**: STT error detection with automatic retry
   - **Manual Fix**: Ensure good microphone quality and quiet environment
   - **What App Does**: Gives specific guidance and restarts recording

#### AI Service Issues
4. **"AI thinking process interrupted"** 🤖
   - **Auto-Handled**: LLM error detection with retry after delay
   - **Manual Fix**: Check internet connection
   - **What App Does**: Provides spoken explanation and retry option

5. **"Voice generation issue"** 🔊
   - **Auto-Handled**: TTS failure detection, text response still shown
   - **Manual Fix**: Check Murf API status
   - **What App Does**: Displays text response even without audio

#### Network & Connection
6. **"Connection issue"** ⚠️
   - **Auto-Handled**: Network timeout detection with auto-retry
   - **Manual Fix**: Check internet connection
   - **What App Does**: Implements 60-second timeouts and smart retry

### Browser Compatibility

**Fully Supported:**
- Chrome 49+
- Firefox 25+
- Safari 14.1+
- Edge 79+

**Limited Support:**
- Internet Explorer: Not supported
- Older mobile browsers: May have limited functionality

### Logging

The application includes console logging for debugging. Check the browser console and terminal output for detailed error information.

## 📝 Usage

### Modern Voice Agent Experience
1. **Click the Smart Button**: Single button interface that shows current state:
   - 🎤 **"Start Recording"** when ready to listen
   - ⏹️ **"Stop Recording"** during recording (with pulsing animation)
   - ⏳ **"Processing..."** while AI processes your question
   - 🎤 **"Ask Another Question"** when ready for next interaction

2. **Natural Conversation Flow**:
   - Grant microphone permission when prompted
   - Speak clearly while watching the real-time timer
   - Audio response plays automatically (no visible player controls)
   - Button automatically becomes ready for your next question

3. **Advanced Processing Visualization**:
   - 🎙️ **Transcribing audio**: Speech converted to text
   - 🔍 **Analyzing question**: AI understanding context  
   - 🤖 **Generating response**: Creating comprehensive answer
   - 🎵 **Creating speech**: Converting to natural voice

4. **Rich Response Display**:
   - **Your Question**: Clear transcription of what you asked
   - **AI Response**: Markdown-formatted answer with syntax highlighting
   - **Session History**: Access previous conversations via dropdown
   - **Auto-Continue**: Seamless flow to next question

### Tips for Best Experience
- **Clear Speech**: Speak distinctly at moderate pace for best transcription
- **Good Microphone**: Use quality microphone in quiet environment
- **Stable Connection**: Ensure reliable internet for AI processing
- **Natural Questions**: Ask clear, specific questions for detailed responses

## 🆕 Key Features Highlights

### Smart Interface Design
- **Single Button Control**: Eliminates confusion with one intelligent button that adapts to context
- **Hidden Audio Player**: Clean interface with automatic audio playback - no visible controls needed
- **State-Aware Animations**: Visual feedback shows exactly what's happening at each stage
- **Seamless Flow**: From question to response to next question without manual intervention

### Session & History Management
- **URL Session Sharing**: Share specific conversations with others via URL parameters
- **Persistent Memory**: All conversations stored for future reference and context
- **Interactive History**: Browse and replay previous conversations with a click
- **Auto-Session Creation**: Intelligent session management without user intervention

### Production-Ready Reliability  
- **Comprehensive Error Handling**: Every possible failure scenario covered with appropriate recovery
- **Spoken Error Messages**: Audio feedback even when things go wrong
- **Smart Auto-Recovery**: Different recovery strategies based on error type
- **Graceful Degradation**: Continues working even when services fail

## 🤝 Contributing

Feel free to contribute to this project by:
- Reporting bugs
- Suggesting new features
- Submitting pull requests
- Improving documentation

## 📄 License

This project is open source and available under the [MIT License](LICENSE).