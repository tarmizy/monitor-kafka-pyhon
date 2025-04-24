#!/bin/bash

# Development environment settings
RETENTION_TIME=259200000    # 3 days
RETENTION_SIZE=268435456    # 256MB
KAFKA_SERVER="localhost:9092"
KAFKA_BIN="/usr/local/kafka/bin"

echo "🔧 Setting Development Environment Retention Policy"
echo "================================================"
echo "Retention Time: 3 days"
echo "Retention Size: 256MB"
echo "Kafka Server: $KAFKA_SERVER"
echo

# Get confirmation
read -p "Do you want to proceed? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Operation cancelled"
    exit 1
fi

# Get all topics
echo "📋 Getting list of topics..."
topics=$($KAFKA_BIN/kafka-topics.sh --bootstrap-server $KAFKA_SERVER --list)

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to get topic list"
    exit 1
fi

# Update retention for each topic
for topic in $topics
do
    echo "🔄 Setting retention for topic: $topic"
    $KAFKA_BIN/kafka-configs.sh --bootstrap-server $KAFKA_SERVER \
        --entity-type topics \
        --entity-name $topic \
        --alter \
        --add-config retention.ms=$RETENTION_TIME,retention.bytes=$RETENTION_SIZE
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully updated retention for: $topic"
    else
        echo "❌ Failed to update retention for: $topic"
    fi
    echo
done

echo "🎉 Development environment retention policy has been applied!"
echo "💡 Tips for development:"
echo "   - Data akan otomatis terhapus setelah 3 hari"
echo "   - Setiap topic maksimal menyimpan 256MB data"
echo "   - Jika butuh data lebih lama, backup sebelum terhapus"
echo "   - Monitor penggunaan disk secara berkala"
