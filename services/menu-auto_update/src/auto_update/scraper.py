"""
KAIST Cafeteria Menu Scraper
- Extracts menu, allergy, and price data from KAIST cafeteria web pages.
- Outputs structured JSON for downstream use.
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from typing import List, Dict, Any

# ---------------------- Extraction Helpers ----------------------

def read_urls(filepath: str) -> List[str]:
    """Read URLs from a text file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def extract_restaurant_name(soup: BeautifulSoup) -> str:
    """Extract the restaurant name from the soup."""
    h3 = soup.select_one('div#tab_item_1 h3')
    if not h3:
        return None
    match = re.search(r'\[(.*?)\]', h3.text)
    if match:
        name = match.group(1)
        name = re.sub(r'\([^)]*\)', '', name).strip()
        return name
    return None

def extract_allergy_mapping(soup: BeautifulSoup) -> Dict[str, str]:
    """Extract allergy number-to-name mapping from the soup."""
    allergy_map = {}
    p = soup.select_one('div#tab_item_1 p')
    if not p:
        return allergy_map
    text = p.get_text(separator=' ').replace('\n', ' ').replace('\r', ' ').strip()
    bracket_match = re.search(r'\[(.*?)\]', text)
    mapping_str = None
    if bracket_match:
        mapping_str = bracket_match.group(1)
    else:
        mapping_match = re.search(r'((?:\d+\.?\s*[^\d]+[\/\,]?\s*){5,})', text)
        if mapping_match:
            mapping_str = mapping_match.group(1)
        else:
            mapping_str = text
    matches = re.findall(r'(\d+)\.?\s*([A-Za-z\uAC00-\uD7A3][A-Za-z\uAC00-\uD7A3\s\-]*?)(?:\s*\([^)]*\))?(?=\s*[\/\,]|\s+\d+\.?|$)', mapping_str)
    for num, allergy in matches:
        allergy_map[num] = allergy.strip(' -').replace('  ', ' ').lower()
    if not allergy_map:
        text = text.lower().split('allergy')[-1].strip()
        pattern = r"(\d+).\s*([^/]+)"
        allergy_mapping = {int(num): name.strip().lower() for num, name in re.findall(pattern, text)}
        for num, allergy in allergy_mapping.items():
            allergy_map[str(num)] = allergy.strip(' -').replace('  ', ' ').lower()
    return allergy_map

def split_menu_by_br(td) -> List[str]:
    """Split a table cell by <br><br> and clean up each chunk."""
    html = str(td)
    html = re.sub(r'^<td[^>]*>', '', html)
    html = re.sub(r'</td>$', '', html)
    menu_chunks = re.split(r'<br\s*/?>\s*(?:\r?\n)?\s*<br\s*/?>', html, flags=re.IGNORECASE)
    items = []
    for chunk in menu_chunks:
        text = BeautifulSoup(chunk, 'html.parser').get_text(separator=' ').strip()
        if text:
            items.append(text)
    return items

# ---------------------- Menu Extraction & Processing ----------------------

