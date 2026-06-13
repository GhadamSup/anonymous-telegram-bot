import json
import sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database.connection import db

class MessageService:
    """Service for message operations"""
    
    def __init__(self):
        self.db = db
    
    def extract_media_info(self, message):
        """Extract media information from a message"""
        media_data = {
            'media_type': None,
            'file_id': None,
            'file_unique_id': None,
            'file_size': None,
            'mime_type': None,
            'duration': None,
            'width': None,
            'height': None,
            'caption': message.caption or "",
            'media_info': {}
        }
        
        if message.photo:
            media_data['media_type'] = 'photo'
            photo = message.photo[-1]
            media_data['file_id'] = photo.file_id
            media_data['file_unique_id'] = photo.file_unique_id
            media_data['file_size'] = photo.file_size
            media_data['width'] = photo.width
            media_data['height'] = photo.height
            
        elif message.video:
            media_data['media_type'] = 'video'
            video = message.video
            media_data['file_id'] = video.file_id
            media_data['file_unique_id'] = video.file_unique_id
            media_data['file_size'] = video.file_size
            media_data['mime_type'] = video.mime_type
            media_data['duration'] = video.duration
            media_data['width'] = video.width
            media_data['height'] = video.height
            
        elif message.voice:
            media_data['media_type'] = 'voice'
            voice = message.voice
            media_data['file_id'] = voice.file_id
            media_data['file_unique_id'] = voice.file_unique_id
            media_data['file_size'] = voice.file_size
            media_data['mime_type'] = voice.mime_type
            media_data['duration'] = voice.duration
            
        elif message.audio:
            media_data['media_type'] = 'audio'
            audio = message.audio
            media_data['file_id'] = audio.file_id
            media_data['file_unique_id'] = audio.file_unique_id
            media_data['file_size'] = audio.file_size
            media_data['mime_type'] = audio.mime_type
            media_data['duration'] = audio.duration
            
        elif message.document:
            media_data['media_type'] = 'document'
            doc = message.document
            media_data['file_id'] = doc.file_id
            media_data['file_unique_id'] = doc.file_unique_id
            media_data['file_size'] = doc.file_size
            media_data['mime_type'] = doc.mime_type
            
        elif message.sticker:
            media_data['media_type'] = 'sticker'
            sticker = message.sticker
            media_data['file_id'] = sticker.file_id
            media_data['file_unique_id'] = sticker.file_unique_id
            media_data['file_size'] = sticker.file_size
            media_data['width'] = sticker.width
            media_data['height'] = sticker.height
            
        elif message.animation:
            media_data['media_type'] = 'animation'
            anim = message.animation
            media_data['file_id'] = anim.file_id
            media_data['file_unique_id'] = anim.file_unique_id
            media_data['file_size'] = anim.file_size
            media_data['mime_type'] = anim.mime_type
            media_data['duration'] = anim.duration
            
        elif message.video_note:
            media_data['media_type'] = 'video_note'
            vn = message.video_note
            media_data['file_id'] = vn.file_id
            media_data['file_unique_id'] = vn.file_unique_id
            media_data['file_size'] = vn.file_size
            media_data['duration'] = vn.duration
        
        return media_data if media_data['media_type'] else None
    
    async def send_media(self, context, target_id, sender_id, media_data, caption=None):
        """Send media to a user with reply button"""
        reply_markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("↩️ Reply", callback_data=f"reply_{sender_id}")
        ]])
        
        try:
            media_type = media_data['media_type']
            file_id = media_data['file_id']
            
            if media_type == 'photo':
                await context.bot.send_photo(target_id, file_id, caption=caption, reply_markup=reply_markup)
            elif media_type == 'video':
                await context.bot.send_video(target_id, file_id, caption=caption, reply_markup=reply_markup)
            elif media_type == 'voice':
                await context.bot.send_voice(target_id, file_id, caption=caption, reply_markup=reply_markup)
            elif media_type == 'audio':
                await context.bot.send_audio(target_id, file_id, caption=caption, reply_markup=reply_markup)
            elif media_type == 'document':
                await context.bot.send_document(target_id, file_id, caption=caption, reply_markup=reply_markup)
            elif media_type == 'sticker':
                await context.bot.send_sticker(target_id, file_id, reply_markup=reply_markup)
            elif media_type == 'animation':
                await context.bot.send_animation(target_id, file_id, caption=caption, reply_markup=reply_markup)
            elif media_type == 'video_note':
                await context.bot.send_video_note(target_id, file_id, reply_markup=reply_markup)
            return True
        except Exception as e:
            print(f"Error sending media: {e}")
            return False
    
    def log_text_message(self, sender_id, receiver_id, content, is_reply=False):
        """Log a text message"""
        conn = self.db.get_connection()
        conn.execute("""
            INSERT INTO messages (sender_id, receiver_id, message_type, content, is_reply)
            VALUES (?, ?, 'text', ?, ?)
        """, (sender_id, receiver_id, content, int(is_reply)))
        conn.commit()
        conn.close()
    
    def log_media_message(self, sender_id, receiver_id, media_data, is_reply=False):
        """Log a media message"""
        conn = self.db.get_connection()
        conn.execute("""
            INSERT INTO messages (
                sender_id, receiver_id, message_type, content,
                file_id, file_unique_id, file_size, mime_type,
                duration, width, height, caption, media_info, is_reply
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sender_id, receiver_id, media_data['media_type'],
            media_data.get('caption'),
            media_data.get('file_id'), media_data.get('file_unique_id'),
            media_data.get('file_size'), media_data.get('mime_type'),
            media_data.get('duration'), media_data.get('width'),
            media_data.get('height'), media_data.get('caption'),
            json.dumps(media_data.get('media_info', {})),
            int(is_reply)
        ))
        conn.commit()
        conn.close()
    
    def get_stats(self):
        """Get message statistics"""
        conn = self.db.get_connection()
        
        stats = {}
        stats['total_messages'] = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        stats['media_messages'] = conn.execute(
            "SELECT COUNT(*) FROM messages WHERE message_type != 'text'"
        ).fetchone()[0]
        stats['reply_messages'] = conn.execute(
            "SELECT COUNT(*) FROM messages WHERE is_reply = 1"
        ).fetchone()[0]
        stats['total_conversations'] = conn.execute(
            "SELECT COUNT(DISTINCT conversation_id) FROM messages"
        ).fetchone()[0]
        
        conn.close()
        return stats
    
    def get_all_conversations(self):
        """Get all conversations with messages"""
        conn = self.db.get_connection()
        conn.row_factory = sqlite3.Row
        
        conversations = conn.execute("""
            SELECT DISTINCT 
                sender_id, receiver_id,
                MIN(timestamp) as started_at,
                MAX(timestamp) as last_message,
                COUNT(*) as message_count
            FROM messages
            GROUP BY 
                MIN(sender_id, receiver_id),
                MAX(sender_id, receiver_id)
            ORDER BY last_message DESC
        """).fetchall()
        
        result = []
        for conv in conversations:
            conv_dict = dict(conv)
            messages = conn.execute("""
                SELECT * FROM messages 
                WHERE (sender_id = ? AND receiver_id = ?) 
                   OR (sender_id = ? AND receiver_id = ?)
                ORDER BY timestamp ASC
            """, (conv['sender_id'], conv['receiver_id'], 
                  conv['receiver_id'], conv['sender_id'])).fetchall()
            conv_dict['messages'] = [dict(msg) for msg in messages]
            result.append(conv_dict)
        
        conn.close()
        return result