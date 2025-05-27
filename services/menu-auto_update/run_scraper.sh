#!/bin/bash
cd /app
export PYTHONPATH=$(pwd)/src:$PYTHONPATH
python ./src/auto_update/scraper.py