def extract_menus(soup: BeautifulSoup, allergy_map: Dict[str, str], restaurant_name: str) -> List[Dict[str, Any]]:
    """Extract all menus for a restaurant from the soup."""
    menus = []
    table = soup.select_one('div#tab_item_1 table')
    if not table:
        return menus
    tds = table.select('tbody tr td')
    meal_types = ['breakfast', 'lunch', 'dinner']
    for idx, td in enumerate(tds):
        meal = meal_types[idx] if idx < len(meal_types) else f'meal_{idx}'
        menu_items = split_menu_by_br(td)
        # Salad handling
        salad_menu_name = None
        salad_ingredients = None
        salad_allergy_numbers = None
        new_menu_items = []
        for item in menu_items:
            if 'vegetable salad & dressing' in item.lower():
                parts = [x.strip() for x in re.split(r'<br\s*/?>', item) if x.strip()]
                menu_name = parts[0] if parts else ''
                allergies = re.findall(r'\(([^)]*)\)', item)
                allergy_numbers = []
                for a in allergies:
                    a = a.replace("Contains: ", "").strip()
                    if re.match(r'^[\d,\s]+$', a):
                        allergy_numbers.extend([x.strip() for x in a.split(',') if x.strip()])
                allergy_numbers = list(set(allergy_numbers))
                ingredients = []
                for num in allergy_numbers:
                    if num in allergy_map:
                        ingredients.append({'name': allergy_map[num], 'description': ''})
                price = None
                price_pattern = re.compile(r'(?:([\d,]+)[\s\-]*(₩|KRW|Won|won)|(?:₩|KRW|Won|won)[\s\-]*([\d,]+))', re.IGNORECASE)
                price_match = price_pattern.search(item)
                if not price_match:
                    price_match = price_pattern.search(menu_name)
                if price_match:
                    price_str = price_match.group(1) or price_match.group(3)
                    if price_str:
                        price = float(price_str.replace(',', ''))
                if price is None:
                    salad_menu_name = menu_name
                    salad_ingredients = ingredients
                    salad_allergy_numbers = allergy_numbers
                    continue
            new_menu_items.append(item)
        # Process all other menus, add salad info if needed
        for item in new_menu_items:
            if 'global leadership' in item.lower():
                continue
            parts = [x.strip() for x in re.split(r'<br\s*/?>', item) if x.strip()]
            if not parts:
                continue
            menu_name = parts[0]
            description = ' '.join(parts[1:]) if len(parts) > 1 else ''
            allergies = re.findall(r'\(([^)]*)\)', item)
            allergy_numbers = []
            for a in allergies:
                a = a.replace("Contains: ", "").strip()
                if re.match(r'^[\d,\s]+$', a):
                    allergy_numbers.extend([x.strip() for x in a.split(',') if x.strip()])
            allergy_numbers = list(set(allergy_numbers))
            ingredients = []
            for num in allergy_numbers:
                if num in allergy_map:
                    ingredients.append({'name': allergy_map[num], 'description': ''})
            price = None
            price_pattern = re.compile(r'(?:([\d,]+)[\s\-]*(₩|KRW|Won|won)|(?:₩|KRW|Won|won)[\s\-]*([\d,]+))', re.IGNORECASE)
            price_match = price_pattern.search(item)
            if not price_match:
                price_match = price_pattern.search(menu_name + ' ' + description)
            if price_match:
                price_str = price_match.group(1) or price_match.group(3)
                if price_str:
                    price = float(price_str.replace(',', ''))
            if price is None:
                if restaurant_name == 'Undergraduate Cafeteria':
                    if meal == 'breakfast':
                        price = 3500
                    elif meal == 'lunch':
                        price = 5500
                    elif meal == 'dinner':
                        price = 5500
                elif restaurant_name == 'West-Campus Student Cafeteria':
                    if meal == 'breakfast':
                        price = 3700
                    elif meal == 'lunch':
                        price = 5000
                    elif meal == 'dinner':
                        price = 5000
            # Add salad info if present and not already included
            if salad_ingredients:
                if salad_menu_name and salad_menu_name not in menu_name:
                    menu_name = f"{menu_name} + {salad_menu_name}"
                existing_names = set(i['name'] for i in ingredients)
                for ing in salad_ingredients:
                    if ing['name'] not in existing_names:
                        ingredients.append(ing)
                        existing_names.add(ing['name'])
                allergy_numbers = list(set(allergy_numbers) | set(salad_allergy_numbers or []))
            menus.append({
                'meal': meal,
                'menu_name': menu_name,
                'description': description,
                'ingredients': ingredients,
                'allergy_numbers': allergy_numbers,
                'price': price
            })
    return menus

