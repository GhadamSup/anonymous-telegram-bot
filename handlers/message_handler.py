from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config.settings import settings
from database.user_repository import UserRepository
from services.message_service import MessageService
from services.channel_service import ChannelService

class MessageHandler:
    """Handler for text and media messages"""
    
    def __init__(self):
        self.user_repo = UserRepository()
        self.message_service = MessageService()
        self.channel_service = ChannelService()
    
    async def _check_channels(self, update, context):
        """Check if user has joined required channels"""
        user = update.effective_user
        
        if user.id in settings.ADMIN_IDS:
            return True
        
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
            return False
        
        return True
    
    async def handle_text(self, update, context):
        """Handle text messages"""
        user = update.effective_user
        
        if self.user_repo.is_banned(user.id):
            await update.message.reply_text("🚫 You are banned from using this bot.")
            return
        
        if not await self._check_channels(update, context):
            return
        
        self.user_repo.update_last_active(user.id)
        
        if user.id in settings.ADMIN_IDS:
            waiting = context.user_data.get('waiting_for')
            if waiting in ['ban_id', 'unban_id', 'broadcast_message', 'add_channel']:
                from .admin_handler import AdminHandler
                admin = AdminHandler()
                if waiting == 'ban_id':
                    await admin.process_ban_id(update, context)
                elif waiting == 'unban_id':
                    await admin.process_unban_id(update, context)
                elif waiting == 'broadcast_message':
                    await admin.process_broadcast(update, context)
                elif waiting == 'add_channel':
                    await admin.process_add_channel(update, context)
                return
        
        replying_to = self.user_repo.get_replying_to(user.id)
        
        if replying_to:
            if self.user_repo.is_banned(replying_to):
                await update.message.reply_text("❌ This user is no longer available.")
                self.user_repo.clear_replying_to(user.id)
                return
            
            try:
                await context.bot.send_message(
                    replying_to,
                    f"💬 Reply:\n\n{update.message.text}",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("↩️ Reply", callback_data=f"reply_{user.id}")
                    ]])
                )
                await update.message.reply_text("✅ Reply sent!")
                self.message_service.log_text_message(user.id, replying_to, update.message.text, is_reply=True)
            except:
                await update.message.reply_text("❌ Couldn't send reply.")
            
            self.user_repo.clear_replying_to(user.id)
            return
        
        if 'send_to' in context.user_data:
            target_id = context.user_data['send_to']
            del context.user_data['send_to']
            
            if self.user_repo.is_banned(target_id):
                await update.message.reply_text("❌ This user is no longer available.")
                return
            
            try:
                await context.bot.send_message(
                    target_id,
                    f"💬 Anonymous message:\n\n{update.message.text}",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("↩️ Reply", callback_data=f"reply_{user.id}")
                    ]])
                )
                await update.message.reply_text("✅ Your anonymous message has been sent!")
                self.message_service.log_text_message(user.id, target_id, update.message.text)
            except:
                await update.message.reply_text("❌ Couldn't deliver message.")
            return
        
        await update.message.reply_text(
            "❌ You're not in a conversation!\n"
            "Use /start to get your link or click someone else's link to send a message."
        )
    
    async def handle_media(self, update, context):
        """Handle media messages"""
        user = update.effective_user
        
        if self.user_repo.is_banned(user.id):
            await update.message.reply_text("🚫 You are banned from using this bot.")
            return
        
        if not await self._check_channels(update, context):
            return
        
        self.user_repo.update_last_active(user.id)
        
        media_data = self.message_service.extract_media_info(update.message)
        if not media_data:
            return
        
        replying_to = self.user_repo.get_replying_to(user.id)
        
        if replying_to:
            if self.user_repo.is_banned(replying_to):
                await update.message.reply_text("❌ This user is no longer available.")
                self.user_repo.clear_replying_to(user.id)
                return
            
            caption_text = f"💬 Reply:\n\n{media_data['caption']}" if media_data.get('caption') else "💬 Reply"
            
            success = await self.message_service.send_media(context, replying_to, user.id, media_data, caption_text)
            
            if success:
                await update.message.reply_text("✅ Reply sent!")
                self.message_service.log_media_message(user.id, replying_to, media_data, is_reply=True)
            else:
                await update.message.reply_text("❌ Couldn't send reply.")
            
            self.user_repo.clear_replying_to(user.id)
            return
        
        if 'send_to' in context.user_data:
            target_id = context.user_data['send_to']
            del context.user_data['send_to']
            
            if self.user_repo.is_banned(target_id):
                await update.message.reply_text("❌ This user is no longer available.")
                return
            
            caption_text = f"💬 Anonymous message:\n\n{media_data['caption']}" if media_data.get('caption') else "💬 Anonymous message"
            
            success = await self.message_service.send_media(context, target_id, user.id, media_data, caption_text)
            
            if success:
                await update.message.reply_text("✅ Your anonymous message has been sent!")
                self.message_service.log_media_message(user.id, target_id, media_data)
            else:
                await update.message.reply_text("❌ Couldn't deliver message.")
            return
        
        await update.message.reply_text(
            "❌ You're not in a conversation!\n"
            "Use /start to get your link or click someone else's link to send a message."
        )