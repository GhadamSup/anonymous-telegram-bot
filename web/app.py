from flask import Flask, render_template, jsonify, request, redirect, url_for, session, Response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from functools import wraps
from config.settings import settings
from database.user_repository import UserRepository
from database.conversation_repository import ConversationRepository
from database.channel_repository import ChannelRepository
from database.stats_repository import StatsRepository
from database.connection import db
from services.system_service import SystemService
import secrets
import asyncio
import os
import subprocess
import sys
import pyotp
import qrcode
import io
import base64
import hashlib
import bcrypt
import logging
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.getenv("WEB_SECRET_KEY", secrets.token_hex(32))

# Session security
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# HTTPS enforcement (set force_https=True in production with SSL)
Talisman(app, force_https=False, session_cookie_secure=False)

# Rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

CORS(app)

# Audit logging
audit_logger = logging.getLogger('audit')
audit_handler = logging.FileHandler('audit.log')
audit_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
audit_logger.addHandler(audit_handler)
audit_logger.setLevel(logging.INFO)

# Repositories & Services
user_repo = UserRepository()
conv_repo = ConversationRepository()
channel_repo = ChannelRepository()
system_service = SystemService()
stats_repo = StatsRepository()

# Initialize stats table
stats_repo.init_stats_table()

# Bot instance
bot_instance = None

def set_bot_instance(bot):
    global bot_instance
    bot_instance = bot

def is_bot_available():
    return bot_instance is not None and bot_instance.app is not None

def check_bot_status():
    if bot_instance is None:
        return False
    try:
        if hasattr(bot_instance, 'is_running') and bot_instance.is_running:
            return True
        if hasattr(bot_instance, 'app') and bot_instance.app:
            return True
        return False
    except:
        return False

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def audit_log(action, details=""):
    """Log admin actions"""
    ip = request.remote_addr
    user = session.get('username', 'unknown')
    audit_logger.info(f"IP={ip} User={user} Action={action} {details}")

def hash_text(text):
    """Hash text with SHA-256 (for username)"""
    return hashlib.sha256(text.encode()).hexdigest()

