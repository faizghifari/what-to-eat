"""
KAIST Cafeteria Menu Scraper
- Extracts menu, allergy, and price data from KAIST cafeteria web pages.
- Outputs structured JSON for downstream use.
"""

import requests
from bs4 import BeautifulSoup

from auto_update.config import read_restaurant_config
from auto_update.menu_service import (
    get_restaurant_id_by_name,
    delete_menus_by_restaurant_id,
    insert_menus,
    adjust_menus_with_llm,
)
from auto_update.extract_helpers import (
    extract_restaurant_name,
    extract_allergy_mapping,
)
from auto_update.menu_processing import extract_menus, postprocess_cafeteria_menus

# ---------------------- Scraping Orchestration ----------------------


def sync_menus_to_service(scraped_data):
    for entry in scraped_data:
        restaurant_name = entry["restaurant_name"]
        restaurant_id = get_restaurant_id_by_name(restaurant_name)
        if not restaurant_id:
            print(f"Unknown restaurant: {restaurant_name}, skipping...")
            continue
        print(f"Syncing menus for {restaurant_name}...")
        try:
            delete_menus_by_restaurant_id(restaurant_id)
        except Exception as e:
            print(f"Failed to delete menus for {restaurant_name}: {e}")
            continue
        try:
            adjusted_menus = adjust_menus_with_llm(entry["menus"])
            insert_menus(restaurant_id, adjusted_menus)
        except Exception as e:
            print(f"Failed to insert menus for {restaurant_name}: {e}")


def scrape_kaist_menus(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    restaurant_name = extract_restaurant_name(soup)
    allergy_map = extract_allergy_mapping(soup)
    menus = extract_menus(soup, allergy_map, restaurant_name)
    menus = postprocess_cafeteria_menus(menus, allergy_map)
    return {"restaurant_name": restaurant_name, "menus": menus}


def main():
    config = read_restaurant_config("scraper_config.json")
    all_data = []
    for entry in config:
        url = entry["url"]
        restaurant_name = entry["restaurant_name"]
        print(f"Scraping {url}...")
        try:
            data = scrape_kaist_menus(url)
            data["restaurant_name"] = restaurant_name
            all_data.append(data)
        except Exception as e:
            print(f"Error scraping {url}: {e}")
    sync_menus_to_service(all_data)
    print("Scraping and sync complete.")


if __name__ == "__main__":
    main()
