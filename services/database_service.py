from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Dict, Optional
from datetime import datetime
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class DatabaseService:
    def __init__(self, mongodb_url: str = None):
        self.mongodb_url = mongodb_url or os.getenv("MONGODB_URL")
        self.client = None
        self.db = None
        self.in_memory_store = {}
        self.user_sessions = {}  # Track user sessions for better organization
    
    async def connect(self) -> bool:
        try:
            self.client = AsyncIOMotorClient(self.mongodb_url)
            self.db = self.client.voice_agents
            await self.client.admin.command('ping')
            logger.info("✅ Connected to MongoDB successfully")
            return True
        except Exception as e:
            logger.warning(f"⚠️  MongoDB connection failed: {e}")
            logger.info("💾 Using in-memory storage as fallback")
            self.client = None
            self.db = None
            return False
    
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self.db is not None
    
    async def test_connection(self) -> bool:
        """Test database connection"""
        if self.db is not None:
            try:
                await self.client.admin.command('ping')
                return True
            except Exception as e:
                logger.error(f"Database connection test failed: {e}")
                return False
        return False
    
    async def get_chat_history(self, session_id: str) -> List[Dict]:
        """Get chat history for a session"""
        if self.db is not None:
            try:
                chat_history = await self.db.chat_sessions.find_one({"session_id": session_id})
                if chat_history and "messages" in chat_history:
                    return chat_history["messages"]
                return []
            except Exception as e:
                logger.error(f"Failed to get chat history from MongoDB: {str(e)}")
                return self.in_memory_store.get(session_id, [])
        else:
            return self.in_memory_store.get(session_id, [])
    
    async def add_message_to_history(self, session_id: str, role: str, content: str) -> bool:
        """Add a message to chat history with improved error handling"""
        if not session_id or not role or not content:
            logger.error(f"Invalid parameters for add_message_to_history: session_id={session_id}, role={role}, content_length={len(content) if content else 0}")
            return False
            
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now()
        }
        
        # Track user sessions for analytics
        if session_id not in self.user_sessions:
            self.user_sessions[session_id] = {
                "created_at": datetime.now(),
                "message_count": 0,
                "last_activity": datetime.now()
            }
        
        self.user_sessions[session_id]["message_count"] += 1
        self.user_sessions[session_id]["last_activity"] = datetime.now()
        
        if self.db is not None:
            try:
                # Update chat session with user session metadata
                session_metadata = {
                    "session_id": session_id,
                    "created_at": self.user_sessions[session_id]["created_at"],
                    "message_count": self.user_sessions[session_id]["message_count"],
                    "last_activity": self.user_sessions[session_id]["last_activity"]
                }
                
                result = await self.db.chat_sessions.update_one(
                    {"session_id": session_id},
                    {
                        "$push": {"messages": message},
                        "$set": {
                            "last_updated": datetime.now(),
                            **session_metadata
                        }
                    },
                    upsert=True
                )
                
                if result.matched_count > 0 or result.upserted_id:
                    logger.info(f"✅ Message saved to MongoDB for session {session_id}: {role} - {content[:50]}...")
                else:
                    logger.warning(f"⚠️ MongoDB update didn't match any documents for session {session_id}")
                    
                return True
            except Exception as e:
                logger.error(f"❌ Failed to save message to MongoDB: {str(e)}")
                # Fallback to in-memory storage
                if session_id not in self.in_memory_store:
                    self.in_memory_store[session_id] = []
                self.in_memory_store[session_id].append(message)
                logger.info(f"💾 Message saved to in-memory storage for session {session_id}: {role} - {content[:50]}...")
                return True
        else:
            # In-memory storage when MongoDB is not available
            if session_id not in self.in_memory_store:
                self.in_memory_store[session_id] = []
            self.in_memory_store[session_id].append(message)
            logger.info(f"💾 Message saved to in-memory storage for session {session_id}: {role} - {content[:50]}...")
            return True
    
    async def get_user_sessions(self, limit: int = 50) -> List[Dict]:
        """Get recent user sessions for analytics"""
        if self.db is not None:
            try:
                sessions = await self.db.chat_sessions.find(
                    {},
                    {"session_id": 1, "created_at": 1, "message_count": 1, "last_activity": 1}
                ).sort("last_activity", -1).limit(limit).to_list(length=limit)
                return sessions
            except Exception as e:
                logger.error(f"Failed to get user sessions from MongoDB: {str(e)}")
                return []
        else:
            # Return in-memory session data
            return list(self.user_sessions.items())[:limit]
    
    async def clear_session_history(self, session_id: str) -> bool:
        """Clear chat history for a specific session"""
        if self.db is not None:
            try:
                result = await self.db.chat_sessions.delete_one({"session_id": session_id})
                logger.info(f"Cleared chat history for session {session_id}")
                return result.deleted_count > 0
            except Exception as e:
                logger.error(f"Failed to clear session history from MongoDB: {str(e)}")
                if session_id in self.in_memory_store:
                    del self.in_memory_store[session_id]
                return True
        else:
            if session_id in self.in_memory_store:
                del self.in_memory_store[session_id]
            if session_id in self.user_sessions:
                del self.user_sessions[session_id]
            return True
    
    async def get_session_stats(self, session_id: str) -> Dict:
        """Get statistics for a specific session"""
        if self.db is not None:
            try:
                session = await self.db.chat_sessions.find_one({"session_id": session_id})
                if session:
                    return {
                        "session_id": session_id,
                        "message_count": len(session.get("messages", [])),
                        "created_at": session.get("created_at"),
                        "last_activity": session.get("last_activity"),
                        "total_user_messages": len([m for m in session.get("messages", []) if m["role"] == "user"]),
                        "total_assistant_messages": len([m for m in session.get("messages", []) if m["role"] == "assistant"])
                    }
                return {}
            except Exception as e:
                logger.error(f"Failed to get session stats from MongoDB: {str(e)}")
                return {}
        else:
            messages = self.in_memory_store.get(session_id, [])
            session_info = self.user_sessions.get(session_id, {})
            return {
                "session_id": session_id,
                "message_count": len(messages),
                "created_at": session_info.get("created_at"),
                "last_activity": session_info.get("last_activity"),
                "total_user_messages": len([m for m in messages if m["role"] == "user"]),
                "total_assistant_messages": len([m for m in messages if m["role"] == "assistant"])
            }
    
    async def close(self):
        if self.client:
            self.client.close()
            logger.info("Database connection closed")
