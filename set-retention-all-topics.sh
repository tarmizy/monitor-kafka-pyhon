#!/bin/bash

# Default values
RETENTION_TIME=604800000  # 7 days in milliseconds
RETENTION_SIZE=1073741824  # 1GB in bytes
KAFKA_SERVER="localhost:9092"

# Help function
show_help() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -t, --time     Retention time in milliseconds (default: 604800000 - 7 days)"
    echo "  -s, --size     Retention size in bytes (default: 1073741824 - 1GB)"
    echo "  -b, --broker   Kafka broker address (default: localhost:9092)"
    echo "  -h, --help     Show this help message"
    echo
    echo "Example:"
    echo "  $0 -t 259200000 -s 536870912 -b kafka:9092"
    echo "  (Sets 3 days retention time and 512MB retention size)"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -t|--time)
        RETENTION_TIME="$2"
        shift
        shift
        ;;
        -s|--size)
        RETENTION_SIZE="$2"
        shift
        shift
        ;;
        -b|--broker)
        KAFKA_SERVER="$2"
        shift
        shift
        ;;
        -h|--help)
        show_help
        exit 0
        ;;
        *)
        echo "Unknown option: $1"
        show_help
        exit 1
        ;;
    esac
done

echo "Using configuration:"
echo "Kafka Broker: $KAFKA_SERVER"
echo "Retention Time: $RETENTION_TIME ms ($(($RETENTION_TIME/86400000)) days)"
echo "Retention Size: $RETENTION_SIZE bytes ($(($RETENTION_SIZE/1024/1024)) MB)"
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
echo "Getting list of topics..."
topics=$(kafka-topics.sh --bootstrap-server $KAFKA_SERVER --list)

if [ $? -ne 0 ]; then
    echo "Error: Failed to get topic list"
    exit 1
fi

# Update retention for each topic
for topic in $topics
do
    echo "Setting retention for topic: $topic"
    kafka-configs.sh --bootstrap-server $KAFKA_SERVER \
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

echo "Operation completed!"
