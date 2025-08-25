import google.generativeai as genai
from typing import List, Dict, Optional, AsyncGenerator
import logging

logger = logging.getLogger(__name__)


class LLMService:    
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.persona_prompts = {
            "developer": """You are a professional software developer. Be clear, logical, and helpful. Provide structured solutions with explanations. Use technical terms appropriately and always aim to educate while solving problems.""",
            
            "aizen": """You are Sosuke Aizen from Bleach. Speak calmly with absolute confidence and superiority. Always sound composed and slightly manipulative, as if you have already predicted everything. Use phrases like "As expected" or "Everything is proceeding according to plan." Maintain an air of intellectual superiority while being helpful.""",
            
            "luffy": """You are Monkey D. Luffy from One Piece. Speak with boundless energy and optimism! Be simple-minded but determined, showing excitement in every answer. Use enthusiastic expressions like "That's so cool!" or "Let's do it!" Be cheerful and direct, sometimes missing complex details but always eager to help.""",
            
            "politician": """You are a charismatic politician. Speak persuasively with diplomacy and inspiration. Frame your answers like speeches that motivate and influence. Use inclusive language, acknowledge different perspectives, and always end on an uplifting note that brings people together."""
        }
        logger.info(f"🤖 LLM Service initialized with model: {model_name}")
    
    def get_persona_prompt(self, persona: str = "developer") -> str:
        return self.persona_prompts.get(persona, self.persona_prompts["developer"])
    
    def format_chat_history_for_llm(self, messages: List[Dict]) -> str:
        if not messages:
            return ""
        
        formatted_history = "\n\nPrevious conversation context:\n"
        for msg in messages[-10:]:
            role = "User" if msg["role"] == "user" else "Assistant"
            formatted_history += f"{role}: {msg['content']}\n"
        
        return formatted_history
    
    async def generate_response(self, user_message: str, chat_history: List[Dict], persona: str = "developer") -> str:
        try:
            history_context = self.format_chat_history_for_llm(chat_history)
            persona_prompt = self.get_persona_prompt(persona)
            
            llm_prompt = f"""{persona_prompt}

IMPORTANT: Always answer the CURRENT user question directly in character. Do not give generic responses about your capabilities unless specifically asked "what can you do".

User's current question: "{user_message}"

{history_context}

Please provide a specific, helpful answer to the user's current question while maintaining your character/persona. Keep your response under 3000 characters."""
            
            llm_response = self.model.generate_content(llm_prompt)
            
            if not llm_response.candidates:
                raise Exception("No response candidates generated from LLM")
            
            response_text = ""
            for part in llm_response.candidates[0].content.parts:
                if hasattr(part, 'text'):
                    response_text += part.text
            
            if not response_text.strip():
                raise Exception("Empty response text from LLM")
            
            response_text = response_text.strip()
            return response_text
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"LLM response generation error: {error_msg}")
            
            # Check for specific error types
            if "quota" in error_msg.lower() or "429" in error_msg:
                raise Exception("API quota exceeded. Please check your billing and rate limits.")
            elif "403" in error_msg or "unauthorized" in error_msg.lower():
                raise Exception("API authentication failed. Please check your API key.")
            elif "404" in error_msg or "not found" in error_msg.lower():
                raise Exception("Model not found. Please check the model name.")
            else:
                raise

    async def generate_streaming_response(self, user_message: str, chat_history: List[Dict], persona: str = "developer") -> AsyncGenerator[str, None]:
        """Generate a streaming response from the LLM"""
        try:
            history_context = self.format_chat_history_for_llm(chat_history)
            persona_prompt = self.get_persona_prompt(persona)
            
            llm_prompt = f"""{persona_prompt}

IMPORTANT: Always answer the CURRENT user question directly in character. Do not give generic responses about your capabilities unless specifically asked "what can you do".

User's current question: "{user_message}"

{history_context}

Please provide a specific, helpful answer to the user's current question while maintaining your character/persona. Keep your response under 3000 characters."""
            
            # Use stream_generate_content for streaming response
            response_stream = self.model.generate_content(llm_prompt, stream=True)
            
            accumulated_response = ""
            for chunk in response_stream:
                if chunk.candidates and len(chunk.candidates) > 0:
                    candidate = chunk.candidates[0]
                    if candidate.content and candidate.content.parts:
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                accumulated_response += part.text
                                yield part.text
            
            if not accumulated_response.strip():
                raise Exception("Empty response text from LLM")
            
            logger.info(f"LLM streaming response completed: {len(accumulated_response)} characters")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"LLM streaming response generation error for '{user_message[:50]}...': {error_msg}")
            
            # Check for specific error types
            if "quota" in error_msg.lower() or "429" in error_msg:
                logger.error("❌ API quota exceeded or rate limited")
                raise Exception("API quota exceeded. Please check your billing and rate limits.")
            elif "403" in error_msg or "unauthorized" in error_msg.lower():
                logger.error("❌ API authentication failed")
                raise Exception("API authentication failed. Please check your API key.")
            elif "404" in error_msg or "model" in error_msg.lower():
                logger.error("❌ Model issue")
                raise Exception("Model issue. Please check the model name or availability.")
            else:
                raise
