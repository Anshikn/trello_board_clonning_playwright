from utils.retry import retry


def extract_board(page):
    board_data = []

    page.wait_for_selector('[data-testid="list"]')

    list_count = page.locator('[data-testid="list"]').count()

    for i in range(list_count):

        # Re-query list fresh every iteration
        lst = page.locator('[data-testid="list"]').nth(i)

        list_title = lst.locator('[data-testid="list-name"]').inner_text()
        cards_data = []

        card_count = lst.locator('[data-testid="card-name"]').count()

        for j in range(card_count):

            # Re-query card fresh every iteration
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

    card_title = card_locator.text_content().strip() if card_locator.text_content() else ""

    # Open modal via click
    card_locator.click(force=True)

    # Wait for the card back to load
    page.get_by_test_id("card-back-name").wait_for(state="visible", timeout=10000)
    page.wait_for_timeout(1500)  # Give Trello time to render all sections

    # Use card-back-name as the dialog container (it IS the main dialog in Trello)
    dialog = page.get_by_test_id("card-back-name")

    # ---- DESCRIPTION ----
    description = ""
    try:
        desc_block = dialog.locator('[data-testid="description-content-area"]')
        if desc_block.count() > 0:
            description = desc_block.inner_text(timeout=5000).strip()
    except Exception:
        pass

    # ---- LABELS ----
    labels = []
    try:
        # Wait for labels to load if any
        label_container = dialog.locator('[data-testid="card-back-labels-container"]')
        if label_container.count() > 0:
            label_elements = label_container.locator('[data-testid="card-label"]')
            for l in range(label_elements.count()):
                el = label_elements.nth(l)
                name = el.inner_text().strip()
                color = el.get_attribute("data-color") or ""
                if name:
                    labels.append({"name": name, "color": color})
    except Exception:
        pass

    # ---- CHECKLIST ----
    checklist_items = []
    try:
        checklist_title = ""
        cl_title = dialog.locator('[data-testid="checklist-title"]')
        if cl_title.count() > 0:
            checklist_title = cl_title.inner_text().strip()

        items = dialog.locator('[data-testid="check-item-container"]')
        for k in range(items.count()):
            item = items.nth(k)
            # The checklist item text is in the aria-label of the checkbox input
            checkbox = item.locator('[data-testid="clickable-checkbox"] input[type="checkbox"]')
            if checkbox.count() > 0:
                item_name = checkbox.get_attribute("aria-label") or ""
                is_checked = checkbox.get_attribute("aria-checked") == "true"
                checklist_items.append({
                    "name": item_name,
                    "checked": is_checked
                })
    except Exception:
        pass

    # ---- DUE DATE ----
    due_date = ""
    try:
        due = dialog.locator('[data-testid="due-date-badge"]')
        if due.count() > 0:
            due_date = due.inner_text().strip()
    except Exception:
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
                
                # Check if this specific attachment is the cover
                # Trello adds a "Cover" badge to the thumbnail in the list
                is_cover = el.locator('..').locator('text="Cover"').count() > 0
                
                if url:
                    attachments.append({
                        "name": name, 
                        "url": url,
                        "is_cover": is_cover
                    })
    except Exception:
        pass

    # ---- COVER (Directly from header) ----
    cover = None
    try:
        # Trello covers are in card-back-cover section
        cover_container = page.locator('[data-testid="card-back-cover-container"]')
        if cover_container.count() == 0:
            cover_container = page.locator('[data-testid="card-cover"]')
            
        if cover_container.count() > 0:
            style = cover_container.get_attribute("style") or ""
            if "background-image" in style:
                cover = {"type": "image", "style": style}
            else:
                color = cover_container.get_attribute("data-color")
                if not color:
                    # Look for child with color
                    child_color = cover_container.locator('[data-color]').first
                    if child_color.count() > 0:
                        color = child_color.get_attribute("data-color")
                
                if color:
                    cover = {"type": "color", "value": color}
                else:
                    cover = {"type": "color", "style": style}
    except Exception:
        pass

    # ---- COMMENTS ----
    comments = []
    try:
        comment_elements = dialog.locator('[data-testid="comment-container"]')
        for k in range(comment_elements.count()):
            comment_text = comment_elements.nth(k).inner_text().strip()
            if comment_text:
                comments.append(comment_text)
    except Exception:
        pass

    # Close modal
    close_btn = page.locator('[aria-label="Close dialog"]')
    if close_btn.count() > 0:
        close_btn.click()
    else:
        page.keyboard.press("Escape")

    # Wait for the dialog to fully close
    page.get_by_test_id("card-back-name").wait_for(state="hidden", timeout=10000)

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
