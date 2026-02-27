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

- `main.py`: The entry point for the cloning process.
- `services/extractor.py`: Extracts data from the source board.
- `services/builder.py`: Rebuilds the extracted board at the new destination.
- `config.py`: Configuration settings.
- `TRELLO_UI_REFERENCE.md`: Reference for Trello's DOM structure and Playwright selectors.

## Troubleshooting

- **Headless Mode**: If attachments or covers aren't appearing correctly, try running in **Headed mode** (`HEADLESS = False`). Trello's UI sometimes requires a visible window to correctly process sidebar interactions.
- **Timeouts**: For very large boards or slow connections, increase the `TIMEOUT` and `page.wait_for_timeout` values in `services/builder.py`.
- **Authorization**: Ensure `trello_auth.json` is fresh. If you encounter redirects to login, repeat the auth extraction.
