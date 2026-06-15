# Anonymous Telegram Bridge Bot

A professional Telegram bot that enables anonymous messaging between users through deep linking, mandatory sponsored channel subscriptions, and a comprehensive admin management system.

---

## Features

### Anonymous Messaging

- Unique deep links for every user
- Anonymous one-click messaging
- Threaded conversations through inline reply buttons
- Complete anonymity between participants
- Conversation continuation via reply system
- Automatic conversation management

### Full Media Support

Supported message types:

- Text
- Photos
- Videos
- Voice messages
- Audio files
- Documents
- Stickers
- GIFs / Animations
- Video notes

### Sponsored Channel System

- Force-join verification
- Multiple sponsored channels support
- Automatic membership validation
- Channel activation/deactivation
- Admin bypass support
- Invite link management

### Administration Panel

#### User Management

- Ban users
- Unban users
- View banned users

#### Bot Management

- Broadcast announcements
- Restart bot
- Stop bot
- Manage sponsored channels

#### Data Management

- Export users to CSV
- Browse conversations
- Export message history
- View conversation statistics

#### System Monitoring

- CPU usage
- RAM usage
- Disk usage
- Network statistics
- Process information

### Security

- Admin-only management panel
- User banning system
- Environment-based configuration
- SQLite foreign key constraints
- WAL database mode support

---

# How It Works

### Receiving Anonymous Messages

1. Start the bot using `/start`
2. Join all required sponsored channels
3. Verify channel membership
4. Receive your personal anonymous messaging link

Example:

```text
https://t.me/YourBotUsername?start=123456789
```

5. Share the link anywhere

### Sending Anonymous Messages

1. Open someone's anonymous link
2. Send one message anonymously
3. Message is delivered without revealing your identity
4. Continue chatting through the reply system

### Anonymous Replies

- Every received message contains a **Reply** button
- Replies remain anonymous
- Both users communicate through the bot
- Identity is never exposed

---

# Project Architecture

The project follows a modular architecture with clear separation of concerns.

```text
anonymous-telegram-bot/
│
├── .env
├── .gitignore
├── requirements.txt
├── README.md
├── main.py
│
├── config/
│   ├── __init__.py
│   └── settings.py
│
├── database/
│   ├── __init__.py
│   ├── connection.py
│   ├── user_repository.py
│   ├── conversation_repository.py
│   └── channel_repository.py
│
├── handlers/
│   ├── __init__.py
│   ├── start_handler.py
│   ├── message_handler.py
│   ├── admin_handler.py
│   └── reply_handler.py
│
├── services/
│   ├── __init__.py
│   ├── message_service.py
│   ├── channel_service.py
│   └── system_service.py
│
└── keyboards/
    ├── __init__.py
    └── inline_keyboards.py
```

---

# Installation

## Requirements

- Python 3.9+
- Telegram Bot Token from BotFather

## Clone Repository

```bash
git clone https://github.com/GhadamSup/anonymous-telegram-bot.git
cd anonymous-telegram-bot
```

## Create Virtual Environment

### Linux / macOS

```bash
python -m venv venv
source venv/bin/activate
```

### Windows

```powershell
python -m venv venv
venv\Scripts\activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Configuration

Create a `.env` file in the project root.

```env
BOT_TOKEN=your_bot_token
ADMIN_IDS=123456789,987654321
DB_PATH=bot.db
LOG_LEVEL=INFO
```

## Environment Variables

| Variable | Description |
|-----------|-------------|
| BOT_TOKEN | Telegram Bot Token from BotFather |
| ADMIN_IDS | Comma-separated Telegram user IDs |
| DB_PATH | SQLite database path |
| LOG_LEVEL | Logging level |

---

# Running The Bot

```bash
python main.py
```

---

# Commands

## User Commands

| Command | Description |
|----------|-------------|
| `/start` | Start bot or open anonymous link |
| `/stop` | End current conversation |
| `/cancel` | Cancel active operation |

## Admin Commands

| Command | Description |
|----------|-------------|
| `/admin` | Open administration panel |

---

# Admin Panel

The admin panel is divided into multiple categories.

## Manage Users

- Ban user
- Unban user
- View banned users

## Manage Bot

- Sponsored channels
- Broadcast messages
- Restart bot
- Stop bot

## Manage Data

- Export users
- Browse conversations
- Export messages

## Statistics

### User Statistics

- Total users
- Total messages
- Total conversations

### System Statistics

- CPU
- RAM
- Disk
- Network
- Process information

---

# Sponsored Channels

The bot supports mandatory channel subscriptions.

Features:

- Multiple channels
- Invite links
- Membership verification
- Enable/disable channels
- Admin exemption

Users must join all active channels before accessing any bot functionality.

---

# Database Structure

The bot uses SQLite.

## Users

```text
user_id
username
first_name
last_name
full_name
profile_link
language_code
is_premium
is_bot
linked_to
replying_to
joined_date
last_active
is_banned
```

## Conversations

```text
id
user_a_id
user_b_id
started_at
last_message_at
ended_at
status
message_count
```

## Messages

```text
id
conversation_id
sender_id
receiver_id
message_type
content
file_id
file_unique_id
file_size
mime_type
duration
width
height
caption
media_info
timestamp
is_read
is_reply
```

## Channels

```text
id
channel_id
channel_username
channel_title
invite_link
is_active
added_date
```

---

# Technical Stack

| Technology | Purpose |
|------------|----------|
| Python 3.9+ | Core language |
| python-telegram-bot 21.6 | Telegram Bot API |
| SQLite3 | Database |
| aiosqlite | Async database layer |
| psutil | System monitoring |
| python-dotenv | Environment management |

---

# Logging

The bot logs:

- User registrations
- Anonymous messages
- Media transfers
- Conversations
- Channel verification events
- Administrative actions
- Errors and exceptions

---

# Security Features

- Anonymous communication layer
- Identity protection
- Admin-only controls
- User banning system
- Foreign key constraints
- Environment-based secrets
- Controlled conversation routing

---

# Future Improvements

- PostgreSQL support
- Redis caching
- Rate limiting
- Multi-language support
- Docker deployment
- Web dashboard
- Advanced analytics
- Message scheduling

---

# License

This project is open source.

You are free to use, modify, and distribute it according to your needs.

---

Built with ❤️ using Python and Telegram Bot API.
