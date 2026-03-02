from utils.retry import retry
import os


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

    # ---- DUE DATE ----
    due_date = ""
    try:
        due = dialog.locator('[data-testid="due-date-badge"]')
        if due.count() > 0:
            due_date = due.inner_text().strip()
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
        "checklist": checklist_items,
        "due_date": due_date,
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
