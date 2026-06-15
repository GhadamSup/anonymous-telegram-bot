from .connection import db
from typing import Optional, List, Dict

class ConversationRepository:
    """Data access layer for conversations"""
    
    @staticmethod
    def get_or_create(user_a_id: int, user_b_id: int) -> int:
        """Get existing conversation or create new one"""
        conn = db.get_connection()
        
        # Ensure consistent ordering (smaller ID first)
        a, b = min(user_a_id, user_b_id), max(user_a_id, user_b_id)
        
        # Check if conversation exists
        result = conn.execute(
            "SELECT id FROM conversations WHERE user_a_id = ? AND user_b_id = ? AND status = 'active'",
            (a, b)
        ).fetchone()
        
        if result:
            conn.close()
            return result[0]
        
        # Create new conversation
        cursor = conn.execute(
            "INSERT INTO conversations (user_a_id, user_b_id) VALUES (?, ?)",
            (a, b)
        )
        conversation_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return conversation_id
    
    @staticmethod
    def add_message(conversation_id: int, sender_id: int, receiver_id: int,
                   message_type: str, content: str = None, file_id: str = None,
                   file_unique_id: str = None, file_size: int = None,
                   mime_type: str = None, duration: int = None,
                   width: int = None, height: int = None,
                   caption: str = None, media_info: str = None,
                   is_reply: bool = False) -> int:
        """Add a message to conversation"""
        conn = db.get_connection()
        
        cursor = conn.execute("""
            INSERT INTO messages (
                conversation_id, sender_id, receiver_id, message_type,
                content, file_id, file_unique_id, file_size, mime_type,
                duration, width, height, caption, media_info, is_reply
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            conversation_id, sender_id, receiver_id, message_type,
            content, file_id, file_unique_id, file_size, mime_type,
            duration, width, height, caption, media_info, int(is_reply)
        ))
        
        # Update conversation metadata
        conn.execute("""
            UPDATE conversations 
            SET last_message_at = CURRENT_TIMESTAMP,
                message_count = message_count + 1
            WHERE id = ?
        """, (conversation_id,))
        
        conn.commit()
        message_id = cursor.lastrowid
        conn.close()
        return message_id
    
    @staticmethod
    def get_messages(conversation_id: int, limit: int = 100) -> List[Dict]:
        """Get all messages in a conversation"""
        conn = db.get_connection()
        
        messages = conn.execute("""
            SELECT m.*, 
                   s.first_name as sender_name, s.username as sender_username,
                   r.first_name as receiver_name, r.username as receiver_username
            FROM messages m
            LEFT JOIN users s ON m.sender_id = s.user_id
            LEFT JOIN users r ON m.receiver_id = r.user_id
            WHERE m.conversation_id = ?
            ORDER BY m.timestamp ASC
            LIMIT ?
        """, (conversation_id, limit)).fetchall()
        
        conn.close()
        return [dict(msg) for msg in messages]
    
    @staticmethod
    def get_user_conversations(user_id: int, limit: int = 20) -> List[Dict]:
        """Get all conversations for a user"""
        conn = db.get_connection()
        
        conversations = conn.execute("""
            SELECT c.*,
                   CASE 
                       WHEN c.user_a_id = ? THEN u2.first_name 
                       ELSE u1.first_name 
                   END as other_user_name,
                   CASE 
                       WHEN c.user_a_id = ? THEN u2.username 
                       ELSE u1.username 
                   END as other_user_username,
                   CASE 
                       WHEN c.user_a_id = ? THEN c.user_b_id 
                       ELSE c.user_a_id 
                   END as other_user_id,
                   (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id) as total_messages,
                   (SELECT m2.timestamp FROM messages m2 WHERE m2.conversation_id = c.id ORDER BY m2.timestamp DESC LIMIT 1) as last_message_time,
                   (SELECT m3.content FROM messages m3 WHERE m3.conversation_id = c.id ORDER BY m3.timestamp DESC LIMIT 1) as last_message_text
            FROM conversations c
            LEFT JOIN users u1 ON c.user_a_id = u1.user_id
            LEFT JOIN users u2 ON c.user_b_id = u2.user_id
            WHERE (c.user_a_id = ? OR c.user_b_id = ?)
            ORDER BY last_message_time DESC
            LIMIT ?
        """, (user_id, user_id, user_id, user_id, user_id, limit)).fetchall()
        
        conn.close()
        return [dict(conv) for conv in conversations]
    
    @staticmethod
    def end_conversation(conversation_id: int):
        """End a conversation"""
        conn = db.get_connection()
        conn.execute("""
            UPDATE conversations 
            SET status = 'ended', ended_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (conversation_id,))
        conn.commit()
        conn.close()
    
    @staticmethod
    def end_user_conversations(user_id: int):
        """End all active conversations for a user"""
        conn = db.get_connection()
        conn.execute("""
            UPDATE conversations 
            SET status = 'ended', ended_at = CURRENT_TIMESTAMP 
            WHERE (user_a_id = ? OR user_b_id = ?) AND status = 'active'
        """, (user_id, user_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_all_conversations(limit: int = 50) -> List[Dict]:
        """Get all conversations"""
        conn = db.get_connection()
        
        conversations = conn.execute("""
            SELECT c.*,
                   u1.first_name as user_a_name, u1.username as user_a_username,
                   u2.first_name as user_b_name, u2.username as user_b_username,
                   (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id) as total_messages
            FROM conversations c
            LEFT JOIN users u1 ON c.user_a_id = u1.user_id
            LEFT JOIN users u2 ON c.user_b_id = u2.user_id
            ORDER BY c.last_message_at DESC
            LIMIT ?
        """, (limit,)).fetchall()
        
        conn.close()
        return [dict(conv) for conv in conversations]
    
    @staticmethod
    def get_stats() -> Dict:
        """Get conversation statistics"""
        conn = db.get_connection()
        
        stats = {}
        stats['total_conversations'] = conn.execute(
            "SELECT COUNT(*) FROM conversations"
        ).fetchone()[0]
        stats['active_conversations'] = conn.execute(
            "SELECT COUNT(*) FROM conversations WHERE status = 'active'"
        ).fetchone()[0]
        stats['total_messages'] = conn.execute(
            "SELECT COUNT(*) FROM messages"
        ).fetchone()[0]
        stats['media_messages'] = conn.execute(
            "SELECT COUNT(*) FROM messages WHERE message_type != 'text'"
        ).fetchone()[0]
        stats['reply_messages'] = conn.execute(
            "SELECT COUNT(*) FROM messages WHERE is_reply = 1"
        ).fetchone()[0]
        
        conn.close()
        return stats