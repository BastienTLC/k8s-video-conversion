import os
import json
import time
from kafka import KafkaConsumer, KafkaProducer
import subprocess
from minio import Minio
from minio.error import S3Error

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET_BASE = os.getenv("MINIO_BUCKET_BASE", "video-base")
MINIO_BUCKET_CONVERT = os.getenv("MINIO_BUCKET_CONVERT", "video-convert")
KAFKA_CONSUMER_GROUP = os.getenv("KAFKA_CONSUMER_GROUP", "video-converter-group")

# Initialize MinIO client
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False  # Set to True if using HTTPS
)

# Ensure buckets exist
if not minio_client.bucket_exists(MINIO_BUCKET_BASE):
    minio_client.make_bucket(MINIO_BUCKET_BASE)
if not minio_client.bucket_exists(MINIO_BUCKET_CONVERT):
    minio_client.make_bucket(MINIO_BUCKET_CONVERT)

def wait_for_kafka_ready(broker, retries=5, delay=5):
    for attempt in range(retries):
        try:
            print(f"Attempting to connect to Kafka (try {attempt + 1}/{retries})...")
            consumer = KafkaConsumer(
                bootstrap_servers=broker,
                api_version_auto_timeout_ms=2000
            )
            consumer.close()
            print("Kafka is ready.")
            return
        except Exception as e:
            print(f"Kafka not ready yet: {e}")
            time.sleep(delay)
    raise Exception("Kafka is not ready after multiple retries.")

def convert_video(task):
    input_file = f"tmp/input/{task['video_id']}"
    video_name, video_base_format = os.path.splitext(task['video_id'])
    output_file = f"tmp/output/{video_name}.{task['format']}"

    try:
        # Download the video from MinIO
        minio_client.fget_object(MINIO_BUCKET_BASE, task['video_id'], input_file)
        minio_client.remove_object(MINIO_BUCKET_BASE, task['video_id'])

        # Convert the video
        result = subprocess.run(
            [
                "ffmpeg",
                "-y",  # Overwrite output file without asking
                "-i", input_file,  # Input file
                "-c:v", "libx264",  # Use H.264 codec (plus rapide que H.265)
                "-preset", "ultrafast",  # Fastest encoding preset, minimal CPU usage
                "-crf", "35",  # High compression, reduces CPU usage
                "-c:a", "aac",  # Efficient and widely supported audio codec
                "-b:a", "96k",  # Lower audio bitrate to reduce processing
                output_file
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            print(f"FFmpeg error for video_id {task['video_id']}: {result.stderr}")
            return {"video_id": task["video_id"], "status": "failed", "error": result.stderr}

        if result.returncode != 0:
            print(f"FFmpeg error for video_id {task['video_id']}: {result.stderr}")
            return {"video_id": task["video_id"], "status": "failed", "error": result.stderr}

        # Upload the converted video to MinIO
        converted_video_id = f"{video_name}.{task['format']}"
        minio_client.fput_object(MINIO_BUCKET_CONVERT, converted_video_id, output_file)

        print(f"Completed conversion for video_id: {task['video_id']}, output_file: {output_file}")
        return {"video_id": task["video_id"], "status": "completed", "output_file": converted_video_id}

    except Exception as e:
        print(f"Exception during conversion for video_id {task['video_id']}: {e}")
        return {"video_id": task["video_id"], "status": "failed", "error": str(e)}
    finally:
        # Clean up temporary files
        if os.path.exists(input_file):
            os.remove(input_file)
        if os.path.exists(output_file):
            os.remove(output_file)

# Ensure Kafka is ready
wait_for_kafka_ready(KAFKA_BROKER)

# Kafka consumer and producer
consumer = KafkaConsumer(
    "task_queue",
    bootstrap_servers=KAFKA_BROKER,
    group_id=KAFKA_CONSUMER_GROUP,
    auto_offset_reset='earliest',
    enable_auto_commit=False,
    value_deserializer=lambda v: json.loads(v.decode('utf-8'))
)
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

print("Starting Kafka consumer loop")

for message in consumer:
    print(f"Received message: {message}")
    try:
        task = message.value
        print(f"Received task: {task}")

        # Perform video conversion
        result = convert_video(task)

        # Send result to result_queue
        print(f"Sending result: {result}")
        producer.send("result_queue", value=result)

        consumer.commit()
        print(f"Committed message: {message.offset}")

    except Exception as e:
        print(f"Error processing message: {e}")
