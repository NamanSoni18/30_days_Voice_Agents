# Voice Agent - Real-Time Conversation System

A voice-based conversation application built with FastAPI that supports both traditional file upload and real-time streaming conversations. The system integrates speech recognition, AI language models, and text-to-speech services to create a complete voice interaction experience.

## Features

### Core Functionality
- **Speech Recognition**: Convert audio to text using AssemblyAI
- **AI Conversations**: Generate responses using Google Gemini
- **Text-to-Speech**: Convert AI responses to audio using Murf AI
- **Session Management**: Persistent conversation history across sessions
- **Real-time Chat History**: Live updates to conversation display without page refresh
- **Modal View**: Click on any conversation to view it in a detailed popup modal

### Interaction Modes
- **File Upload Mode**: Upload audio files for processing
- **Real-time Streaming Mode**: Live audio streaming with instant processing
- **WebSocket Communication**: Real-time bidirectional communication
- **Database Storage**: Conversation persistence with MongoDB or in-memory fallback

### User Interface
- **Dual Interface**: Traditional upload and streaming controls
- **Live Status Updates**: Real-time connection and processing status
- **Chat History Panel**: Collapsible conversation history view
- **Audio Playback**: Built-in audio player for generated responses
- **Session Tracking**: Unique session IDs for conversation continuity

## Project Structure

```
├── main.py                           # FastAPI application with all endpoints
├── services/                         # Service integrations
│   ├── assemblyai_streaming_service.py    # Real-time speech recognition
│   ├── llm_service.py                     # Google Gemini integration
│   ├── murf_websocket_service.py          # Real-time text-to-speech
│   ├── stt_service.py                     # File-based speech recognition
│   ├── tts_service.py                     # Traditional TTS processing
│   └── database_service.py               # MongoDB operations
├── models/
│   └── schemas.py                    # Data models and validation
├── static/
│   ├── app.js                        # Frontend JavaScript logic
│   └── style.css                     # Application styling
├── templates/
│   └── index.html                    # Main application interface
├── utils/                            # Utilities
│   ├── constants.py                  # Application constants
│   ├── json_utils.py                 # JSON processing utilities
│   └── logging_config.py             # Logging configuration
└── streamed_audio/                   # Saved audio files from streaming sessions
```

## Setup Instructions

### Prerequisites
- Python 3.7+
- Web browser with microphone support
- MongoDB (optional - uses in-memory storage as fallback)

### Required API Keys
Create a `.env` file with the following:
```
GEMINI_API_KEY=your_google_gemini_api_key
ASSEMBLYAI_API_KEY=your_assemblyai_api_key
MURF_API_KEY=your_murf_api_key
MURF_VOICE_ID=en-IN-aarav
MONGODB_URL=your_mongodb_connection_string
```

### Installation
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create the `.env` file with your API keys
4. Run the application: `python main.py`
5. Open your browser to `http://127.0.0.1:8000`

## API Endpoints

### Web Interface
- `GET /` - Main application interface

### Chat API
- `POST /agent/chat/{session_id}` - Process uploaded audio file
- `GET /agent/chat/{session_id}/history` - Get conversation history
- `DELETE /agent/chat/{session_id}/history` - Clear session history

### WebSocket
- `ws://localhost:8000/ws/audio-stream` - Real-time audio streaming

### System
- `GET /api/backend` - Backend status check

## How It Works

### Traditional Mode
1. User uploads an audio file
2. System transcribes audio using AssemblyAI
3. AI generates response using Google Gemini
4. Response is converted to speech using Murf AI
5. Conversation is saved to database
6. Audio response is returned to user

### Streaming Mode
1. User connects via WebSocket
2. Browser captures live audio from microphone
3. Audio is streamed in real-time to AssemblyAI
4. Transcribed text triggers AI response generation
5. AI response streams back to user in real-time
6. Response is converted to audio using Murf WebSocket
7. Audio chunks are played as they arrive
8. Complete conversation is saved to database immediately

### Real-time Updates
- User messages appear in chat history when spoken
- AI responses update character by character as generated
- Database saves responses immediately when complete
- No page refresh needed for chat history updates
- Modal popup shows full conversation details on click

## Technical Details

### Audio Configuration
- Sample Rate: 16kHz
- Format: PCM (Pulse Code Modulation)
- Channels: Mono
- Chunk Size: 4096 samples

### Database Schema
- Sessions tracked by unique session IDs
- Messages stored with role (user/assistant), content, and timestamp
- Fallback to in-memory storage if MongoDB unavailable
- Session metadata includes message count and activity tracking

### Error Handling
- Graceful degradation when services are unavailable
- Fallback audio messages for errors
- Connection retry logic for WebSocket streams
- Comprehensive logging for debugging

## Configuration

### Environment Variables
- `GEMINI_API_KEY` - Google Gemini API access
- `ASSEMBLYAI_API_KEY` - AssemblyAI speech recognition
- `MURF_API_KEY` - Murf text-to-speech
- `MURF_VOICE_ID` - Voice selection (default: en-IN-aarav)
- `MONGODB_URL` - Database connection string

### Audio Settings
The application automatically configures optimal audio settings for real-time processing. Manual configuration is available in the frontend JavaScript for specific use cases.

## Troubleshooting

### Common Issues
- **Microphone not working**: Check browser permissions and system settings
- **API errors**: Verify API keys are correctly set in `.env` file
- **Connection issues**: Ensure all required services are accessible
- **Audio playback problems**: Check browser Web Audio API support

### Logging
Application logs are written to `voice_agent.log` with detailed information about:
- Service initialization status
- WebSocket connection events
- API call success/failure
- Audio processing metrics
- Database operations

## Dependencies

### Backend
- FastAPI - Web framework
- Uvicorn - ASGI server
- Motor - Async MongoDB driver
- Google Generative AI - Language model
- WebSockets - Real-time communication

### Frontend
- Vanilla JavaScript - No frameworks
- Web Audio API - Audio processing
- WebSocket API - Real-time communication
- Marked.js - Markdown rendering (optional)
- Highlight.js - Code syntax highlighting (optional)

## Development

### Running in Development
```bash
python main.py
```
This starts the server with auto-reload enabled for development.

### Project Structure Notes
- All service integrations are modular and can be swapped
- Frontend uses vanilla JavaScript for maximum compatibility
- Error handling includes fallback options for all external services
- Session management works with or without database connectivity