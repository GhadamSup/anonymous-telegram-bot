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
        
        # Set bot reference in admin handler for restart/stop
        admin_handler.set_bot(self)
        
        # Command handlers
        self.app.add_handler(CommandHandler("start", start_handler.handle))
        self.app.add_handler(CommandHandler("stop", start_handler.stop))
        self.app.add_handler(CommandHandler("cancel", start_handler.cancel))
        self.app.add_handler(CommandHandler("admin", admin_handler.show_panel))
        
        # Callback handlers - ORDER MATTERS! More specific patterns first
        # Handle reply callbacks
        self.app.add_handler(CallbackQueryHandler(reply_handler.handle, pattern="^reply_"))
        # Handle channel verification
        self.app.add_handler(CallbackQueryHandler(reply_handler.handle, pattern="^verify_channels"))
        # Handle admin callbacks
        self.app.add_handler(CallbackQueryHandler(admin_handler.handle_button, pattern="^admin_"))
        
        # Message handlers
        self.app.add_handler(TGMessageHandler(filters.TEXT & ~filters.COMMAND, message_handler.handle_text))
        self.app.add_handler(TGMessageHandler(~filters.COMMAND & ~filters.TEXT, message_handler.handle_media))
        
        # Error handler
        self.app.add_error_handler(self._error_handler)
    
    async def _error_handler(self, update, context):
        logger.error(f"Update {update} caused error {context.error}")
    
    def stop_bot(self):
        """Stop the bot gracefully"""
        logger.info("Stopping bot...")
        if self.app.running:
            self.app.stop_running()
    
    def restart_bot(self):
        """Restart the bot"""
        logger.info("Restarting bot...")
        import sys
        import os
        python = sys.executable
        script = settings.SCRIPT_PATH
        os.execv(python, [python, script])
    
    def run(self):
        """Start the bot"""
        logger.info("Starting bot...")
        self.app.run_polling()

if __name__ == "__main__":
    bot = AnonymousBridgeBot()
    bot.run()