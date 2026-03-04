from utils.retry import retry
import os
import re
import datetime


def get_month_number(month_str):
    """Converts month name or abbreviation to month number."""
    months = {
        'jan': 1, 'january': 1,
        'feb': 2, 'february': 2,
        'mar': 3, 'march': 3,
        'apr': 4, 'april': 4,
        'may': 5,
        'jun': 6, 'june': 6,
        'jul': 7, 'july': 7,
        'aug': 8, 'august': 8,
        'sep': 9, 'september': 9,
        'oct': 10, 'october': 10,
        'nov': 11, 'november': 11,
        'dec': 12, 'december': 12
    }
    return months.get(month_str.lower()[:3])


def parse_trello_date(date_str):
    """Parses Trello date strings (like '2 Mar, 10:18' or 'Mar 4') to DD/MM/YYYY."""
    if not date_str:
        return ""
    
    try:
        # Example: '2 Mar, 10:18' or '2 Mar'
        # Remove extra text like status
        clean_str = date_str.split('\n')[0].split(',')[0].strip()
        
        # Look for Day and Month
        # Pattern: '2 Mar' or 'Mar 4' or '02/03/2026'
        if re.match(r'^\d+/\d+/\d+$', clean_str):
            return clean_str
            
        match = re.search(r'(\d+)\s+([A-Za-z]+)', clean_str)
        if match:
            day = int(match.group(1))
            month = get_month_number(match.group(2))
        else:
            match = re.search(r'([A-Za-z]+)\s+(\d+)', clean_str)
            if match:
                month = get_month_number(match.group(1))
                day = int(match.group(2))
            else:
                return clean_str

        # If we have month and day, assume current year unless year is present
        year = datetime.datetime.now().year
        year_match = re.search(r'\b(20\d{2})\b', date_str)
        if year_match:
            year = int(year_match.group(1))
            
        if day and month:
            return f"{day:02d}/{month:02d}/{year}"
            
    except:
        pass
    return date_str


def extract_board(page):
    """Extracts all lists and cards from the current board."""
    board_data = []
    page.wait_for_selector('[data-testid="list"]')

    list_count = page.locator('[data-testid="list"]').count()

    for i in range(list_count):
        lst = page.locator('[data-testid="list"]').nth(i)
        list_title = lst.locator('[data-testid="list-name"]').inner_text()
        cards_data = []

        card_count = lst.locator('[data-testid="card-name"]').count()
        for j in range(card_count):
            card = page.locator('[data-testid="list"]').nth(i) \
                        .locator('[data-testid="card-name"]').nth(j)
            card_data = extract_card(page, card)
            cards_data.append(card_data)

        board_data.append({
            "list_title": list_title,
            "cards": cards_data
        })

    return board_data


