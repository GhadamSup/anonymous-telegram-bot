from telegram import Update
from telegram.ext import ContextTypes
from database.user_repository import UserRepository

class ReplyHandler:
    """Handler for reply button callbacks"""
    
    def __init__(self):
        self.user_repo = UserRepository()
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle reply button clicks"""
        query = update.callback_query
        await query.answer()
        
        if self.user_repo.is_banned(query.from_user.id):
            await query.edit_message_text("🚫 You are banned from using this bot.")
            return
        
        if query.data.startswith("reply_"):
            sender_id = int(query.data.split("_")[1])
            
            if self.user_repo.is_banned(sender_id):
                await query.edit_message_text("❌ This user is no longer available.")
                return
            
            self.user_repo.set_replying_to(query.from_user.id, sender_id)
            
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text(
                "✍️ Type your reply now...\n"
                "Send any message (text, photo, video, voice, etc.) to reply.\n"
                "Send /cancel to cancel."
            )