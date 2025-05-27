import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup


def extract_restaurant_name(soup: BeautifulSoup) -> str:
    h3 = soup.select_one("div#tab_item_1 h3")
    if not h3:
        return None
    match = re.search(r"\[(.*?)\]", h3.text)
    if match:
        name = match.group(1)
        name = re.sub(r"\([^)]*\)", "", name).strip()
        return name
    return None


def extract_allergy_mapping(soup: BeautifulSoup) -> Dict[str, str]:
    allergy_map = {}
    p = soup.select_one("div#tab_item_1 p")
    if not p:
        return allergy_map
    text = p.get_text(separator=" ").replace("\n", " ").replace("\r", " ").strip()
    bracket_match = re.search(r"\[(.*?)\]", text)
    mapping_str = None
    if bracket_match:
        mapping_str = bracket_match.group(1)
    else:
        mapping_match = re.search(r"((?:\d+\.?\s*[^\d]+[\/\,]?\s*){5,})", text)
        if mapping_match:
            mapping_str = mapping_match.group(1)
        else:
            mapping_str = text
    matches = re.findall(
        r"(\d+)\.?\s*([A-Za-z\uAC00-\uD7A3][A-Za-z\uAC00-\uD7A3\s\-]*?)(?:\s*\([^)]*\))?(?=\s*[\/\,]|\s+\d+\.?|$)",
        mapping_str,
    )
    for num, allergy in matches:
        allergy_map[num] = allergy.strip(" -").replace("  ", " ").lower()
    if not allergy_map:
        text = text.lower().split("allergy")[-1].strip()
        pattern = r"(\d+).\s*([^/]+)"
        allergy_mapping = {
            int(num): name.strip().lower() for num, name in re.findall(pattern, text)
        }
        for num, allergy in allergy_mapping.items():
            allergy_map[str(num)] = allergy.strip(" -").replace("  ", " ").lower()
    return allergy_map


def split_menu_by_br(td) -> List[str]:
    html = str(td)
    html = re.sub(r"^<td[^>]*>", "", html)
    html = re.sub(r"</td>$", "", html)
    menu_chunks = re.split(
        r"<br\s*/?>\s*(?:\r?\n)?\s*<br\s*/?>", html, flags=re.IGNORECASE
    )
    items = []
    for chunk in menu_chunks:
        text = BeautifulSoup(chunk, "html.parser").get_text(separator=" ").strip()
        if text:
            items.append(text)
    return items
