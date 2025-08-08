# 30 Days of Voice Agents - Echo Bot Application

A modern web application built with FastAPI, Murf AI, and AssemblyAI that creates an intelligent "Echo Bot" - record your voice, and the AI will echo it back using Murf's natural-sounding voices! This project demonstrates seamless integration between speech-to-text and text-to-speech AI services.

## ✨ Features

### 🎙️ Intelligent Echo Bot
- **Voice Recording**: Record audio directly from your microphone using browser's MediaRecorder API
- **Real-time Timer**: See recording duration with a visual recording indicator
- **Instant Playback**: Automatically plays back your original recorded voice
- **AI-Powered Transcription**: Convert your speech to text using AssemblyAI's advanced speech recognition
- **AI Voice Echo**: Generate natural-sounding echo using Murf AI's text-to-speech with the "en-IN-aarav" voice
- **Complete Voice Loop**: Record → Transcribe → Generate → Play back in one seamless flow

### 🎨 Technical Features
- **Modern Web Interface**: Clean, responsive design with intuitive controls
- **FastAPI Backend**: High-performance async Python web framework
- **Real-time Feedback**: Loading states, recording indicators, and comprehensive error handling
- **Audio Playback**: Built-in HTML5 audio players with standard controls
- **Cross-browser Support**: Works on Chrome, Firefox, Safari, and other modern browsers
- **Environment-based Configuration**: Secure API key management
- **No File Storage**: Direct audio processing without saving files on server

## 📁 Project Structure

```
30 Days of Voice Agents/
├── main.py                 # FastAPI backend server with Echo Bot endpoint
├── requirements.txt        # Python dependencies
├── templates/
│   └── index.html         # Main HTML page with Echo Bot interface
├── static/
│   ├── app.js            # Frontend JavaScript for recording and playback
│   └── style.css         # CSS styles and responsive design
├── __pycache__/           # Python bytecode cache
└── README.md             # Project documentation
```

## 🔧 How It Works

### Echo Bot Workflow
1. **Recording**: User clicks "Start Recording" and speaks into microphone
2. **Audio Capture**: Browser's MediaRecorder API captures audio with real-time timer
3. **Playback**: Original recording is immediately played back to user
4. **AI Processing**: User clicks "Echo with Murf Voice" to trigger AI processing
5. **Transcription**: FastAPI backend sends audio to AssemblyAI for speech-to-text conversion
6. **Voice Generation**: Transcribed text is sent to Murf AI to generate natural speech using "en-IN-aarav" voice
7. **Echo Playback**: AI-generated audio is played back, completing the echo cycle
8. **Error Handling**: Comprehensive error messages for various scenarios (API failures, no speech detected, etc.)

## 🚀 Quick Start

