# KAIST Menu Auto Update Service

This directory contains a Dockerized Python scraper and auto-update for KAIST cafeteria menus.

## Files

- `kaist_menu_scraper.py`: Main scraping script (in `src/auto_update/`)
- `kaist_web_list.txt`: List of URLs to scrape
- `Dockerfile`: Container definition
- `run_scraper.sh`: Script run by cron to execute the scraper
- `crontab.txt`: Crontab entry for running the scraper daily at 1 AM KST

## Build the Docker Image

From this directory, run:

```
docker build -t kaist-menu-scraper .
```

## Run the Container (with Cron Inside)

To start the container (it will run the scraper daily at 1 AM KST):

```
docker run -d --name kaist-menu-scraper --restart unless-stopped \
  -v %cd%/src:/app/src \
  -v %cd%:/app \
  kaist-menu-scraper
```

- On Linux/macOS, replace `%cd%` with `$(pwd)`.
- The container will keep running and execute the scraper daily at 1 AM KST (Asia/Seoul time).
- Output and logs will be in the container's `/app/src/auto_update/kaist_menu_data.json` and `/app/cron.log` (also mapped to your host).

## Manual Run (Optional)

To run the scraper immediately (without waiting for cron):

```
docker exec kaist-menu-scraper /app/run_scraper.sh
```

## Stopping/Removing the Container

```
docker stop kaist-menu-scraper
# To remove:
docker rm kaist-menu-scraper
```

## Output

- The output file `kaist_menu_data.json` will be written to the `src/auto_update/` directory.
- Cron logs are in `cron.log` in the container (and mapped to your host).

---

**Tip:** You can adjust the volume mounts if you want the output elsewhere.
