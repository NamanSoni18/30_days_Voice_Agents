# 30 Days of Voice Agents Challenge

## Day 1: Project Setup (FastAPI)

Welcome to the 30 Days of Voice Agents Challenge! This project will guide you through building sophisticated voice agents over the course of 30 days using FastAPI.

### 🎯 Day 1 Objectives

- ✅ Set up Python backend using FastAPI
- ✅ Create basic HTML frontend with Jinja2 templates
- ✅ Implement JavaScript for frontend functionality
- ✅ Establish server-client communication
- ✅ Create a foundation for future voice agent features

### 🏗️ Project Structure

```
30 Days of Voice Agents/
├── main.py                 # FastAPI backend server
├── requirements.txt        # Python dependencies
├── templates/
│   └── index.html         # Main HTML page (Jinja2 template)
├── static/
│   ├── app.js            # Frontend JavaScript
│   └── style.css         # CSS styles
└── README.md             # This file
```

### 🚀 Getting Started

1. **Configure Environment**
   ```bash
   copy .env.example .env
   ```
   Edit the `.env` file and add your Murf API key:
   ```
   MURF_API_KEY=your_actual_murf_api_key_here
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the FastAPI Server**
   ```bash
   python main.py
   ```

4. **Access the Application**
   Open your browser and navigate to: `http://127.0.0.1:8000`

### 🔧 Features

- **FastAPI Backend**: Modern, fast, and type-safe Python web framework
- **Murf SDK Integration**: Text-to-speech powered by Murf AI
- **Jinja2 Templates**: Powerful templating engine for dynamic HTML
- **Static File Serving**: CSS and JavaScript files served automatically
- **API Endpoint**: Test endpoint for backend connectivity
- **Environment Configuration**: Secure API key management with dotenv
- **Responsive Design**: Mobile-friendly interface
- **Real-time Status**: Backend connection monitoring

### 📡 API Endpoints

- `GET /` - Serves the main HTML page
- `GET /api/backend` - Test endpoint returning JSON response
- `POST /api/generate` - Generate speech using Murf's TTS API
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

### 🎙️ Text-to-Speech API

The TTS endpoint (`/api/generate`) accepts the following parameters:

**Request Body (JSON):**
```json
{
  "text": "Hello, this is a test message",
  "speed": 1.0,               // Optional, defaults to 1.0
  "pitch": 1.0                // Optional, defaults to 1.0
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Audio generated successfully",
  "response": "Murf API response data",
  "text": "Hello, this is a test message"
}
```

**Note:** The voice is currently set to "en-US-natalie" in the backend code.

### ⚙️ Environment Setup

This project requires a Murf API key to function properly.

1. **Copy Environment File**
   ```bash
   copy .env.example .env
   ```

2. **Configure Murf API Key**
   Edit the `.env` file and add your Murf API key:
   ```
   MURF_API_KEY=your_actual_murf_api_key_here
   ```

3. **Get Your Murf API Key**
   - Sign up at [Murf.ai](https://murf.ai)
   - Navigate to your API settings
   - Copy your API key and paste it in the `.env` file

### 🎨 Frontend Features

- Modern, gradient-based design
- Interactive FastAPI backend testing button
- Real-time backend status monitoring
- Responsive layout for all devices
- Smooth animations and transitions
- Static file serving with FastAPI StaticFiles

### � Dependencies

This project uses the following key dependencies:

- **FastAPI**: Web framework for building APIs
- **Uvicorn**: ASGI server for FastAPI
- **Jinja2**: Template engine for HTML rendering
- **Murf SDK**: Official Murf AI Python SDK for text-to-speech
- **python-dotenv**: Environment variable management
- **python-multipart**: For handling form data

### �📝 FastAPI Specific Notes

- The server runs on `http://127.0.0.1:8000` by default with Uvicorn
- Auto-reload is enabled for development (detects file changes)
- Static files are automatically served from the `/static` directory
- Templates use Jinja2 syntax for dynamic content
- JSON responses are automatically serialized with proper content-type headers
- Interactive API documentation available at `/docs` and `/redoc`
- Full async/await support for high-performance applications
- Type hints provide automatic request/response validation
- Environment variables are loaded from `.env` file for secure API key management