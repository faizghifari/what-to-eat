# Dockerfile for KAIST Menu Scraper
FROM python:3.12-slim

# Upgrade system packages to fix vulnerabilities
RUN apt-get update && apt-get upgrade -y

# Set timezone to Asia/Seoul
ENV TZ=Asia/Seoul
RUN apt-get install -y cron tzdata procps && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Set working directory
WORKDIR /app

# Copy source code and config
COPY src/ ./src/
COPY scraper_config.json ./scraper_config.json
COPY run_scraper.sh ./run_scraper.sh
COPY crontab.txt ./crontab.txt
COPY .env ./
# Copy requirements.txt before installing dependencies
COPY requirements.txt ./

RUN chmod +x /app/run_scraper.sh

# Install crontab
RUN crontab /app/crontab.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Start cron in the background and tail the log so output is visible and the log file is created if missing
CMD ["/bin/bash", "-c", "cron && mkdir -p /app/logs && touch /app/logs/cron.log && tail -F /app/logs/cron.log"]
