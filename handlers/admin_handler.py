import os
import json
import psutil
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import TelegramError
from config.settings import settings
from database.user_repository import UserRepository
from database.conversation_repository import ConversationRepository
from database.channel_repository import ChannelRepository
from services.system_service import SystemService

class AdminHandler:
    """Handler for admin commands and callbacks"""
    
    def __init__(self):
        self.user_repo = UserRepository()
        self.conv_repo = ConversationRepository()
        self.channel_repo = ChannelRepository()
        self.system_service = SystemService()
        self.bot = None
    
    def set_bot(self, bot):
        """Set reference to main bot for restart/stop"""
        self.bot = bot
    
    # ============================================
    # MAIN PANELS
    # ============================================
    
    async def show_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show main admin panel"""
        user = update.effective_user
        
        if user.id not in settings.ADMIN_IDS:
            await update.message.reply_text("❌ You don't have permission.")
            return
        
        text = (
            f"🛡️ **Admin Panel**\n\n"
            f"Welcome, {user.first_name}!\n"
            f"Select a category to manage:\n\n"
            f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        keyboard = [
            [InlineKeyboardButton("👥 Manage Users", callback_data="admin_menu_users")],
            [InlineKeyboardButton("🤖 Manage Bot", callback_data="admin_menu_bot")],
            [InlineKeyboardButton("📊 Manage Data", callback_data="admin_menu_data")],
            [InlineKeyboardButton("📈 Statistics", callback_data="admin_menu_stats")],
        ]
        
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def _show_main_menu(self, query, context):
        """Show main admin panel from callback"""
        user = query.from_user
        
        text = (
            f"🛡️ **Admin Panel**\n\n"
            f"Welcome, {user.first_name}!\n"
            f"Select a category to manage:\n\n"
            f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        keyboard = [
            [InlineKeyboardButton("👥 Manage Users", callback_data="admin_menu_users")],
            [InlineKeyboardButton("🤖 Manage Bot", callback_data="admin_menu_bot")],
            [InlineKeyboardButton("📊 Manage Data", callback_data="admin_menu_data")],
            [InlineKeyboardButton("📈 Statistics", callback_data="admin_menu_stats")],
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    # ============================================
    # MENU: MANAGE USERS
    # ============================================
    
    async def _show_users_menu(self, query, context):
        """Show user management menu"""
        text = (
            f"👥 **Manage Users**\n\n"
            f"Select an action:"
        )
        
        keyboard = [
            [InlineKeyboardButton("🚫 Ban User", callback_data="admin_ban_user")],
            [InlineKeyboardButton("✅ Unban User", callback_data="admin_unban_user")],
            [InlineKeyboardButton("📋 View Banned Users", callback_data="admin_view_banned")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="admin_back_to_main")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    # ============================================
    # MENU: MANAGE BOT
    # ============================================
    
    async def _show_bot_menu(self, query, context):
        """Show bot management menu"""
        text = (
            f"🤖 **Manage Bot**\n\n"
            f"⚠️ Use these controls carefully!\n\n"
            f"Select an action:"
        )
        
        keyboard = [
            [InlineKeyboardButton("📢 Sponsored Channels", callback_data="admin_channels_menu")],
            [InlineKeyboardButton("📣 Broadcast Message", callback_data="admin_broadcast")],
            [InlineKeyboardButton("🔄 Restart Bot", callback_data="admin_restart_bot")],
            [InlineKeyboardButton("🛑 Stop Bot", callback_data="admin_stop_bot")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="admin_back_to_main")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    # ============================================
    # MENU: MANAGE DATA
    # ============================================
    
    async def _show_data_menu(self, query, context):
        """Show data management menu"""
        text = (
            f"📊 **Manage Data**\n\n"
            f"Select an action:"
        )
        
        keyboard = [
            [InlineKeyboardButton("📋 Export User List", callback_data="admin_export_users")],
            [InlineKeyboardButton("💬 Browse Conversations", callback_data="admin_browse_convos")],
            [InlineKeyboardButton("📥 Export All Messages", callback_data="admin_export_all_messages")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="admin_back_to_main")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    # ============================================
    # MENU: STATISTICS
    # ============================================
    
    async def _show_stats_menu(self, query, context):
        """Show statistics menu"""
        text = (
            f"📈 **Statistics**\n\n"
            f"Select a category to view:"
        )
        
        keyboard = [
            [InlineKeyboardButton("👥 User Statistics", callback_data="admin_quick_stats")],
            [InlineKeyboardButton("🖥 System Statistics", callback_data="admin_system_stats")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="admin_back_to_main")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    # ============================================
    # SPONSORED CHANNELS MANAGEMENT
    # ============================================
    
    async def _show_channels_menu(self, query, context):
        """Show sponsored channels menu"""
        channels = self.channel_repo.get_all_channels()
        
        if not channels:
            text = (
                f"📢 **Sponsored Channels**\n\n"
                f"No channels added yet.\n"
                f"Add channels that users must join to use the bot."
            )
        else:
            text = f"📢 **Sponsored Channels** ({len(channels)})\n\n"
            for i, ch in enumerate(channels):
                status = "🟢" if ch['is_active'] else "🔴"
                title = ch.get('channel_title') or ch.get('channel_username') or f"ID: {ch['channel_id']}"
                text += f"{i+1}. {status} {title}\n"
                if ch.get('channel_username'):
                    text += f"   @{ch['channel_username']}\n"
                text += "\n"
        
        keyboard = []
        
        # Channel buttons
        for ch in channels:
            title = ch.get('channel_title') or ch.get('channel_username') or f"Channel {ch['channel_id']}"
            keyboard.append([
                InlineKeyboardButton(
                    f"{'🟢' if ch['is_active'] else '🔴'} {title[:30]}",
                    callback_data=f"admin_channel_toggle_{ch['channel_id']}"
                ),
                InlineKeyboardButton(
                    "🗑️",
                    callback_data=f"admin_channel_remove_{ch['channel_id']}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("➕ Add Channel", callback_data="admin_add_channel")])
        keyboard.append([InlineKeyboardButton("🔙 Back to Bot Menu", callback_data="admin_menu_bot")])
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def process_add_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process adding a new channel via invite link"""
        text = update.message.text.strip()
        bot_username = context.bot.username
        
        # Check if it's a valid invite link
        if not text.startswith('https://t.me/'):
            await update.message.reply_text(
                "❌ Invalid format. Please send a valid Telegram invite link.\n"
                "Example: `https://t.me/+abc123def` or `https://t.me/channelname`\n"
                "Send /cancel to abort.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data="admin_channels_menu")
                ]]),
                parse_mode='Markdown'
            )
            return
        
        # Show processing message
        status_msg = await update.message.reply_text("🔍 Fetching channel information...")
        
        try:
            # Try to get chat info from the invite link
            if '/+' in text:
                try:
                    chat = await context.bot.get_chat(text)
                except:
                    await status_msg.delete()
                    await update.message.reply_text(
                        "❌ **Cannot access this channel!**\n\n"
                        "Please make sure:\n"
                        f"1. The bot (@{bot_username}) is added as **admin** to the channel\n"
                        "2. The invite link is valid and not expired\n\n"
                        "**Steps:**\n"
                        "1. Go to your channel\n"
                        "2. Open Channel Info → Administrators\n"
                        f"3. Add @{bot_username} as administrator\n"
                        "4. Grant permission to manage invite links\n"
                        "5. Send the invite link again",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🔙 Back", callback_data="admin_channels_menu")
                        ]]),
                        parse_mode='Markdown'
                    )
                    return
            else:
                channel_username = text.split('/')[-1].replace('@', '')
                try:
                    chat = await context.bot.get_chat(f"@{channel_username}")
                except:
                    await status_msg.delete()
                    await update.message.reply_text(
                        "❌ **Channel not found!**\n\n"
                        "Make sure the channel exists and is public.",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🔙 Back", callback_data="admin_channels_menu")
                        ]]),
                        parse_mode='Markdown'
                    )
                    return
            
            channel_id = chat.id
            channel_title = chat.title
            channel_username = chat.username
            
            # CRITICAL: Check if bot is admin in this channel
            try:
                bot_member = await context.bot.get_chat_member(
                    chat_id=channel_id,
                    user_id=context.bot.id
                )
                
                if bot_member.status not in ['administrator', 'creator']:
                    await status_msg.delete()
                    await update.message.reply_text(
                        f"❌ **Bot is NOT an admin in this channel!**\n\n"
                        f"**Channel:** {channel_title}\n"
                        f"**Bot Status:** {bot_member.status}\n\n"
                        f"**Required:** Administrator\n\n"
                        f"Please make the bot an admin first:\n"
                        f"1. Go to: {channel_title}\n"
                        f"2. Open Channel Info → Administrators\n"
                        f"3. Add @{bot_username} as administrator\n"
                        f"4. Grant these permissions:\n"
                        f"   • View messages\n"
                        f"   • Manage invite links (optional)\n"
                        f"5. Send the link again",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🔙 Back", callback_data="admin_channels_menu")
                        ]]),
                        parse_mode='Markdown'
                    )
                    return
                    
            except TelegramError as e:
                await status_msg.delete()
                await update.message.reply_text(
                    f"❌ **Cannot verify bot permissions!**\n\n"
                    f"Error: {str(e)}\n\n"
                    f"Make sure:\n"
                    f"1. The bot is a member of the channel\n"
                    f"2. The bot has admin rights\n"
                    f"3. The channel is accessible",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Back", callback_data="admin_channels_menu")
                    ]]),
                    parse_mode='Markdown'
                )
                return
            
            # Get or create invite link
            try:
                invite_link = chat.invite_link
                if not invite_link:
                    invite_link_obj = await context.bot.create_chat_invite_link(
                        chat_id=channel_id,
                        creates_join_request=False
                    )
                    invite_link = invite_link_obj.invite_link
            except:
                invite_link = text
            
            # Check if channel already exists
            existing = self.channel_repo.get_channel(channel_id)
            if existing:
                await status_msg.delete()
                await update.message.reply_text(
                    "❌ This channel is already added to the sponsored list.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Back", callback_data="admin_channels_menu")
                    ]])
                )
                return
            
            # Add channel to database
            self.channel_repo.add_channel(
                channel_id=channel_id,
                channel_username=channel_username,
                channel_title=channel_title,
                invite_link=invite_link
            )
            
            context.user_data['waiting_for'] = None
            
            await status_msg.delete()
            await update.message.reply_text(
                f"✅ **Channel added successfully!**\n\n"
                f"📢 **Title:** {channel_title}\n"
                f"🆔 **ID:** `{channel_id}`\n"
                f"🔗 **Username:** @{channel_username or 'Private'}\n"
                f"🔗 **Link:** {invite_link}\n"
                f"🛡️ **Bot Role:** Admin ✅\n\n"
                f"Users will now be required to join this channel before using the bot.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Channels", callback_data="admin_channels_menu")
                ]]),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await status_msg.delete()
            await update.message.reply_text(
                f"❌ **Error:** {str(e)}\n\n"
                "Please try again or send /cancel to abort.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data="admin_channels_menu")
                ]])
            )
    
    async def _toggle_channel(self, query, context, channel_id):
        """Toggle channel active status"""
        channel = self.channel_repo.get_channel(channel_id)
        
        if not channel:
            await query.answer("Channel not found!")
            return
        
        new_status = not channel['is_active']
        self.channel_repo.toggle_channel(channel_id, new_status)
        
        await query.answer(f"Channel {'activated' if new_status else 'deactivated'}!")
        await self._show_channels_menu(query, context)
    
    async def _remove_channel(self, query, context, channel_id):
        """Remove a channel"""
        channel = self.channel_repo.get_channel(channel_id)
        
        if not channel:
            await query.answer("Channel not found!")
            return
        
        self.channel_repo.remove_channel(channel_id)
        
        await query.answer("Channel removed!")
        await self._show_channels_menu(query, context)
    
    # ============================================
    # USER STATISTICS
    # ============================================
    
    async def _show_quick_stats(self, query, context):
        """Show quick user statistics"""
        stats = self.user_repo.get_stats()
        conv_stats = self.conv_repo.get_stats()
        
        text = (
            f"👥 **User Statistics**\n\n"
            f"👥 Total Users: **{stats['total_users']}**\n"
            f"💎 Premium Users: **{stats['premium_users']}**\n"
            f"🚫 Banned Users: **{stats['banned_users']}**\n"
            f"👤 Active Chats: **{stats['active_chats']}**\n\n"
            f"💬 Total Messages: **{conv_stats['total_messages']}**\n"
            f"🖼 Media Messages: **{conv_stats['media_messages']}**\n"
            f"↩️ Replies: **{conv_stats['reply_messages']}**\n"
            f"📁 Conversations: **{conv_stats['total_conversations']}**\n"
            f"🟢 Active: **{conv_stats['active_conversations']}**\n\n"
            f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="admin_quick_stats")],
            [InlineKeyboardButton("🔙 Back to Statistics", callback_data="admin_menu_stats")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    # ============================================
    # SYSTEM STATISTICS
    # ============================================
    
    async def _show_system_stats_menu(self, query, context):
        """Show system statistics menu"""
        text = (
            f"🖥 **System Resources**\n\n"
            f"Select a category to view:"
        )
        
        keyboard = [
            [InlineKeyboardButton("📊 System Overview", callback_data="admin_sys_overview")],
            [InlineKeyboardButton("🔥 CPU Usage", callback_data="admin_sys_cpu")],
            [InlineKeyboardButton("💾 Memory Usage", callback_data="admin_sys_memory")],
            [InlineKeyboardButton("💿 Disk Usage", callback_data="admin_sys_disk")],
            [InlineKeyboardButton("🌐 Network Usage", callback_data="admin_sys_network")],
            [InlineKeyboardButton("⚙️ Bot Process", callback_data="admin_sys_process")],
            [InlineKeyboardButton("🔙 Back to Statistics", callback_data="admin_menu_stats")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def _show_system_overview(self, query, context):
        """Show system overview"""
        stats = self.system_service.get_all_stats()
        
        text = (
            f"🖥 **System Overview**\n\n"
            f"**System:**\n"
            f"• OS: {stats['system']['os']}\n"
            f"• Host: {stats['system']['hostname']}\n"
            f"• Python: {stats['system']['python_version']}\n"
            f"• Uptime: {stats['system']['uptime']}\n\n"
            f"**CPU:** {stats['cpu']['percent']}% | Cores: {stats['cpu']['count']}\n"
            f"**RAM:** {stats['memory']['percent']}% ({stats['memory']['used_gb']}/{stats['memory']['total_gb']} GB)\n"
            f"**Disk:** {stats['disk']['percent']}% ({stats['disk']['used_gb']}/{stats['disk']['total_gb']} GB)\n"
            f"**Process:** {stats['process']['memory_used_mb']} MB RAM\n\n"
            f"🕐 {stats['timestamp']}"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="admin_sys_overview")],
            [InlineKeyboardButton("🔙 Back to System Menu", callback_data="admin_system_stats")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def _show_cpu_stats(self, query, context):
        """Show CPU statistics"""
        cpu = self.system_service.get_cpu_usage()
        
        bar_length = 20
        filled = int(cpu['percent'] / 100 * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        text = (
            f"🔥 **CPU Usage**\n\n"
            f"[{bar}] {cpu['percent']}%\n\n"
            f"• Cores: {cpu['count']}\n"
            f"• Frequency: {cpu['frequency']:.0f} MHz\n"
            f"• Per-core usage:\n"
        )
        
        per_cpu = psutil.cpu_percent(interval=1, percpu=True)
        for i, percent in enumerate(per_cpu):
            bar_len = 10
            filled = int(percent / 100 * bar_len)
            bar = "█" * filled + "░" * (bar_len - filled)
            text += f"  Core {i}: [{bar}] {percent}%\n"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="admin_sys_cpu")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_system_stats")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def _show_memory_stats(self, query, context):
        """Show memory statistics"""
        mem = self.system_service.get_memory_usage()
        
        bar_length = 20
        filled = int(mem['percent'] / 100 * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        text = (
            f"💾 **Memory Usage**\n\n"
            f"[{bar}] {mem['percent']}%\n\n"
            f"• Total: {mem['total_gb']} GB\n"
            f"• Used: {mem['used_gb']} GB\n"
            f"• Available: {mem['available_gb']} GB\n"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="admin_sys_memory")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_system_stats")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def _show_disk_stats(self, query, context):
        """Show disk statistics"""
        disk = self.system_service.get_disk_usage()
        
        bar_length = 20
        filled = int(disk['percent'] / 100 * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        text = (
            f"💿 **Disk Usage**\n\n"
            f"[{bar}] {disk['percent']}%\n\n"
            f"• Total: {disk['total_gb']} GB\n"
            f"• Used: {disk['used_gb']} GB\n"
            f"• Free: {disk['free_gb']} GB\n"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="admin_sys_disk")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_system_stats")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def _show_network_stats(self, query, context):
        """Show network statistics"""
        net = self.system_service.get_network_usage()
        
        text = (
            f"🌐 **Network Usage** (since bot start)\n\n"
            f"📤 Sent: {net['sent_mb']} MB\n"
            f"📥 Received: {net['recv_mb']} MB\n\n"
            f"• Packets sent: {net['packets_sent']:,}\n"
            f"• Packets received: {net['packets_recv']:,}\n"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="admin_sys_network")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_system_stats")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def _show_process_stats(self, query, context):
        """Show bot process statistics"""
        proc = self.system_service.get_process_info()
        
        text = (
            f"⚙️ **Bot Process**\n\n"
            f"• PID: {proc['pid']}\n"
            f"• Status: {proc['status']}\n"
            f"• CPU: {proc['cpu_percent']}%\n"
            f"• Memory: {proc['memory_used_mb']} MB ({proc['memory_percent']}%)\n"
            f"• Threads: {proc['threads']}\n"
            f"• Started: {proc['created']}\n"
            f"• Uptime: {proc['uptime']}\n"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="admin_sys_process")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_system_stats")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    # ============================================
    # BUTTON HANDLER (ROUTER)
    # ============================================
    
    async def handle_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all admin button clicks"""
        query = update.callback_query
        await query.answer()
        
        if query.from_user.id not in settings.ADMIN_IDS:
            await query.edit_message_text("❌ You don't have permission.")
            return
        
        data = query.data
        
        # Main menu navigation
        if data == "admin_back_to_main":
            await self._show_main_menu(query, context)
        elif data == "admin_menu_users":
            await self._show_users_menu(query, context)
        elif data == "admin_menu_bot":
            await self._show_bot_menu(query, context)
        elif data == "admin_menu_data":
            await self._show_data_menu(query, context)
        elif data == "admin_menu_stats":
            await self._show_stats_menu(query, context)
        elif data == "admin_quick_stats":
            await self._show_quick_stats(query, context)
        
        # Sponsored channels
        elif data == "admin_channels_menu":
            await self._show_channels_menu(query, context)
        elif data == "admin_add_channel":
            context.user_data['waiting_for'] = 'add_channel'
            await query.edit_message_text(
                "📢 **Add Sponsored Channel**\n\n"
                "Send me the channel invite link.\n\n"
                "**Requirements:**\n"
                "• Bot must be **admin** in the channel\n"
                "• Link format: `https://t.me/+abc123` or `https://t.me/channelname`\n\n"
                "**Examples:**\n"
                "• Private: `https://t.me/+abcdef123456`\n"
                "• Public: `https://t.me/mychannel`\n\n"
                "Send /cancel to abort.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data="admin_channels_menu")
                ]]),
                parse_mode='Markdown'
            )
        elif data.startswith("admin_channel_toggle_"):
            channel_id = int(data.split("_")[-1])
            await self._toggle_channel(query, context, channel_id)
        elif data.startswith("admin_channel_remove_"):
            channel_id = int(data.split("_")[-1])
            await self._remove_channel(query, context, channel_id)
        
        # System stats
        elif data == "admin_system_stats":
            await self._show_system_stats_menu(query, context)
        elif data == "admin_sys_overview":
            await self._show_system_overview(query, context)
        elif data == "admin_sys_cpu":
            await self._show_cpu_stats(query, context)
        elif data == "admin_sys_memory":
            await self._show_memory_stats(query, context)
        elif data == "admin_sys_disk":
            await self._show_disk_stats(query, context)
        elif data == "admin_sys_network":
            await self._show_network_stats(query, context)
        elif data == "admin_sys_process":
            await self._show_process_stats(query, context)
        
        # User management
        elif data == "admin_ban_user":
            context.user_data['waiting_for'] = 'ban_id'
            await query.edit_message_text(
                "🚫 **Ban User**\n\n"
                "Send me the User ID to ban.\n"
                "Send /cancel to abort.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data="admin_menu_users")
                ]]),
                parse_mode='Markdown'
            )
        elif data == "admin_unban_user":
            context.user_data['waiting_for'] = 'unban_id'
            await query.edit_message_text(
                "✅ **Unban User**\n\n"
                "Send me the User ID to unban.\n"
                "Send /cancel to abort.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data="admin_menu_users")
                ]]),
                parse_mode='Markdown'
            )
        elif data == "admin_view_banned":
            await self._view_banned(query, context)
        
        # Bot management
        elif data == "admin_restart_bot":
            await self._confirm_restart(query, context)
        elif data == "admin_restart_confirm":
            await self._restart_bot(query, context)
        elif data == "admin_stop_bot":
            await self._confirm_stop(query, context)
        elif data == "admin_stop_confirm":
            await self._stop_bot(query, context)
        elif data == "admin_broadcast":
            await self._broadcast_confirm(query, context)
        elif data == "admin_broadcast_confirm":
            context.user_data['waiting_for'] = 'broadcast_message'
            await query.edit_message_text(
                "📢 **Broadcast Mode**\n\n"
                "Send me the message to broadcast.\n"
                "Send /cancel to abort.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data="admin_menu_bot")
                ]]),
                parse_mode='Markdown'
            )
        
        # Data management
        elif data == "admin_export_users":
            await self._export_users(query, context)
        elif data == "admin_export_all_messages":
            await self._export_all_messages(query, context)
        elif data == "admin_browse_convos":
            await self._show_conversations_list(query, context, page=0)
        elif data.startswith("admin_convos_page_"):
            page = int(data.split("_")[-1])
            await self._show_conversations_list(query, context, page)
        elif data.startswith("admin_view_convo_"):
            conv_id = int(data.split("_")[-1])
            await self._show_conversation_messages(query, context, conv_id, page=0)
        elif data.startswith("admin_convo_msgs_page_"):
            parts = data.split("_")
            conv_id = int(parts[3])
            page = int(parts[4])
            await self._show_conversation_messages(query, context, conv_id, page)
    
    # ============================================
    # PROCESS FUNCTIONS (TEXT INPUT)
    # ============================================
    
    async def process_ban_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process ban user ID"""
        if not update.message.text.isdigit():
            await update.message.reply_text(
                "❌ Invalid ID. Send /cancel to abort.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Users Menu", callback_data="admin_menu_users")
                ]])
            )
            return
        
        target_id = int(update.message.text)
        target = self.user_repo.get_info(target_id)
        
        if not target:
            await update.message.reply_text(
                "❌ User not found.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Users Menu", callback_data="admin_menu_users")
                ]])
            )
            return
        
        if target['is_banned']:
            await update.message.reply_text(
                "❌ User already banned.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Users Menu", callback_data="admin_menu_users")
                ]])
            )
            return
        
        self.user_repo.ban(target_id)
        self.conv_repo.end_user_conversations(target_id)
        
        try:
            await context.bot.send_message(target_id, "🚫 You have been banned by an administrator.")
        except:
            pass
        
        context.user_data['waiting_for'] = None
        await update.message.reply_text(
            f"✅ User banned: {target.get('first_name', 'Unknown')} (ID: {target_id})",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Users Menu", callback_data="admin_menu_users")
            ]])
        )
    
    async def process_unban_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process unban user ID"""
        if not update.message.text.isdigit():
            await update.message.reply_text(
                "❌ Invalid ID. Send /cancel to abort.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Users Menu", callback_data="admin_menu_users")
                ]])
            )
            return
        
        target_id = int(update.message.text)
        target = self.user_repo.get_info(target_id)
        
        if not target:
            await update.message.reply_text(
                "❌ User not found.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Users Menu", callback_data="admin_menu_users")
                ]])
            )
            return
        
        if not target['is_banned']:
            await update.message.reply_text(
                "❌ User not banned.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Users Menu", callback_data="admin_menu_users")
                ]])
            )
            return
        
        self.user_repo.unban(target_id)
        
        try:
            await context.bot.send_message(target_id, "✅ You have been unbanned.")
        except:
            pass
        
        context.user_data['waiting_for'] = None
        await update.message.reply_text(
            f"✅ User unbanned: {target.get('first_name', 'Unknown')} (ID: {target_id})",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Users Menu", callback_data="admin_menu_users")
            ]])
        )
    
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
        await update.message.reply_text(
            f"✅ Broadcast completed!\n✅ {success_count} sent, ❌ {fail_count} failed",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Bot Menu", callback_data="admin_menu_bot")
            ]])
        )
    
    # ============================================
    # CONVERSATION VIEWING
    # ============================================
    
    async def _show_conversations_list(self, query, context, page=0):
        """Show paginated list of conversations"""
        per_page = 10
        offset = page * per_page
        
        conversations = self.conv_repo.get_all_conversations(limit=100)
        total_pages = max(1, (len(conversations) + per_page - 1) // per_page)
        page_convos = conversations[offset:offset + per_page]
        
        if not conversations:
            await query.edit_message_text(
                "📁 **No conversations found.**",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Data Menu", callback_data="admin_menu_data")
                ]]),
                parse_mode='Markdown'
            )
            return
        
        text = f"📁 **Conversations** (Page {page + 1}/{total_pages})\n\n"
        
        for i, conv in enumerate(page_convos):
            user_a = f"{conv.get('user_a_name', 'Unknown')}"
            user_b = f"{conv.get('user_b_name', 'Unknown')}"
            msg_count = conv.get('total_messages', 0)
            status = conv.get('status', 'unknown')
            status_icon = "🟢" if status == 'active' else "🔴"
            
            text += (
                f"{offset + i + 1}. {status_icon} #{conv['id']}\n"
                f"   {user_a} ↔ {user_b}\n"
                f"   💬 {msg_count} messages\n\n"
            )
        
        keyboard = []
        
        for conv in page_convos:
            keyboard.append([
                InlineKeyboardButton(
                    f"📋 View #{conv['id']}",
                    callback_data=f"admin_view_convo_{conv['id']}"
                )
            ])
        
        nav_buttons = []
        if page > 0:
            nav_buttons.append(
                InlineKeyboardButton("⬅️ Previous", callback_data=f"admin_convos_page_{page - 1}")
            )
        if page < total_pages - 1:
            nav_buttons.append(
                InlineKeyboardButton("Next ➡️", callback_data=f"admin_convos_page_{page + 1}")
            )
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        keyboard.append([InlineKeyboardButton("🔙 Back to Data Menu", callback_data="admin_menu_data")])
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def _show_conversation_messages(self, query, context, conv_id, page=0):
        """Show messages from a specific conversation"""
        per_page = 15
        offset = page * per_page
        
        messages = self.conv_repo.get_messages(conv_id, limit=500)
        total_pages = max(1, (len(messages) + per_page - 1) // per_page)
        page_messages = messages[offset:offset + per_page]
        
        if not messages:
            await query.edit_message_text(
                "📁 **No messages in this conversation.**",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to List", callback_data="admin_browse_convos")
                ]]),
                parse_mode='Markdown'
            )
            return
        
        conversations = self.conv_repo.get_all_conversations()
        conv_info = next((c for c in conversations if c['id'] == conv_id), None)
        
        if conv_info:
            user_a = f"{conv_info.get('user_a_name', 'Unknown')} ({conv_info['user_a_id']})"
            user_b = f"{conv_info.get('user_b_name', 'Unknown')} ({conv_info['user_b_id']})"
            header = (
                f"💬 **Conversation #{conv_id}**\n"
                f"{user_a} ↔ {user_b}\n"
                f"Status: {conv_info.get('status', 'unknown')}\n"
                f"Page {page + 1}/{total_pages} | Total: {len(messages)} messages\n"
                f"{'─' * 30}\n\n"
            )
        else:
            header = f"💬 **Conversation #{conv_id}**\nPage {page + 1}/{total_pages}\n{'─' * 30}\n\n"
        
        messages_text = ""
        for msg in page_messages:
            sender_name = msg.get('sender_name', 'Unknown')
            msg_type = msg.get('message_type', 'text')
            content = msg.get('content') or msg.get('caption') or ''
            timestamp = msg.get('timestamp', '')
            is_reply = "↩️ " if msg.get('is_reply') else ""
            
            type_icon = {
                'text': '💬', 'photo': '📷', 'video': '🎥', 'voice': '🎤',
                'audio': '🎵', 'document': '📄', 'sticker': '🎯',
                'animation': '🎬', 'video_note': '📹'
            }.get(msg_type, '📝')
            
            if content and len(content) > 100:
                content = content[:97] + "..."
            
            messages_text += (
                f"{type_icon} {is_reply}**{sender_name}**:\n"
                f"{content or f'[{msg_type}]'}\n"
                f"_{timestamp}_\n\n"
            )
        
        full_text = header + messages_text
        
        keyboard = []
        nav_buttons = []
        if page > 0:
            nav_buttons.append(
                InlineKeyboardButton("⬅️ Newer", callback_data=f"admin_convo_msgs_page_{conv_id}_{page - 1}")
            )
        if page < total_pages - 1:
            nav_buttons.append(
                InlineKeyboardButton("Older ➡️", callback_data=f"admin_convo_msgs_page_{conv_id}_{page + 1}")
            )
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        keyboard.append([
            InlineKeyboardButton("🔙 Back to List", callback_data="admin_browse_convos"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="admin_back_to_main")
        ])
        
        await query.edit_message_text(
            full_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    # ============================================
    # EXPORT FUNCTIONS
    # ============================================
    
    async def _export_users(self, query, context):
        """Export users as CSV"""
        users = self.user_repo.get_all()
        
        if not users:
            await query.edit_message_text(
                "No users in database.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data="admin_menu_data")
                ]])
            )
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
        
        await query.edit_message_text(
            f"✅ Exported {len(users)} users!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Data Menu", callback_data="admin_menu_data")
            ]])
        )
    
    async def _export_all_messages(self, query, context):
        """Export all messages as JSON file"""
        conversations = self.conv_repo.get_all_conversations(limit=200)
        
        if not conversations:
            await query.edit_message_text(
                "No conversations to export.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data="admin_menu_data")
                ]])
            )
            return
        
        export_data = {
            "export_date": datetime.now().isoformat(),
            "total_conversations": len(conversations),
            "conversations": []
        }
        
        for conv in conversations:
            messages = self.conv_repo.get_messages(conv['id'], limit=1000)
            conv_export = {
                "conversation_id": conv['id'],
                "user_a": {"id": conv['user_a_id'], "name": conv.get('user_a_name'), "username": conv.get('user_a_username')},
                "user_b": {"id": conv['user_b_id'], "name": conv.get('user_b_name'), "username": conv.get('user_b_username')},
                "status": conv.get('status'),
                "started_at": conv.get('started_at'),
                "message_count": len(messages),
                "messages": [{k: str(v) for k, v in msg.items()} for msg in messages]
            }
            export_data["conversations"].append(conv_export)
        
        filename = f"bot_messages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
        
        await context.bot.send_document(
            query.from_user.id,
            document=open(filename, 'rb'),
            filename=filename,
            caption=f"💬 Complete message export - {len(conversations)} conversations"
        )
        
        os.remove(filename)
        
        await query.edit_message_text(
            f"✅ Exported {len(conversations)} conversations!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Data Menu", callback_data="admin_menu_data")
            ]])
        )
    
    # ============================================
    # BOT CONTROL
    # ============================================
    
    async def _broadcast_confirm(self, query, context):
        """Confirm broadcast"""
        user_count = len(self.user_repo.get_all_user_ids())
        
        keyboard = [[
            InlineKeyboardButton("✅ Yes, Send", callback_data="admin_broadcast_confirm"),
            InlineKeyboardButton("❌ Cancel", callback_data="admin_menu_bot")
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
            await query.edit_message_text(
                "✅ No banned users.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data="admin_menu_users")
                ]])
            )
            return
        
        banned_list = "🚫 **Banned Users:**\n\n"
        for user in banned:
            banned_list += f"• ID: `{user['user_id']}` - {user.get('first_name', 'N/A')} (@{user.get('username', 'N/A')})\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Users Menu", callback_data="admin_menu_users")]]
        
        await query.edit_message_text(
            banned_list,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def _confirm_restart(self, query, context):
        """Confirm bot restart"""
        keyboard = [[
            InlineKeyboardButton("⚠️ Yes, Restart", callback_data="admin_restart_confirm"),
            InlineKeyboardButton("❌ Cancel", callback_data="admin_menu_bot")
        ]]
        
        await query.edit_message_text(
            "🔄 **Restart Bot**\n\n"
            "⚠️ This will restart the bot process.\n"
            "All active conversations will be preserved.\n"
            "The bot will be back online in a few seconds.\n\n"
            "Are you sure?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def _restart_bot(self, query, context):
        """Restart the bot"""
        await query.edit_message_text("🔄 Restarting bot...")
        
        if self.bot:
            self.bot.restart_bot()
    
    async def _confirm_stop(self, query, context):
        """Confirm bot stop"""
        keyboard = [[
            InlineKeyboardButton("🛑 Yes, Stop", callback_data="admin_stop_confirm"),
            InlineKeyboardButton("❌ Cancel", callback_data="admin_menu_bot")
        ]]
        
        await query.edit_message_text(
            "🛑 **Stop Bot**\n\n"
            "⚠️ This will completely stop the bot.\n"
            "It will NOT come back online automatically.\n"
            "You'll need to manually restart it.\n\n"
            "Are you sure?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def _stop_bot(self, query, context):
        """Stop the bot"""
        await query.edit_message_text("🛑 Bot stopped. Goodbye! 👋")
        
        if self.bot:
            self.bot.stop_bot()