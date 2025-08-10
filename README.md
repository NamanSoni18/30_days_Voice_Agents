# 30 Days of Voice Agents - AI Voice Agent Application

A modern web application built with FastAPI, Murf AI, AssemblyAI, and Google Gemini that creates an intelligent AI Voice Agent. Record your voice questions and get AI-powered responses with natural text-to-speech playback! This project demonstrates seamless integration between speech-to-text, large language models, and text-to-speech AI services with advanced Markdown rendering and real-time processing feedback.

## ✨ Features

### 🤖 AI Voice Agent
- **Voice Recording**: Record audio questions directly from your microphone using browser's MediaRecorder API
- **Real-time Timer**: See recording duration with a visual recording indicator and pulsing animation
- **AI Transcription**: Convert your speech to text using AssemblyAI's advanced speech recognition
- **Smart AI Responses**: Get intelligent, well-formatted answers from Google Gemini with Markdown support
- **Natural Voice Playback**: Hear responses in natural-sounding voices using Murf AI text-to-speech
- **Complete Voice Loop**: Record → Transcribe → Process with AI → Generate Speech → Play back
- **Advanced Loading States**: Step-by-step visual feedback showing transcription, analysis, generation, and speech creation

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
- **Responsive Design**: Optimized for desktop, tablet, and mobile devices
- **Loading Animations**: Professional spinning loaders and animated progress indicators
- **Error Handling**: Comprehensive error messages with visual feedback

### 🔧 Technical Features
- **FastAPI Backend**: High-performance async Python web framework with automatic API documentation
- **Modern JavaScript**: Clean, vanilla JavaScript with advanced audio processing
- **Cross-browser Support**: Works on Chrome, Firefox, Safari, and other modern browsers
- **Environment-based Configuration**: Secure API key management for all services
- **No File Storage**: Direct audio processing without saving files on server
- **Syntax Highlighting**: Code blocks with professional highlighting using Highlight.js

## 📁 Project Structure

```
30 Days of Voice Agents/
├── main.py                 # FastAPI backend server with AI Voice Agent endpoint
├── requirements.txt        # Python dependencies (FastAPI, Murf, AssemblyAI, Gemini)
├── .env                   # Environment variables (API keys)
├── .env.example           # Example environment configuration
├── .gitignore             # Git ignore patterns
├── templates/
│   └── index.html         # Main HTML page with Voice Agent interface and Markdown support
├── static/
│   ├── app.js            # Frontend JavaScript for recording, processing, and Markdown rendering
│   └── style.css         # CSS styles with Markdown formatting and loading animations
├── __pycache__/           # Python bytecode cache
└── README.md             # Project documentation
```

## 🔧 How It Works

### AI Voice Agent Workflow
1. **Recording**: User clicks "Start Voice Query" and speaks their question into microphone
2. **Audio Capture**: Browser's MediaRecorder API captures audio with real-time timer
3. **Processing Feedback**: Visual step-by-step progress shows:
   - Transcribing audio using AssemblyAI
   - Analyzing question with AI
   - Generating response with Google Gemini
   - Creating speech with Murf AI
4. **AI Processing**: FastAPI backend processes the complete pipeline:
   - Speech-to-text conversion via AssemblyAI
   - Smart prompt engineering for Markdown-formatted responses
   - AI response generation via Google Gemini (configurable model)
   - Text-to-speech conversion via Murf AI
5. **Rich Display**: Results shown with:
   - Original transcription of user's question
   - AI response with full Markdown rendering (lists, code, tables, etc.)
   - Natural voice audio playback of the response
6. **Error Handling**: Comprehensive error messages for various scenarios

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

3. **Set up your API keys**
   
   Create a `.env` file in the project root:
   ```bash
   MURF_API_KEY=your_actual_murf_api_key_here
   ASSEMBLYAI_API_KEY=your_actual_assemblyai_api_key_here
   MURF_VOICE_ID=en-IN-aarav
   GEMINI_API_KEY=your_actual_gemini_api_key_here
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
| `GET` | `/` | Serves the main application HTML page |
| `POST` | `/llm/query` | Complete AI Voice Agent workflow: transcribe audio, process with AI, and generate speech response |
| `GET` | `/api/backend` | Test endpoint for backend connectivity |
| `GET` | `/docs` | Interactive API documentation (Swagger UI) |
| `GET` | `/redoc` | Alternative API documentation (ReDoc) |

### AI Voice Agent API (`/llm/query`)

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
- **[AssemblyAI](https://www.assemblyai.com/)**: AI-powered speech-to-text transcription service
- **[Murf AI](https://murf.ai)**: Text-to-speech API for natural voice generation (using "en-IN-aarav" voice)
- **[Google Gemini](https://ai.google.dev/)**: Advanced large language model for text-based AI queries (using Gemini 2.5 Pro)
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

## 🐛 Troubleshooting

### Common Issues

#### API Key Related
1. **"MURF_API_KEY environment variable not set", "AssemblyAI API key not set", or "Gemini API key not set"**
   - Make sure you have created a [`.env`](.env) file in the project root
   - Verify your API keys are correctly set in the `.env` file
   - Ensure your API keys are not set to placeholder values like "your_murf_api_key_here"

#### Echo Bot Related
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

#### LLM Query Related
8. **"No response generated from Gemini API"**
   - Verify your Gemini API key is valid and active
   - Check that your query text is not empty
   - Ensure you have sufficient API quota/credits

9. **"LLM query error"**
   - Check your internet connection
   - Verify the Gemini API service is not experiencing outages
   - Ensure your API key has the correct permissions

#### General API Errors
10. **Murf API errors**
    - Verify your Murf API key is valid and has sufficient credits
    - Check that your Murf account is active and in good standing

11. **AssemblyAI API errors**
    - Verify your AssemblyAI API key is valid
    - Check that you have sufficient API credits
    - Ensure the audio file format is supported

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
- **Advanced Markdown Support**: Rich text formatting with syntax highlighting for technical content
- **Real-time Processing Feedback**: Step-by-step visual progress with professional loading animations
- **Modern Web Technologies**: Leverages latest browser APIs for audio recording and processing
- **No File Storage**: Direct audio processing without server-side file storage for better performance and privacy
- **Production Ready**: Comprehensive error handling and browser compatibility
- **User-Friendly**: Intuitive interface with clear visual feedback and real-time recording indicators
- **Voice Quality**: Uses Murf AI's high-quality voices for natural-sounding responses
- **Intelligent Responses**: Powered by Google Gemini with smart prompt engineering for formatted output
- **Cross-Platform**: Works seamlessly across desktop, tablet, and mobile devices
- **Professional UI**: Modern design with animations, transitions, and responsive layouts