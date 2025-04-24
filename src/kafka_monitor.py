import os
import time
import json
import psutil
import logging
from datetime import datetime
from dotenv import load_dotenv
from confluent_kafka.admin import AdminClient, ConfigResource
from confluent_kafka import Consumer, KafkaError
from telegram_notifier import TelegramNotifier

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class KafkaMonitor:
    def __init__(self):
        # Load environment variables
        load_dotenv('config/config.env')
        
        # Kafka configuration
        self.kafka_config = {
            'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
            'group.id': os.getenv('KAFKA_CONSUMER_GROUP'),
            'auto.offset.reset': 'earliest'
        }
        
        # Initialize Kafka admin client
        self.admin_client = AdminClient(self.kafka_config)
        
        # Initialize Telegram notifier
        self.telegram = TelegramNotifier()
        
        # Monitoring thresholds
        self.alert_threshold_lag = int(os.getenv('ALERT_THRESHOLD_LAG', 1000))
        self.alert_threshold_partition_count = int(os.getenv('ALERT_THRESHOLD_PARTITION_COUNT', 0))
        
        # Retention monitoring settings
        self.monitor_retention = os.getenv('MONITOR_RETENTION_ENABLED', 'true').lower() == 'true'
        self.retention_warning_threshold_ms = int(os.getenv('RETENTION_WARNING_THRESHOLD_MS', 259200000))
        self.retention_warning_threshold_bytes = int(os.getenv('RETENTION_WARNING_THRESHOLD_BYTES', 268435456))
        
        # Resource monitoring settings
        self.memory_warning_threshold = int(os.getenv('MEMORY_WARNING_THRESHOLD', 80))
        self.disk_warning_threshold = int(os.getenv('DISK_WARNING_THRESHOLD', 80))
        self.monitor_paths = json.loads(os.getenv('MONITOR_PATHS', '["/"]'))
        
        # Daily report settings
        self.daily_report_enabled = os.getenv('DAILY_REPORT_ENABLED', 'true').lower() == 'true'
        self.daily_report_time = os.getenv('DAILY_REPORT_TIME', '00:00')
        self.last_report_date = None
        
        # Last alert timestamps to prevent alert spam
        self.last_memory_alert = 0
        self.last_disk_alert = {}
        self.alert_cooldown = 3600  # 1 hour cooldown between alerts
    
    def should_send_daily_report(self):
        """Check if it's time to send daily report"""
        if not self.daily_report_enabled:
            logger.info("Daily report is disabled")
            return False
            
        current_time = datetime.now()
        report_hour, report_minute = map(int, self.daily_report_time.split(':'))
        
        logger.info(f"Checking daily report time - Current: {current_time.strftime('%H:%M')}, Target: {self.daily_report_time}")
        
        # Check if it's report time and we haven't sent report today
        if (current_time.hour == report_hour and 
            current_time.minute == report_minute and 
            (self.last_report_date is None or 
             current_time.date() > self.last_report_date)):
            self.last_report_date = current_time.date()
            logger.info("It's time to send daily report!")
            return True
        return False
    
    def check_memory_usage(self):
        """Check system memory usage"""
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        warnings = []
        current_time = time.time()
        
        if memory_percent > self.memory_warning_threshold:
            if current_time - self.last_memory_alert > self.alert_cooldown:
                self.last_memory_alert = current_time
                warnings.append(
                    f"⚠️ Memory Usage Warning:\n"
                    f"   - Current Usage: {memory_percent:.1f}%\n"
                    f"   - Available: {memory.available / 1024 / 1024:.1f} MB\n"
                    f"   - Total: {memory.total / 1024 / 1024:.1f} MB"
                )
        
        return memory_percent, warnings
    
    def check_disk_usage(self):
        """Check disk usage for monitored paths"""
        warnings = []
        current_time = time.time()
        
        for path in self.monitor_paths:
            try:
                disk_usage = psutil.disk_usage(path)
                usage_percent = disk_usage.percent
                
                if usage_percent > self.disk_warning_threshold:
                    if path not in self.last_disk_alert or current_time - self.last_disk_alert[path] > self.alert_cooldown:
                        self.last_disk_alert[path] = current_time
                        warnings.append(
                            f"⚠️ Disk Usage Warning for {path}:\n"
                            f"   - Current Usage: {usage_percent:.1f}%\n"
                            f"   - Free Space: {disk_usage.free / 1024 / 1024 / 1024:.1f} GB\n"
                            f"   - Total Space: {disk_usage.total / 1024 / 1024 / 1024:.1f} GB"
                        )
            except Exception as e:
                logger.error(f"Error checking disk usage for {path}: {str(e)}")
        
        return warnings
    
    def generate_resource_report(self):
        """Generate resource usage report"""
        memory = psutil.virtual_memory()
        report_lines = [
            "💻 Resource Usage Report:",
            "",
            "🧠 Memory Usage:",
            f"   - Used: {memory.percent:.1f}%",
            f"   - Available: {memory.available / 1024 / 1024:.1f} MB",
            f"   - Total: {memory.total / 1024 / 1024:.1f} MB",
            "",
            "💾 Disk Usage:"
        ]
        
        for path in self.monitor_paths:
            try:
                disk = psutil.disk_usage(path)
                report_lines.extend([
                    f"\n   📁 {path}:",
                    f"      - Used: {disk.percent:.1f}%",
                    f"      - Free: {disk.free / 1024 / 1024 / 1024:.1f} GB",
                    f"      - Total: {disk.total / 1024 / 1024 / 1024:.1f} GB"
                ])
            except Exception as e:
                report_lines.append(f"   ❌ Error checking {path}: {str(e)}")
        
        return "\n".join(report_lines)
    
    def generate_daily_report(self, topics, cluster_status):
        """Generate daily status report"""
        report_lines = [
            "📊 Laporan Harian Kafka Monitor",
            f"📅 Tanggal: {datetime.now().strftime('%Y-%m-%d')}",
            f"🕒 Waktu: {datetime.now().strftime('%H:%M:%S')}",
            "",
            f"🖥️ Status Cluster: {'✅ Sehat' if cluster_status else '❌ Bermasalah'}",
            f"📚 Total Topics: {len(topics)}",
            "",
            "📈 Detail Topics:"
        ]
        
        for topic_name in topics:
            # Get topic details
            partition_count = len(topics[topic_name].partitions)
            lag = self.check_consumer_lag(topic_name)
            retention_warnings = self.check_topic_retention(topic_name) if self.monitor_retention else []
            
            topic_details = [
                f"\n🔹 Topic: {topic_name}",
                f"   - Partisi: {partition_count}",
                f"   - Consumer Lag: {lag} messages"
            ]
            
            if retention_warnings:
                topic_details.append("   - Peringatan Retention:")
                for warning in retention_warnings:
                    topic_details.append(f"     {warning}")
            
            report_lines.extend(topic_details)
        
        # Add resource usage report
        report_lines.extend(["", self.generate_resource_report()])
        
        return "\n".join(report_lines)
    
    def check_broker_status(self):
        """Check if Kafka brokers are available"""
        try:
            metadata = self.admin_client.list_topics(timeout=10)
            return True, "Brokers are healthy"
        except Exception as e:
            return False, f"Failed to connect to brokers: {str(e)}"
    
    def check_consumer_lag(self, topic):
        """Check consumer lag for a topic"""
        try:
            consumer = Consumer(self.kafka_config)
            consumer.subscribe([topic])
            
            # Get current end offsets
            assignments = consumer.assignment()
            end_offsets = {}
            for tp in assignments:
                end_offsets[tp] = consumer.get_watermark_offsets(tp)[1]
            
            # Get current positions
            positions = {}
            for tp in assignments:
                positions[tp] = consumer.position(tp)
            
            # Calculate total lag
            total_lag = sum(end_offsets[tp] - positions[tp] for tp in assignments)
            
            consumer.close()
            return total_lag
            
        except Exception as e:
            logger.error(f"Error checking consumer lag for topic {topic}: {str(e)}")
            return 0
    
    def check_topic_retention(self, topic):
        """Check retention settings for a topic"""
        try:
            resource = ConfigResource(ConfigResource.Type.TOPIC, topic)
            result = self.admin_client.describe_configs([resource])
            
            warnings = []
            for res, f in result.items():
                config = f.result()
                retention_ms = int(config.get('retention.ms', {}).value or 0)
                retention_bytes = int(config.get('retention.bytes', {}).value or -1)
                
                if retention_ms > self.retention_warning_threshold_ms:
                    warnings.append(f"⚠️ Retention time ({retention_ms/86400000:.1f} days) exceeds threshold ({self.retention_warning_threshold_ms/86400000:.1f} days)")
                
                if retention_bytes != -1 and retention_bytes > self.retention_warning_threshold_bytes:
                    warnings.append(f"⚠️ Retention size ({retention_bytes/1024/1024:.1f} MB) exceeds threshold ({self.retention_warning_threshold_bytes/1024/1024:.1f} MB)")
            
            return warnings
            
        except Exception as e:
            logger.error(f"Error checking retention for topic {topic}: {str(e)}")
            return []
    
    def monitor(self):
        """Main monitoring function"""
        logger.info("Starting Kafka monitoring service...")
        self.telegram.send_message("🚀 Kafka monitoring service started!")
        
        while True:
            try:
                # Check system resources
                memory_percent, memory_warnings = self.check_memory_usage()
                disk_warnings = self.check_disk_usage()
                
                # Send resource warnings if any
                for warning in memory_warnings + disk_warnings:
                    self.telegram.send_alert(warning)
                
                # Check broker status
                status, message = self.check_broker_status()
                if not status:
                    self.telegram.send_alert(f"❌ Kafka Cluster Alert: {message}")
                    continue
                
                # Get all topics
                metadata = self.admin_client.list_topics()
                topics = metadata.topics
                
                # Monitor each topic
                for topic_name in topics:
                    # Check partition count
                    partition_count = len(topics[topic_name].partitions)
                    if partition_count <= self.alert_threshold_partition_count:
                        self.telegram.send_alert(
                            f"⚠️ Topic Alert: {topic_name}\n"
                            f"Partition count ({partition_count}) is below threshold"
                        )
                    
                    # Check consumer lag
                    lag = self.check_consumer_lag(topic_name)
                    if lag > self.alert_threshold_lag:
                        self.telegram.send_alert(
                            f"⚠️ Consumer Lag Alert: {topic_name}\n"
                            f"Current lag: {lag} messages"
                        )
                    
                    # Check retention settings
                    if self.monitor_retention:
                        retention_warnings = self.check_topic_retention(topic_name)
                        if retention_warnings:
                            self.telegram.send_alert(
                                f"📢 Peringatan Retention untuk Topic: {topic_name}\n" +
                                "\n".join(retention_warnings)
                            )
                
                # Check if it's time for daily report
                if self.should_send_daily_report():
                    report = self.generate_daily_report(topics, status)
                    self.telegram.send_message(report)
                    logger.info("Daily report sent successfully")
                
            except Exception as e:
                logger.error(f"Error in monitoring: {str(e)}")
                self.telegram.send_alert(f"❌ Monitoring Error: {str(e)}")
            
            # Wait for next check interval
            time.sleep(int(os.getenv('CHECK_INTERVAL', 300)))

if __name__ == '__main__':
    monitor = KafkaMonitor()
    monitor.monitor()
