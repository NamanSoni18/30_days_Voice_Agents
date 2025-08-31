import asyncio
import websockets
import json
import base64
import uuid
from typing import Optional, AsyncGenerator
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class MurfWebSocketService:
    """Murf WebSocket TTS service for streaming text-to-speech"""
    
    def __init__(self, api_key: str, voice_id: str = "en-US-amara"):
        self.api_key = api_key
        self.voice_id = voice_id
        self.ws_url = "wss://api.murf.ai/v1/speech/stream-input"
        self.websocket = None
        self.is_connected = False
        # Use session-specific context IDs to avoid context limit exceeded errors
        self.current_context_id = None
        self.active_contexts = set()  # Track active contexts
        # Add a lock to prevent concurrent recv() calls
        self._recv_lock = asyncio.Lock()
        self._connecting = False
        
    async def connect(self):
        """Establish WebSocket connection to Murf"""
        # Prevent multiple concurrent connections
        if self._connecting or self.is_connected:
            logger.info("Already connected or connecting to Murf WebSocket")
            return
            
        self._connecting = True
        try:
            connection_url = f"{self.ws_url}?api-key={self.api_key}&sample_rate=44100&channel_type=MONO&format=WAV"
            self.websocket = await websockets.connect(connection_url)
            self.is_connected = True
            logger.info("[SUCCESS] Connected to Murf WebSocket")
            
            # Only clear context on first connection, not every time
            # await self.clear_context()
            
            # Send initial voice configuration
            await self._send_voice_config()
            
        except Exception as e:
            logger.error(f"Failed to connect to Murf WebSocket: {str(e)}")
            self.is_connected = False
            raise
        finally:
            self._connecting = False
    
    async def ensure_connected(self):
        """Ensure WebSocket is connected, reconnect if necessary"""
        if not self.is_connected or not self.websocket or self.websocket.closed:
            logger.info("WebSocket not connected, attempting to reconnect...")
            await self.connect()
        elif self.websocket.open:
            # Test connection with a ping
            try:
                await self.websocket.ping()
                logger.debug("WebSocket connection is healthy")
            except Exception as e:
                logger.warning(f"WebSocket ping failed: {e}, reconnecting...")
                await self.connect()
        else:
            logger.info("WebSocket connection state unknown, reconnecting...")
            await self.connect()
    
    async def _send_voice_config(self, context_id: str = None):
        """Send voice configuration to Murf WebSocket"""
        try:
            if context_id is None:
                context_id = f"voice_agent_context_{uuid.uuid4().hex[:8]}"
            
            # Always clear all contexts before creating a new one to prevent limit exceeded
            if self.active_contexts:
                logger.info(f"Clearing {len(self.active_contexts)} active contexts before creating new one")
                await self._clear_all_contexts()
            
            self.current_context_id = context_id
            self.active_contexts.add(context_id)
            
            voice_config_msg = {
                "voice_config": {
                    "voiceId": self.voice_id,
                    "style": "Conversational",
                    "rate": 0,
                    "pitch": 0,
                    "variation": 1
                },
                "context_id": context_id
            }
            logger.info(f"Sending voice config with context_id: {context_id}")
            await self.websocket.send(json.dumps(voice_config_msg))
            
            # Wait for acknowledgment with shorter timeout
            try:
                async with self._recv_lock:
                    response = await asyncio.wait_for(self.websocket.recv(), timeout=3.0)
                    data = json.loads(response)
                    logger.info(f"Voice config response: {data}")
                    
                    # Check for context limit exceeded error
                    if "error" in data and "Exceeded Active context limit" in data["error"]:
                        logger.warning(f"Context limit exceeded, clearing all contexts and retrying")
                        await self._clear_all_contexts()
                        # Retry with a new context ID after clearing
                        new_context_id = f"voice_agent_context_{uuid.uuid4().hex[:8]}"
                        await self._send_voice_config(new_context_id)
                        return
                        
            except asyncio.TimeoutError:
                logger.warning("Voice config acknowledgment timeout - continuing anyway")
                # Don't fail here, continue with TTS processing
            
        except Exception as e:
            logger.error(f"Failed to send voice config: {str(e)}")
            raise
    
    async def ensure_connected(self):
        """Ensure WebSocket is connected, reconnect if necessary"""
        # Check connection status more safely
        needs_reconnect = False
        
        if not self.is_connected or not self.websocket:
            needs_reconnect = True
        else:
            # Safely check if websocket is closed
            try:
                is_closed = getattr(self.websocket, 'closed', False)
                if is_closed:
                    needs_reconnect = True
            except Exception:
                # If we can't check the status, assume we need to reconnect
                needs_reconnect = True
        
        if needs_reconnect:
            logger.info("WebSocket not connected, attempting to reconnect...")
            await self.connect()
    
    async def disconnect(self):
        """Close WebSocket connection"""
        try:
            if self.websocket and self.is_connected:
                await self.websocket.close()
                self.is_connected = False
                logger.info("Disconnected from Murf WebSocket")
        except Exception as e:
            logger.error(f"Error disconnecting from Murf WebSocket: {str(e)}")
    
    async def stream_text_to_audio(self, text_stream: AsyncGenerator[str, None], session_id: str = None) -> AsyncGenerator[dict, None]:
        """
        Stream text chunks to Murf and yield base64 audio responses
        """
        if not self.is_connected:
            raise Exception("WebSocket not connected. Call connect() first.")
        
        try:
            # Generate a unique context ID for this session to avoid conflicts
            context_id = f"voice_agent_context_{uuid.uuid4().hex[:8]}"
            
            # Always ensure we have a fresh context for each request
            await self._send_voice_config(context_id)
            
            accumulated_text = ""
            chunk_count = 0
            
            # Collect all text chunks first
            text_chunks = []
            async for text_chunk in text_stream:
                if text_chunk:
                    text_chunks.append(text_chunk)
                    accumulated_text += text_chunk
                    chunk_count += 1
            
            logger.info(f"Collected {chunk_count} text chunks, total length: {len(accumulated_text)}")
            
            # Send all text in one message (better for TTS quality)
            text_msg = {
                "context_id": context_id,
                "text": accumulated_text,
                "end": True  # End context immediately after sending to free up resources
            }
            
            logger.info(f"Sending complete text ({len(accumulated_text)} chars): {accumulated_text[:100]}...")
            await self.websocket.send(json.dumps(text_msg))
            
            # Listen for audio responses with timeout
            audio_received = False
            timeout_count = 0
            max_timeouts = 2
            
            async for audio_response in self._listen_for_audio_with_timeout():
                audio_received = True
                yield audio_response
                # Break on final audio chunk
                if audio_response.get("type") == "audio_chunk" and audio_response.get("is_final"):
                    break
                elif audio_response.get("type") == "timeout":
                    timeout_count += 1
                    if timeout_count >= max_timeouts:
                        logger.error(f"Too many timeouts ({timeout_count}), giving up on TTS")
                        break
            
            if not audio_received:
                logger.error("No audio chunks received from Murf WebSocket")
                raise Exception("No audio response received from TTS service")
            
            # Immediately clear the context after successful completion
            try:
                await self._clear_specific_context(context_id)
                logger.info(f"Successfully cleared context {context_id} after TTS completion")
            except Exception as e:
                logger.warning(f"Failed to clear context {context_id} after completion: {e}")
            
        except Exception as e:
            logger.error(f"Error in stream_text_to_audio: {str(e)}")
            # Try to clear the context even on error
            try:
                if 'context_id' in locals():
                    await self._clear_specific_context(context_id)
            except:
                pass
            raise
    
    def get_current_context_id(self) -> Optional[str]:
        """Get the current context ID"""
        return self.current_context_id
    
    async def _listen_for_audio_with_timeout(self) -> AsyncGenerator[dict, None]:
        """Listen for audio with better timeout handling"""
        audio_chunk_count = 0
        total_audio_size = 0
        
        try:
            while True:
                try:
                    # Use recv lock to prevent concurrent recv() calls
                    async with self._recv_lock:
                        response = await asyncio.wait_for(self.websocket.recv(), timeout=30.0)  # Reduced timeout for better responsiveness
                    
                    data = json.loads(response)
                    logger.debug(f"📥 Received response: {list(data.keys())}")
                    
                    if "audio" in data:
                        audio_chunk_count += 1
                        audio_base64 = data["audio"]
                        total_audio_size += len(audio_base64)
                        
                        # Yield the response
                        yield {
                            "type": "audio_chunk",
                            "audio_base64": audio_base64,
                            "context_id": data.get("context_id"),
                            "chunk_number": audio_chunk_count,
                            "chunk_size": len(audio_base64),
                            "total_size": total_audio_size,
                            "timestamp": datetime.now().isoformat(),
                            "is_final": data.get("final", False)
                        }
                        
                        # Check if this is the final audio chunk
                        if data.get("final"):
                            logger.info(f"Received final audio chunk. Total chunks: {audio_chunk_count}, Total size: {total_audio_size}")
                            break
                    
                    elif "error" in data:
                        logger.error(f"Murf WebSocket error: {data['error']}")
                        yield {
                            "type": "error",
                            "error": data["error"],
                            "timestamp": datetime.now().isoformat()
                        }
                        break
                    
                    else:
                        # Non-audio response
                        logger.debug(f"Received non-audio response: {data}")
                        yield {
                            "type": "status",
                            "data": data,
                            "timestamp": datetime.now().isoformat()
                        }
                
                except asyncio.TimeoutError:
                    logger.warning("Timeout waiting for Murf response")
                    yield {
                        "type": "timeout",
                        "timestamp": datetime.now().isoformat()
                    }
                    # Continue waiting for a bit more
                    continue
                    
                except websockets.exceptions.ConnectionClosed:
                    logger.warning("WebSocket connection closed unexpectedly")
                    self.is_connected = False
                    break
                    
                except Exception as e:
                    logger.error(f"Error receiving response: {str(e)}")
                    yield {
                        "type": "error", 
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                    break
        
        except Exception as e:
            logger.error(f"Fatal error in audio listening: {str(e)}")
            yield {
                "type": "error",
                "error": f"Fatal error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _listen_for_audio(self) -> AsyncGenerator[dict, None]:
        audio_chunk_count = 0
        total_audio_size = 0
        
        try:
            while True:
                try:
                    # Use recv lock to prevent concurrent recv() calls
                    async with self._recv_lock:
                        response = await asyncio.wait_for(self.websocket.recv(), timeout=90.0)  # Increased timeout for TTS processing
                    
                    data = json.loads(response)
                    # logger.info(f"📥 Received response: {list(data.keys())}")
                    
                    if "audio" in data:
                        audio_chunk_count += 1
                        audio_base64 = data["audio"]
                        total_audio_size += len(audio_base64)
                        
                        # Yield the response
                        yield {
                            "type": "audio_chunk",
                            "audio_base64": audio_base64,
                            "context_id": data.get("context_id"),
                            "chunk_number": audio_chunk_count,
                            "chunk_size": len(audio_base64),
                            "total_size": total_audio_size,
                            "timestamp": datetime.now().isoformat(),
                            "is_final": data.get("final", False)
                        }
                        
                        # Check if this is the final audio chunk
                        if data.get("final"):
                            logger.info(f"Received final audio chunk. Total chunks: {audio_chunk_count}, Total size: {total_audio_size}")
                            break
                    
                    else:
                        # Non-audio response
                        # logger.info(f"Received non-audio response: {data}")
                        yield {
                            "type": "status",
                            "data": data,
                            "timestamp": datetime.now().isoformat()
                        }
                
                except asyncio.TimeoutError:
                    logger.warning("Timeout waiting for Murf response - attempting reconnection")
                    # Try to reconnect if we timeout
                    try:
                        await self.connect()
                        logger.info("Reconnected to Murf WebSocket after timeout")
                        # Continue listening after reconnection
                        continue
                    except Exception as reconnect_error:
                        logger.error(f"Failed to reconnect: {reconnect_error}")
                        break
                except websockets.exceptions.ConnectionClosed:
                    logger.warning("WebSocket connection closed unexpectedly")
                    self.is_connected = False
                    break
                except Exception as e:
                    logger.error(f"Error receiving response: {str(e)}")
                    break
                except websockets.exceptions.ConnectionClosed:
                    logger.info("Murf WebSocket connection closed")
                    break
                except Exception as e:
                    logger.error(f"Error receiving from Murf WebSocket: {str(e)}")
                    break
            
        except Exception as e:
            logger.error(f"Error in _listen_for_audio (total chunks processed: {audio_chunk_count}): {str(e)}")
            raise
    
    async def clear_context(self):
        """Clear the current context - wrapper for backward compatibility"""
        if self.current_context_id:
            await self._clear_specific_context(self.current_context_id)
    
    async def _clear_specific_context(self, context_id: str):
        """Clear a specific context"""
        try:
            if not self.websocket or not self.is_connected:
                return  # No connection to clear
                
            clear_msg = {
                "context_id": context_id,
                "clear": True
            }
            
            logger.info(f"Clearing Murf context: {context_id}")
            await self.websocket.send(json.dumps(clear_msg))
            
            # Use the recv lock to prevent concurrency issues
            async with self._recv_lock:
                try:
                    response = await asyncio.wait_for(self.websocket.recv(), timeout=3.0)
                    data = json.loads(response)
                    logger.info(f"Context clear response for {context_id}: {data}")
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout waiting for context clear acknowledgment for {context_id}")
            
            # Remove from active contexts
            self.active_contexts.discard(context_id)
            if self.current_context_id == context_id:
                self.current_context_id = None
            
        except Exception as e:
            logger.error(f"Error clearing context {context_id}: {str(e)}")
            # Don't raise here - clearing context is best effort
    
    async def _clear_all_contexts(self):
        """Clear all active contexts"""
        logger.info(f"Clearing all {len(self.active_contexts)} active contexts")
        
        # Use a copy of the set to avoid modification during iteration
        contexts_to_clear = list(self.active_contexts)
        
        for context_id in contexts_to_clear:
            try:
                await self._clear_specific_context(context_id)
            except Exception as e:
                logger.warning(f"Failed to clear context {context_id}: {e}")
                # Remove from tracking even if clear failed
                self.active_contexts.discard(context_id)
        
        # Force clear all tracking
        self.active_contexts.clear()
        self.current_context_id = None
        logger.info("All contexts cleared and reset")
