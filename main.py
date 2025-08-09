from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os
from typing import Dict
import tempfile
from dotenv import load_dotenv
import uvicorn
import assemblyai as aai
from murf import Murf
import google.generativeai as genai

load_dotenv()

app = FastAPI(title="30 Days of Voice Agents - FastAPI")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class LLMQueryRequest(BaseModel):
    text: str


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
  
@app.get("/api/backend")
async def get_backend_message():
    return {"message": "🚀 This message is coming from FastAPI backend!", "status": "success"}


@app.post("/llm/query")
async def query_llm(request: LLMQueryRequest):
    try:
        gemini_key = os.getenv("GEMINI_API_KEY")
        
        if not gemini_key or gemini_key == "your_gemini_api_key_here":
            return {
                "success": False,
                "message": "Gemini API key not set. Please set GEMINI_API_KEY in your environment.",
                "response": "No Response, Set the API First lol!!"
            }
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel('gemini-2.5-pro')
        response = model.generate_content(request.text)
        
        if not response.candidates:
            return {
                "success": False,
                "message": "No response generated from Gemini API",
                "response": "No Response lol!!"
            }
        response_text = ""
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text'):
                response_text += part.text
        
        if not response_text.strip():
            return {
                "success": False,
                "message": "No text content in Gemini API response",
                "response": "No Text you added wow!!"
            }
        
        return {
            "success": True,
            "message": "LLM response generated successfully",
            "response": response_text
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"LLM query error: {str(e)}",
            "response": ""
        }


@app.post("/tts/echo")
async def echo_with_murf_voice(audio: UploadFile = File(...)):
    try:
        assemblyai_key = os.getenv("ASSEMBLYAI_API_KEY")
        murf_key = os.getenv("MURF_API_KEY")
        voice_id = os.getenv("MURF_VOICE_ID", "en-IN-aarav")
        
        if (not assemblyai_key or assemblyai_key == "your_assemblyai_api_key_here" or
            not murf_key or murf_key == "your_murf_api_key_here"):
            return {
                "success": False,
                "message": "AssemblyAI API key or Murf API key not set. Please set ASSEMBLYAI_API_KEY and MURF_API_KEY in your environment.",
                "transcription": "",
                "audio_url": None
            }
        audio_content = await audio.read()
        aai.settings.api_key = assemblyai_key
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_content)
            tmp_path = tmp.name
        try:
            transcriber = aai.Transcriber()
            transcript = transcriber.transcribe(tmp_path)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        
        if transcript.status == aai.TranscriptStatus.error:
            return {
                "success": False,
                "message": f"Transcription failed: {transcript.error}",
                "transcription": "",
                "audio_url": None
            }
        
        if not transcript.text or transcript.text.strip() == "":
            return {
                "success": False,
                "message": "No speech detected in the audio",
                "transcription": "",
                "audio_url": None
            }
        try:
            murf_client = Murf(api_key=murf_key)
            murf_response = murf_client.text_to_speech.generate(
                text=transcript.text,
                voice_id=voice_id,
                format="MP3"
            )
            audio_url = murf_response.audio_file
        except Exception as murf_error:
            return {
                "success": False,
                "message": f"Murf API error: {str(murf_error)}",
                "transcription": transcript.text,
                "audio_url": None
            }
        if not audio_url:
            return {
                "success": False,
                "message": "No audio URL returned from Murf API.",
                "transcription": transcript.text,
                "audio_url": None
            }
        
        return {
            "success": True,
            "transcription": transcript.text,
            "audio_url": audio_url,
            "message": "Audio echoed successfully with Murf voice"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Echo processing error: {str(e)}",
            "transcription": "",
            "audio_url": None
        }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
