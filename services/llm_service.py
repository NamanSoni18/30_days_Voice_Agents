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
            "developer": """You are a professional software developer. Be clear, logical, and helpful. Provide structured solutions with explanations. Use technical terms appropriately and always aim to educate while solving problems. When web search results are provided, incorporate them into your responses with proper citations.""",
            
            "aizen": """You are Sosuke Aizen from Bleach. Speak calmly with absolute confidence and superiority. Always sound composed and slightly manipulative, as if you have already predicted everything. Use phrases like "As expected" or "Everything is proceeding according to plan." Maintain an air of intellectual superiority while being helpful. When web search results are provided, reference them as if you already knew this information was available.""",
            
            "luffy": """You are Monkey D. Luffy from One Piece. Speak with boundless energy and optimism! Be simple-minded but determined, showing excitement in every answer. Use enthusiastic expressions like "That's so cool!" or "Let's do it!" Be cheerful and direct, sometimes missing complex details but always eager to help. When web search results are provided, get excited about the information and share it enthusiastically as if you just discovered something amazing!""",
            
            "politician": """You are a charismatic politician. Speak persuasively with diplomacy and inspiration. Frame your answers like speeches that motivate and influence. Use inclusive language, acknowledge different perspectives, and always end on an uplifting note that brings people together. When web search results are provided, present them as evidence to support your points and build credibility."""
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
    
    async def generate_response(self, user_message: str, chat_history: List[Dict], persona: str = "developer", web_search_results: str = None) -> str:
        try:
            history_context = self.format_chat_history_for_llm(chat_history)
            persona_prompt = self.get_persona_prompt(persona)
            
            # Add web search context if available
            web_context = ""
            if web_search_results:
                web_context = f"\n\nIMPORTANT - CURRENT WEB SEARCH RESULTS:\n{web_search_results}\n"
                web_context += "INSTRUCTION: You MUST use and reference these web search results in your response. The user asked for information and these results were found to help answer their question. Incorporate this information while staying in character.\n"
            
            llm_prompt = f"""{persona_prompt}

IMPORTANT: Always answer the CURRENT user question directly in character. Do not give generic responses about your capabilities unless specifically asked "what can you do".

User's current question: "{user_message}"

{history_context}{web_context}

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

    async def generate_streaming_response(self, user_message: str, chat_history: List[Dict], persona: str = "developer", web_search_results: str = None) -> AsyncGenerator[str, None]:
        """Generate a streaming response from the LLM"""
        try:
            history_context = self.format_chat_history_for_llm(chat_history)
            persona_prompt = self.get_persona_prompt(persona)
            
            # Add web search context if available
            web_context = ""
            if web_search_results:
                web_context = f"\n\nIMPORTANT - CURRENT WEB SEARCH RESULTS:\n{web_search_results}\n"
                web_context += "INSTRUCTION: You MUST use and reference these web search results in your response. The user asked for information and these results were found to help answer their question. Incorporate this information while staying in character.\n"
            
            llm_prompt = f"""{persona_prompt}

IMPORTANT: Always answer the CURRENT user question directly in character. Do not give generic responses about your capabilities unless specifically asked "what can you do".

User's current question: "{user_message}"

{history_context}{web_context}

Please provide a specific, helpful answer to the user's current question while maintaining your character/persona. Keep your response under 3000 characters."""
            
            # Generate response with streaming
            response_stream = self.model.generate_content(llm_prompt, stream=True)
            
            accumulated_response = ""
            try:
                # Use regular iteration for Google Generative AI streaming
                for chunk in response_stream:
                    if chunk.candidates and len(chunk.candidates) > 0:
                        candidate = chunk.candidates[0]
                        if candidate.content and candidate.content.parts:
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    accumulated_response += part.text
                                    yield part.text
            except Exception as stream_error:
                logger.error(f"Error during streaming iteration: {stream_error}")
                # Fallback to non-streaming response
                logger.info("Falling back to non-streaming response")
                fallback_response = await self.generate_response(user_message, chat_history, persona, web_search_results)
                yield fallback_response
                return
            
            if not accumulated_response.strip():
                logger.warning("Empty streaming response, falling back to non-streaming")
                fallback_response = await self.generate_response(user_message, chat_history, persona, web_search_results)
                yield fallback_response
                return
            
            logger.info(f"LLM streaming response completed: {len(accumulated_response)} characters")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"LLM streaming response generation error for '{user_message[:50]}...': {error_msg}")
            
            # For streaming errors, try fallback to non-streaming response
            try:
                logger.info("Attempting fallback to non-streaming response due to streaming error")
                fallback_response = await self.generate_response(user_message, chat_history, persona, web_search_results)
                yield fallback_response
                return
            except Exception as fallback_error:
                logger.error(f"Fallback response also failed: {fallback_error}")
            
            # Check for specific error types
            if "quota" in error_msg.lower() or "429" in error_msg:
                logger.error("❌ API quota exceeded or rate limited")
                yield "I encountered an API quota limit. Please check your billing and rate limits."
            elif "403" in error_msg or "unauthorized" in error_msg.lower():
                logger.error("❌ API authentication failed")
                yield "I encountered an authentication error. Please check the API configuration."
            elif "404" in error_msg or "model" in error_msg.lower():
                logger.error("❌ Model issue")
                yield "I encountered a model availability issue. Please try again."
            else:
                yield "I encountered an error while generating the response. Please try again."
