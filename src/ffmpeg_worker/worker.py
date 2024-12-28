import logging
from kafka import KafkaConsumer, KafkaProducer
import subprocess
import os
import json
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
SHARED_STORAGE_BASE_PATH = os.getenv("SHARED_STORAGE_BASE_PATH", "/home/bastien/shared_storage/base")
SHARED_STORAGE_CONVERT_PATH = os.getenv("SHARED_STORAGE_CONVERT_PATH", "/home/bastien/shared_storage/convert")

def wait_for_kafka_ready(broker, retries=5, delay=5):
    for attempt in range(retries):
        try:
            logging.info(f"Attempting to connect to Kafka (try {attempt + 1}/{retries})...")
            consumer = KafkaConsumer(
                bootstrap_servers=broker,
                api_version_auto_timeout_ms=2000
            )
            consumer.close()
            logging.info("Kafka is ready.")
            return
        except Exception as e:
            logging.warning(f"Kafka not ready yet: {e}")
            time.sleep(delay)
    raise Exception("Kafka is not ready after multiple retries.")

def convert_video(task):
    input_file = os.path.join(SHARED_STORAGE_BASE_PATH, task["video_id"])
    os.makedirs(SHARED_STORAGE_CONVERT_PATH, exist_ok=True)
    video_name = task["video_id"].split(".")[0]
    output_file = os.path.join(SHARED_STORAGE_CONVERT_PATH, f"{video_name}.{task['format']}")

    try:
        result = subprocess.run(
            ["ffmpeg", "-i", input_file, output_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            logging.error(f"FFmpeg error for video_id {task['video_id']}: {result.stderr}")
            return {"video_id": task["video_id"], "status": "failed", "error": result.stderr}

        logging.info(f"Completed conversion for video_id: {task['video_id']}, output_file: {output_file}")
        return {"video_id": task["video_id"], "status": "completed", "output_file": output_file}

    except Exception as e:
        logging.error(f"Exception during conversion for video_id {task['video_id']}: {e}")
        return {"video_id": task["video_id"], "status": "failed", "error": str(e)}

# Ensure Kafka is ready
wait_for_kafka_ready(KAFKA_BROKER)

# Kafka consumer and producer
consumer = KafkaConsumer(
    "task_queue",
    bootstrap_servers=KAFKA_BROKER,
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    value_deserializer=lambda v: json.loads(v.decode('utf-8'))
)
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

logging.info("Starting Kafka consumer loop")

for message in consumer:
    try:
        task = message.value
        logging.info(f"Received task: {task}")

        # Perform video conversion
        result = convert_video(task)

        # Send result to result_queue
        logging.info(f"Sending result: {result}")
        producer.send("result_queue", value=result)

    except Exception as e:
        logging.error(f"Error processing message: {e}")
