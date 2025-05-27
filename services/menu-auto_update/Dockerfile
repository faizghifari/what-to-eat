# Dockerfile for KAIST Menu Scraper

FROM python:3.11-slim

# Set timezone to Asia/Seoul
ENV TZ=Asia/Seoul
RUN apt-get update && \
    apt-get install -y cron tzdata && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && \
    pip install --no-cache-dir requests beautifulsoup4 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy scripts and input files
COPY src/kaist_menu_scraper.py ./src/kaist_menu_scraper.py
COPY kaist_web_list.txt ./kaist_web_list.txt
COPY run_scraper.sh ./run_scraper.sh
COPY crontab.txt ./crontab.txt

RUN chmod +x /app/run_scraper.sh

# Install crontab
RUN crontab /app/crontab.txt

# Start cron and keep container running
CMD ["/bin/bash", "-c", "cron && tail -f /dev/null"]
