# KAIST Menu Auto Update Service

This service scrapes KAIST cafeteria menus, enhances menu names and descriptions using Google GenAI, and syncs the results directly to a Supabase database.

## Features

- Scrapes menu, allergy, and price data from KAIST cafeteria web pages.
- Uses Google GenAI (Gemini) to generate improved menu names and descriptions.
- Syncs data directly to Supabase (no REST API service required).
- Dockerized and runs on a schedule via cron.

## Files

- `src/auto_update/scraper.py`: Main scraping and sync script
- `scraper_config.json`: List of restaurant URLs and names to scrape
- `Dockerfile`: Container definition
- `run_scraper.sh`: Script run by cron to execute the scraper
- `crontab.txt`: Crontab entry for running the scraper daily at 1 AM KST
- `.env`: Environment variables for Supabase and Google GenAI credentials

## Environment Variables

Create a `.env` file in the project root with the following (see `.env.example` for an example):

```
SUPABASE_URL=... # Your Supabase project URL
SUPABASE_KEY=... # Your Supabase service role key
GOOGLE_API_KEY=... # Your Google GenAI API key
GOOGLE_GENAI_MODEL=... # e.g. gemini-2.0-pro
```

## Build the Docker Image

From this directory, run:

```
docker build -t menu-auto_update-service .
```

## Run the Container (with Cron Inside)

To start the container (it will run the scraper daily at 1 AM KST):

```
docker run -d --name menu-auto_update-service --restart unless-stopped \
  -v %cd%/src:/app/src \
  -v %cd%:/app \
  --env-file .env \
  menu-auto_update-service
```

- On Linux/macOS, replace `%cd%` with `$(pwd)`.
- The container will keep running and execute the scraper daily at 1 AM KST (Asia/Seoul time).
- Output and logs will be in the container's `/app/cron.log` (also mapped to your host).

## Manual Run (Optional)

To run the scraper immediately (without waiting for cron):

```
docker exec menu-auto_update-service /app/run_scraper.sh
```

## Stopping/Removing the Container

```
docker stop menu-auto_update-service
# To remove:
docker rm menu-auto_update-service
```

---

**Tip:** You can adjust the volume mounts if you want the output elsewhere.
