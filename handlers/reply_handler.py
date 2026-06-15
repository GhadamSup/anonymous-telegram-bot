from telegram import Update
from telegram.ext import ContextTypes
from config.settings import settings
from database.user_repository import UserRepository
from services.channel_service import ChannelService

class ReplyHandler:
    """Handler for reply button callbacks"""
    
    def __init__(self):
        self.user_repo = UserRepository()
        self.channel_service = ChannelService()
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle reply button clicks"""
        query = update.callback_query
        
        user_id = query.from_user.id
        
        if self.user_repo.is_banned(user_id):
            await query.answer("🚫 You are banned from using this bot.")
            await query.edit_message_text("🚫 You are banned from using this bot.")
            return
        
        # Handle channel join verification
        if query.data == "verify_channels":
            all_joined, not_joined, joined = await self.channel_service.check_user_joined_channels(
                context, user_id
            )
            
            if all_joined:
                await query.edit_message_text(
                    "✅ **Verification successful!**\n\n"
                    "You have joined all required channels.\n"
                    "You can now use the bot.\n\n"
                    "Use /start to get your anonymous messaging link!",
                    parse_mode='Markdown'
                )
                await query.answer("✅ Verification successful!")
            else:
                # Answer with a popup notification instead of editing if content is the same
                channel_names = ", ".join([
                    ch.get('channel_title', 'Channel') 
                    for ch in not_joined
                ])
                await query.answer(
                    f"❌ You still need to join: {channel_names}",
                    show_alert=True
                )
            return
        
        if query.data.startswith("reply_"):
            sender_id = int(query.data.split("_")[1])
            
            if self.user_repo.is_banned(sender_id):
                await query.answer("❌ This user is no longer available.")
                await query.edit_message_text("❌ This user is no longer available.")
                return
            
            self.user_repo.set_replying_to(user_id, sender_id)
            
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text(
                "✍️ Type your reply now...\n"
                "Send any message (text, photo, video, voice, etc.) to reply.\n"
                "Send /cancel to cancel."
            )
            await query.answer()