def postprocess_cafeteria_menus(menus: List[Dict[str, Any]], allergy_map: Dict[str, str]) -> List[Dict[str, Any]]:
    """Post-process menus with <Cafeteria> in the name, splitting and merging as needed."""
    processed = []
    for menu in menus:
        if '<Cafeteria>' in menu['menu_name']:
            base = menu['menu_name'].replace('<Cafeteria>', '').strip()
            parts = re.split(r'\r', base)
            parts = [p.strip() for p in parts if p.strip()]
            prev_menu = None
            for part in parts:
                price_pattern = re.compile(r'(?:([\d,]+)[\s\-]*(₩|KRW|Won|won)|(?:₩|KRW|Won|won)[\s\-]*([\d,]+))', re.IGNORECASE)
                price_match = price_pattern.search(part)
                price = float((price_match.group(1) or price_match.group(3)).replace(',', '')) if price_match and (price_match.group(1) or price_match.group(3)) else None
                allergies = re.findall(r'\(([^)]*)\)', part)
                allergy_numbers = []
                for a in allergies:
                    a = a.replace("Contains: ", "").strip()
                    if re.match(r'^[\d,\s]+$', a):
                        allergy_numbers.extend([x.strip() for x in a.split(',') if x.strip()])
                allergy_numbers = list(set(allergy_numbers))
                menu_name_clean = re.sub(r'\([^)]*\)', '', part).strip()
                menu_name_clean = re.sub(r'(₩|KRW|Won|won)?\s*[\d,]+(₩|KRW|Won|won)?', '', menu_name_clean, flags=re.IGNORECASE).strip()
                menu_name_clean = re.sub(r'^\+\s*', '', menu_name_clean)
                menu_name_clean = re.sub(r'\s*\+$', '', menu_name_clean)
                menu_name_clean = re.sub(r'\s+', ' ', menu_name_clean).strip()
                menu_name_clean = menu_name_clean.replace(' KRW', ' ').strip()
                ingredients = []
                for num in allergy_numbers:
                    if num in allergy_map:
                        ingredients.append({'name': allergy_map[num], 'description': ''})
                if price is not None:
                    processed.append({
                        'meal': menu['meal'],
                        'menu_name': menu_name_clean,
                        'description': menu['description'],
                        'ingredients': ingredients,
                        'allergy_numbers': allergy_numbers,
                        'price': price
                    })
                    prev_menu = processed[-1]
                else:
                    if prev_menu:
                        prev_menu['menu_name'] += ' + ' + menu_name_clean
                        existing_names = set(i['name'] for i in prev_menu['ingredients'])
                        for ing in ingredients:
                            if ing['name'] not in existing_names:
                                prev_menu['ingredients'].append(ing)
                                existing_names.add(ing['name'])
                        prev_menu['allergy_numbers'] = list(set(prev_menu['allergy_numbers']) | set(allergy_numbers))
            continue
        processed.append(menu)
    return processed

# ---------------------- Scraping Orchestration ----------------------

MENU_SERVICE_HOST = "menu-service:8000"  # Change as needed for your docker-compose setup
RESTAURANT_ID_MAP = {
    "Undergraduate Cafeteria": 3,
    "West-Campus Student Cafeteria": 11,
    "East-Campus Graduate and Ph.D. Cafeteria": 12,
    "East-Campus Faculty Cafeteria": 15,
    "Faculty Cafeteria": 16,
}

def get_existing_menus(restaurant_id):
    url = f"http://{MENU_SERVICE_HOST}/restaurant/{restaurant_id}/menu"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()

def delete_menu(menu_id):
    url = f"http://{MENU_SERVICE_HOST}/menu/{menu_id}"
    resp = requests.delete(url)
    resp.raise_for_status()

def post_menu(restaurant_id, menu):
    url = f"http://{MENU_SERVICE_HOST}/restaurant/{restaurant_id}/menu"
    payload = {
        "name": menu["menu_name"],
        "description": menu.get("description", ""),
        "main_ingredients": [i["name"] for i in menu.get("ingredients", []) if i.get("name")],
        "price": menu["price"],
    }
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    return resp.json()

def sync_menus_to_service(scraped_data):
    for entry in scraped_data:
        restaurant_name = entry["restaurant_name"]
        restaurant_id = RESTAURANT_ID_MAP.get(restaurant_name)
        if not restaurant_id:
            print(f"Unknown restaurant: {restaurant_name}, skipping...")
            continue
        print(f"Syncing menus for {restaurant_name} (ID: {restaurant_id})...")
        # 1. List all current menus
        try:
            current_menus = get_existing_menus(restaurant_id)
        except Exception as e:
            print(f"Failed to list menus for {restaurant_name}: {e}")
            continue
        # 2. Delete all current menus
        for m in current_menus:
            try:
                delete_menu(m["id"])
            except Exception as e:
                print(f"Failed to delete menu {m['id']}: {e}")
        # 3. Insert all scraped menus
        for menu in entry["menus"]:
            try:
                post_menu(restaurant_id, menu)
            except Exception as e:
                print(f"Failed to insert menu {menu.get('menu_name')}: {e}")

def main():
    """Main entry point: scrape all URLs and sync to menu service API."""
    urls = read_urls('kaist_web_list.txt')
    all_data = []
    for url in urls:
        print(f'Scraping {url}...')
        try:
            data = scrape_kaist_menus(url)
            all_data.append(data)
        except Exception as e:
            print(f'Error scraping {url}: {e}')
    sync_menus_to_service(all_data)
    print('Scraping and sync complete.')

if __name__ == '__main__':
    main()
