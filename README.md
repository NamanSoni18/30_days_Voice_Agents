# 30 Days of Voice Agents - Bulletproof AI Voice Agent with Chat History

A robust, production-ready web application built with FastAPI, Murf AI, AssemblyAI, and Google Gemini that creates an intelligent AI Voice Agent with persistent chat history and **comprehensive error handling**. Record your voice questions and get AI-powered responses with natural text-to-speech playback! This project demonstrates seamless integration between speech-to-text, large language models, text-to-speech AI services, MongoDB for conversation memory, and **bulletproof error recovery systems**.

## ✨ Features

### 🛡️ **NEW: Bulletproof Error Handling & Recovery**
- **Intelligent Fallback Audio**: When any API fails, get spoken error messages via Murf TTS
- **Graceful API Failure Recovery**: Handles STT, LLM, and TTS failures independently with specific error types
- **Auto-Recovery Mechanisms**: Automatically restarts recording after certain error types
- **Smart Error Detection**: Identifies missing API keys, wrong credentials, network issues, and more
- **User-Friendly Error Messages**: Clear, emoji-enhanced messages with specific guidance
- **Fallback Response Generation**: Even when TTS fails, text responses are still displayed
- **Network Timeout Handling**: 60-second request timeouts with abort controllers
- **Error Type Classification**: Different handling for `api_keys_missing`, `stt_error`, `tts_error`, `llm_error`, `no_speech`, `file_error`, `general_error`
- **Comprehensive Logging**: Detailed server-side logging for debugging and monitoring
- **Production-Ready Resilience**: Continues operation even when individual services fail

### 🤖 AI Voice Agent with Memory
- **Voice Recording**: Record audio questions directly from your microphone using browser's MediaRecorder API
- **Real-time Timer**: See recording duration with a visual recording indicator and pulsing animation
- **AI Transcription**: Convert your speech to text using AssemblyAI's advanced speech recognition
- **Smart AI Responses**: Get intelligent, well-formatted answers from Google Gemini with conversation context
- **Natural Voice Playback**: Hear responses in natural-sounding voices using Murf AI text-to-speech
- **Complete Voice Loop**: Record → Transcribe → Process with AI → Generate Speech → Play back
- **Advanced Loading States**: Step-by-step visual feedback showing transcription, analysis, generation, and speech creation
- **💾 Chat History**: Persistent conversation history stored in MongoDB with session-based tracking
- **🔄 Auto-Recording**: Automatically starts recording for next question after AI response playback ends
- **🗨️ Contextual Conversations**: AI remembers previous messages for more natural follow-up interactions
- **📁 Session Management**: Share sessions via URL parameters or continue previous conversations
- **🔍 Interactive History**: Click on previous conversation cards to replay them in the main interface
- **🛡️ Fallback Storage**: Seamless operation with in-memory storage when MongoDB is unavailable

### 🎨 Advanced UI Features
- **Markdown Rendering**: Rich text formatting with support for:
  - **Bold** and *italic* text formatting
  - `Inline code` and code blocks with syntax highlighting
  - Bullet points and numbered lists
  - Headers and subheaders
  - Tables and blockquotes
  - Horizontal rules and links
- **Real-time Processing Feedback**: Visual step-by-step progress indicator showing:
  - 🎙️ Transcribing audio
  - 🔍 Analyzing question  
  - 🤖 Generating response
  - 🎵 Creating speech
- **Session Information Display**: Clear visibility of current session ID with management controls
- **Chat History Dropdown**: Collapsible conversation history with organized message cards
- **Interactive Conversation Cards**: Click on any previous conversation to replay it
- **Responsive Design**: Optimized for desktop, tablet, and mobile devices
- **Loading Animations**: Professional spinning loaders and animated progress indicators
- **Error Handling**: Comprehensive error messages with visual feedback and **intelligent recovery**
- **🛡️ Fallback Audio Responses**: Spoken error messages when APIs fail
- **⚡ Auto-Recovery**: Smart restart mechanisms for recording and processing
- **🔧 Production-Ready**: Handles API failures, network issues, and edge cases gracefully

### 🔧 Technical Features
- **FastAPI Backend**: High-performance async Python web framework with automatic API documentation
- **MongoDB Integration**: Robust chat history storage with automatic fallback to in-memory storage
- **Session-based API**: RESTful endpoints supporting session-specific operations (`/agent/chat/{session_id}`)
- **Modern JavaScript**: Clean, vanilla JavaScript with advanced audio processing and session management
- **Cross-browser Support**: Works on Chrome, Firefox, Safari, and other modern browsers
- **Environment-based Configuration**: Secure API key management for all services
- **No File Storage**: Direct audio processing without saving files on server
- **Syntax Highlighting**: Code blocks with professional highlighting using Highlight.js
- **URL Session Parameters**: Share conversations via URL with session_id parameter
- **Memory Management**: Intelligent context windowing to maintain performance with long conversations
- **🛡️ Advanced Error Handling**: Comprehensive try-catch blocks with specific error types and fallback responses
- **🔄 Smart Recovery**: Auto-restart mechanisms for different failure scenarios
- **📊 Detailed Logging**: Production-ready logging with traceback information
- **⏱️ Timeout Management**: Request timeouts with abort controllers for better UX
- **🎯 Error Classification**: Specific handling for API keys, STT, LLM, TTS, and network failures

