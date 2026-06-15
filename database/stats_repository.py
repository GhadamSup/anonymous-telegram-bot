from .connection import db
from datetime import datetime, timedelta
from typing import List, Dict

class StatsRepository:
    """Data access layer for statistics tracking"""
    
    @staticmethod
    def init_stats_table():
        """Create stats tracking tables"""
        conn = db.get_connection()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS daily_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE NOT NULL,
                total_users INTEGER DEFAULT 0,
                new_users INTEGER DEFAULT 0,
                total_messages INTEGER DEFAULT 0,
                text_messages INTEGER DEFAULT 0,
                media_messages INTEGER DEFAULT 0,
                reply_messages INTEGER DEFAULT 0,
                active_chats INTEGER DEFAULT 0
            );
            
            CREATE TABLE IF NOT EXISTS hourly_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                hour INTEGER NOT NULL,
                messages_count INTEGER DEFAULT 0,
                UNIQUE(timestamp, hour)
            );
        """)
        conn.commit()
        conn.close()
    
    @staticmethod
    def record_daily_stats():
        """Record current stats for today"""
        today = datetime.now().strftime('%Y-%m-%d')
        conn = db.get_connection()
        
        # Get current counts
        total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        total_messages = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        text_messages = conn.execute("SELECT COUNT(*) FROM messages WHERE message_type = 'text'").fetchone()[0]
        media_messages = conn.execute("SELECT COUNT(*) FROM messages WHERE message_type != 'text'").fetchone()[0]
        reply_messages = conn.execute("SELECT COUNT(*) FROM messages WHERE is_reply = 1").fetchone()[0]
        active_chats = conn.execute("SELECT COUNT(*) FROM users WHERE linked_to IS NOT NULL").fetchone()[0] // 2
        
        # Get yesterday's total users to calculate new users
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        yesterday_users = conn.execute(
            "SELECT total_users FROM daily_stats WHERE date = ?", (yesterday,)
        ).fetchone()
        
        if yesterday_users:
            new_users = max(0, total_users - yesterday_users[0])
        else:
            new_users = 0
        
        # Get yesterday's messages to calculate today's messages
        yesterday_msgs = conn.execute(
            "SELECT total_messages FROM daily_stats WHERE date = ?", (yesterday,)
        ).fetchone()
        
        if yesterday_msgs:
            today_messages = max(0, total_messages - yesterday_msgs[0])
        else:
            today_messages = total_messages
        
        # Insert or update today's stats
        conn.execute("""
            INSERT INTO daily_stats (date, total_users, new_users, total_messages, text_messages, media_messages, reply_messages, active_chats)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                total_users = excluded.total_users,
                new_users = excluded.new_users,
                total_messages = excluded.total_messages,
                text_messages = excluded.text_messages,
                media_messages = excluded.media_messages,
                reply_messages = excluded.reply_messages,
                active_chats = excluded.active_chats
        """, (today, total_users, new_users, today_messages, text_messages, media_messages, reply_messages, active_chats))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def record_hourly_message():
        """Record message count for current hour"""
        now = datetime.now()
        timestamp = now.strftime('%Y-%m-%d')
        hour = now.hour
        
        conn = db.get_connection()
        
        # Count messages in this hour
        hour_start = now.replace(minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S')
        hour_end = now.replace(minute=59, second=59, microsecond=999999).strftime('%Y-%m-%d %H:%M:%S')
        
        msg_count = conn.execute(
            "SELECT COUNT(*) FROM messages WHERE timestamp BETWEEN ? AND ?",
            (hour_start, hour_end)
        ).fetchone()[0]
        
        conn.execute("""
            INSERT INTO hourly_stats (timestamp, hour, messages_count)
            VALUES (?, ?, ?)
            ON CONFLICT(timestamp, hour) DO UPDATE SET
                messages_count = excluded.messages_count
        """, (timestamp, hour, msg_count))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_daily_stats(days: int = 7) -> List[Dict]:
        """Get daily stats for the last N days"""
        conn = db.get_connection()
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        stats = conn.execute("""
            SELECT * FROM daily_stats 
            WHERE date >= ? 
            ORDER BY date ASC
        """, (start_date,)).fetchall()
        
        conn.close()
        return [dict(s) for s in stats]
    
    @staticmethod
    def get_hourly_stats(days: int = 1) -> List[Dict]:
        """Get hourly stats for the last N days"""
        conn = db.get_connection()
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        stats = conn.execute("""
            SELECT * FROM hourly_stats 
            WHERE timestamp >= ? 
            ORDER BY timestamp ASC, hour ASC
        """, (start_date,)).fetchall()
        
        conn.close()
        return [dict(s) for s in stats]
    
    @staticmethod
    def get_message_type_stats() -> Dict:
        """Get current message type breakdown"""
        conn = db.get_connection()
        
        text = conn.execute("SELECT COUNT(*) FROM messages WHERE message_type = 'text'").fetchone()[0]
        media = conn.execute("SELECT COUNT(*) FROM messages WHERE message_type != 'text'").fetchone()[0]
        replies = conn.execute("SELECT COUNT(*) FROM messages WHERE is_reply = 1").fetchone()[0]
        
        conn.close()
        return {
            'text': text,
            'media': media,
            'replies': replies
        }