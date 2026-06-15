import sqlite3

class DatabaseConnection:
    """Singleton database connection manager"""
    
    _instance = None
    
    def __new__(cls, db_path: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.db_path = db_path or "bot.db"
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize database and create tables"""
        conn = self.get_connection()
        
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                full_name TEXT,
                profile_link TEXT,
                language_code TEXT,
                is_premium INTEGER DEFAULT 0,
                is_bot INTEGER DEFAULT 0,
                linked_to INTEGER,
                replying_to INTEGER,
                joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_banned INTEGER DEFAULT 0
            );
            
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_a_id INTEGER NOT NULL,
                user_b_id INTEGER NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP,
                status TEXT DEFAULT 'active',
                message_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_a_id) REFERENCES users(user_id),
                FOREIGN KEY (user_b_id) REFERENCES users(user_id),
                UNIQUE(user_a_id, user_b_id)
            );
            
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,
                message_type TEXT NOT NULL DEFAULT 'text',
                content TEXT,
                file_id TEXT,
                file_unique_id TEXT,
                file_size INTEGER,
                mime_type TEXT,
                duration INTEGER,
                width INTEGER,
                height INTEGER,
                caption TEXT,
                media_info TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_read INTEGER DEFAULT 0,
                is_reply INTEGER DEFAULT 0,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
                FOREIGN KEY (sender_id) REFERENCES users(user_id),
                FOREIGN KEY (receiver_id) REFERENCES users(user_id)
            );
            
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER UNIQUE NOT NULL,
                channel_username TEXT,
                channel_title TEXT,
                invite_link TEXT,
                is_active INTEGER DEFAULT 1,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
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
            
            CREATE TABLE IF NOT EXISTS admin_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            
            CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
            CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_id);
            CREATE INDEX IF NOT EXISTS idx_messages_receiver ON messages(receiver_id);
            CREATE INDEX IF NOT EXISTS idx_conversations_users ON conversations(user_a_id, user_b_id);
        """)
        
        conn.commit()
        conn.close()
        
        self._run_migrations()
    
    def _run_migrations(self):
        """Add missing columns for backward compatibility"""
        conn = self.get_connection()
        
        migrations = [
            "ALTER TABLE users ADD COLUMN linked_to INTEGER",
            "ALTER TABLE users ADD COLUMN replying_to INTEGER",
            "ALTER TABLE users ADD COLUMN first_name TEXT",
            "ALTER TABLE users ADD COLUMN last_name TEXT",
            "ALTER TABLE users ADD COLUMN full_name TEXT",
            "ALTER TABLE users ADD COLUMN profile_link TEXT",
            "ALTER TABLE users ADD COLUMN language_code TEXT",
            "ALTER TABLE users ADD COLUMN is_premium INTEGER DEFAULT 0",
            "ALTER TABLE users ADD COLUMN is_bot INTEGER DEFAULT 0",
            "ALTER TABLE users ADD COLUMN last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE users ADD COLUMN is_banned INTEGER DEFAULT 0",
            "ALTER TABLE conversations ADD COLUMN last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE conversations ADD COLUMN message_count INTEGER DEFAULT 0",
            "ALTER TABLE channels ADD COLUMN invite_link TEXT"
        ]
        
        for migration in migrations:
            try:
                conn.execute(migration)
            except sqlite3.OperationalError:
                pass
        
        conn.commit()
        conn.close()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

# Singleton instance
db = DatabaseConnection()