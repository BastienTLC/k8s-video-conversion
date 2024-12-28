#!/bin/bash

TOPICS=(
  "task_queue"
  "result_queue"
)

PARTITIONS=1
REPLICATION_FACTOR=1

for topic in "${TOPICS[@]}"; do
  echo "Creating topic: $topic"
  kafka-topics.sh --create \
    --topic "$topic" \
    --partitions $PARTITIONS \
    --replication-factor $REPLICATION_FACTOR \
    --bootstrap-server localhost:9092
done
