FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app
COPY video_test.py /app/video_test.py
COPY 720x480_1mb.mp4 /app/720x480_1mb.mp4


EXPOSE 8089

CMD ["locust", "-f", "video_test.py"]
