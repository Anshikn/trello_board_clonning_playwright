import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://trello.com/")
    page.get_by_test_id("list-name-textarea").click()
    page.get_by_test_id("list-name-textarea").fill("List-name")
    page.get_by_test_id("list-composer-add-list-button").click()
    page.get_by_test_id("list-add-card-button").click()
    page.get_by_test_id("list-card-composer-textarea").fill("card-title")
    page.get_by_test_id("list-card-composer-add-card-button").click()
    page.get_by_test_id("card-name").click()
    page.get_by_test_id("description-button").click()
    page.get_by_test_id("card-back-title-input").click()
    page.get_by_test_id("card-back-title-input").click()
    page.get_by_test_id("editor-content-container").get_by_role("paragraph").click()
    page.get_by_role("textbox", name="Description").fill("description")
    page.get_by_test_id("description-save-button").click()
    page.get_by_role("button", name="Labels").click()
    page.get_by_role("textbox", name="Search labels…").fill("labels")
    page.get_by_role("button", name="Create a new label").click()
    page.get_by_test_id("color-tile-green").click()
    page.get_by_test_id("labels-popover-create-label-screen").get_by_role("button", name="Create").click()
    page.get_by_role("button", name="Close popover").click()
    page.get_by_role("button", name="Checklist").click()
    page.get_by_role("textbox", name="Title", exact=True).fill("checklist")
    page.get_by_test_id("checklist-add-button").click()
    page.get_by_test_id("check-item-name-input").fill("item-1")
    page.get_by_test_id("check-item-add-button").click()
    page.get_by_test_id("check-item-name-input").fill("item2")
    page.get_by_test_id("check-item-add-button").click()
    page.locator("li:nth-child(2) > .YkivUYixygZz1r > .QAbIzaY_2ICVlA > .I1mTB4BD1hFm9_ > .ZAcH7Pr9TT7uUR > svg").click()
    page.get_by_test_id("card-back-new-comment-input-skeleton").click()
    page.get_by_role("textbox", name="Main content area, start").fill("comment")
    page.get_by_test_id("card-back-comment-save-button").click()
    page.get_by_role("button", name="Attachment").click()
    page.get_by_role("button", name="Choose a file").click()
    page.get_by_role("button", name="Choose a file").set_input_files("Click Link in Bio - iPad wallpaper ideas.jpeg")

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
