from telegram import Update
from telegram.ext import ContextTypes
from config.settings import settings
from database.user_repository import UserRepository
from services.channel_service import ChannelService

class StartHandler:
    """Handler for /start command"""
    
    def __init__(self):
        self.user_repo = UserRepository()
        self.channel_service = ChannelService()
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        if self.user_repo.is_banned(user.id):
            await update.message.reply_text("🚫 You are banned from using this bot.")
            return
        
        # Check channel membership FIRST (admins bypass)
        if user.id not in settings.ADMIN_IDS:
            all_joined, not_joined, _ = await self.channel_service.check_user_joined_channels(
                context, user.id
            )
            
            if not all_joined:
                keyboard = self.channel_service.get_join_keyboard(not_joined)
                channel_list = "\n".join([
                    f"• {ch.get('channel_title', 'Channel')}"
                    for ch in not_joined
                ])
                
                await update.message.reply_text(
                    f"⚠️ **You must join these channels to use the bot:**\n\n"
                    f"{channel_list}\n\n"
                    f"Click the buttons below to join each channel.\n"
                    f"After joining ALL channels, click the **Verify** button.",
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
                return
        
        # Collect user data
        username = user.username
        first_name = user.first_name
        last_name = user.last_name
        full_name = user.full_name
        profile_link = f"https://t.me/{username}" if username else f"tg://user?id={user.id}"
        language_code = user.language_code
        is_premium = user.is_premium or False
        is_bot = user.is_bot or False
        
        # Save user
        self.user_repo.add_or_update(
            user.id, username, first_name, last_name, full_name,
            profile_link, language_code, is_premium, is_bot
        )
        self.user_repo.update_last_active(user.id)
        
        # Deep link handling
        if context.args and context.args[0].isdigit():
            target_id = int(context.args[0])
            
            if target_id == user.id:
                await update.message.reply_text("❌ You can't message yourself!")
                return
            
            if self.user_repo.is_banned(target_id):
                await update.message.reply_text("❌ This user is no longer available.")
                return
            
            target = self.user_repo.get_info(target_id)
            if not target:
                await update.message.reply_text("❌ This link is invalid.")
                return
            
            context.user_data['send_to'] = target_id
            
            await update.message.reply_text(
                "✉️ You can send ONE anonymous message to this person.\n"
                "You can send text, photos, videos, voice notes, stickers, and more!\n"
                "Send your message now...\n"
                "Send /cancel to abort."
            )
            return
        
        # Generate link
        bot_username = context.bot.username
        link = f"https://t.me/{bot_username}?start={user.id}"
        
        await update.message.reply_text(
            f"👋 Welcome {user.first_name}!\n\n"
            f"🔗 Your anonymous messaging link:\n{link}\n\n"
            f"Share this link - anyone who clicks it can send you ONE anonymous message.\n"
            f"Supports text, photos, videos, voice notes, and more!"
        )
    
    async def stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stop command"""
        user = update.effective_user
        
        if self.user_repo.is_banned(user.id):
            return
        
        partner = self.user_repo.unlink(user.id)
        self.user_repo.clear_replying_to(user.id)
        
        if context.user_data.get('waiting_for'):
            context.user_data['waiting_for'] = None
        
        await update.message.reply_text("🔕 Chat ended.")
        
        if partner:
            self.user_repo.clear_replying_to(partner)
            try:
                await context.bot.send_message(partner, "🔕 The other person ended the chat.")
            except:
                pass
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /cancel command"""
        user = update.effective_user
        
        self.user_repo.clear_replying_to(user.id)
        
        if 'send_to' in context.user_data:
            del context.user_data['send_to']
        
        if context.user_data.get('waiting_for'):
            context.user_data['waiting_for'] = None
            
            if user.id in settings.ADMIN_IDS:
                await update.message.reply_text("❌ Operation cancelled.")
                from .admin_handler import AdminHandler
                await AdminHandler().show_panel(update, context)
                return
        
        await update.message.reply_text("❌ Operation cancelled.")