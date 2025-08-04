# 30 Days of Voice Agents - Text-to-Speech Application

A modern web application built with FastAPI and Murf AI that converts text to high-quality speech. This project demonstrates the integration of a Python backend with Murf's text-to-speech API and features a responsive web interface.

## ✨ Features

- **Text-to-Speech Conversion**: Convert any text (up to 500 characters) to natural-sounding speech using Murf AI
- **Modern Web Interface**: Clean, responsive design with real-time character counting
- **FastAPI Backend**: High-performance async Python web framework
- **Real-time Feedback**: Loading states and error handling for better user experience
- **Audio Playback**: Built-in audio player with controls
- **Keyboard Shortcuts**: Press Ctrl+Enter to quickly generate audio
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
├── __pycache__/           # Python bytecode cache
└── README.md             # Project documentation
```

## 🔧 How It Works

1. **Frontend**: User enters text in the web interface (up to 500 characters)
2. **API Request**: JavaScript sends a POST request to `/api/generate` with the text
3. **Murf Integration**: FastAPI backend calls Murf AI's text-to-speech API
4. **Audio Response**: Generated audio is returned and played in the browser
5. **Error Handling**: Comprehensive error messages for various failure scenarios

## 🚀 Quick Start

### Prerequisites
- Python 3.7 or higher
- A Murf AI API key ([Get one here](https://murf.ai))

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

5. **Open your browser**
   
   Navigate to: `http://127.0.0.1:8000`

## � API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Serves the main HTML page |
| `POST` | `/api/generate` | Generate speech from text using Murf AI |
| `GET` | `/api/backend` | Test endpoint for backend connectivity |
| `GET` | `/docs` | Interactive API documentation (Swagger UI) |
| `GET` | `/redoc` | Alternative API documentation (ReDoc) |

### Text-to-Speech API (`/api/generate`)

**Request Body:**
```json
{
  "text": "Hello, this is a test message",
  "speed": 1.0,    // Optional, defaults to 1.0
  "pitch": 1.0     // Optional, defaults to 1.0
}
```

**Response (Success):**
```json
{
  "status": "success",
  "message": "Audio generated successfully",
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

- **[FastAPI](https://fastapi.tiangolo.com/)**: Modern, fast web framework for building APIs with Python
- **[Murf AI SDK](https://murf.ai)**: Official Python SDK for text-to-speech conversion
- **[Uvicorn](https://www.uvicorn.org/)**: Lightning-fast ASGI server for production
- **[Jinja2](https://jinja.palletsprojects.com/)**: Template engine for dynamic HTML rendering
- **[python-dotenv](https://pypi.org/project/python-dotenv/)**: Environment variable management
- **HTML5 & CSS3**: Modern web standards with responsive design
- **Vanilla JavaScript**: Frontend interactivity without external frameworks

## 🎨 Frontend Features

- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **Real-time Character Counter**: Visual feedback with color-coded limits (green/yellow/red)
- **Loading States**: Visual feedback during audio generation
- **Error Handling**: User-friendly error messages for various scenarios
- **Keyboard Shortcuts**: Ctrl+Enter to quickly generate audio
- **Audio Controls**: Built-in HTML5 audio player with standard controls
- **Smooth Animations**: CSS transitions for better user experience

## 📦 Dependencies

This project uses the following Python packages (see `requirements.txt`):

```
fastapi==0.104.1          # Web framework for building APIs
uvicorn[standard]==0.24.0 # ASGI server for FastAPI
jinja2==3.1.2             # Template engine for HTML rendering
python-multipart==0.0.6   # For handling form data
python-dotenv==1.0.0      # Environment variable management
murf==2.0.0               # Official Murf AI Python SDK
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

1. **"MURF_API_KEY environment variable not set"**
   - Make sure you have created a `.env` file in the project root
   - Verify your API key is correctly set in the `.env` file

2. **"Could not connect to backend"**
   - Ensure the FastAPI server is running on `http://127.0.0.1:8000`
   - Check the browser console for detailed error messages

3. **Audio generation fails**
   - Verify your Murf API key is valid and has sufficient credits
   - Check that your text doesn't exceed the 500 character limit

### Logging

The application includes console logging for debugging. Check the browser console and terminal output for detailed error information.

## 📝 Usage

1. **Enter Text**: Type or paste your text into the textarea (max 500 characters)
2. **Character Counter**: Watch the real-time character count with color-coded feedback
3. **Generate Audio**: Click "Generate Audio" or press Ctrl+Enter
4. **Loading State**: The button shows "Generating..." while processing
5. **Play Audio**: Use the built-in audio controls to play the generated speech
6. **Error Handling**: Any errors will be displayed with helpful messages

## 🤝 Contributing

Feel free to contribute to this project by:
- Reporting bugs
- Suggesting new features
- Submitting pull requests
- Improving documentation

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

**Built with ❤️ using FastAPI and Murf AI**