def hash_password(password):
    """Hash password with bcrypt"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, hashed):
    """Verify password against bcrypt hash"""
    return bcrypt.checkpw(password.encode(), hashed.encode())

def encrypt_secret(secret):
    """Encrypt 2FA secret"""
    key = hashlib.sha256(app.secret_key.encode()).digest()
    nonce = os.urandom(16)
    encrypted = bytes([a ^ b for a, b in zip(secret.encode(), key[:len(secret)])])
    return (nonce + encrypted).hex()

def decrypt_secret(encrypted_hex):
    """Decrypt 2FA secret"""
    data = bytes.fromhex(encrypted_hex)
    nonce = data[:16]
    encrypted = data[16:]
    key = hashlib.sha256(app.secret_key.encode()).digest()
    decrypted = bytes([a ^ b for a, b in zip(encrypted, key[:len(encrypted)])])
    return decrypted.decode()

def get_setting(key):
    """Get a setting from database"""
    conn = db.get_connection()
    result = conn.execute("SELECT value FROM admin_settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return result[0] if result else None

def set_setting(key, value):
    """Save a setting to database"""
    conn = db.get_connection()
    conn.execute("INSERT OR REPLACE INTO admin_settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def is_first_run():
    """Check if admin credentials exist in database"""
    return get_setting('admin_username_hash') is None

def save_credentials(username, password):
    """Save hashed credentials to database"""
    set_setting('admin_username_hash', hash_text(username))
    set_setting('admin_password_hash', hash_password(password))

def verify_credentials(username, password):
    """Verify credentials against database"""
    stored_user = get_setting('admin_username_hash')
    stored_pass = get_setting('admin_password_hash')
    if not stored_user or not stored_pass:
        return False
    return hash_text(username) == stored_user and verify_password(password, stored_pass)

def generate_csrf_token():
    """Generate CSRF token"""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']

def validate_csrf():
    """Validate CSRF token from form"""
    token = request.form.get('csrf_token', '')
    return token == session.get('csrf_token', '')

def generate_qr(secret):
    """Generate QR code for Google Authenticator"""
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name="Bot Admin", issuer_name="Anonymous Bot")
    
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode()

# Make CSRF token available to all templates
@app.context_processor
def inject_csrf():
    return dict(csrf_token=generate_csrf_token())

# ============================================
# PAGE ROUTES
# ============================================

@app.route('/')
def index():
    if 'logged_in' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if is_first_run():
        return redirect(url_for('setup_admin'))
    
    twofa_setup = get_setting('2fa_secret_encrypted') is not None
    
    if request.method == 'POST':
        if not validate_csrf():
            audit_log("LOGIN_FAILED", "CSRF validation failed")
            return render_template('login.html', error='Invalid request', require_2fa=twofa_setup)
        
        username = request.form.get('username')
        password = request.form.get('password')
        code = request.form.get('code', '')
        
        if verify_credentials(username, password):
            if twofa_setup:
                if not code:
                    return render_template('login.html', error='2FA code required', require_2fa=True)
                
                encrypted = get_setting('2fa_secret_encrypted')
                secret = decrypt_secret(encrypted)
                
                totp = pyotp.TOTP(secret, interval=30)
                if totp.verify(code, valid_window=2):
                    session.clear()
                    session['logged_in'] = True
                    session['username'] = username
                    session.permanent = True
                    audit_log("LOGIN_SUCCESS", "2FA verified")
                    return redirect(url_for('dashboard'))
                else:
                    audit_log("LOGIN_FAILED", "Invalid 2FA code")
                    return render_template('login.html', error='Invalid 2FA code', require_2fa=True)
            else:
                session.clear()
                session['logged_in'] = True
                session['username'] = username
                session.permanent = True
                audit_log("LOGIN_SUCCESS", "No 2FA")
                return redirect(url_for('setup_2fa'))
        else:
            audit_log("LOGIN_FAILED", f"Invalid credentials for user: {username}")
            return render_template('login.html', error='Invalid credentials', require_2fa=twofa_setup)
    
    return render_template('login.html', require_2fa=get_setting('2fa_secret_encrypted') is not None)

@app.route('/setup-admin', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def setup_admin():
    if not is_first_run():
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        if not validate_csrf():
            return render_template('setup_admin.html', error='Invalid request')
        
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        if not username or len(username) < 4:
            return render_template('setup_admin.html', error='Username must be at least 4 characters')
        
        if not password or len(password) < 12:
            return render_template('setup_admin.html', error='Password must be at least 12 characters')
        
        if not any(c.isupper() for c in password):
            return render_template('setup_admin.html', error='Password must contain at least one uppercase letter')
        
        if not any(c.islower() for c in password):
            return render_template('setup_admin.html', error='Password must contain at least one lowercase letter')
        
        if not any(c.isdigit() for c in password):
            return render_template('setup_admin.html', error='Password must contain at least one number')
        
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            return render_template('setup_admin.html', error='Password must contain at least one special character')
        
        if password != confirm_password:
            return render_template('setup_admin.html', error='Passwords do not match')
        
        save_credentials(username, password)
        session.clear()
        session['logged_in'] = True
        session['username'] = username
        session.permanent = True
        audit_log("ADMIN_SETUP", f"Admin account created: {username}")
        return redirect(url_for('setup_2fa'))
    
    return render_template('setup_admin.html')

@app.route('/setup-2fa', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def setup_2fa():
    if get_setting('2fa_secret_encrypted') is not None:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        if not validate_csrf():
            return render_template('setup_2fa.html', secret='', qr_image='', error='Invalid request')
        
        secret = request.form.get('secret')
        code = request.form.get('code')
        
        totp = pyotp.TOTP(secret, interval=30)
        
        if totp.verify(code, valid_window=5):
            encrypted = encrypt_secret(secret)
            set_setting('2fa_secret_encrypted', encrypted)
            session['2fa_verified'] = True
            audit_log("2FA_SETUP", "2FA enabled successfully")
            return redirect(url_for('dashboard'))
        else:
            return render_template('setup_2fa.html', 
                                 secret=secret, 
                                 qr_image=generate_qr(secret), 
                                 error='Invalid code. Please try again.')
    
    secret = pyotp.random_base32()
    qr_img = generate_qr(secret)
    
    return render_template('setup_2fa.html', secret=secret, qr_image=qr_img)

@app.route('/logout')
def logout():
    audit_log("LOGOUT")
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/users')
@login_required
def users():
    return render_template('users.html')

@app.route('/conversations')
@login_required
def conversations():
    return render_template('conversations.html')

@app.route('/channels')
@login_required
def channels():
    return render_template('channels.html')

@app.route('/broadcast')
@login_required
def broadcast():
    return render_template('broadcast.html')

@app.route('/settings')
@login_required
def settings_page():
    return render_template('settings.html')

# ============================================
# API ROUTES - STATS
# ============================================

@app.route('/api/stats')
@login_required
def api_stats():
    user_stats = user_repo.get_stats()
    conv_stats = conv_repo.get_stats()
    
    sys_stats = {'cpu': {'percent': 0}, 'memory': {'percent': 0}, 'disk': {'percent': 0}}
    try:
        sys_stats = system_service.get_all_stats()
    except:
        pass
    
    return jsonify({
        'users': user_stats,
        'conversations': conv_stats,
        'system': {
            'cpu': sys_stats.get('cpu', {}),
            'memory': sys_stats.get('memory', {}),
            'disk': sys_stats.get('disk', {}),
        }
    })

@app.route('/api/stats/daily')
@login_required
def api_daily_stats():
    days = request.args.get('days', 7, type=int)
    try:
        stats = stats_repo.get_daily_stats(days)
        return jsonify(stats)
    except:
        return jsonify([])

@app.route('/api/stats/message-types')
@login_required
def api_message_types():
    try:
        stats = stats_repo.get_message_type_stats()
        return jsonify(stats)
    except:
        return jsonify({'text': 0, 'media': 0, 'replies': 0})

# ============================================
# API ROUTES - USERS
# ============================================

@app.route('/api/users')
@login_required
def api_users():
    users = user_repo.get_all()
    return jsonify([dict(u) for u in users])

@app.route('/api/users/<int:user_id>/ban', methods=['POST'])
@login_required
def api_ban_user(user_id):
    user_repo.ban(user_id)
    conv_repo.end_user_conversations(user_id)
    audit_log("BAN_USER", f"Banned user ID: {user_id}")
    return jsonify({'success': True, 'message': 'User banned successfully'})

@app.route('/api/users/<int:user_id>/unban', methods=['POST'])
@login_required
def api_unban_user(user_id):
    user_repo.unban(user_id)
    audit_log("UNBAN_USER", f"Unbanned user ID: {user_id}")
    return jsonify({'success': True, 'message': 'User unbanned successfully'})

# ============================================
# API ROUTES - CONVERSATIONS
# ============================================

@app.route('/api/conversations')
@login_required
def api_conversations():
    conversations = conv_repo.get_all_conversations(limit=200)
    return jsonify([dict(c) for c in conversations])

@app.route('/api/conversations/<int:conv_id>/messages')
@login_required
def api_conversation_messages(conv_id):
    messages = conv_repo.get_messages(conv_id, limit=500)
    return jsonify([dict(m) for m in messages])

# ============================================
# API ROUTES - CHANNELS
# ============================================

@app.route('/api/channels')
@login_required
def api_channels():
    channels = channel_repo.get_all_channels()
    return jsonify([dict(c) for c in channels])

@app.route('/api/channels/add', methods=['POST'])
@login_required
def api_add_channel():
    if not is_bot_available():
        return jsonify({'error': 'Bot is not connected. Start the bot first.'}), 503
    
    data = request.json
    link = data.get('link', '')
    
    if not link:
        return jsonify({'error': 'Invite link is required'}), 400
    
    async def add_channel():
        try:
            bot = bot_instance.app.bot
            if '/+' in link:
                chat = await bot.get_chat(link)
            else:
                username = link.split('/')[-1].replace('@', '')
                chat = await bot.get_chat(f"@{username}")
            
            bot_member = await bot.get_chat_member(chat.id, bot.id)
            if bot_member.status not in ['administrator', 'creator']:
                return {'error': 'Bot is not admin in this channel'}
            
            invite_link = chat.invite_link or link
            
            channel_repo.add_channel(
                channel_id=chat.id,
                channel_username=chat.username,
                channel_title=chat.title,
                invite_link=invite_link
            )
            audit_log("ADD_CHANNEL", f"Added channel: {chat.title} ({chat.id})")
            return {'success': True}
        except Exception as e:
            return {'error': str(e)}
    
    result = asyncio.run(add_channel())
    return jsonify(result)

@app.route('/api/channels/<int:channel_id>/toggle', methods=['POST'])
@login_required
def api_toggle_channel(channel_id):
    channel = channel_repo.get_channel(channel_id)
    if channel:
        channel_repo.toggle_channel(channel_id, not channel['is_active'])
        audit_log("TOGGLE_CHANNEL", f"Channel {channel_id} toggled")
        return jsonify({'success': True})
    return jsonify({'error': 'Channel not found'}), 404

@app.route('/api/channels/<int:channel_id>/remove', methods=['DELETE'])
@login_required
def api_remove_channel(channel_id):
    channel_repo.remove_channel(channel_id)
    audit_log("REMOVE_CHANNEL", f"Removed channel ID: {channel_id}")
    return jsonify({'success': True})

# ============================================
# API ROUTES - BROADCAST
# ============================================

@app.route('/api/broadcast', methods=['POST'])
@login_required
def api_broadcast():
    if not is_bot_available():
        return jsonify({'error': 'Bot is not connected. Start the bot first.'}), 503
    
    data = request.json
    message = data.get('message', '')
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    async def send_broadcast():
        bot = bot_instance.app.bot
        user_ids = user_repo.get_all_user_ids()
        success = 0
        failed = 0
        
        for uid in user_ids:
            try:
                await bot.send_message(
                    uid,
                    f"📢 **Announcement from Admin:**\n\n{message}",
                    parse_mode='Markdown'
                )
                success += 1
            except:
                failed += 1
        
        return {'success': True, 'sent': success, 'failed': failed, 'total': len(user_ids)}
    
    result = asyncio.run(send_broadcast())
    audit_log("BROADCAST", f"Sent to {result.get('sent', 0)} users")
    return jsonify(result)

# ============================================
# API ROUTES - BOT CONTROL
# ============================================

@app.route('/api/bot/restart', methods=['POST'])
@login_required
def api_restart_bot():
    if not is_bot_available():
        return jsonify({'error': 'Bot is not running. Start it manually.'}), 503
    audit_log("RESTART_BOT")
    bot_instance.restart_bot()
    return jsonify({'success': True, 'message': 'Bot restarting...'})

@app.route('/api/bot/stop', methods=['POST'])
@login_required
def api_stop_bot():
    if not is_bot_available():
        return jsonify({'error': 'Bot is not running.'}), 503
    audit_log("STOP_BOT")
    bot_instance.stop_bot()
    return jsonify({'success': True, 'message': 'Bot stopping...'})

# ============================================
# API ROUTES - EXPORT
# ============================================

@app.route('/api/export/users')
@login_required
def api_export_users():
    users = user_repo.get_all()
    csv = "ID,Username,First Name,Last Name,Full Name,Premium,Banned\n"
    for u in users:
        csv += f"{u.get('user_id')},{u.get('username','')},{u.get('first_name','')},{u.get('last_name','')},{u.get('full_name','')},{u.get('is_premium')},{u.get('is_banned')}\n"
    
    audit_log("EXPORT_USERS")
    return Response(
        csv,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=users.csv"}
    )

@app.route('/api/export/messages')
@login_required
def api_export_messages():
    conversations = conv_repo.get_all_conversations(limit=500)
    export_data = {
        "export_date": datetime.now().isoformat(),
        "conversations": []
    }
    for conv in conversations:
        messages = conv_repo.get_messages(conv['id'], limit=1000)
        export_data["conversations"].append({
            "id": conv['id'],
            "users": f"{conv.get('user_a_name')} ↔ {conv.get('user_b_name')}",
            "messages": [dict(m) for m in messages]
        })
    
    audit_log("EXPORT_MESSAGES")
    return jsonify(export_data)

def run_web(host='0.0.0.0', port=5000, debug=False):
    app.run(host=host, port=port, debug=debug)