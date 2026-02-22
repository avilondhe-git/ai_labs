"""
Conversation Memory using Azure Cosmos DB
Purpose: Persistent conversation history storage and retrieval
"""

from typing import List, Dict, Optional
from datetime import datetime
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from config.config import settings
from config.logger import app_logger as logger


class ConversationMemory:
    """
    Manages conversation history in Cosmos DB
    
    WHY: Cosmos DB provides:
         - Global distribution (low latency worldwide)
         - NoSQL flexibility (schema evolution)
         - Automatic indexing (fast queries)
         - Multi-model support (document storage)
         - 99.999% SLA (enterprise reliability)
    """
    
    def __init__(self):
        """Initialize Cosmos DB client and container"""
        
        try:
            # WHY: CosmosClient manages connection pooling automatically
            self.client = CosmosClient(
                url=settings.cosmos_endpoint,
                credential=settings.cosmos_key
            )
            
            # Get or create database
            self.database = self.client.create_database_if_not_exists(
                id=settings.cosmos_database
            )
            
            # Get or create container
            # WHY: session_id as partition key enables efficient conversation retrieval
            self.container = self.database.create_container_if_not_exists(
                id=settings.cosmos_container,
                partition_key=PartitionKey(path="/session_id"),
                offer_throughput=400  # WHY: 400 RU/s is minimum for production
            )
            
            logger.info(f"✓ Connected to Cosmos DB: {settings.cosmos_database}/{settings.cosmos_container}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Cosmos DB: {e}")
            raise
    
    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Save a conversation message to Cosmos DB
        
        Args:
            session_id: Unique session identifier
            role: Message role ('user', 'assistant', 'system')
            content: Message content
            metadata: Optional metadata (tool calls, costs, etc.)
            
        Returns:
            Created message document
        """
        
        message = {
            "id": f"{session_id}_{datetime.utcnow().timestamp()}",
            "session_id": session_id,
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        try:
            # WHY: upsert_item creates or replaces document atomically
            created_message = self.container.upsert_item(message)
            logger.debug(f"Message saved: {role} in session {session_id}")
            return created_message
            
        except Exception as e:
            logger.error(f"Failed to save message: {e}")
            raise
    
    def get_conversation_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Retrieve conversation history for a session
        
        Args:
            session_id: Unique session identifier
            limit: Optional limit on number of messages to return
            
        Returns:
            List of messages ordered by timestamp
        """
        
        try:
            # WHY: Query by partition key (session_id) is most efficient
            query = f"""
                SELECT * FROM c 
                WHERE c.session_id = @session_id 
                ORDER BY c.timestamp ASC
            """
            
            parameters = [{"name": "@session_id", "value": session_id}]
            
            messages = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=False  # WHY: Single partition query is faster
            ))
            
            # Apply limit if specified
            if limit:
                messages = messages[-limit:]  # WHY: Get most recent messages
            
            logger.debug(f"Retrieved {len(messages)} messages for session {session_id}")
            return messages
            
        except Exception as e:
            logger.error(f"Failed to retrieve conversation: {e}")
            return []
    
    def get_session_state(self, session_id: str) -> Optional[Dict]:
        """
        Get session state (last interaction, message count, etc.)
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Session state dictionary or None
        """
        
        try:
            messages = self.get_conversation_history(session_id)
            
            if not messages:
                return None
            
            return {
                "session_id": session_id,
                "message_count": len(messages),
                "first_message": messages[0]["timestamp"],
                "last_message": messages[-1]["timestamp"],
                "last_role": messages[-1]["role"]
            }
            
        except Exception as e:
            logger.error(f"Failed to get session state: {e}")
            return None
    
    def clear_session(self, session_id: str) -> int:
        """
        Delete all messages in a session
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Number of messages deleted
        """
        
        try:
            messages = self.get_conversation_history(session_id)
            
            deleted_count = 0
            for message in messages:
                self.container.delete_item(
                    item=message["id"],
                    partition_key=session_id
                )
                deleted_count += 1
            
            logger.info(f"Cleared {deleted_count} messages from session {session_id}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to clear session: {e}")
            return 0
    
    def delete_old_sessions(self, days_old: int = 30) -> int:
        """
        Delete sessions older than specified days
        
        Args:
            days_old: Age threshold in days
            
        Returns:
            Number of sessions deleted
        """
        
        from datetime import timedelta
        
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=days_old)).isoformat()
            
            # WHY: Cross-partition query needed to find old sessions
            query = f"""
                SELECT DISTINCT c.session_id FROM c 
                WHERE c.timestamp < @cutoff_date
            """
            
            parameters = [{"name": "@cutoff_date", "value": cutoff_date}]
            
            old_sessions = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            deleted_count = 0
            for session in old_sessions:
                self.clear_session(session["session_id"])
                deleted_count += 1
            
            logger.info(f"Deleted {deleted_count} sessions older than {days_old} days")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to delete old sessions: {e}")
            return 0


# ====================
# USAGE EXAMPLE
# ====================
if __name__ == "__main__":
    print("\n💾 Testing Conversation Memory...")
    
    memory = ConversationMemory()
    
    # Test session
    session_id = "test-session-001"
    
    # Save messages
    print(f"\nSaving messages to session: {session_id}")
    memory.save_message(session_id, "user", "Hello, what can you do?")
    memory.save_message(session_id, "assistant", "I'm an AI agent with tools for search, email, and data analysis.")
    memory.save_message(session_id, "user", "Great! Search for AI trends.")
    
    # Retrieve history
    print("\nRetrieving conversation history...")
    history = memory.get_conversation_history(session_id)
    
    for i, msg in enumerate(history, 1):
        print(f"{i}. [{msg['role']}]: {msg['content']}")
    
    # Get session state
    print("\nSession state:")
    state = memory.get_session_state(session_id)
    if state:
        print(f"  Messages: {state['message_count']}")
        print(f"  Last activity: {state['last_message']}")
    
    # Clean up
    print(f"\nCleaning up test session...")
    deleted = memory.clear_session(session_id)
    print(f"✓ Deleted {deleted} messages")
    
    print("\n✅ Memory test complete!")
