from kafka import KafkaConsumer, KafkaProducer
import subprocess

consumer = KafkaConsumer('task-queue', bootstrap_servers='kafka-service:9092')
producer = KafkaProducer(bootstrap_servers='kafka-service:9092')

for message in consumer:
    task = message.value.decode('utf-8')
    input_path, output_path, format = task.split(',')
    subprocess.run(['ffmpeg', '-i', input_path, '-f', format, output_path])
    producer.send('result-queue', f'{output_path}'.encode('utf-8'))
