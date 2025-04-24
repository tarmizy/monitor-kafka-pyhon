import os
import logging
import asyncio
from telegram import Bot
from telegram.error import TelegramError
from dotenv import load_dotenv

class TelegramNotifier:
    def __init__(self):
        # Load environment variables
        load_dotenv('config/config.env')
        
        # Initialize Telegram bot
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.bot = Bot(token=self.bot_token)
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    def send_message(self, message):
        """Send a regular message to Telegram"""
        try:
            asyncio.get_event_loop().run_until_complete(
                self._send_message(message)
            )
        except Exception as e:
            self.logger.error(f"Failed to send Telegram message: {str(e)}")
    
    def send_alert(self, message):
        """Send an alert message to Telegram"""
        alert_message = f"🚨 ALERT 🚨\n\n{message}"
        self.send_message(alert_message)
    
    async def _send_message(self, message):
        """Internal async method to send message"""
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            self.logger.info("Message sent successfully to Telegram")
        except TelegramError as e:
            self.logger.error(f"Telegram error: {str(e)}")
            raise
