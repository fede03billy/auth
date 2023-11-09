#!/bin/bash
# redis_backup.sh

while true; do
  redis-cli BGSAVE
  # Sleep for an hour
  sleep 3600
done

### Dockerfile spec
# # Copy the backup script to the container
# COPY redis_backup.sh /usr/local/bin/redis_backup.sh
# # Set the backup script to be executable
# RUN chmod +x /usr/local/bin/redis_backup.sh
