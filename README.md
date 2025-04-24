# Kafka Telegram Monitor

A Python-based monitoring system for Apache Kafka that sends notifications via Telegram.

## Features

- Monitor Kafka broker status
- Track consumer lag across topics
- Monitor partition count
- Send alerts via Telegram when thresholds are exceeded
- Daily status reports
- Configurable monitoring intervals and thresholds

## Setup

1. Create a virtual environment and activate it:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the application:
   - Copy `config/config.env` and update with your settings
   - Set your Telegram Bot Token and Chat ID
   - Configure Kafka connection details
   - Adjust monitoring thresholds as needed

4. Create a Telegram Bot:
   - Talk to [@BotFather](https://t.me/botfather) on Telegram
   - Create a new bot and get the token
   - Start a chat with your bot and get the chat ID

## Configuration

Edit `config/config.env` to set:

- `KAFKA_BOOTSTRAP_SERVERS`: Kafka broker addresses
- `KAFKA_CONSUMER_GROUP`: Consumer group ID for lag monitoring
- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
- `TELEGRAM_CHAT_ID`: Your Telegram chat ID
- `CHECK_INTERVAL`: How often to check (in seconds)
- `ALERT_THRESHOLD_LAG`: Consumer lag threshold
- `ALERT_THRESHOLD_PARTITION_COUNT`: Minimum partition count

## Running the Monitor

```bash
source venv/bin/activate
python src/kafka_monitor.py
```

## Alerts

You will receive Telegram notifications for:
- Broker connectivity issues
- High consumer lag
- Low partition count
- Daily status reports

## Contributing

Feel free to submit issues and enhancement requests!
