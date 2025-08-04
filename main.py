from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
import os
from typing import Optional
from dotenv import load_dotenv
import murf

load_dotenv()

app = FastAPI(title="30 Days of Voice Agents - FastAPI")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class TextToSpeechRequest(BaseModel):
    text: str
    speed: Optional[float] = 1.0
    pitch: Optional[float] = 1.0

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
  
@app.get("/api/backend")
async def get_backend_message():
    return {"message": "🚀 This message is coming from FastAPI backend!", "status": "success"}

@app.post("/api/generate")
async def text_to_speech(request: TextToSpeechRequest):
    murf_api_key = os.getenv("MURF_API_KEY")
    if not murf_api_key:
        raise HTTPException(
            status_code=500, 
            detail="MURF_API_KEY environment variable not set"
        )
    
    try:
        client = murf.Murf(api_key=murf_api_key)
        response = client.text_to_speech.generate(
            text=request.text,
            voice_id="en-US-natalie",  # Using a common voice ID
        )
        
        return {
            "status": "success",
            "message": "Audio generated successfully",
            "response": response.audio_file,
            "text": request.text
        }
                
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Murf SDK error: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
