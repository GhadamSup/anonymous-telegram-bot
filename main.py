import logging
import sys
import os
from config.settings import settings
from handlers.start_handler import StartHandler
from handlers.message_handler import MessageHandler
from handlers.admin_handler import AdminHandler
from handlers.reply_handler import ReplyHandler
from database.stats_repository import StatsRepository
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler as TGMessageHandler, filters

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)

class AnonymousBridgeBot:
    """Main bot application"""
    
    def __init__(self):
        self.app = Application.builder().token(settings.BOT_TOKEN).build()
        self.is_running = False
        self.stats_repo = StatsRepository()
        self.stats_repo.init_stats_table()
        self._register_handlers()
    
    def _register_handlers(self):
        start_handler = StartHandler()
        message_handler = MessageHandler()
        admin_handler = AdminHandler()
        reply_handler = ReplyHandler()
        
        admin_handler.set_bot(self)
        
        self.app.add_handler(CommandHandler("start", start_handler.handle))
        self.app.add_handler(CommandHandler("stop", start_handler.stop))
        self.app.add_handler(CommandHandler("cancel", start_handler.cancel))
        self.app.add_handler(CommandHandler("admin", admin_handler.show_panel))
        
        self.app.add_handler(CallbackQueryHandler(reply_handler.handle, pattern="^reply_"))
        self.app.add_handler(CallbackQueryHandler(reply_handler.handle, pattern="^verify_channels"))
        self.app.add_handler(CallbackQueryHandler(admin_handler.handle_button, pattern="^admin_"))
        
        self.app.add_handler(TGMessageHandler(filters.TEXT & ~filters.COMMAND, message_handler.handle_text))
        self.app.add_handler(TGMessageHandler(~filters.COMMAND & ~filters.TEXT, message_handler.handle_media))
        
        self.app.add_error_handler(self._error_handler)
    
    async def _error_handler(self, update, context):
        logger.error(f"Update {update} caused error {context.error}")
    
    async def _record_stats_callback(self, context):
        self.stats_repo.record_daily_stats()
        self.stats_repo.record_hourly_message()
    
    def stop_bot(self):
        logger.info("Stopping bot...")
        self.is_running = False
        if self.app.running:
            self.app.stop_running()
    
    def restart_bot(self):
        logger.info("Restarting bot...")
        python = sys.executable
        script = settings.SCRIPT_PATH
        os.execv(python, [python, script])
    
    def run(self):
        self.is_running = True
        logger.info("Starting bot...")
        
        job_queue = self.app.job_queue
        if job_queue:
            job_queue.run_repeating(self._record_stats_callback, interval=1800, first=10)
        
        self.app.run_polling()


if __name__ == "__main__":
    bot = AnonymousBridgeBot()
    
    try:
        from web.app import set_bot_instance
        set_bot_instance(bot)
        logger.info("Connected to web panel")
    except Exception as e:
        logger.warning(f"Could not connect to web panel: {e}")
    
    try:
        bot.run()
    except KeyboardInterrupt:
        bot.is_running = False
        print("\nBot stopped.")
    except Exception as e:
        bot.is_running = False
        print(f"Error: {e}")