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

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the FastAPI Server**
   ```bash
   python main.py
   ```

3. **Access the Application**
   Open your browser and navigate to: `http://127.0.0.1:8000`

### 🔧 Features

- **FastAPI Backend**: Modern, fast, and type-safe Python web framework
- **Jinja2 Templates**: Powerful templating engine for dynamic HTML
- **Static File Serving**: CSS and JavaScript files served automatically
- **API Endpoint**: Test endpoint for backend connectivity
- **Responsive Design**: Mobile-friendly interface
- **Real-time Status**: Backend connection monitoring

### 📡 API Endpoints

- `GET /` - Serves the main HTML page
- `GET /api/backend` - Test endpoint returning JSON response
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

### 🎨 Frontend Features

- Modern, gradient-based design
- Interactive FastAPI backend testing button
- Real-time backend status monitoring
- Responsive layout for all devices
- Smooth animations and transitions
- Static file serving with FastAPI StaticFiles

### 📝 FastAPI Specific Notes

- The server runs on `http://127.0.0.1:8000` by default with Uvicorn
- Auto-reload is enabled for development (detects file changes)
- Static files are automatically served from the `/static` directory
- Templates use Jinja2 syntax for dynamic content
- JSON responses are automatically serialized with proper content-type headers
- Interactive API documentation available at `/docs` and `/redoc`
- Full async/await support for high-performance applications
- Type hints provide automatic request/response validation