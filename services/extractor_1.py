from utils.retry import retry

def extract_board(page):
    board_data = []

    lists = page.locator('[data-testid="list"]').all()

    for lst in lists:
        list_title = lst.locator('[data-testid="list-name"]').inner_text()
        cards_data = []

        cards = lst.locator('[data-testid="card-name"]').all()

        for card in cards:
            card_data = extract_card_data(page, card)
            cards_data.append(card_data)

        board_data.append({
            "list_title": list_title,
            "cards": cards_data
        })

    return board_data


@retry(times=3, delay=2)
def extract_card(page, card_locator):
    card_title = card_locator.inner_text()
    card_locator.evaluate("(el) => el.click()")


    # page.wait_for_selector('[data-testid="card-back-title"]')
    page.wait_for_url("**/c/**")
    page.wait_for_selector('[role="dialog"]')


    description = ""
    if page.locator('[data-testid="card-back-description"]').count() > 0:
        description = page.locator(
            '[data-testid="card-back-description"]'
        ).inner_text()

    labels = page.locator('[data-testid="card-label"]').all_inner_texts()
    checklist_items = page.locator(
        '[data-testid="checklist-item"]'
    ).all_inner_texts()

    # Due date
    due_date = ""
    if page.locator('[data-testid="due-date-badge"]').count() > 0:
        due_date = page.locator(
            '[data-testid="due-date-badge"]'
        ).inner_text()

    # Attachment URLs
    attachments = page.locator(
        '[data-testid="attachment-name"]'
    ).all_inner_texts()

    page.get_by_label("Close dialog").click()
    page.wait_for_timeout(500)

    return {
        "title": card_title,
        "description": description,
        "labels": labels,
        "checklist": checklist_items,
        "due_date": due_date,
        "attachments": attachments
    }

@retry(times=3, delay=2)
def extract_card_data(page, card_locator):

    card_data = {
        "title": "",
        "description": "",
        "labels": [],
        "checklist": [],
        "due_date": "",
        "attachments": []
    }

    # Open card via href (stable method)
    href = card_locator.get_attribute("href")
    page.goto("https://trello.com" + href)

    # Wait for modal
    page.wait_for_url("**/c/**")
    dialog = page.locator('[role="dialog"]')
    dialog.wait_for()

    # ---- TITLE ----
    card_data["title"] = dialog.get_by_role("heading").first.inner_text()

    # ---- DESCRIPTION ----
    description_block = dialog.locator('[data-testid="card-back-description"]')
    if description_block.count() > 0:
        card_data["description"] = description_block.inner_text().strip()

    # ---- LABELS ----
    labels = dialog.locator('[data-testid="card-label"]')
    for i in range(labels.count()):
        card_data["labels"].append(labels.nth(i).inner_text())

    # ---- CHECKLIST ----
    checklist_items = dialog.locator('[data-testid="checklist-item"]')
    for i in range(checklist_items.count()):
        card_data["checklist"].append(checklist_items.nth(i).inner_text())

    # ---- DUE DATE ----
    due = dialog.locator('[data-testid="due-date-badge"]')
    if due.count() > 0:
        card_data["due_date"] = due.inner_text()

    # ---- ATTACHMENTS ----
    attachments = dialog.locator('[data-testid="attachment-link"]')
    for i in range(attachments.count()):
        card_data["attachments"].append(
            attachments.nth(i).get_attribute("href")
        )

    # Close modal
    page.keyboard.press("Escape")
    page.wait_for_url("**/b/**")

    return card_data
