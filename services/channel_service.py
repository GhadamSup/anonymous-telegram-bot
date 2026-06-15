from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
from database.channel_repository import ChannelRepository

class ChannelService:
    """Service for channel verification"""
    
    def __init__(self):
        self.channel_repo = ChannelRepository()
    
    async def check_user_joined_channels(self, context, user_id: int) -> tuple:
        """
        Check if user has joined all required channels
        Returns: (all_joined: bool, not_joined_channels: list, joined_channels: list)
        """
        channels = self.channel_repo.get_active_channels()
        
        if not channels:
            return True, [], []
        
        not_joined = []
        joined = []
        
        for channel in channels:
            try:
                member = await context.bot.get_chat_member(
                    chat_id=channel['channel_id'],
                    user_id=user_id
                )
                
                # Check if user is a member
                if member.status in ['left', 'kicked', 'banned']:
                    not_joined.append(channel)
                else:
                    joined.append(channel)
            except TelegramError as e:
                print(f"Error checking channel {channel['channel_id']}: {e}")
                not_joined.append(channel)
        
        all_joined = len(not_joined) == 0
        return all_joined, not_joined, joined
    
    def get_join_keyboard(self, not_joined_channels: list) -> InlineKeyboardMarkup:
        """Create keyboard with join buttons for required channels"""
        keyboard = []
        
        for channel in not_joined_channels:
            # Use the invite_link that admin provided when adding the channel
            url = channel.get('invite_link')
            
            # Fallback: if no invite_link, try username, then channel ID
            if not url:
                if channel.get('channel_username'):
                    url = f"https://t.me/{channel['channel_username']}"
                else:
                    url = f"https://t.me/c/{str(channel['channel_id'])[4:]}"
            
            channel_title = channel.get('channel_title', 'Channel')
            keyboard.append([
                InlineKeyboardButton(
                    f"📢 Join {channel_title[:30]}",
                    url=url
                )
            ])
        
        # Add verify button
        keyboard.append([
            InlineKeyboardButton("✅ I've Joined All Channels", callback_data="verify_channels")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    async def verify_and_show_join_prompt(self, update, context, user_id: int) -> bool:
        """
        Verify channel membership and show join prompt if needed
        Returns: True if user can proceed, False if blocked
        """
        all_joined, not_joined, _ = await self.check_user_joined_channels(context, user_id)
        
        if not all_joined:
            keyboard = self.get_join_keyboard(not_joined)
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