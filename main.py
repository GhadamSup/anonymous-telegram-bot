import logging
from config.settings import settings
from handlers.start_handler import StartHandler
from handlers.message_handler import MessageHandler
from handlers.admin_handler import AdminHandler
from handlers.reply_handler import ReplyHandler
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler as TGMessageHandler, filters

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)

class AnonymousBridgeBot:
    """Main bot application"""
    
    def __init__(self):
        self.app = Application.builder().token(settings.BOT_TOKEN).build()
        self._register_handlers()
    
    def _register_handlers(self):
        """Register all handlers"""
        start_handler = StartHandler()
        message_handler = MessageHandler()
        admin_handler = AdminHandler()
        reply_handler = ReplyHandler()
        
        # Command handlers
        self.app.add_handler(CommandHandler("start", start_handler.handle))
        self.app.add_handler(CommandHandler("stop", start_handler.stop))
        self.app.add_handler(CommandHandler("cancel", start_handler.cancel))
        self.app.add_handler(CommandHandler("admin", admin_handler.show_panel))
        
        # Callback handlers
        self.app.add_handler(CallbackQueryHandler(reply_handler.handle, pattern="^reply_"))
        self.app.add_handler(CallbackQueryHandler(admin_handler.handle_button, pattern="^admin_"))
        
        # Message handlers
        self.app.add_handler(TGMessageHandler(filters.TEXT & ~filters.COMMAND, message_handler.handle_text))
        self.app.add_handler(TGMessageHandler(~filters.COMMAND & ~filters.TEXT, message_handler.handle_media))
        
        # Error handler
        self.app.add_error_handler(self._error_handler)
    
    async def _error_handler(self, update, context):
        logger.error(f"Update {update} caused error {context.error}")
    
    def run(self):
        logger.info("Starting bot...")
        self.app.run_polling()

if __name__ == "__main__":
    bot = AnonymousBridgeBot()
    bot.run()