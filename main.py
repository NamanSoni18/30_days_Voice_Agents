from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import requests
import os
import uuid
from typing import Dict
from dotenv import load_dotenv
import uvicorn

load_dotenv()

app = FastAPI(title="30 Days of Voice Agents - FastAPI")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class TTSRequest(BaseModel):
    text: str

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
  
@app.get("/api/backend")
async def get_backend_message():
    return {"message": "🚀 This message is coming from FastAPI backend!", "status": "success"}

@app.post("/tts/generate")
async def generate_tts(request: TTSRequest):
    api_key = os.getenv("MURF_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Murf API key not set.")
    url = "https://api.murf.ai/v1/speech/generate"
    payload = {
        "text": request.text,
        "voiceId": "en-US-natalie",  
        "format": "mp3"
    }
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    data = response.json()
    audio_url = data.get("audioFile")
    if not audio_url:
        raise HTTPException(status_code=500, detail="No audio URL returned.")
    return {"audio_url": audio_url}

@app.post("/upload-audio")
async def upload_audio_file(audio: UploadFile = File(...)) -> Dict:
    try:
        unique_filename = f"{uuid.uuid4()}.wav"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        content = await audio.read()
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        file_size = os.path.getsize(file_path)
        
        return {
            "success": True,
            "filename": unique_filename,
            "original_filename": audio.filename,
            "content_type": audio.content_type,
            "size": file_size,
            "message": "Audio file uploaded successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
