from .connection import db
from typing import List, Dict, Optional

class ChannelRepository:
    """Data access layer for sponsored channels"""
    
    @staticmethod
    def add_channel(channel_id: int, channel_username: str, channel_title: str = None, invite_link: str = None):
        """Add a sponsored channel"""
        conn = db.get_connection()
        conn.execute("""
            INSERT INTO channels (channel_id, channel_username, channel_title, invite_link, is_active)
            VALUES (?, ?, ?, ?, 1)
        """, (channel_id, channel_username, channel_title, invite_link))
        conn.commit()
        conn.close()
    
    @staticmethod
    def remove_channel(channel_id: int):
        """Remove a sponsored channel"""
        conn = db.get_connection()
        conn.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
        conn.commit()
        conn.close()
    
    @staticmethod
    def toggle_channel(channel_id: int, is_active: bool):
        """Enable or disable a channel"""
        conn = db.get_connection()
        conn.execute("UPDATE channels SET is_active = ? WHERE channel_id = ?", 
                    (1 if is_active else 0, channel_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_all_channels() -> List[Dict]:
        """Get all sponsored channels"""
        conn = db.get_connection()
        channels = conn.execute("""
            SELECT * FROM channels ORDER BY added_date DESC
        """).fetchall()
        conn.close()
        return [dict(ch) for ch in channels]
    
    @staticmethod
    def get_active_channels() -> List[Dict]:
        """Get active sponsored channels"""
        conn = db.get_connection()
        channels = conn.execute("""
            SELECT * FROM channels WHERE is_active = 1
        """).fetchall()
        conn.close()
        return [dict(ch) for ch in channels]
    
    @staticmethod
    def get_channel(channel_id: int) -> Optional[Dict]:
        """Get a specific channel"""
        conn = db.get_connection()
        channel = conn.execute(
            "SELECT * FROM channels WHERE channel_id = ?", (channel_id,)
        ).fetchone()
        conn.close()
        return dict(channel) if channel else None