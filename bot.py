import os
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

load_dotenv()

# Get admin IDs from .env
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]

# Database functions
def init_db():
    conn = sqlite3.connect("bot.db")
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, 
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            full_name TEXT,
            profile_link TEXT,
            language_code TEXT,
            is_premium INTEGER DEFAULT 0,
            is_bot INTEGER DEFAULT 0,
            joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_banned INTEGER DEFAULT 0
        )
    """)
    
    # Add columns that might be missing from old databases
    try:
        conn.execute("ALTER TABLE users ADD COLUMN linked_to INTEGER")
    except sqlite3.OperationalError:
        pass
    
    try:
        conn.execute("ALTER TABLE users ADD COLUMN replying_to INTEGER")
    except sqlite3.OperationalError:
        pass
    
    try:
        conn.execute("ALTER TABLE users ADD COLUMN first_name TEXT")
    except sqlite3.OperationalError:
        pass
    
    try:
        conn.execute("ALTER TABLE users ADD COLUMN last_name TEXT")
    except sqlite3.OperationalError:
        pass
    
    try:
        conn.execute("ALTER TABLE users ADD COLUMN full_name TEXT")
    except sqlite3.OperationalError:
        pass
    
    try:
        conn.execute("ALTER TABLE users ADD COLUMN profile_link TEXT")
    except sqlite3.OperationalError:
        pass
    
    try:
        conn.execute("ALTER TABLE users ADD COLUMN language_code TEXT")
    except sqlite3.OperationalError:
        pass
    
    try:
        conn.execute("ALTER TABLE users ADD COLUMN is_premium INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    
    try:
        conn.execute("ALTER TABLE users ADD COLUMN is_bot INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    
    try:
        conn.execute("ALTER TABLE users ADD COLUMN joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    except sqlite3.OperationalError:
        pass
    
    try:
        conn.execute("ALTER TABLE users ADD COLUMN last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    except sqlite3.OperationalError:
        pass
    
    try:
        conn.execute("ALTER TABLE users ADD COLUMN is_banned INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    
    conn.commit()
    conn.close()

def add_or_update_user(user_id, username, first_name, last_name, full_name, 
                       profile_link, language_code, is_premium, is_bot):
    """Add or update user with available Telegram data"""
    conn = sqlite3.connect("bot.db")
    
    cursor = conn.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    exists = cursor.fetchone()
    
    if exists:
        conn.execute("""
            UPDATE users SET 
                username = ?,
                first_name = ?,
                last_name = ?,
                full_name = ?,
                profile_link = ?,
                language_code = ?,
                is_premium = ?,
                is_bot = ?,
                last_active = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (username, first_name, last_name, full_name, profile_link, 
              language_code, is_premium, is_bot, user_id))
    else:
        conn.execute("""
            INSERT INTO users (
                user_id, username, first_name, last_name, full_name,
                profile_link, language_code, is_premium, is_bot
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, username, first_name, last_name, full_name,
              profile_link, language_code, is_premium, is_bot))
    
    conn.commit()
    conn.close()

def update_last_active(user_id):
    """Update user's last active timestamp"""
    conn = sqlite3.connect("bot.db")
    conn.execute("UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def is_user_banned(user_id):
    conn = sqlite3.connect("bot.db")
    cursor = conn.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result and result[0] == 1

def ban_user(user_id):
    conn = sqlite3.connect("bot.db")
    conn.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (user_id,))
    conn.execute("UPDATE users SET linked_to = NULL WHERE user_id = ? OR linked_to = ?", (user_id, user_id))
    conn.execute("UPDATE users SET replying_to = NULL WHERE user_id = ? OR replying_to = ?", (user_id, user_id))
    conn.commit()
    conn.close()

def unban_user(user_id):
    conn = sqlite3.connect("bot.db")
    conn.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_user_info(user_id):
    conn = sqlite3.connect("bot.db")
    cursor = conn.execute("SELECT user_id, username, first_name, is_banned FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_banned_users():
    conn = sqlite3.connect("bot.db")
    cursor = conn.execute("SELECT user_id, username, first_name FROM users WHERE is_banned = 1")
    users = cursor.fetchall()
    conn.close()
    return users

def get_all_user_ids():
    conn = sqlite3.connect("bot.db")
    cursor = conn.execute("SELECT user_id FROM users WHERE is_banned = 0")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

def get_linked_user(user_id):
    conn = sqlite3.connect("bot.db")
    cursor = conn.execute("SELECT linked_to FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result and result[0] else None

def set_replying_to(user_id, target_id):
    conn = sqlite3.connect("bot.db")
    conn.execute("UPDATE users SET replying_to = ? WHERE user_id = ?", (target_id, user_id))
    conn.commit()
    conn.close()

def get_replying_to(user_id):
    conn = sqlite3.connect("bot.db")
    cursor = conn.execute("SELECT replying_to FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result and result[0] else None

def clear_replying_to(user_id):
    conn = sqlite3.connect("bot.db")
    conn.execute("UPDATE users SET replying_to = NULL WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def unlink_user(user_id):
    conn = sqlite3.connect("bot.db")
    cursor = conn.execute("SELECT linked_to FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    partner = result[0] if result else None
    
    if partner:
        conn.execute("UPDATE users SET linked_to = NULL WHERE user_id IN (?, ?)", (user_id, partner))
        conn.execute("UPDATE users SET replying_to = NULL WHERE user_id IN (?, ?)", (user_id, partner))
    
    conn.commit()
    conn.close()
    return partner

def get_all_users():
    conn = sqlite3.connect("bot.db")
    
    cursor = conn.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    
    all_cols = [
        "user_id", "username", "first_name", "last_name", "full_name",
        "profile_link", "language_code", "is_premium", "is_bot",
        "linked_to", "replying_to", "joined_date", "last_active", "is_banned"
    ]
    
    select_cols = []
    for col in all_cols:
        if col in columns:
            select_cols.append(col)
        else:
            select_cols.append(f"NULL as {col}")
    
    query = f"SELECT {', '.join(select_cols)} FROM users"
    cursor = conn.execute(query)
    users = cursor.fetchall()
    conn.close()
    return users

def get_db_stats():
    conn = sqlite3.connect("bot.db")
    
    cursor = conn.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(*) FROM users WHERE linked_to IS NOT NULL")
    active_chats = cursor.fetchone()[0] // 2
    
    cursor = conn.execute("SELECT COUNT(*) FROM users WHERE replying_to IS NOT NULL")
    replying_users = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
    banned_users = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1")
    premium_users = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total_users": total_users,
        "active_chats": active_chats,
        "replying_users": replying_users,
        "banned_users": banned_users,
        "premium_users": premium_users
    }

# Bot handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if is_user_banned(user.id):
        await update.message.reply_text("🚫 You are banned from using this bot.")
        return
    
    # Collect ALL available data from Telegram API
    username = user.username
    first_name = user.first_name
    last_name = user.last_name
    full_name = user.full_name
    
    # Build direct profile link
    if username:
        profile_link = f"https://t.me/{username}"
    else:
        profile_link = f"tg://user?id={user.id}"
    
    # Available from Telegram API
    language_code = user.language_code
    is_premium = 1 if user.is_premium else 0
    is_bot = 1 if user.is_bot else 0
    
    # Save to database
    add_or_update_user(
        user.id, username, first_name, last_name, full_name,
        profile_link, language_code, is_premium, is_bot
    )
    
    update_last_active(user.id)
    
    # Deep link handling
    if context.args and context.args[0].isdigit():
        target_id = int(context.args[0])
        
        if target_id == user.id:
            await update.message.reply_text("❌ You can't message yourself!")
            return
        
        if is_user_banned(target_id):
            await update.message.reply_text("❌ This user is no longer available.")
            return
        
        conn = sqlite3.connect("bot.db")
        cursor = conn.execute("SELECT user_id FROM users WHERE user_id = ?", (target_id,))
        target_exists = cursor.fetchone()
        conn.close()
        
        if not target_exists:
            await update.message.reply_text("❌ This link is invalid or the user doesn't exist.")
            return
        
        context.user_data['send_to'] = target_id
        
        await update.message.reply_text(
            f"✉️ You can send ONE anonymous message to this person.\n"
            f"You can send text, photos, videos, voice notes, stickers, and more!\n"
            f"Send your message now...\n"
            f"Send /cancel to abort."
        )
        return
    
    bot_username = context.bot.username
    link = f"https://t.me/{bot_username}?start={user.id}"
    
    await update.message.reply_text(
        f"👋 Welcome {user.first_name}!\n\n"
        f"🔗 Your anonymous messaging link:\n{link}\n\n"
        f"Share this link - anyone who clicks it can send you ONE anonymous message.\n"
        f"Supports text, photos, videos, voice notes, and more!"
    )

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if is_user_banned(user.id):
        await update.message.reply_text("🚫 You are banned from using this bot.")
        return
    
    # Update last active
    update_last_active(user.id)
    
    # Check if admin is in special mode
    if user.id in ADMIN_IDS:
        if context.user_data.get('waiting_for') == 'ban_id':
            await process_ban_id(update, context)
            return
        elif context.user_data.get('waiting_for') == 'unban_id':
            await process_unban_id(update, context)
            return
        elif context.user_data.get('waiting_for') == 'broadcast_message':
            await process_broadcast(update, context)
            return
    
    # Reply mode
    replying_to = get_replying_to(user.id)
    
    if replying_to:
        if is_user_banned(replying_to):
            await update.message.reply_text("❌ This user is no longer available.")
            clear_replying_to(user.id)
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
        except:
            await update.message.reply_text("❌ Couldn't send reply.")
        clear_replying_to(user.id)
        return
    
    # One-time message from deep link
    if 'send_to' in context.user_data:
        target_id = context.user_data['send_to']
        del context.user_data['send_to']
        
        if is_user_banned(target_id):
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
            await update.message.reply_text(
                "✅ Your anonymous message has been sent!\n"
                "If they reply, you'll get a Reply button to continue the conversation."
            )
        except:
            await update.message.reply_text("❌ Couldn't deliver message.")
        return
    
    await update.message.reply_text(
        "❌ You're not in a conversation!\n"
        "Use /start to get your link or click someone else's link to send a message."
    )

async def handle_media_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if is_user_banned(user.id):
        await update.message.reply_text("🚫 You are banned from using this bot.")
        return
    
    update_last_active(user.id)
    
    # Determine media type and get file_id
    media_type = None
    file_id = None
    caption = update.message.caption or ""
    
    if update.message.photo:
        media_type = 'photo'
        file_id = update.message.photo[-1].file_id
    elif update.message.video:
        media_type = 'video'
        file_id = update.message.video.file_id
    elif update.message.voice:
        media_type = 'voice'
        file_id = update.message.voice.file_id
    elif update.message.audio:
        media_type = 'audio'
        file_id = update.message.audio.file_id
    elif update.message.document:
        media_type = 'document'
        file_id = update.message.document.file_id
    elif update.message.sticker:
        media_type = 'sticker'
        file_id = update.message.sticker.file_id
    elif update.message.animation:
        media_type = 'animation'
        file_id = update.message.animation.file_id
    elif update.message.video_note:
        media_type = 'video_note'
        file_id = update.message.video_note.file_id
    
    if not media_type:
        return
    
    # Reply mode
    replying_to = get_replying_to(user.id)
    
    if replying_to:
        if is_user_banned(replying_to):
            await update.message.reply_text("❌ This user is no longer available.")
            clear_replying_to(user.id)
            return
        
        caption_text = f"💬 Reply:\n\n{caption}" if caption else "💬 Reply"
        
        success = await send_media_with_reply(
            context, replying_to, user.id, media_type, file_id, caption_text
        )
        
        if success:
            await update.message.reply_text("✅ Reply sent!")
        else:
            await update.message.reply_text("❌ Couldn't send reply.")
        
        clear_replying_to(user.id)
        return
    
    # One-time message from deep link
    if 'send_to' in context.user_data:
        target_id = context.user_data['send_to']
        del context.user_data['send_to']
        
        if is_user_banned(target_id):
            await update.message.reply_text("❌ This user is no longer available.")
            return
        
        caption_text = f"💬 Anonymous message:\n\n{caption}" if caption else "💬 Anonymous message"
        
        success = await send_media_with_reply(
            context, target_id, user.id, media_type, file_id, caption_text
        )
        
        if success:
            await update.message.reply_text(
                "✅ Your anonymous message has been sent!\n"
                "If they reply, you'll get a Reply button to continue the conversation."
            )
        else:
            await update.message.reply_text("❌ Couldn't deliver message.")
        return
    
    await update.message.reply_text(
        "❌ You're not in a conversation!\n"
        "Use /start to get your link or click someone else's link to send a message."
    )

async def send_media_with_reply(context, target_id, sender_id, media_type, file_id, caption=None):
    """Send media to target user with Reply button"""
    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("↩️ Reply", callback_data=f"reply_{sender_id}")
    ]])
    
    try:
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

async def process_ban_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if not update.message.text.isdigit():
        await update.message.reply_text("❌ Invalid ID. Send /cancel to abort.")
        return
    
    target_id = int(update.message.text)
    target = get_user_info(target_id)
    
    if not target:
        await update.message.reply_text("❌ User not found. Send /cancel to abort.")
        return
    
    if target[3] == 1:
        await update.message.reply_text(f"❌ User already banned. Send /cancel to abort.")
        return
    
    ban_user(target_id)
    
    try:
        await context.bot.send_message(target_id, "🚫 You have been banned by an administrator.")
    except:
        pass
    
    context.user_data['waiting_for'] = None
    await show_admin_panel(update, context, f"✅ User banned: {target[2]} (ID: {target[0]})\n\n")

async def process_unban_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if not update.message.text.isdigit():
        await update.message.reply_text("❌ Invalid ID. Send /cancel to abort.")
        return
    
    target_id = int(update.message.text)
    target = get_user_info(target_id)
    
    if not target:
        await update.message.reply_text("❌ User not found. Send /cancel to abort.")
        return
    
    if target[3] == 0:
        await update.message.reply_text(f"❌ User not banned. Send /cancel to abort.")
        return
    
    unban_user(target_id)
    
    try:
        await context.bot.send_message(target_id, "✅ You have been unbanned. You can use the bot again.")
    except:
        pass
    
    context.user_data['waiting_for'] = None
    await show_admin_panel(update, context, f"✅ User unbanned: {target[2]} (ID: {target[0]})\n\n")

async def process_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    broadcast_text = update.message.text
    context.user_data['waiting_for'] = None
    
    status_msg = await update.message.reply_text("📤 Starting broadcast...")
    
    user_ids = get_all_user_ids()
    
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
    
    result_message = (
        f"✅ Broadcast completed!\n\n"
        f"📊 **Results:**\n"
        f"• ✅ Sent: **{success_count}**\n"
        f"• ❌ Failed: **{fail_count}**\n"
        f"• 📝 Total: **{len(user_ids)}**\n\n"
    )
    
    await status_msg.delete()
    await show_admin_panel(update, context, result_message)

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE, prefix_message=""):
    stats = get_db_stats()
    
    stats_message = prefix_message + (
        f"📊 **Bot Statistics**\n\n"
        f"👥 Total Users: **{stats['total_users']}**\n"
        f"💎 Premium Users: **{stats['premium_users']}**\n"
        f"💬 Active Conversations: **{stats['active_chats']}**\n"
        f"✍️ Users in Reply Mode: **{stats['replying_users']}**\n"
        f"🚫 Banned Users: **{stats['banned_users']}**\n"
        f"🕐 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    keyboard = [
        [InlineKeyboardButton("📋 Export User List", callback_data="admin_export_users")],
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

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if is_user_banned(query.from_user.id):
        await query.edit_message_text("🚫 You are banned from using this bot.")
        return
    
    if query.data.startswith("reply_"):
        sender_id = int(query.data.split("_")[1])
        
        if is_user_banned(sender_id):
            await query.edit_message_text("❌ This user is no longer available.")
            return
        
        set_replying_to(query.from_user.id, sender_id)
        
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(
            "✍️ Type your reply now...\n"
            "Send any message (text, photo, video, voice, etc.) to reply.\n"
            "Send /cancel to cancel."
        )

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ You don't have permission.")
        return
    
    await show_admin_panel(update, context)

async def admin_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id not in ADMIN_IDS:
        await query.edit_message_text("❌ You don't have permission.")
        return
    
    if query.data == "admin_export_users":
        users = get_all_users()
        
        if not users:
            await query.edit_message_text("No users in database.")
            return
        
        csv_content = "User ID,Username,First Name,Last Name,Full Name,Profile Link,Language,Premium,Bot,Linked To,Replying To,Joined,Last Active,Banned\n"
        for user in users:
            row = [str(val).replace(",", " ") if val is not None else "N/A" for val in user]
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
    
    elif query.data == "admin_broadcast":
        user_count = len(get_all_user_ids())
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Yes, Send Broadcast", callback_data="admin_broadcast_confirm"),
                InlineKeyboardButton("❌ Cancel", callback_data="admin_back_to_panel")
            ]
        ]
        
        await query.edit_message_text(
            f"📢 **Broadcast Message**\n\n"
            f"This will send to **{user_count}** users.\n\n"
            f"Continue?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif query.data == "admin_broadcast_confirm":
        context.user_data['waiting_for'] = 'broadcast_message'
        
        await query.edit_message_text(
            "📢 **Broadcast Mode**\n\n"
            "Send me the message to broadcast.\n"
            "Send /cancel to abort.",
            parse_mode='Markdown'
        )
    
    elif query.data == "admin_ban_user":
        context.user_data['waiting_for'] = 'ban_id'
        
        await query.edit_message_text(
            "🚫 **Ban User**\n\n"
            "Send me the User ID to ban.\n"
            "Send /cancel to abort.",
            parse_mode='Markdown'
        )
    
    elif query.data == "admin_unban_user":
        context.user_data['waiting_for'] = 'unban_id'
        
        await query.edit_message_text(
            "✅ **Unban User**\n\n"
            "Send me the User ID to unban.\n"
            "Send /cancel to abort.",
            parse_mode='Markdown'
        )
    
    elif query.data == "admin_view_banned":
        banned = get_banned_users()
        
        if not banned:
            await query.edit_message_text("✅ No banned users.")
            return
        
        banned_list = "🚫 **Banned Users:**\n\n"
        for user in banned:
            banned_list += f"• ID: `{user[0]}` - {user[2] or 'N/A'} (@{user[1] or 'N/A'})\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_back_to_panel")]]
        
        await query.edit_message_text(
            banned_list,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif query.data == "admin_back_to_panel":
        await show_admin_panel_from_callback(query, context)
    
    elif query.data == "admin_refresh_stats":
        await show_admin_panel_from_callback(query, context)

async def show_admin_panel_from_callback(query, context):
    stats = get_db_stats()
    
    stats_message = (
        f"📊 **Bot Statistics (Updated)**\n\n"
        f"👥 Total Users: **{stats['total_users']}**\n"
        f"💎 Premium Users: **{stats['premium_users']}**\n"
        f"💬 Active Conversations: **{stats['active_chats']}**\n"
        f"✍️ Users in Reply Mode: **{stats['replying_users']}**\n"
        f"🚫 Banned Users: **{stats['banned_users']}**\n"
        f"🕐 Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    keyboard = [
        [InlineKeyboardButton("📋 Export User List", callback_data="admin_export_users")],
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

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    clear_replying_to(user.id)
    
    if 'send_to' in context.user_data:
        del context.user_data['send_to']
    
    if context.user_data.get('waiting_for'):
        context.user_data['waiting_for'] = None
        
        if user.id in ADMIN_IDS:
            await update.message.reply_text("❌ Operation cancelled.")
            await show_admin_panel(update, context)
            return
    
    await update.message.reply_text("❌ Operation cancelled.")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if is_user_banned(user.id):
        return
    
    partner = unlink_user(user.id)
    clear_replying_to(user.id)
    
    if context.user_data.get('waiting_for'):
        context.user_data['waiting_for'] = None
    
    await update.message.reply_text("🔕 Chat ended.")
    
    if partner:
        clear_replying_to(partner)
        try:
            await context.bot.send_message(partner, "🔕 The other person ended the chat.")
        except:
            pass

def main():
    init_db()
    app = Application.builder().token(os.getenv("BOT_TOKEN")).build()
    
    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("admin", admin_command))
    
    # Callback handlers
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^reply_"))
    app.add_handler(CallbackQueryHandler(admin_button_handler, pattern="^admin_"))
    
    # Text message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    # Media handler - simple approach
    app.add_handler(MessageHandler(
        filters.PHOTO | filters.VIDEO | filters.VOICE | 
        filters.AUDIO | filters.Document.ALL | filters.Sticker.ALL | 
        filters.ANIMATION | filters.VIDEO_NOTE,
        handle_media_message
    ))
    
    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()