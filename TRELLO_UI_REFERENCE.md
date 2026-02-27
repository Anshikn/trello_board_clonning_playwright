# Trello HTML Structure & Selectors Reference

This document serves as a guide to Trello's DOM structure and key Playwright selectors based on recent cloning automation. Trello frequently uses dynamic classes, so relying on `data-testid`, `aria-label`, placeholder text, and specific icon identifiers is critical for robustness.

## 1. Board & Lists Layout

### Lists
*   **List Container**: `[data-testid="list"]`
*   **List Name/Title**: `[data-testid="list-name"]`
*   **Add Another List Button**: `[data-testid="list-composer-button"]` or `button:has-text("Add another list")`
*   **New List Name Input**: `input[placeholder*="Enter list name"]`

### Cards (on the board view)
*   **Card Container**: `[data-testid="list-card"]`
*   **Card Title**: `[data-testid="card-name"]`
*   **Add a Card Button (at bottom of list)**: `[data-testid="list-add-card-button"]`

## 2. Card Modal (Back of Card)

The main container for an opened card is usually identifiable by the card title area `[data-testid="card-back-name"]`.

### Basic Details
*   **Description Content**: `[data-testid="description-content-area"]`
*   **Comment Input Area**: `[data-testid="card-back-new-comment-input-skeleton"]` -> followed by actual text editor `[data-testid="click-wrapper"]` or tiptap content-editable area.
*   **Save Comment Button**: `[data-testid="card-back-comment-save-button"]`

### Sidebar Buttons (Add to Card)
Trello groups addition actions in the right sidebar. Due to responsiveness or state, these can sometimes be hidden behind an "Add" button menu (`[data-testid="card-back-add-to-card-button"]`).

*   **Labels**: `[data-testid="card-back-labels-button"]` or `button:has-text("Labels")`
*   **Checklist**: `button:has([data-testid="ChecklistIcon"])` or `button:has-text("Checklist")`
*   **Attachment**: `button:has([data-testid="AttachmentIcon"])` or `button:has-text("Attachment")`

---

## 3. Popovers (Crucial Dynamics)

Trello uses a global popover container that floats above the DOM. This makes scoped searches sometimes fail if you only search within the card modal. 
*   **Global Popover Container**: `[data-testid="popover-container"]` or `[role="dialog"]` (specifically the last one in the DOM). ALWAYS scope searches within this container when interacting with popover elements to avoid accidentally clicking global elements (like the main header's "Create board" button).
*   **Popover Close Button**: `[data-testid="popover-close-button"]`. (Avoid pressing "Escape" to close popovers during automation, as it might accidentally close the entire card modal if the popover closed quickly on its own).

### A. Labels Popover
1.  **Search Input**: 
    *   `input[placeholder*="Search labels"]`
    *   `[data-testid="labels-search-input"]`
2.  **Label Selection (Finding an existing label)**:
    *   Search within the popover for: `[data-testid="card-label"]:has-text("Your Label")`
    *   Checkboxes for labels: `[data-testid="clickable-checkbox"]` next to the label span.
3.  **Label Creation (If search yields no exact match)**:
    *   **Create Button**: `button:has-text("Create a new label")`
    *   **Title Input**: The `input[type="text"]` found near `label:has-text("Title")`
    *   **Color Selection**: `button[data-testid="color-tile-{color_val}"]` (e.g., `color-tile-green`. *Note: avoid matching just `data-color="green"` as it might ambiguously click `green_light` or `green_dark` versions.*)
    *   **Submit Button**: `[data-testid="create-label-submit-button"]` or `.locator('[data-testid="popover-container"], [role="dialog"]').last.locator('button').filter(has_text=re.compile(r"^Create$"))`

### B. Checklist Popover
1.  **Add Checklist Confirmation Button**: `[data-testid="checklist-add-button"]`
2.  **Checklist Container (Inside Card)**: `[data-testid="checklist"]`
3.  **Checklist Title**: `[data-testid="checklist-title"]`
4.  **Add Item Input**: `textarea[placeholder="Add an item"]` or `input[placeholder="Add an item"]`
5.  **Individual Checklist Items**: `[data-testid="check-item-container"]`
6.  **Toggling Checklist Checkbox**: `[data-testid="clickable-checkbox"]` or `input[type="checkbox"]` inside the item container.

### C. Attachments Popover
1.  **URL Input (Paste Link)**: `input[placeholder*="Paste any link"]`
2.  **Name Input (Display Text)**: `input#attachmentName`
3.  **Insert/Add Button**: `button:has-text("Insert")` or `button:has-text("Add")` or `[data-testid="attachment-add-submit-button"]`

---

## 4. Header & Board Creation Flow

*   **Global Add Menu Button**: `[data-testid="header-create-menu-button"]`
*   **Create Board Option**: `[data-testid="header-create-board-button"]` or `button:has-text("Create board")`
*   **Board Title Input**: `[data-testid="create-board-title-input"]`
*   **Submit Create Board**: `[data-testid="create-board-submit-button"]`
*   **Board Name Display (To confirm ready state)**: `[data-testid="board-name-display"]`

---

## 5. Playwright Automation Best Practices for Trello
1.  **`force=True` on Clicks**: Trello's heavy use of absolute positioned overlapping layers (Atlantis components) can frequently result in "element intercepts pointer events" errors. Use `click(force=True)` for elements like checkboxes and sidebar buttons.
2.  **Patience with Popovers**: Always `page.wait_for_timeout(500)` or explicitly wait for the `[data-testid="popover-container"]` visibility after clicking a button that should spawn a popover.
3.  **Closing Popovers Safely**: Do not blindly send `page.keyboard.press("Escape")`. Use `[data-testid="popover-close-button"]` instead. If Trello autorenders away a popover, hitting Escape will accidentally close the card modal underneath it.
4.  **Dynamic Rendering of Modals**: Always re-query `.locator()` structures instead of saving locators into memory for long periods, as React re-renders will cause `ElementHandle` or strict locators to go stale.
5.  **Scope Within Active Popover**: Use `page.locator('[data-testid="popover-container"], [role="dialog"]').last` as your parent container when interacting with popover content (e.g., searching for a "Create" or "Add" button). Trello's DOM is large and global searches can accidentally interact with the wrong elements.
