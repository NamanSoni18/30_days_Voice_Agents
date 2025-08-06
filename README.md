# 30 Days of Voice Agents - Text-to-Speech & Audio Upload Application

A modern web application built with FastAPI and Murf AI that features text-to-speech conversion, voice recording, and audio file upload capabilities. This project demonstrates the integration of a Python backend with Murf's text-to-speech API alongside client-side audio recording and server-side file handling.

## ✨ Features

### 🎤 Text-to-Speech Generator
- **Text-to-Speech Conversion**: Convert any text (up to 500 characters) to natural-sounding speech using Murf AI
- **Real-time Character Counting**: Visual feedback with color-coded limits (green/yellow/red)
- **Keyboard Shortcuts**: Press Ctrl+Enter to quickly generate audio

### 🎙️ Audio Recording & Upload
- **Voice Recording**: Record audio directly from your microphone using browser's MediaRecorder API
- **Real-time Timer**: See recording duration in real-time
- **Instant Playback**: Automatically plays back your recorded voice
- **Audio Upload**: Upload recorded audio files to the server with validation
- **File Management**: Server-side storage with unique filenames and metadata tracking
- **Supported Formats**: WAV, MP3, WebM (with codecs), OGG, M4A, and WAVE files

### 🎨 General Features
- **Modern Web Interface**: Clean, responsive design with separate containers for each feature
- **FastAPI Backend**: High-performance async Python web framework
- **Real-time Feedback**: Loading states and comprehensive error handling
- **Audio Playback**: Built-in HTML5 audio players with standard controls
- **Cross-browser Support**: Works on Chrome, Firefox, Safari, and other modern browsers
- **Environment-based Configuration**: Secure API key management

## 📁 Project Structure

```
30 Days of Voice Agents/
├── main.py                 # FastAPI backend server
├── requirements.txt        # Python dependencies
├── templates/
│   └── index.html         # Main HTML page with Jinja2 templating
├── static/
│   ├── app.js            # Frontend JavaScript functionality
│   └── style.css         # CSS styles and responsive design
├── uploads/               # Directory for uploaded audio files
├── __pycache__/           # Python bytecode cache
└── README.md             # Project documentation
```

## 🔧 How It Works

### Text-to-Speech Generator
1. **Frontend**: User enters text in the web interface (up to 500 characters)
2. **API Request**: JavaScript sends a POST request to `/tts/generate` with the text
3. **Murf Integration**: FastAPI backend calls Murf AI's text-to-speech API via HTTP requests
4. **Audio Response**: Generated audio URL is returned and played in the browser
5. **Error Handling**: Comprehensive error messages for various failure scenarios

### Audio Recording & Upload
1. **Microphone Access**: Browser requests microphone permission from user
2. **Recording**: MediaRecorder API captures audio with real-time timer display
3. **Audio Processing**: Recorded audio chunks are compiled into a playable blob
4. **File Upload**: Audio blob is uploaded to `/upload-audio` endpoint with validation
5. **Server Storage**: Files are saved to `/uploads` directory with unique UUIDs
6. **Metadata Response**: Server returns file information including size and filename

## 🚀 Quick Start

