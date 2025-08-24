# 🎤 Real-Time Voice Agent with Streaming AI

A cutting-edge **real-time voice conversation agent** built with FastAPI, featuring live streaming transcription, AI responses, and text-to-speech generation. This application demonstrates the future of voice-enabled human-computer interaction with sub-second latency and natural conversation flow.

## ✨ Key Features

### 🚀 Real-Time Streaming Capabilities
- **Live Voice Streaming**: Real-time 16kHz PCM audio transmission via WebSocket
- **Instant Transcription**: AssemblyAI Universal Streaming for live speech-to-text
- **Streaming AI Responses**: Google Gemini with character-by-character response generation
- **Murf WebSocket TTS**: Revolutionary real-time text-to-speech streaming with base64 audio output
- **Complete Voice Pipeline**: End-to-end streaming from voice input to audio response
- **Turn Detection**: Natural conversation flow with intelligent speaker turn recognition

### 🎯 Dual-Mode Architecture
- **Traditional Mode**: File-based audio processing for compatibility
- **Streaming Mode**: Real-time voice conversations with instant feedback
- **Seamless Switching**: Automatic fallback between modes based on connection quality
- **Unified History**: Conversation persistence across both interaction modes

### 🛠️ AI Service Integration
- **Speech Recognition**: AssemblyAI with both file-based and streaming modes
- **Language Model**: Google Gemini with streaming response capabilities
- **Text-to-Speech**: Murf AI with traditional API and WebSocket streaming
- **Database**: MongoDB for session persistence and conversation history

### 🌐 Advanced WebSocket Infrastructure
- **Connection Management**: Robust WebSocket lifecycle handling with auto-reconnection
- **Real-Time Monitoring**: Live connection status and performance metrics
- **Error Recovery**: Intelligent error detection and stream resumption
- **Concurrent Sessions**: Support for multiple simultaneous streaming conversations

## 🏗️ Project Structure

```
voice-agent/
├── main.py                     # FastAPI application with dual-mode endpoints
├── services/                   # AI service integrations
│   ├── assemblyai_streaming_service.py   # Real-time transcription
│   ├── llm_service.py                   # Streaming AI responses
│   ├── murf_websocket_service.py        # Real-time TTS streaming
│   ├── stt_service.py                   # Traditional speech-to-text
│   ├── tts_service.py                   # Traditional text-to-speech
│   └── database_service.py              # MongoDB session management
├── models/
│   └── schemas.py              # Pydantic models for streaming data validation
├── static/
│   ├── app.js                  # WebSocket client with real-time audio handling
│   └── style.css               # Modern responsive UI
├── templates/
│   └── index.html              # Dual-mode interface
├── utils/                      # Logging and configuration utilities
└── streamed_audio/            # Auto-saved streaming audio sessions
```

## ⚡ Quick Start

### Prerequisites
- Python 3.7 or higher
- Modern web browser with microphone support
- MongoDB (local or cloud) - optional, falls back to in-memory storage

