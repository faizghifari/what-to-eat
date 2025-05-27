#!/bin/bash
cd /app
export PYTHONPATH=$(pwd)/src:$PYTHONPATH
/usr/local/bin/python ./src/auto_update/scraper.py