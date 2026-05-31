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
*   **Card Composer Textarea**: `[data-testid="list-card-composer-textarea"]`
*   **Composer Add Button**: `[data-testid="list-card-composer-add-card-button"]`

---

## 2. Card Modal (Back of Card)

The main container for an opened card is usually identifiable by the card title area `[data-testid="card-back-name"]`.

### Basic Details
*   **Description Area**: `[data-testid="description-content-area"]`
*   **Description Edit Trigger**: `[data-testid="description-edit-button"]` or `[data-testid="click-wrapper"]` (for new cards).
*   **Rich Text Editor**: `[role="textbox"]` (ProseMirror based).
*   **Description Save Button**: `[data-testid="description-save-button"]`
*   **Comment Input Area**: `[data-testid="card-back-new-comment-input-skeleton"]` -> followed by actual text editor `[role="textbox"]`.
*   **Save Comment Button**: `[data-testid="card-back-comment-save-button"]`

### Sidebar Buttons (Add to Card)
Trello groups addition actions in the right sidebar. Due to responsiveness or state, these can sometimes be hidden behind an "Add" button menu (`[data-testid="card-back-add-to-card-button"]`).

*   **Labels**: `[data-testid="card-back-labels-button"]` or `button:has-text("Labels")`
*   **Checklist**: `button:has([data-testid="ChecklistIcon"])` or `button:has-text("Checklist")`
*   **Attachment**: `button:has([data-testid="AttachmentIcon"])` or `button:has-text("Attachment")`
*   **Cover**: `[data-testid="card-back-cover-button"]` or `button:has-text("Cover")`

---

## 3. Popovers (Crucial Dynamics)

Trello uses a global popover container that floats above the DOM. This makes scoped searches sometimes fail if you only search within the card modal. 
*   **Global Popover Container**: `[data-testid="popover-container"]` or `[role="dialog"]`. Always use `.last` to target the active one.
*   **Popover Close Button**: `[data-testid="popover-close-button"]`. 

### A. Labels Popover
1.  **Search Input**: `input[placeholder*="Search labels"]`
2.  **Label Selection (Finding an existing label)**:
    *   **Selector**: `popover.locator('[data-testid="card-label"]').filter(has_text=re.compile(f'^{re.escape(label_name)}$'))`
    *   **Selection Check**: Look for `[data-testid="card-label-checkmark"]` or `svg[data-testid="CheckIcon"]` to avoid toggling OFF.
3.  **Label Creation**:
    *   **Create Button**: `button:has-text("Create a new label")`
    *   **Name Input**: `popover.locator('input').first`
    *   **Color Selection**: `button[data-testid="color-tile-{color_val}"]` (e.g., `green`, `yellow`, `orange`).
    *   **Submit Button**: `popover.locator('button').filter(has_text=re.compile(r"^Create$"))`

### B. Checklist Popover
1.  **Add Checklist Confirmation**: `popover.locator('button').filter(has_text=re.compile(r"^(Add|Create)$"))`
2.  **Add Item Input**: `textarea[placeholder="Add an item"]` or `page.get_by_placeholder("Add an item")`.
3.  **Toggling Checklist Checkbox**: `[data-testid="clickable-checkbox"]` or `input[type="checkbox"]` inside `[data-testid="check-item-container"]`.

### C. Members Popover
1.  **Trigger**: `[data-testid="card-back-members-button"]` or `button:has-text("Members")`.
2.  **Assigned Members (on card)**: Found in `[data-testid="card-back-members-container"]`.
3.  **Member Identification (Heuristic)**: Members are identifiable by `button[title]` where the title contains a username in parentheses, e.g., `Name (username)`.
4.  **Search Input**: `[role="textbox"][name="Search members"]` or `input[placeholder*="Search"]`.
5.  **Selection**: Typing the name and clicking the result or pressing `Enter`.

### D. Dates Popover
1.  **Trigger**: `button:has-text("Dates")` or clicking the existing date badge/button.
2.  **Date Input**: `input[data-testid="due-date-field"]` or the first input with a date placeholder.
3.  **Date Format Requirement**: Trello's UI input typically expects `DD/MM/YYYY` (or `MM/DD/YYYY` depending on user locale, but `DD/MM/YYYY` is a safe target for consistent parsing).
4.  **Time Input**: `input[placeholder*="time"]`.
5.  **Save Button**: `[data-testid="save-date-button"]`, `button:has-text("Save")`, or `button[type="submit"]`.
6.  **Verification**: The badge should update with the selected date and time.

### E. Attachments Popover
Trello now supports both URL pasting and local file uploads.

1.  **Local File Upload**:
    *   **Trigger**: `page.get_by_role("button", name="Choose a file")`
    *   **Action**: Use `expect_file_chooser` logic.
    *   **Fallback**: `input[type="file"]` (hidden).
2.  **URL Input (Paste Link)**: `input[placeholder*="Paste any link"]`
3.  **Insert/Add Button**: `button:has-text("Insert")` or `button:has-text("Add")`
4.  **Verification**: Wait for `[data-testid="attachment-list"]` to contain text matching the filename.

### F. Cover Popover
1.  **Color Selections**: `button[data-color="{color_val}"]`
2.  **Image Selections (From Attachments)**: 
    *   **Select Item**: `[data-testid="cover-attachment-item"]`
    *   **Fallback**: `button[style*="background-image"]`.

---

## 4. Header & Board Creation Flow

*   **Global Add Menu Button**: `[data-testid="header-create-menu-button"]`
*   **Create Board Option**: `[data-testid="header-create-board-button"]`
*   **Board Title Input**: `[data-testid="create-board-title-input"]`
*   **Submit Create Board**: `[data-testid="create-board-submit-button"]`
*   **Board Name Display**: `[data-testid="board-name-display"]`

---

## 5. Playwright Automation Best Practices for Trello

1.  **`force=True` on Clicks**: Essential for Trello's overlapping layers.
2.  **Strict Text Matching**: When selecting labels, use regex `^Name$` to avoid selecting "Status Done" when searching for "Done".
3.  **File Upload Handling**: Always use `page.expect_file_chooser()` for the "Choose a file" button to handle the OS native dialog.
4.  **Patience with Popovers**: Use `page.wait_for_timeout(800)` after clicking menu buttons.
5.  **Attachment Processing**: When uploading, wait for the thumbnail to appear in the card (`[data-testid="attachment-list"]`) before continuing or setting it as a cover.
6.  **Avoid Escape Key**: Closing popovers with Escape can accidentally close the card modal. Use `[data-testid="popover-close-button"]` or click the card header area to dismiss.
7.  **Scope Within Active Popover**: Always use `page.locator('[data-testid="popover-container"], [role="dialog"]').last` as the parent for popover interactions.
