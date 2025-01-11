from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import NoBrokersAvailable
from minio import Minio
from minio.error import S3Error
import os
import json
import time

app = Flask(__name__)
CORS(app)  # Allow CORS for all routes

# Kafka configuration
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
print(f"Connecting to Kafka broker at {KAFKA_BROKER}")

# MinIO configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET_BASE = os.getenv("MINIO_BUCKET_BASE", "video-base")
MINIO_BUCKET_CONVERT = os.getenv("MINIO_BUCKET_CONVERT", "video-convert")

# Initialize MinIO client
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False  # Set to True if using HTTPS
)

# Ensure the base bucket exists
if not minio_client.bucket_exists(MINIO_BUCKET_BASE):
    minio_client.make_bucket(MINIO_BUCKET_BASE)

def create_kafka_producer():
    while True:
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BROKER,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            print("Kafka producer connected successfully.")
            return producer
        except NoBrokersAvailable as e:
            print(f"Failed to connect to Kafka broker: {e}. Retrying in 5 seconds...")
            time.sleep(5)  # Wait 5 seconds before retrying

producer = create_kafka_producer()


video_formats = [
    {"Format": "MP4", "Extension": "mp4"},
    {"Format": "AVI", "Extension": "avi"},
    {"Format": "MKV", "Extension": "mkv"},
    {"Format": "MOV", "Extension": "mov"},
    {"Format": "WMV", "Extension": "wmv"},
    {"Format": "FLV", "Extension": "flv"},
    {"Format": "WEBM", "Extension": "webm"},
    {"Format": "MPEG", "Extension": "mpeg"},
    {"Format": "3GP", "Extension": "3gp"},
    {"Format": "OGG", "Extension": "ogv"}
]

@app.route('/submit', methods=['POST'])
def submit_video():
    print("Received /submit request.")
    file = request.files.get('file')
    format = request.form.get('format')

    if not file or not format:
        print("Invalid input: file or format missing.")
        return jsonify({"error": "Invalid input"}), 400

    if format not in [f["Extension"] for f in video_formats]:
        print(f"Invalid format: {format}")
        return jsonify({"error": "Invalid format"}), 400

    video_name, video_base_format = os.path.splitext(file.filename)
    timestamp = int(time.time())
    video_id = f"{video_name}_{timestamp}{video_base_format}"

    try:
        # Upload the video to MinIO
        minio_client.put_object(
            MINIO_BUCKET_BASE, video_id, file, length=-1, part_size=10*1024*1024
        )
        print(f"Uploaded video {video_id} to MinIO bucket {MINIO_BUCKET_BASE}.")

        task = {"video_id": video_id, "format": format}
        print(f"Task to send: {task}")

        producer.send("task_queue", value=task)
        print("Task sent to Kafka successfully.")

        return jsonify({"video_id": video_id}), 200

    except S3Error as e:
        print(f"Failed to upload video to MinIO: {e}")
        return jsonify({"error": "Failed to upload video"}), 500
    except Exception as e:
        print(f"Error processing task: {e}")
        return jsonify({"error": "Failed to process task"}), 500

@app.route('/status/<video_id>', methods=['GET'])
def check_status(video_id):
    print(f"Received /status request for video_id: {video_id}")
    try:
        consumer = KafkaConsumer(
            "result_queue",
            bootstrap_servers=KAFKA_BROKER,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            value_deserializer=lambda v: json.loads(v.decode('utf-8'))
        )
        print("Connected to Kafka consumer for result_queue.")

        for message in consumer:
            result = message.value
            print(f"Received message from Kafka: {result}")
            if result["video_id"] == video_id:
                print(f"Matching result found for video_id: {video_id}")
                return jsonify(result), 200

    except Exception as e:
        print(f"Failed to consume messages from Kafka: {e}")
        return jsonify({"error": "Failed to check status"}), 500

    print(f"No matching result found for video_id: {video_id}")
    return jsonify({"status": "processing"}), 200

@app.route('/download/<video_id>', methods=['GET'])
def download_file(video_id):
    print(f"Received /download request for video_id: {video_id}")
    temp_file = f"/tmp/{video_id}"

    try:
        # Download the file from MinIO
        minio_client.fget_object(MINIO_BUCKET_CONVERT, video_id, temp_file)
        print(f"File {video_id} downloaded to temporary location {temp_file}")

        # Serve the file for download
        return send_file(temp_file, as_attachment=True)
    except S3Error as e:
        print(f"Failed to download file {video_id} from MinIO: {e}")
        return jsonify({"error": "File not found"}), 404
    finally:
        minio_client.remove_object(MINIO_BUCKET_CONVERT, video_id)
        # Clean up the temporary file
        if os.path.exists(temp_file):
            os.remove(temp_file)
            print(f"Temporary file {temp_file} deleted.")


@app.route('/health', methods=['GET'])
def health():
    try:
        KafkaConsumer(bootstrap_servers=KAFKA_BROKER).close()

        if not minio_client.bucket_exists(MINIO_BUCKET_BASE):
            raise Exception("MinIO base bucket non disponible")

        return jsonify({"status": "healthy"}), 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


@app.route('/ready', methods=['GET'])
def ready():

    try:
        KafkaProducer(bootstrap_servers=KAFKA_BROKER).close()

        if not minio_client.bucket_exists(MINIO_BUCKET_BASE):
            raise Exception("MinIO base bucket non disponible")

        return jsonify({"status": "ready"}), 200
    except Exception as e:
        print(f"Readiness check failed: {e}")
        return jsonify({"status": "not ready", "error": str(e)}), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