@retry(times=3, delay=2)
def extract_card(page, card_locator):
    """Opens a card modal, extracts all data, then closes it."""
    card_title = card_locator.text_content().strip() if card_locator.text_content() else ""
    print(f"  Extracting card: {card_title}")

    # Open modal
    card_locator.click(force=True)

    # Wait for the modal — the dialog root has data-testid="card-back-name"
    dialog = page.locator('[data-testid="card-back-name"]')
    dialog.wait_for(state="visible", timeout=10000)
    page.wait_for_timeout(1500)  # Let sections load

    # ---- DESCRIPTION ----
    description = ""
    try:
        desc_block = dialog.locator('[data-testid="description-content-area"]')
        if desc_block.count() > 0:
            description = desc_block.inner_text(timeout=5000).strip()
    except:
        pass

    # ---- LABELS ----
    labels = []
    try:
        label_container = dialog.locator('[data-testid="card-back-labels-container"]')
        if label_container.count() > 0:
            label_elements = label_container.locator('[data-testid="card-label"]')
            for l in range(label_elements.count()):
                el = label_elements.nth(l)
                name = el.inner_text().strip()
                color = el.get_attribute("data-color") or ""
                if name:
                    labels.append({"name": name, "color": color})
    except:
        pass

    # ---- CHECKLIST ----
    checklist_items = []
    try:
        items = dialog.locator('[data-testid="check-item-container"]')
        for k in range(items.count()):
            item = items.nth(k)
            item_name = ""

            # Get name from checkbox aria-label
            checkbox = item.locator('input[type="checkbox"]')
            if checkbox.count() > 0:
                item_name = checkbox.get_attribute("aria-label") or ""

            # Fallback to visible text
            if not item_name:
                item_name = item.inner_text().strip()

            is_checked = False
            if checkbox.count() > 0:
                is_checked = checkbox.get_attribute("aria-checked") == "true"

            if item_name:
                checklist_items.append({"name": item_name, "checked": is_checked})
    except:
        pass

    # ---- MEMBERS ----
    members = []
    try:
        # Assigned members in Trello are strictly in this container
        container = dialog.locator('[data-testid="card-back-members-container"]')
        if container.count() > 0:
            member_elements = container.locator('[data-testid="member-avatar"], button[title]').all()
            for el in member_elements:
                title = el.get_attribute("title") or el.get_attribute("aria-label") or ""
                # Heuristic: Assigned member titles always have (username)
                if title and "(" in title and ")" in title:
                    name = title.split("(")[0].strip()
                    if name and name not in members and name != "Members":
                        members.append(name)
        
        # Backup: Search for a header labeled "Members" but only look in its immediate sibling
        if not members:
            header = dialog.locator('h3').filter(has_text=re.compile(r"^Members$", re.I)).first
            if header.count() > 0:
                parent = header.locator('xpath=..')
                member_elements = parent.locator('button[title]').all()
                for el in member_elements:
                    title = el.get_attribute("title") or ""
                    if title and "(" in title and ")" in title:
                        name = title.split("(")[0].strip()
                        if name and name not in members:
                            members.append(name)
    except:
        pass

    # ---- DATE (Extracted and parsed to DD/MM/YYYY) ----
    manual_date = ""
    try:
        # Look for the header "Due date" or "Date"
        date_header = dialog.locator('h3').filter(has_text=re.compile(r"^(Due date|Date)$", re.I)).first
        if date_header.count() > 0:
            parent = date_header.locator('xpath=..')
            inner = parent.inner_text().replace(date_header.inner_text(), "").strip()
            # The first line is the date string
            date_str = inner.split('\n')[0].strip()
            # If it has a comma, the part before it is the date, after is time
            raw_date = date_str.split(',')[0].strip()
            raw_time = date_str.split(',')[1].strip() if ',' in date_str else ""
            
            parsed_d = parse_trello_date(raw_date)
            if parsed_d:
                manual_date = f"{parsed_d}, {raw_time}" if raw_time else parsed_d
    except:
        pass

    # ---- CUSTOM FIELDS (Power-ups) ----
    custom_fields = {}
    try:
        cf_items = dialog.locator('[data-testid="custom-field-item"]')
        for c in range(cf_items.count()):
            item = cf_items.nth(c)
            label_el = item.locator('[data-testid="custom-field-item-label"]')
            value_el = item.locator('[data-testid="custom-field-item-value"]')
            if label_el.count() > 0 and value_el.count() > 0:
                label = label_el.inner_text().strip()
                value = value_el.inner_text().strip()
                custom_fields[label] = value
    except:
        pass

    # ---- ATTACHMENTS ----
    attachments = []
    try:
        att_section = dialog.locator('[data-testid="attachment-list"]')
        if att_section.count() > 0:
            att_elements = att_section.locator('[data-testid="attachment-thumbnail"]')
            for a in range(att_elements.count()):
                el = att_elements.nth(a)
                url = el.get_attribute("href") or ""
                name_el = el.locator('..').locator('[data-testid="attachment-thumbnail-name"]')
                name = name_el.inner_text().strip() if name_el.count() > 0 else ""
                is_cover = el.locator('..').locator('text="Cover"').count() > 0

                if url:
                    print(f"    - Downloading: {name}...")
                    local_path = download_attachment(page, url, name)
                    attachments.append({
                        "name": name,
                        "url": url,
                        "is_cover": is_cover,
                        "local_path": local_path
                    })
    except Exception as e:
        print(f"    Warning: Attachments extraction error: {e}")

    # ---- COVER ----
    cover = None
    try:
        cover_container = page.locator('[data-testid="card-cover"]')
        if cover_container.count() > 0:
            style = cover_container.get_attribute("style") or ""
            if "background-image" in style:
                cover = {"type": "image", "style": style}
            else:
                color = cover_container.get_attribute("data-color")
                if color:
                    cover = {"type": "color", "value": color}
    except:
        pass

    # ---- COMMENTS ----
    comments = []
    try:
        comment_elements = dialog.locator('[data-testid="comment-container"]')
        for k in range(comment_elements.count()):
            comment_text = comment_elements.nth(k).inner_text().strip()
            if comment_text:
                comments.append(comment_text)
    except:
        pass

    # Close modal
    close_btn = page.locator('button[aria-label="Close dialog"]')
    if close_btn.count() > 0 and close_btn.first.is_visible():
        close_btn.first.click(force=True)
    else:
        page.keyboard.press("Escape")

    try:
        dialog.wait_for(state="hidden", timeout=5000)
    except:
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

    return {
        "title": card_title,
        "description": description,
        "labels": labels,
        "members": members,
        "Date": manual_date,
        "custom_fields": custom_fields,
        "checklist": checklist_items,
        "attachments": attachments,
        "cover": cover,
        "comments": comments
    }


def download_attachment(page, url, name):
    """Downloads an attachment using the browser's authenticated session."""
    if not url or "trello.com" not in url:
        return None

    try:
        os.makedirs("data/attachments", exist_ok=True)
        safe_name = "".join([c for c in name if c.isalnum() or c in "._- "]).strip()
        if not safe_name:
            import hashlib
            safe_name = "att_" + hashlib.md5(url.encode()).hexdigest()[:8]

        file_path = os.path.abspath(f"data/attachments/{safe_name}")

        response = page.request.get(url)
        if response.status == 200:
            with open(file_path, "wb") as f:
                f.write(response.body())
            return file_path
        else:
            print(f"      × Download failed: status {response.status}")
    except Exception as e:
        print(f"      × Download error: {e}")

    return None