### Prerequisites
- Python 3.7 or higher
- A Murf AI API key ([Get one here](https://murf.ai))
- Modern web browser with microphone support (Chrome, Firefox, Safari, Edge)

### Installation

1. **Clone or download this repository**

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your Murf API key**
   
   Create a `.env` file in the project root:
   ```bash
   MURF_API_KEY=your_actual_murf_api_key_here
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

5. **Open your browser and allow microphone access**
   
   Navigate to: `http://127.0.0.1:8000`
   
   **Important**: When using the Echo Bot feature, your browser will request microphone permission. Click "Allow" to enable voice recording functionality.

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Serves the main HTML page |
| `POST` | `/tts/generate` | Generate speech from text using Murf AI |
| `POST` | `/upload-audio` | Upload audio files to server with validation |
| `GET` | `/api/backend` | Test endpoint for backend connectivity |
| `GET` | `/docs` | Interactive API documentation (Swagger UI) |
| `GET` | `/redoc` | Alternative API documentation (ReDoc) |

### Text-to-Speech API (`/tts/generate`)

**Request Body:**
```json
{
  "text": "Hello, this is a test message"
}
```

**Response (Success):**
```json
{
  "audio_url": "https://murf.ai/audio/generated-audio-file-url"
}
```

**Response (Error):**
```json
{
  "detail": "Error message describing what went wrong"
}
```

### Audio Upload API (`/upload-audio`)

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
  "filename": "a1b2c3d4-e5f6-7890-abcd-ef1234567890.webm",
  "original_filename": "recording_1754473144560.webm",
  "content_type": "audio/webm;codecs=opus",
  "size": 45632,
  "message": "Audio file uploaded successfully"
}
```

**Response (Error):**
```json
{
  "detail": "Invalid file type: image/png. Allowed types: .wav, .mp3, .webm, .ogg, .m4a, .wave"
}
```
  "response": "base64_encoded_audio_data_or_url",
  "text": "Hello, this is a test message"
}
```

**Response (Error):**
```json
{
  "detail": "Error message describing what went wrong"
}
```

> **Note**: The application currently uses the "en-US-natalie" voice from Murf AI.

## 🛠️ Technologies Used

### Backend
- **[FastAPI](https://fastapi.tiangolo.com/)**: Modern, fast web framework for building APIs with Python
- **[Murf AI SDK](https://murf.ai)**: Official Python SDK for text-to-speech conversion
- **[Uvicorn](https://www.uvicorn.org/)**: Lightning-fast ASGI server for production
- **[Jinja2](https://jinja.palletsprojects.com/)**: Template engine for dynamic HTML rendering
- **[python-dotenv](https://pypi.org/project/python-dotenv/)**: Environment variable management

### Frontend
- **HTML5 & CSS3**: Modern web standards with responsive design
- **Vanilla JavaScript**: Frontend interactivity without external frameworks
- **MediaRecorder API**: Browser-native audio recording capabilities
- **Web Audio API**: Real-time audio processing and playback
- **Blob API**: Handling recorded audio data

## 🎨 Frontend Features

### Text-to-Speech Section
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **Real-time Character Counter**: Visual feedback with color-coded limits (green/yellow/red)
- **Loading States**: Visual feedback during audio generation
- **Keyboard Shortcuts**: Ctrl+Enter to quickly generate audio

### Echo Bot Section
- **Real-time Recording Timer**: Shows recording duration (0s, 1s, 2s...)
- **Visual Recording Indicator**: Animated pulsing dot during recording
- **Microphone Permission Handling**: Clear error messages for permission issues
- **Audio Format Support**: Multiple codec support (WebM, MP4, OGG, WAV)
- **Resource Management**: Automatic cleanup of microphone and audio resources

### General UI Features
- **Dual Container Layout**: Separate, visually distinct sections for each feature
- **Error Handling**: User-friendly error messages for various scenarios
- **Audio Controls**: Built-in HTML5 audio players with standard controls
- **Smooth Animations**: CSS transitions and keyframe animations
- **Cross-browser Compatibility**: Tested on major modern browsers

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
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Required: Your Murf AI API key
MURF_API_KEY=your_actual_murf_api_key_here
```

### Getting Your Murf API Key

1. Sign up at [Murf.ai](https://murf.ai)
2. Navigate to your account settings or API section
3. Generate or copy your API key
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

#### Text-to-Speech Related
1. **"MURF_API_KEY environment variable not set"**
   - Make sure you have created a `.env` file in the project root
   - Verify your API key is correctly set in the `.env` file

2. **"Could not connect to backend"**
   - Ensure the FastAPI server is running on `http://127.0.0.1:8000`
   - Check the browser console for detailed error messages

3. **Audio generation fails**
   - Verify your Murf API key is valid and has sufficient credits
   - Check that your text doesn't exceed the 500 character limit

#### Echo Bot Related
4. **"Microphone access denied"**
   - Click "Allow" when the browser requests microphone permission
   - In Chrome: Go to Settings > Privacy and Security > Site Settings > Microphone
   - Ensure the site has permission to access your microphone

5. **"No microphone found"**
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

### Text-to-Speech Generator
1. **Enter Text**: Type or paste your text into the textarea (max 500 characters)
2. **Character Counter**: Watch the real-time character count with color-coded feedback
3. **Generate Audio**: Click "Generate Audio" or press Ctrl+Enter
4. **Loading State**: The button shows "Generating..." while processing
5. **Play Audio**: Use the built-in audio controls to play the generated speech
6. **Error Handling**: Any errors will be displayed with helpful messages

### Audio Recording & Upload
1. **Start Recording**: Click "Start Recording" button
2. **Grant Permission**: Allow microphone access when prompted by your browser
3. **Record Audio**: Speak into your microphone while watching the real-time timer
4. **Stop Recording**: Click "Stop Recording" when finished
5. **Automatic Playback**: Your recorded voice will automatically play back
6. **Upload to Server**: Click "Upload to Server" to save the audio file
7. **Server Processing**: File is validated, saved with unique UUID, and metadata returned
8. **Additional Controls**: Use "Play Again" to replay or "Record Again" for a new recording

### Tips for Best Experience
- **Microphone Quality**: Use a good quality microphone for better recording results
- **Quiet Environment**: Record in a quiet space to minimize background noise
- **Browser Permission**: Always allow microphone access for Echo Bot to work
- **Audio Format**: The app automatically selects the best supported audio format for your browser

## 🤝 Contributing

Feel free to contribute to this project by:
- Reporting bugs
- Suggesting new features
- Submitting pull requests
- Improving documentation

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

**Built with ❤️ using FastAPI, Murf AI, and Web Audio APIs**

### 🎯 Project Highlights
- **Dual Functionality**: Both AI-powered text-to-speech and real-time voice recording
- **Modern Web Technologies**: Leverages latest browser APIs for audio processing
- **Production Ready**: Comprehensive error handling and browser compatibility
- **User-Friendly**: Intuitive interface with clear visual feedback
- **Open Source**: MIT licensed and open for contributions