## 📁 Project Structure

```
30 Days of Voice Agents/
├── main.py                 # FastAPI backend server with AI Voice Agent and chat history endpoints
├── requirements.txt        # Python dependencies (FastAPI, Murf, AssemblyAI, Gemini, MongoDB)
├── .env                   # Environment variables (API keys and MongoDB connection)
├── .env.example           # Example environment configuration with MongoDB setup
├── .gitignore             # Git ignore patterns
├── templates/
│   └── index.html         # Main HTML page with Voice Agent interface, session management, and chat history
├── static/
│   ├── app.js            # Frontend JavaScript for recording, processing, session management, and chat history
│   └── style.css         # CSS styles with Markdown formatting, loading animations, and chat history UI
├── __pycache__/           # Python bytecode cache
└── README.md             # Project documentation
```

## 🔧 How It Works

### AI Voice Agent Workflow with Chat History & Error Handling
1. **Session Initialization**: System generates or retrieves session ID from URL parameters
2. **Recording**: User clicks "Start Voice Query" and speaks their question into microphone
3. **Audio Capture**: Browser's MediaRecorder API captures audio with real-time timer
4. **Processing Feedback**: Visual step-by-step progress shows:
   - Transcribing audio using AssemblyAI
   - Analyzing question with AI (including chat history context)
   - Generating response with Google Gemini
   - Creating speech with Murf AI
5. **AI Processing with Error Handling**: FastAPI backend processes the complete pipeline with comprehensive error recovery:
   - **Audio File Validation**: Checks for valid audio content
   - **Speech-to-text conversion**: via AssemblyAI with STT error handling
   - **Retrieval of conversation history**: from MongoDB with fallback to in-memory storage
   - **Context-aware prompt engineering**: with chat history
   - **AI response generation**: via Google Gemini with LLM error handling
   - **Storage of messages**: in MongoDB with graceful degradation
   - **Text-to-speech conversion**: via Murf AI with TTS error handling
   - **Fallback Audio Generation**: Creates spoken error messages when any step fails
6. **Rich Display with Error Recovery**: Results shown with:
   - Original transcription of user's question (or error explanation)
   - AI response with full Markdown rendering (or fallback error message)
   - Natural voice audio playback (or fallback error audio)
   - Updated chat history dropdown with previous conversations
   - **Auto-Recovery**: Intelligent restart of recording for certain error types
7. **Auto-Continue with Smart Recovery**: After audio playback ends, automatically start recording for the next question, with error-specific recovery logic
8. **Comprehensive Error Handling**: Production-ready error management with user-friendly messages and automatic recovery

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

