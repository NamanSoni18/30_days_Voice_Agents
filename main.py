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


def truncate_text_for_murf(text: str, max_chars: int = 3000) -> str:
    """Truncate text to fit within Murf's character limit while preserving sentence structure."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_sentence_end = max(
        truncated.rfind('.'),
        truncated.rfind('!'),
        truncated.rfind('?')
    )
    
    if last_sentence_end > max_chars * 0.7: 
        return truncated[:last_sentence_end + 1]
    else:
        last_space = truncated.rfind(' ')
        if last_space > 0:
            return truncated[:last_space] + "..."
        else:
            return truncated + "..."


@app.post("/llm/query")
async def query_llm_with_audio(audio: UploadFile = File(...)):
    try:
        gemini_key = os.getenv("GEMINI_API_KEY")
        assemblyai_key = os.getenv("ASSEMBLYAI_API_KEY")
        murf_key = os.getenv("MURF_API_KEY")
        voice_id = os.getenv("MURF_VOICE_ID", "en-IN-aarav")
        
        if (not gemini_key or gemini_key == "your_gemini_api_key_here" or
            not assemblyai_key or assemblyai_key == "your_assemblyai_api_key_here" or
            not murf_key or murf_key == "your_murf_api_key_here"):
            return {
                "success": False,
                "message": "Required API keys not set. Please set GEMINI_API_KEY, ASSEMBLYAI_API_KEY, and MURF_API_KEY in your environment.",
                "transcription": "",
                "llm_response": "",
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
                "llm_response": "",
                "audio_url": None
            }
        
        if not transcript.text or transcript.text.strip() == "":
            return {
                "success": False,
                "message": "No speech detected in the audio",
                "transcription": "",
                "llm_response": "",
                "audio_url": None
            }
        
        transcribed_text = transcript.text
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        llm_prompt = f"""Please provide a helpful and well-formatted response to the following user message. 
                        Guidelines:
                        - Keep your response under 3000 characters to ensure it can be converted to speech effectively
                        - Use Markdown formatting when appropriate:
                          - Use **bold** for emphasis
                          - Use `code` for technical terms or code snippets
                          - Use bullet points (-) or numbered lists (1.) when listing items
                          - Use code blocks (```) for longer code examples
                          - Use headers (##) for sections if needed
                          - Use tables when organizing data
                        - Structure your response clearly and logically
                        - Be concise but comprehensive
                        
                        User message: {transcribed_text}"""
        llm_response = model.generate_content(llm_prompt)
        if not llm_response.candidates:
            return {
                "success": False,
                "message": "No response generated from LLM",
                "transcription": transcribed_text,
                "llm_response": "",
                "audio_url": None
            }
        response_text = ""
        for part in llm_response.candidates[0].content.parts:
            if hasattr(part, 'text'):
                response_text += part.text
        
        if not response_text.strip():
            return {
                "success": False,
                "message": "No text content in LLM response",
                "transcription": transcribed_text,
                "llm_response": "",
                "audio_url": None
            }
        murf_text = truncate_text_for_murf(response_text)
        try:
            murf_client = Murf(api_key=murf_key)
            murf_response = murf_client.text_to_speech.generate(
                text=murf_text,
                voice_id=voice_id,
                format="MP3"
            )
            audio_url = murf_response.audio_file
        except Exception as murf_error:
            return {
                "success": False,
                "message": f"Murf API error: {str(murf_error)}",
                "transcription": transcribed_text,
                "llm_response": response_text,
                "audio_url": None
            }
        if not audio_url:
            return {
                "success": False,
                "message": "No audio URL returned from Murf API",
                "transcription": transcribed_text,
                "llm_response": response_text,
                "audio_url": None
            }
        
        return {
            "success": True,
            "message": "Voice query processed successfully",
            "transcription": transcribed_text,
            "llm_response": response_text,
            "audio_url": audio_url
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Voice query processing error: {str(e)}",
            "transcription": "",
            "llm_response": "",
            "audio_url": None
        }


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
