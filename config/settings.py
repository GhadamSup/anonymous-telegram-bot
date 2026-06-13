import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application settings"""
    
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]
    DB_PATH = os.getenv("DB_PATH", "bot.db")
    
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

settings = Settings()