### API Keys Required
- **Murf AI**: [Get API key](https://murf.ai)
- **AssemblyAI**: [Get API key](https://www.assemblyai.com/)
- **Google Gemini**: [Get API key](https://makersuite.google.com/app/apikey)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd voice-agent
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   
   Create a `.env` file:
   ```bash
   MURF_API_KEY=your_murf_api_key_here
   ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here
   GEMINI_API_KEY=your_gemini_api_key_here
   MURF_VOICE_ID=en-IN-aarav
   MONGODB_URL=mongodb://localhost:27017
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

5. **Access the voice agent**
   
   Navigate to: `http://127.0.0.1:8000`
   
   **Important**: Allow microphone access when prompted by your browser.

## 🎵 Real-Time Streaming Features

### WebSocket Audio Streaming

**Endpoint**: `ws://127.0.0.1:8000/ws/audio-stream`

#### Streaming Flow
1. **Connection**: Client connects to WebSocket endpoint
2. **Audio Capture**: Real-time 16kHz PCM audio streaming
3. **Live Transcription**: AssemblyAI provides instant speech-to-text
4. **Streaming LLM**: Google Gemini generates responses in real-time
5. **Live TTS**: Murf WebSocket converts text to streaming audio
6. **Audio Output**: Base64 audio chunks delivered for playback
7. **Session Persistence**: All conversations saved automatically

#### Message Types
```json
// Real-time transcription
{
  "type": "partial_transcript",
  "text": "Hello how are you",
  "confidence": 0.95,
  "is_final": false
}

// Streaming AI response
{
  "type": "llm_streaming_chunk",
  "chunk": "I'm doing great, thank you! ",
  "accumulated_length": 28
}

// Real-time TTS audio
{
  "type": "murf_audio_chunk",
  "chunk_number": 1,
  "base64_audio": "UklGRvBVAABXQVZFZm10IBAAAAABAA...",
  "audio_size": 21848,
  "final": false
}
```

### Traditional Chat API

**Endpoint**: `POST /agent/chat/{session_id}`

Upload audio files for processing with session-based conversation history.

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Main application interface with dual-mode voice agent |
| `POST` | `/agent/chat/{session_id}` | Traditional voice processing with session history |
| `GET` | `/agent/chat/{session_id}/history` | Retrieve conversation history |
| `GET` | `/api/backend` | Backend connectivity test |
| `WebSocket` | `/ws/audio-stream` | Real-time audio streaming |
| `GET` | `/docs` | Interactive API documentation |

## 🔧 Technical Configuration

### Audio Settings
- **Sample Rate**: 16kHz (optimal for speech recognition)
- **Audio Format**: PCM (Pulse Code Modulation)
- **Channels**: Mono (single channel)
- **Bit Depth**: 16-bit
- **Chunk Size**: 4096 samples for real-time processing

### WebSocket Configuration
- **Connection Timeout**: 30 seconds
- **Message Size Limit**: 64MB for audio chunks
- **Keepalive Interval**: 30 seconds
- **Reconnection Strategy**: Exponential backoff

## 🛠️ Troubleshooting

### Common Issues

**1. Microphone Access Denied**
- Ensure browser has microphone permissions
- Check system privacy settings
- Try refreshing the page and allowing access

**2. WebSocket Connection Fails**
- Verify server is running on port 8000
- Check firewall settings
- Ensure no conflicting applications on the port

**3. Audio Not Playing**
- Check browser audio settings
- Verify Web Audio API support (modern browsers)
- Test with different browsers (Chrome recommended)

**4. Transcription Not Working**
- Verify AssemblyAI API key is valid
- Check internet connection
- Ensure speaking clearly into microphone

**5. AI Responses Not Generating**
- Verify Google Gemini API key is valid
- Check API quota and billing
- Review logs for error messages

### Backend Health Check
Visit `http://localhost:8000/api/backend` to check service status.

### Log Analysis
Check `voice_agent.log` for detailed information:
```bash
tail -f voice_agent.log  # Monitor real-time logs
```

## 📊 Performance & Monitoring

### Built-in Metrics
- **Session Statistics**: Duration, message count, audio size
- **Performance Metrics**: Response times, processing latency
- **Connection Health**: WebSocket status, reconnection events
- **Audio Quality**: Sample rates, chunk processing times

### Data Storage
- **Conversation History**: MongoDB with session-based organization
- **Audio Archives**: Automatic saving in `streamed_audio/` directory
- **Application Logs**: Comprehensive logging in `voice_agent.log`
- **Session Metadata**: Timestamps, user interactions, processing stats

## 🚀 Deployment

### Development
```bash
python main.py  # Runs on localhost:8000
```

### Production Considerations
- Use ASGI server like Gunicorn with Uvicorn workers
- Configure SSL/TLS for secure WebSocket connections
- Set up MongoDB with proper authentication
- Implement rate limiting and API key management
- Configure logging for production monitoring

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Enhanced audio processing algorithms
- Additional language and voice options
- Mobile device optimization
- Performance monitoring dashboards
- Advanced conversation analytics

### Development Setup
1. Fork the repository
2. Create feature branch
3. Follow existing code style
4. Add tests for new features
5. Submit pull request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

**Built with ❤️ for the 30 Days of Voice Agents Challenge**

For questions or support, please open an issue on GitHub.