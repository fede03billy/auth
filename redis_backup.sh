#!/bin/bash
# redis_backup.sh

while true; do
  redis-cli BGSAVE

  # Capture the current date and time
  current_time=$(date +"%Y-%m-%d %H:%M:%S")

  # Log the time when the backup was saved
  echo "Backup saved at $current_time"

  # Sleep for an hour
  sleep 3600
done