### Prerequisites
- Python 3.7 or higher
- A Murf AI API key ([Get one here](https://murf.ai))
- An AssemblyAI API key ([Get one here](https://www.assemblyai.com/))
- Modern web browser with microphone support (Chrome, Firefox, Safari, Edge)

### Installation

1. **Clone or download this repository**

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your API keys**
   
   Create a `.env` file in the project root:
   ```bash
   MURF_API_KEY=your_actual_murf_api_key_here
   ASSEMBLYAI_API_KEY=your_actual_assemblyai_api_key_here
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

5. **Open your browser and allow microphone access**
   
   Navigate to: `http://127.0.0.1:8000`
   
   **Important**: Your browser will request microphone permission. Click "Allow" to enable voice recording functionality.

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Serves the main Echo Bot HTML page |
| `POST` | `/tts/echo` | Complete echo workflow: transcribe audio and generate Murf voice response |
| `GET` | `/api/backend` | Test endpoint for backend connectivity |
| `GET` | `/docs` | Interactive API documentation (Swagger UI) |
| `GET` | `/redoc` | Alternative API documentation (ReDoc) |

### Echo Bot API (`/tts/echo`)

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
  "transcription": "Hello, this is the transcribed text from your recording.",
  "audio_url": "https://murf.ai/audio/generated-echo-file-url",
  "message": "Audio echoed successfully with Murf voice"
}
```

**Response (Error):**
```json
{
  "success": false,
  "message": "Specific error message describing what went wrong",
  "transcription": "",
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
- **[AssemblyAI](https://www.assemblyai.com/)**: AI-powered speech-to-text transcription service
- **[Murf AI](https://murf.ai)**: Text-to-speech API for natural voice generation (using "en-IN-aarav" voice)
- **[Uvicorn](https://www.uvicorn.org/)**: Lightning-fast ASGI server for production
- **[Jinja2](https://jinja.palletsprojects.com/)**: Template engine for dynamic HTML rendering
- **[python-dotenv](https://pypi.org/project/python-dotenv/)**: Environment variable management
- **[requests](https://docs.python-requests.org/)**: HTTP library for API communication

### Frontend
- **HTML5 & CSS3**: Modern web standards with responsive design
- **Vanilla JavaScript**: Frontend interactivity without external frameworks
- **MediaRecorder API**: Browser-native audio recording capabilities
- **Web Audio API**: Real-time audio processing and playback
- **Blob API**: Handling recorded audio data

## 🎨 Frontend Features

### Echo Bot Interface
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **Recording Controls**: Start/Stop recording buttons with visual feedback
- **Real-time Recording Timer**: Shows recording duration (0s, 1s, 2s...)
- **Visual Recording Indicator**: Animated pulsing dot during recording
- **Audio Playback Controls**: Built-in HTML5 audio players for both original and echo audio
- **Transcription Display**: Shows transcribed text in a clean, readable format
- **Loading States**: Visual feedback during AI processing
- **Error Handling**: User-friendly error messages for various scenarios
- **Microphone Permission Handling**: Clear guidance for granting microphone access
- **Audio Format Support**: Automatic format selection based on browser capabilities

## 📦 Dependencies

This project uses the following Python packages (see `requirements.txt`):

```
fastapi==0.104.1          # Web framework for building APIs
uvicorn[standard]==0.24.0 # ASGI server for FastAPI
jinja2==3.1.2             # Template engine for HTML rendering
python-multipart==0.0.6   # For handling form data and file uploads
python-dotenv==1.0.0      # Environment variable management
murf==2.0.0               # Official Murf AI Python SDK
requests==2.31.0          # HTTP library for API calls
assemblyai==0.17.0        # AssemblyAI Python SDK for transcription
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Required: Your Murf AI API key
MURF_API_KEY=your_actual_murf_api_key_here

# Required: Your AssemblyAI API key
ASSEMBLYAI_API_KEY=your_actual_assemblyai_api_key_here

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

## 🐛 Troubleshooting

### Common Issues

#### Echo Bot Related
1. **"MURF_API_KEY environment variable not set" or "AssemblyAI API key not set"**
   - Make sure you have created a `.env` file in the project root
   - Verify your API keys are correctly set in the `.env` file
   - Ensure your API keys are not set to placeholder values like "your_murf_api_key_here"

2. **"Could not connect to backend"**
   - Ensure the FastAPI server is running on `http://127.0.0.1:8000`
   - Check the browser console for detailed error messages

3. **"Microphone access denied"**
   - Click "Allow" when the browser requests microphone permission
   - In Chrome: Go to Settings > Privacy and Security > Site Settings > Microphone
   - Ensure the site has permission to access your microphone

4. **"No microphone found"**
   - Check that your microphone is properly connected
   - Verify the microphone is working in other applications
   - Try refreshing the page and granting permission again

5. **"No speech detected in the audio"**
   - Ensure you're speaking clearly and loudly enough during recording
   - Check that your microphone is not muted
   - Try recording in a quieter environment

6. **Recording not working**
   - Ensure you're using a modern browser (Chrome 49+, Firefox 25+, Safari 14.1+)
   - Check browser console for detailed error messages
   - Try using a different browser if issues persist

7. **"Your browser doesn't support audio recording"**
   - Update your browser to the latest version
   - Use Chrome, Firefox, Safari, or Edge for best compatibility

8. **Murf API errors**
   - Verify your Murf API key is valid and has sufficient credits
   - Check that your Murf account is active and in good standing
   - Check that your microphone is properly connected
   - Verify the microphone is working in other applications
   - Try refreshing the page and granting permission again

6. **Recording not working**
   - Ensure you're using a modern browser (Chrome 49+, Firefox 25+, Safari 14.1+)
   - Check browser console for detailed error messages
   - Try using a different browser if issues persist

7. **"Your browser doesn't support audio recording"**
   - Update your browser to the latest version
   - Use Chrome, Firefox, Safari, or Edge for best compatibility

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

### Echo Bot
1. **Start Recording**: Click "Start Recording" button to begin capturing audio
2. **Grant Permission**: Allow microphone access when prompted by your browser
3. **Speak Clearly**: Talk into your microphone while watching the real-time timer and recording indicator
4. **Stop Recording**: Click "Stop Recording" when you're finished speaking
5. **Listen to Original**: Your recorded voice will automatically play back through the audio player
6. **Generate Echo**: Click "Echo with Murf Voice" to process your recording through AI
7. **AI Processing**: 
   - Your audio is transcribed to text using AssemblyAI
   - The transcribed text is converted to speech using Murf AI's "en-IN-aarav" voice
8. **Listen to Echo**: The AI-generated echo will play automatically, and you can see the transcribed text
9. **Start Over**: Use "Record Again" to create a new recording

### Tips for Best Experience
- **Microphone Quality**: Use a good quality microphone for better recording and transcription results
- **Quiet Environment**: Record in a quiet space to minimize background noise for better transcription accuracy
- **Clear Speech**: Speak clearly and at a moderate pace for optimal transcription results
- **Browser Permission**: Always allow microphone access for the Echo Bot to work properly
- **Audio Format**: The app automatically selects the best supported audio format for your browser
- **Internet Connection**: Ensure stable internet connection for AI processing

## 🤝 Contributing

Feel free to contribute to this project by:
- Reporting bugs
- Suggesting new features
- Submitting pull requests
- Improving documentation

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

**Built with ❤️ using FastAPI, Murf AI, and AssemblyAI**

### 🎯 Project Highlights
- **Seamless AI Integration**: Combines AssemblyAI's speech-to-text with Murf AI's text-to-speech for a complete voice loop
- **Modern Web Technologies**: Leverages latest browser APIs for audio recording and processing
- **No File Storage**: Direct audio processing without server-side file storage for better performance and privacy
- **Production Ready**: Comprehensive error handling and browser compatibility
- **User-Friendly**: Intuitive interface with clear visual feedback and real-time recording indicators
- **Voice Quality**: Uses Murf AI's high-quality "en-IN-aarav" voice for natural-sounding echoes
- **Real-time Feedback**: Live recording timer and visual indicators enhance user experience