3. **Set up MongoDB**
   
   **Option A: Local MongoDB Installation**
   - Install MongoDB Community Server from [https://www.mongodb.com/try/download/community](https://www.mongodb.com/try/download/community)
   - Start MongoDB service: `mongod` (default: localhost:27017)
   
   **Option B: MongoDB Atlas (Cloud)**
   - Create a free account at [https://www.mongodb.com/atlas](https://www.mongodb.com/atlas)
   - Create a cluster and get your connection string
   - Replace `MONGODB_URL` in your `.env` file with your Atlas connection string

4. **Set up your API keys**
   
   Create a `.env` file in the project root:
   ```bash
   MURF_API_KEY=your_actual_murf_api_key_here
   ASSEMBLYAI_API_KEY=your_actual_assemblyai_api_key_here
   MURF_VOICE_ID=en-IN-aarav
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   MONGODB_URL=mongodb://localhost:27017
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

6. **Open your browser and allow microphone access**
   
   Navigate to: `http://127.0.0.1:8000`
   
   **Important**: Your browser will request microphone permission. Click "Allow" to enable voice recording functionality.

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Serves the main application HTML page with session management |
| `POST` | `/agent/chat/{session_id}` | **NEW**: Chat endpoint with persistent history - transcribe audio, process with AI using chat context, and generate speech response |
| `GET` | `/agent/chat/{session_id}/history` | **NEW**: Retrieve chat history for a specific session |
| `POST` | `/llm/query` | Legacy endpoint: Complete AI Voice Agent workflow without chat history |
| `GET` | `/api/backend` | Test endpoint for backend connectivity |
| `GET` | `/docs` | Interactive API documentation (Swagger UI) |
| `GET` | `/redoc` | Alternative API documentation (ReDoc) |

### Chat Agent API (`/agent/chat/{session_id}`) - **NEW**

The new chat endpoint maintains conversation history and provides contextual responses.

**Path Parameter:**
- `session_id`: Unique identifier for the chat session (automatically generated by the UI)

**Request**: Multipart form data with audio file

**Supported File Types:**
- `audio/wav`
- `audio/mp3` 
- `audio/webm` (including codecs like `audio/webm;codecs=opus`)
- `audio/ogg`
- `audio/m4a`
- `audio/wave`
- `audio/mpeg`

**Response (Success):**
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

**Response (Error with Fallback Audio):**
```json
{
  "success": false,
  "message": "I'm having trouble understanding your audio right now. Please try speaking again clearly into your microphone.",
  "transcription": "",
  "llm_response": "I'm having trouble understanding your audio right now. Please try speaking again clearly into your microphone.",
  "audio_url": "https://murf-fallback-audio-url.com/error_response.mp3",
  "error_type": "stt_error"
}
```

**Error Types:**
- `api_keys_missing`: API configuration issues
- `file_error`: Audio file processing problems
- `stt_error`: Speech-to-text transcription failures
- `no_speech`: No speech detected in audio
- `llm_error`: Language model processing issues
- `tts_error`: Text-to-speech generation failures
- `general_error`: Network or unexpected errors

**Chat History Storage:**
- Messages are stored in MongoDB with timestamps
- Each session maintains its own conversation history
- AI responses consider previous context for more natural conversations
- Automatic fallback to in-memory storage when MongoDB is unavailable

### Chat History API (`/agent/chat/{session_id}/history`) - **NEW**

Retrieve the conversation history for a specific session.

**Path Parameter:**
- `session_id`: Unique identifier for the chat session

**Response (Success):**
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
  ]
}
```

**Session Management Features:**
- **URL Parameters**: Sessions can be shared or resumed using `?session_id=your_session_id`
- **Automatic Generation**: New sessions are created automatically when no session ID is provided
- **Interactive History**: Previous conversations are displayed in expandable cards
- **Context Preservation**: Chat history is maintained across browser sessions

### Legacy AI Voice Agent API (`/llm/query`)

**Request**: Multipart form data with audio file

**Supported File Types:**
- `audio/wav`
- `audio/mp3` 
- `audio/webm` (including codecs like `audio/webm;codecs=opus`)
- `audio/ogg`
- `audio/m4a`
- `audio/wave`
- `audio/mpeg`

**Response (Success):**
```json
{
  "success": true,
  "message": "Voice query processed successfully",
  "transcription": "What is artificial intelligence?",
  "llm_response": "# Artificial Intelligence\n\n**Artificial Intelligence (AI)** refers to:\n\n- Machine learning algorithms\n- Neural networks\n- `Natural language processing`\n\n## Applications\n1. Voice assistants\n2. Image recognition\n3. Autonomous vehicles",
  "audio_url": "https://murf.ai/audio/generated-response-file-url"
}
```

**Response (Error):**
```json
{
  "success": false,
  "message": "Specific error message describing what went wrong",
  "transcription": "",
  "llm_response": "",
  "audio_url": null
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

### Backend
- **[FastAPI](https://fastapi.tiangolo.com/)**: Modern, fast web framework for building APIs with Python
- **[MongoDB](https://www.mongodb.com/)**: NoSQL database for persistent chat history storage with Motor async driver
- **[AssemblyAI](https://www.assemblyai.com/)**: AI-powered speech-to-text transcription service
- **[Murf AI](https://murf.ai)**: Text-to-speech API for natural voice generation (using "en-IN-aarav" voice)
- **[Google Gemini](https://ai.google.dev/)**: Advanced large language model for text-based AI queries (using Gemini 2.5 Flash)
- **[Uvicorn](https://www.uvicorn.org/)**: Lightning-fast ASGI server for production
- **[Jinja2](https://jinja.palletsprojects.com/)**: Template engine for dynamic HTML rendering
- **[python-dotenv](https://pypi.org/project/python-dotenv/)**: Environment variable management
- **[Pydantic](https://pydantic-docs.helpmanual.io/)**: Data validation and settings management

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
```

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

### AI Voice Agent
1. **Start Recording**: Click "Start Voice Query" button to begin capturing your question
2. **Grant Permission**: Allow microphone access when prompted by your browser
3. **Ask Your Question**: Speak clearly into your microphone while watching the real-time timer and recording indicator
4. **Stop Recording**: Click "Stop Recording" when you're finished asking your question
5. **Watch Processing**: Observe the step-by-step processing visualization:
   - 🎙️ **Transcribing audio**: Your speech is converted to text using AssemblyAI
   - 🔍 **Analyzing question**: AI understands your question's context and intent
   - 🤖 **Generating response**: Google Gemini creates a comprehensive, Markdown-formatted answer
   - 🎵 **Creating speech**: Murf AI converts the response to natural-sounding speech
6. **View Results**: See your complete interaction:
   - **Your Question**: Transcribed text of what you asked
   - **AI Response**: Rich, formatted answer with Markdown rendering (lists, code, tables, etc.)
   - **Listen to Response**: Natural voice audio playback of the AI's answer
7. **Ask Again**: Use "Ask Another Question" to start a new voice query

### Tips for Best Experience
- **Microphone Quality**: Use a good quality microphone for better recording and transcription results
- **Quiet Environment**: Record in a quiet space to minimize background noise for better transcription accuracy
- **Clear Speech**: Speak clearly and at a moderate pace for optimal transcription results
- **Browser Permission**: Always allow microphone access for the Voice Agent to work properly
- **Audio Format**: The app automatically selects the best supported audio format for your browser
- **Internet Connection**: Ensure stable internet connection for AI processing
- **Question Quality**: Use clear, specific questions for better AI responses with rich formatting
- **Content Types**: Ask about topics that benefit from formatting (programming, tutorials, lists, explanations)

## 🆕 New Features - Chat History & Session Management

### Chat History Features
- **Persistent Conversations**: All messages are stored in MongoDB with timestamps for long-term memory
- **Session-based Organization**: Each conversation is organized by unique session IDs
- **Interactive History UI**: 
  - Expandable chat history dropdown showing previous conversations
  - Click on any conversation card to replay it in the main interface
  - Organized display with user questions and AI responses paired together
- **URL Session Sharing**: Share conversations by copying URL with session_id parameter
- **Auto-Recording Flow**: Seamless conversation flow with automatic recording after AI response

### Session Management
- **Automatic Session Creation**: New sessions generated automatically when accessing the application
- **Session Persistence**: Continue previous conversations by using session_id in URL
- **Fallback Storage**: Graceful degradation to in-memory storage when MongoDB is unavailable
- **Context Awareness**: AI responses consider previous messages for more natural conversations

### Usage Examples
```bash
# Start a new conversation
http://localhost:8000/

# Continue a specific conversation
http://localhost:8000/?session_id=session_abc123_1640995200000

# API: Send voice message to specific session
POST /agent/chat/session_abc123_1640995200000

# API: Get chat history for session
GET /agent/chat/session_abc123_1640995200000/history
```

## 🤝 Contributing

Feel free to contribute to this project by:
- Reporting bugs
- Suggesting new features
- Submitting pull requests
- Improving documentation

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

**Built with ❤️ using FastAPI, Murf AI, AssemblyAI, and Google Gemini**

### 🎯 Project Highlights
- **Complete AI Voice Pipeline**: Combines AssemblyAI's speech-to-text, Google Gemini's language model, and Murf AI's text-to-speech capabilities
- **Persistent Chat Memory**: MongoDB-powered conversation history with session-based organization
- **Interactive Conversation Management**: Click-to-replay previous conversations with organized chat history UI
- **Session URL Sharing**: Share and resume conversations via URL parameters
- **Auto-Recording Flow**: Seamless conversation continuation with automatic recording after responses
- **Advanced Markdown Support**: Rich text formatting with syntax highlighting for technical content
- **Real-time Processing Feedback**: Step-by-step visual progress with professional loading animations
- **Modern Web Technologies**: Leverages latest browser APIs for audio recording and processing
- **No File Storage**: Direct audio processing without server-side file storage for better performance and privacy
- **🛡️ Production-Ready Error Handling**: Comprehensive failure recovery with fallback audio responses
- **⚡ Smart Auto-Recovery**: Intelligent restart mechanisms for different error scenarios
- **🔧 Bulletproof Architecture**: Handles API failures, network issues, and edge cases gracefully
- **📊 Advanced Logging**: Production-ready error tracking and debugging capabilities
- **User-Friendly**: Intuitive interface with clear visual feedback and intelligent error guidance
- **Voice Quality**: Uses Murf AI's high-quality voices for natural-sounding responses and error messages
- **Intelligent Responses**: Powered by Google Gemini with smart prompt engineering for formatted output
- **Cross-Platform**: Works seamlessly across desktop, tablet, and mobile devices
- **Professional UI**: Modern design with animations, transitions, and responsive layouts
- **🎯 Error-First Design**: Built with failure scenarios in mind for maximum reliability