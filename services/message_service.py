import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database.conversation_repository import ConversationRepository

class MessageService:
    """Service for message operations"""
    
    def __init__(self):
        self.conv_repo = ConversationRepository()
    
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
            media_data['media_info'] = {
                "duration": video.duration, "width": video.width,
                "height": video.height, "file_name": video.file_name
            }
            
        elif message.voice:
            media_data['media_type'] = 'voice'
            voice = message.voice
            media_data['file_id'] = voice.file_id
            media_data['file_unique_id'] = voice.file_unique_id
            media_data['file_size'] = voice.file_size
            media_data['mime_type'] = voice.mime_type
            media_data['duration'] = voice.duration
            media_data['media_info'] = {
                "duration": voice.duration, "mime_type": voice.mime_type
            }
            
        elif message.audio:
            media_data['media_type'] = 'audio'
            audio = message.audio
            media_data['file_id'] = audio.file_id
            media_data['file_unique_id'] = audio.file_unique_id
            media_data['file_size'] = audio.file_size
            media_data['mime_type'] = audio.mime_type
            media_data['duration'] = audio.duration
            media_data['media_info'] = {
                "duration": audio.duration, "title": audio.title,
                "performer": audio.performer
            }
            
        elif message.document:
            media_data['media_type'] = 'document'
            doc = message.document
            media_data['file_id'] = doc.file_id
            media_data['file_unique_id'] = doc.file_unique_id
            media_data['file_size'] = doc.file_size
            media_data['mime_type'] = doc.mime_type
            media_data['media_info'] = {
                "file_name": doc.file_name, "mime_type": doc.mime_type
            }
            
        elif message.sticker:
            media_data['media_type'] = 'sticker'
            sticker = message.sticker
            media_data['file_id'] = sticker.file_id
            media_data['file_unique_id'] = sticker.file_unique_id
            media_data['file_size'] = sticker.file_size
            media_data['width'] = sticker.width
            media_data['height'] = sticker.height
            media_data['media_info'] = {
                "emoji": sticker.emoji, "set_name": sticker.set_name
            }
            
        elif message.animation:
            media_data['media_type'] = 'animation'
            anim = message.animation
            media_data['file_id'] = anim.file_id
            media_data['file_unique_id'] = anim.file_unique_id
            media_data['file_size'] = anim.file_size
            media_data['mime_type'] = anim.mime_type
            media_data['duration'] = anim.duration
            media_data['media_info'] = {
                "duration": anim.duration, "file_name": anim.file_name
            }
            
        elif message.video_note:
            media_data['media_type'] = 'video_note'
            vn = message.video_note
            media_data['file_id'] = vn.file_id
            media_data['file_unique_id'] = vn.file_unique_id
            media_data['file_size'] = vn.file_size
            media_data['duration'] = vn.duration
            media_data['media_info'] = {
                "duration": vn.duration, "length": vn.length
            }
        
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
    
    def log_text_message(self, sender_id: int, receiver_id: int, content: str, is_reply: bool = False) -> int:
        """Log a text message to the conversation"""
        conversation_id = self.conv_repo.get_or_create(sender_id, receiver_id)
        
        message_id = self.conv_repo.add_message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            message_type='text',
            content=content,
            is_reply=is_reply
        )
        
        return message_id
    
    def log_media_message(self, sender_id: int, receiver_id: int, media_data: dict, is_reply: bool = False) -> int:
        """Log a media message to the conversation"""
        conversation_id = self.conv_repo.get_or_create(sender_id, receiver_id)
        
        message_id = self.conv_repo.add_message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            message_type=media_data['media_type'],
            content=media_data.get('caption'),
            file_id=media_data.get('file_id'),
            file_unique_id=media_data.get('file_unique_id'),
            file_size=media_data.get('file_size'),
            mime_type=media_data.get('mime_type'),
            duration=media_data.get('duration'),
            width=media_data.get('width'),
            height=media_data.get('height'),
            caption=media_data.get('caption'),
            media_info=json.dumps(media_data.get('media_info', {})),
            is_reply=is_reply
        )
        
        return message_id
    
    def get_conversation_messages(self, user_a_id: int, user_b_id: int, limit: int = 100) -> list:
        """Get all messages between two users"""
        conversation_id = self.conv_repo.get_or_create(user_a_id, user_b_id)
        return self.conv_repo.get_messages(conversation_id, limit)
    
    def get_user_conversations(self, user_id: int) -> list:
        """Get all conversations for a user"""
        return self.conv_repo.get_user_conversations(user_id)
    
    def get_stats(self) -> dict:
        """Get message statistics"""
        return self.conv_repo.get_stats()
    
    def get_all_conversations(self) -> list:
        """Get all conversations with messages"""
        conversations = self.conv_repo.get_all_conversations()
        
        # Add messages to each conversation
        for conv in conversations:
            conv['messages'] = self.conv_repo.get_messages(conv['id'])
        
        return conversations
    
    def end_conversation(self, user_a_id: int, user_b_id: int):
        """End conversation between two users"""
        conversation_id = self.conv_repo.get_or_create(user_a_id, user_b_id)
        self.conv_repo.end_conversation(conversation_id)