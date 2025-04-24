import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot

async def test_telegram():
    # Load environment variables
    load_dotenv('config/config.env')
    
    # Get Telegram configuration
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    try:
        # Initialize bot
        bot = Bot(token=bot_token)
        
        # Send test message
        message = (
            "🔔 Test Koneksi Kafka Monitor\n\n"
            "✅ Koneksi Telegram berhasil!\n"
            "📝 Konfigurasi:\n"
            "- Environment: Development\n"
            "- Retention Time: 3 hari\n"
            "- Retention Size: 256MB per topic\n\n"
            "Monitor akan mengirim notifikasi ketika:\n"
            "1. Ada topic yang menyimpan data > 3 hari\n"
            "2. Ada topic yang ukurannya > 256MB\n"
            "3. Ada masalah dengan Kafka cluster\n"
            "4. Ada consumer lag yang tinggi"
        )
        
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode='HTML'
        )
        print("✅ Test message sent successfully!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_telegram())
