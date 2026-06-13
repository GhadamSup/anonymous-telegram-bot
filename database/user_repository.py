from .connection import db
from typing import Optional, List, Dict

class UserRepository:
    """Data access layer for users"""
    
    @staticmethod
    def add_or_update(user_id: int, username: str, first_name: str, 
                      last_name: str, full_name: str, profile_link: str,
                      language_code: str, is_premium: bool, is_bot: bool):
        conn = db.get_connection()
        
        existing = conn.execute(
            "SELECT user_id FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        
        if existing:
            conn.execute("""
                UPDATE users SET 
                    username = ?, first_name = ?, last_name = ?,
                    full_name = ?, profile_link = ?, language_code = ?,
                    is_premium = ?, is_bot = ?, last_active = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (username, first_name, last_name, full_name, profile_link,
                  language_code, int(is_premium), int(is_bot), user_id))
        else:
            conn.execute("""
                INSERT INTO users (user_id, username, first_name, last_name, 
                                 full_name, profile_link, language_code, is_premium, is_bot)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, username, first_name, last_name, full_name,
                  profile_link, language_code, int(is_premium), int(is_bot)))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def is_banned(user_id: int) -> bool:
        conn = db.get_connection()
        result = conn.execute(
            "SELECT is_banned FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        conn.close()
        return bool(result and result[0])
    
    @staticmethod
    def ban(user_id: int):
        conn = db.get_connection()
        conn.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (user_id,))
        conn.execute("UPDATE users SET linked_to = NULL WHERE user_id = ? OR linked_to = ?", 
                    (user_id, user_id))
        conn.execute("UPDATE users SET replying_to = NULL WHERE user_id = ? OR replying_to = ?", 
                    (user_id, user_id))
        conn.execute("""
            UPDATE conversations SET status = 'ended', ended_at = CURRENT_TIMESTAMP 
            WHERE (user_a_id = ? OR user_b_id = ?) AND status = 'active'
        """, (user_id, user_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def unban(user_id: int):
        conn = db.get_connection()
        conn.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_info(user_id: int) -> Optional[Dict]:
        conn = db.get_connection()
        result = conn.execute(
            "SELECT user_id, username, first_name, is_banned FROM users WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        conn.close()
        return dict(result) if result else None
    
    @staticmethod
    def get_all_user_ids() -> List[int]:
        conn = db.get_connection()
        results = conn.execute(
            "SELECT user_id FROM users WHERE is_banned = 0"
        ).fetchall()
        conn.close()
        return [row[0] for row in results]
    
    @staticmethod
    def get_all() -> List[Dict]:
        conn = db.get_connection()
        results = conn.execute("SELECT * FROM users").fetchall()
        conn.close()
        return [dict(row) for row in results]
    
    @staticmethod
    def get_banned() -> List[Dict]:
        conn = db.get_connection()
        results = conn.execute(
            "SELECT user_id, username, first_name FROM users WHERE is_banned = 1"
        ).fetchall()
        conn.close()
        return [dict(row) for row in results]
    
    @staticmethod
    def update_last_active(user_id: int):
        conn = db.get_connection()
        conn.execute(
            "UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = ?",
            (user_id,)
        )
        conn.commit()
        conn.close()
    
    @staticmethod
    def set_replying_to(user_id: int, target_id: int):
        conn = db.get_connection()
        conn.execute(
            "UPDATE users SET replying_to = ? WHERE user_id = ?",
            (target_id, user_id)
        )
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_replying_to(user_id: int) -> Optional[int]:
        conn = db.get_connection()
        result = conn.execute(
            "SELECT replying_to FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        conn.close()
        return result[0] if result and result[0] else None
    
    @staticmethod
    def clear_replying_to(user_id: int):
        conn = db.get_connection()
        conn.execute(
            "UPDATE users SET replying_to = NULL WHERE user_id = ?", (user_id,)
        )
        conn.commit()
        conn.close()
    
    @staticmethod
    def unlink(user_id: int) -> Optional[int]:
        conn = db.get_connection()
        result = conn.execute(
            "SELECT linked_to FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        partner = result[0] if result and result[0] else None
        
        if partner:
            conn.execute(
                "UPDATE users SET linked_to = NULL WHERE user_id IN (?, ?)",
                (user_id, partner)
            )
            conn.execute(
                "UPDATE users SET replying_to = NULL WHERE user_id IN (?, ?)",
                (user_id, partner)
            )
        
        conn.commit()
        conn.close()
        return partner
    
    @staticmethod
    def get_stats() -> Dict:
        conn = db.get_connection()
        
        stats = {}
        stats['total_users'] = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        stats['active_chats'] = conn.execute(
            "SELECT COUNT(*) FROM users WHERE linked_to IS NOT NULL"
        ).fetchone()[0] // 2
        stats['replying_users'] = conn.execute(
            "SELECT COUNT(*) FROM users WHERE replying_to IS NOT NULL"
        ).fetchone()[0]
        stats['banned_users'] = conn.execute(
            "SELECT COUNT(*) FROM users WHERE is_banned = 1"
        ).fetchone()[0]
        stats['premium_users'] = conn.execute(
            "SELECT COUNT(*) FROM users WHERE is_premium = 1"
        ).fetchone()[0]
        
        conn.close()
        return stats