import os
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config.settings import settings
from database.user_repository import UserRepository
from services.message_service import MessageService

class AdminHandler:
    """Handler for admin commands and callbacks"""
    
    def __init__(self):
        self.user_repo = UserRepository()
        self.message_service = MessageService()
    
    async def show_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show admin panel"""
        user = update.effective_user
        
        if user.id not in settings.ADMIN_IDS:
            await update.message.reply_text("❌ You don't have permission.")
            return
        
        stats = self.user_repo.get_stats()
        msg_stats = self.message_service.get_stats()
        
        stats_message = (
            f"📊 **Bot Statistics**\n\n"
            f"👥 Total Users: **{stats['total_users']}**\n"
            f"💎 Premium Users: **{stats['premium_users']}**\n"
            f"💬 Total Messages: **{msg_stats['total_messages']}**\n"
            f"🖼 Media Messages: **{msg_stats['media_messages']}**\n"
            f"↩️ Replies: **{msg_stats['reply_messages']}**\n"
            f"📁 Conversations: **{msg_stats['total_conversations']}**\n"
            f"👤 Active Chats: **{stats['active_chats']}**\n"
            f"🚫 Banned Users: **{stats['banned_users']}**\n"
            f"🕐 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        keyboard = [
            [InlineKeyboardButton("📋 Export User List", callback_data="admin_export_users")],
            [InlineKeyboardButton("💬 Export Messages", callback_data="admin_export_messages")],
            [InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast")],
            [InlineKeyboardButton("🚫 Ban User", callback_data="admin_ban_user")],
            [InlineKeyboardButton("✅ Unban User", callback_data="admin_unban_user")],
            [InlineKeyboardButton("📋 View Banned Users", callback_data="admin_view_banned")],
            [InlineKeyboardButton("📊 Refresh Stats", callback_data="admin_refresh_stats")]
        ]
        
        await update.message.reply_text(
            stats_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def handle_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin button clicks"""
        query = update.callback_query
        await query.answer()
        
        if query.from_user.id not in settings.ADMIN_IDS:
            await query.edit_message_text("❌ You don't have permission.")
            return
        
        if query.data == "admin_export_users":
            await self._export_users(query, context)
        elif query.data == "admin_export_messages":
            await self._export_messages(query, context)
        elif query.data == "admin_broadcast":
            await self._broadcast_confirm(query, context)
        elif query.data == "admin_broadcast_confirm":
            context.user_data['waiting_for'] = 'broadcast_message'
            await query.edit_message_text(
                "📢 **Broadcast Mode**\n\nSend me the message to broadcast.\nSend /cancel to abort.",
                parse_mode='Markdown'
            )
        elif query.data == "admin_ban_user":
            context.user_data['waiting_for'] = 'ban_id'
            await query.edit_message_text(
                "🚫 **Ban User**\n\nSend me the User ID to ban.\nSend /cancel to abort.",
                parse_mode='Markdown'
            )
        elif query.data == "admin_unban_user":
            context.user_data['waiting_for'] = 'unban_id'
            await query.edit_message_text(
                "✅ **Unban User**\n\nSend me the User ID to unban.\nSend /cancel to abort.",
                parse_mode='Markdown'
            )
        elif query.data == "admin_view_banned":
            await self._view_banned(query, context)
        elif query.data == "admin_back_to_panel":
            await self._show_panel_callback(query, context)
        elif query.data == "admin_refresh_stats":
            await self._show_panel_callback(query, context)
    
    async def process_ban_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process ban user ID"""
        if not update.message.text.isdigit():
            await update.message.reply_text("❌ Invalid ID. Send /cancel to abort.")
            return
        
        target_id = int(update.message.text)
        target = self.user_repo.get_info(target_id)
        
        if not target:
            await update.message.reply_text("❌ User not found.")
            return
        
        if target['is_banned']:
            await update.message.reply_text("❌ User already banned.")
            return
        
        self.user_repo.ban(target_id)
        
        try:
            await context.bot.send_message(target_id, "🚫 You have been banned by an administrator.")
        except:
            pass
        
        context.user_data['waiting_for'] = None
        await self.show_panel(update, context)
    
    async def process_unban_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process unban user ID"""
        if not update.message.text.isdigit():
            await update.message.reply_text("❌ Invalid ID. Send /cancel to abort.")
            return
        
        target_id = int(update.message.text)
        target = self.user_repo.get_info(target_id)
        
        if not target:
            await update.message.reply_text("❌ User not found.")
            return
        
        if not target['is_banned']:
            await update.message.reply_text("❌ User not banned.")
            return
        
        self.user_repo.unban(target_id)
        
        try:
            await context.bot.send_message(target_id, "✅ You have been unbanned.")
        except:
            pass
        
        context.user_data['waiting_for'] = None
        await self.show_panel(update, context)
    
    async def process_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process broadcast message"""
        broadcast_text = update.message.text
        context.user_data['waiting_for'] = None
        
        status_msg = await update.message.reply_text("📤 Starting broadcast...")
        
        user_ids = self.user_repo.get_all_user_ids()
        success_count = 0
        fail_count = 0
        
        for user_id in user_ids:
            try:
                await context.bot.send_message(
                    user_id,
                    f"📢 **Announcement from Admin:**\n\n{broadcast_text}",
                    parse_mode='Markdown'
                )
                success_count += 1
            except:
                fail_count += 1
        
        await status_msg.delete()
        await self.show_panel(update, context)
    
    async def _export_users(self, query, context):
        """Export users as CSV"""
        users = self.user_repo.get_all()
        
        if not users:
            await query.edit_message_text("No users in database.")
            return
        
        csv_content = "User ID,Username,First Name,Last Name,Full Name,Profile Link,Language,Premium,Bot,Banned\n"
        for user in users:
            row = [str(user.get(col, 'N/A')).replace(",", " ") for col in [
                'user_id', 'username', 'first_name', 'last_name', 'full_name',
                'profile_link', 'language_code', 'is_premium', 'is_bot', 'is_banned'
            ]]
            csv_content += ",".join(row) + "\n"
        
        filename = f"bot_users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        await context.bot.send_document(
            query.from_user.id,
            document=open(filename, 'rb'),
            filename=filename,
            caption=f"📋 User export - {len(users)} users"
        )
        
        os.remove(filename)
        await query.edit_message_text(f"✅ Exported {len(users)} users!")
    
    async def _export_messages(self, query, context):
        """Export messages as JSON"""
        conversations = self.message_service.get_all_conversations()
        
        if not conversations:
            await query.edit_message_text("No conversations in database.")
            return
        
        filename = f"bot_messages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(conversations, f, indent=2, default=str)
        
        await context.bot.send_document(
            query.from_user.id,
            document=open(filename, 'rb'),
            filename=filename,
            caption=f"💬 Message export - {len(conversations)} conversations"
        )
        
        os.remove(filename)
        await query.edit_message_text(f"✅ Exported {len(conversations)} conversations!")
    
    async def _broadcast_confirm(self, query, context):
        """Confirm broadcast"""
        user_count = len(self.user_repo.get_all_user_ids())
        
        keyboard = [[
            InlineKeyboardButton("✅ Yes, Send Broadcast", callback_data="admin_broadcast_confirm"),
            InlineKeyboardButton("❌ Cancel", callback_data="admin_back_to_panel")
        ]]
        
        await query.edit_message_text(
            f"📢 **Broadcast Message**\n\nThis will send to **{user_count}** users.\n\nContinue?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def _view_banned(self, query, context):
        """View banned users"""
        banned = self.user_repo.get_banned()
        
        if not banned:
            await query.edit_message_text("✅ No banned users.")
            return
        
        banned_list = "🚫 **Banned Users:**\n\n"
        for user in banned:
            banned_list += f"• ID: `{user['user_id']}` - {user.get('first_name', 'N/A')} (@{user.get('username', 'N/A')})\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_back_to_panel")]]
        
        await query.edit_message_text(
            banned_list,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def _show_panel_callback(self, query, context):
        """Show admin panel from callback"""
        stats = self.user_repo.get_stats()
        msg_stats = self.message_service.get_stats()
        
        stats_message = (
            f"📊 **Bot Statistics (Updated)**\n\n"
            f"👥 Total Users: **{stats['total_users']}**\n"
            f"💎 Premium Users: **{stats['premium_users']}**\n"
            f"💬 Total Messages: **{msg_stats['total_messages']}**\n"
            f"🖼 Media Messages: **{msg_stats['media_messages']}**\n"
            f"↩️ Replies: **{msg_stats['reply_messages']}**\n"
            f"📁 Conversations: **{msg_stats['total_conversations']}**\n"
            f"👤 Active Chats: **{stats['active_chats']}**\n"
            f"🚫 Banned Users: **{stats['banned_users']}**\n"
            f"🕐 Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        keyboard = [
            [InlineKeyboardButton("📋 Export User List", callback_data="admin_export_users")],
            [InlineKeyboardButton("💬 Export Messages", callback_data="admin_export_messages")],
            [InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast")],
            [InlineKeyboardButton("🚫 Ban User", callback_data="admin_ban_user")],
            [InlineKeyboardButton("✅ Unban User", callback_data="admin_unban_user")],
            [InlineKeyboardButton("📋 View Banned Users", callback_data="admin_view_banned")],
            [InlineKeyboardButton("📊 Refresh Stats", callback_data="admin_refresh_stats")]
        ]
        
        await query.edit_message_text(
            stats_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )