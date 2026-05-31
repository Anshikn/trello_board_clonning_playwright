# Trello Board Cloner

Automated tool to clone Trello boards using Playwright and Python.

## Features

- **Full Board Extraction**: Extracts lists, cards, descriptions, labels, checklists, and comments.
- **Attachment Cloning**: Automatically transfers URL-based attachments from the source to the destination board.
- **Cover Photo Cloning**: Supports cloning card cover colors and images.
- **Smart Label Handling**: Matches existing labels by name or creates them if missing.
- **Retry Logic**: Robust handling of Trello's dynamic UI with automatic retries on interaction failures.

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Authentication**:
   The tool requires a `trello_auth.json` file containing your Playwright storage state (cookies/auth). 
   - You can generate this by logging into Trello in a browser and saving the state.

3. **Configuration**:
   Edit `config.py` to specify your source board and destination settings:
   ```python
   SOURCE_BOARD_URL = "https://trello.com/b/your-source-board"
   NEW_BOARD_NAME = "My Cloned Board"
   HEADLESS = False  # Recommendation: Keep False to monitor attachment uploads
   TIMEOUT = 60000
   ```

## Usage

Run the main script:
```bash
python main.py
```

## Project Structure

### Core Logic
- `main.py`: The main entry point that orchestrates the extraction and rebuilding process.
- `services/extractor.py`: Handles navigation to the source board and extracting card details (labels, members, dates, etc.).
- `services/builder.py`: Implements the logic to create a new board and populate it with the extracted data.
- `utils/retry.py`: A utility decorator used throughout the project to handle flakiness in Trello's dynamic UI.

### Data & Configuration
- `config.py`: Central configuration for board URLs, names, and headless mode settings.
- `trello_auth.json`: Stores authentication state (cookies/localStorage) to bypass manual login.
- `data/board_data.json`: The intermediate JSON file generated after extraction, containing all board details.
- `data/attachments/`: Local directory where card attachments are temporarily downloaded during extraction.

### Auxiliary & Debugging Tools
- `reauth.py`: A helper script to launch a browser, allow you to log in manually, and save the session to `trello_auth.json`.
- `codegen.py`: Used with Playwright's code generation tool to inspect Trello's latest selectors.
- `debug_*.py` / `dump_*.py`: A collection of focused scripts used to troubleshoot specific UI components (e.g., labels, covers, dates).
- `*.html` / `*.png`: Snapshots and HTML dumps of the Trello UI captured during development or execution failures for selector analysis.

### Documentation
- `TRELLO_UI_REFERENCE.md`: A comprehensive guide to Trello's DOM structure, including the specific `data-testid` and `aria-label` selectors used in this project.

## Troubleshooting

- **Headless Mode**: If attachments or covers aren't appearing correctly, try running in **Headed mode** (`HEADLESS = False`). Trello's UI sometimes requires a visible window to correctly process sidebar interactions.
- **Timeouts**: For very large boards or slow connections, increase the `TIMEOUT` and `page.wait_for_timeout` values in `services/builder.py`.
- **Authorization**: Ensure `trello_auth.json` is fresh. If you encounter redirects to login, repeat the auth extraction.
