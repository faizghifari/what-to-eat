import re
from typing import List, Dict, Any
from auto_update.extract_helpers import split_menu_by_br

def extract_menus(soup, allergy_map: Dict[str, str], restaurant_name: str) -> List[Dict[str, Any]]:
    menus = []
    table = soup.select_one('div#tab_item_1 table')
    if not table:
        return menus
    tds = table.select('tbody tr td')
    meal_types = ['breakfast', 'lunch', 'dinner']
    for idx, td in enumerate(tds):
        meal = meal_types[idx] if idx < len(meal_types) else f'meal_{idx}'
        menu_items = split_menu_by_br(td)
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
                'main_ingredients': ingredients,
                'price': price
            })
    return menus

def postprocess_cafeteria_menus(menus: List[Dict[str, Any]], allergy_map: Dict[str, str]) -> List[Dict[str, Any]]:
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
                        'main_ingredients': ingredients,
                        'price': price
                    })
                    prev_menu = processed[-1]
                else:
                    if prev_menu:
                        prev_menu['menu_name'] += ' + ' + menu_name_clean
                        existing_names = set(i['name'] for i in prev_menu['main_ingredients'])
                        for ing in ingredients:
                            if ing['name'] not in existing_names:
                                prev_menu['main_ingredients'].append(ing)
                                existing_names.add(ing['name'])
            continue
        processed.append(menu)
    return processed
