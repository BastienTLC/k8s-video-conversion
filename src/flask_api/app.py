import logging
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import NoBrokersAvailable
import os
import logging
import json
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
CORS(app)  # Allow CORS for all routes

# Kafka configuration
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
logging.debug(f"Connecting to Kafka broker at {KAFKA_BROKER}")

def create_kafka_producer():
    while True:
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BROKER,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            logging.info("Kafka producer connected successfully.")
            return producer
        except NoBrokersAvailable as e:
            logging.error(f"Failed to connect to Kafka broker: {e}. Retrying in 5 seconds...")
            time.sleep(5)  # Attendre 5 secondes avant de réessayer

producer = create_kafka_producer()

SHARED_STORAGE_BASE_PATH = os.getenv("SHARED_STORAGE_BASE_PATH", "/home/bastien/shared_storage/base")
SHARED_STORAGE_CONVERT_PATH = os.getenv("SHARED_STORAGE_CONVERT_PATH", "/home/bastien/shared_storage/convert")

@app.route('/submit', methods=['POST'])
def submit_video():
    logging.debug("Received /submit request.")
    file = request.files.get('file')
    format = request.form.get('format')

    if not file or not format:
        logging.warning("Invalid input: file or format missing.")
        return jsonify({"error": "Invalid input"}), 400

    # Ensure base storage path exists
    os.makedirs(SHARED_STORAGE_BASE_PATH, exist_ok=True)
    video_name = file.filename.split(".")[0]
    video_base_format = file.filename.split(".")[1]
    timestamp = int(time.time())
    video_id = f"{video_name}_{timestamp}.{video_base_format}"
    file_path = os.path.join(SHARED_STORAGE_BASE_PATH, video_id)

    file.save(file_path)

    task = {"video_id": video_id, "format": format, "file_path": file_path}
    logging.info(f"Task to send: {task}")

    try:
        producer.send("task_queue", value=task)
        logging.info("Task sent to Kafka successfully.")
    except Exception as e:
        logging.error(f"Failed to send task to Kafka: {e}")
        return jsonify({"error": "Failed to process task"}), 500

    return jsonify({"video_id": video_id}), 200

@app.route('/status/<video_id>', methods=['GET'])
def check_status(video_id):
    logging.debug(f"Received /status request for video_id: {video_id}")
    try:
        consumer = KafkaConsumer(
            "result_queue",
            bootstrap_servers=KAFKA_BROKER,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            value_deserializer=lambda v: json.loads(v.decode('utf-8'))
        )
        logging.info("Connected to Kafka consumer for result_queue.")

        for message in consumer:
            result = message.value
            logging.debug(f"Received message from Kafka: {result}")
            if result["video_id"] == video_id:
                return jsonify(result), 200

    except Exception as e:
        logging.error(f"Failed to consume messages from Kafka: {e}")
        return jsonify({"error": "Failed to check status"}), 500

    return jsonify({"status": "processing"}), 200

@app.route('/download/<video_id>', methods=['GET'])
def download_file(video_id):
    logging.debug(f"Received /download request for video_id: {video_id}")
    output_file = os.path.join(SHARED_STORAGE_CONVERT_PATH, video_id)

    if not os.path.exists(output_file):
        logging.warning(f"File not found: {output_file}")
        return jsonify({"error": "File not found"}), 404

    return send_file(output_file, as_attachment=True)

@app.route('/test', methods=['GET'])
def test():
    logging.debug(f"API is up and running.")
    
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
