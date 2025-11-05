# BGG.CON Badge & Game Availability Checker

A Python program that monitors BGG.CON badge and game availability from the tabletop.events API. The program can run in two modes:

- **Badge Mode** (default): Monitors badge availability and sends Discord notifications when badges become available or sell out
- **Game Mode**: Monitors game availability from the convention library, reads a watchlist from Google Sheets, and updates a spreadsheet with current game states

## Features

- Real-time monitoring of badge availability with Discord notifications
- Game availability tracking with Google Sheets integration
- Automatic spreadsheet updates with game checkout status and timestamps
- Configurable polling intervals with exponential backoff on errors
- Docker support for easy deployment

## Prerequisites

- Python 3.7 or higher
- Discord webhook URL (for notifications)
- Google Cloud Project with Sheets API enabled (for game mode)
- Google OAuth credentials file (`credentials.json`)

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd bgg-tickets
```

### 2. Install Python dependencies

Create a virtual environment (recommended):

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install the required packages:

```bash
pip install -r requirements.txt
```

### 3. Set up Google Sheets API (for game mode only)

If you plan to use game mode, you need to set up Google Sheets API access:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Sheets API
4. Create OAuth 2.0 credentials (Desktop application type)
5. Download the credentials file and save it as `credentials.json` in the project root (or set `GOOGLE_CREDENTIALS_FILE` environment variable to a custom path)
6. The first time you run the program, it will open a browser window for authentication and create `token.json` in the project root (or at the path specified by `GOOGLE_TOKEN_FILE`)

### 4. Configure Discord webhook

Set the `WEBHOOK_URL` environment variable to your Discord webhook URL:

```bash
export WEBHOOK_URL="https://discord.com/api/webhooks/YOUR_WEBHOOK_URL"
```

**Note**: For security, do not hardcode the webhook URL in the code. Always use environment variables.

## Usage

### Badge Mode (Default)

Monitors badge availability and sends Discord notifications:

```bash
python bgg.py
```

The program will:
- Poll the tabletop.events API every 10 seconds
- Send a Discord notification when badges become available
- Send updates when availability changes
- Send periodic status updates every 3 hours

### Game Mode

Monitor game availability from the convention library:

```bash
export BGG_GAME_MODE=true
python bgg.py
```

Game mode requires:
- A Google Sheets spreadsheet with a "Watchlist" sheet containing game names in column A (starting from row 2)
- The spreadsheet ID and range are configured in `bgg.py` (lines 39-40)
- The program will:
  - Read the watchlist from Google Sheets
  - Check availability for each game
  - Update a "Data" sheet with current game states (available, last check-in/out time, time delta)
  - Send Discord notifications when games become available or are checked out

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `WEBHOOK_URL` | Discord webhook URL for notifications | Required |
| `BGG_GAME_MODE` | Enable game mode (`true` or `false`) | `false` |
| `BGG_DEBUG` | Enable debug mode | `false` |
| `BGG_WATCHLIST` | Comma-separated list of games (alternative to Google Sheets) | Empty |
| `GOOGLE_CREDENTIALS_FILE` | Path to Google OAuth credentials file | `credentials.json` |
| `GOOGLE_TOKEN_FILE` | Path to Google OAuth token file | `token.json` |
| `BGG_CONVENTION_UUID` | UUID of the convention to monitor (badge mode) | `C50E2390-C43D-11ED-AB2B-20397E91607B` |
| `BGG_LIBRARY_UUID` | UUID of the library to monitor (game mode) | `0AEB11DA-2B7D-11EC-B400-855F800FD618` |
| `BGG_SPREADSHEET_ID` | Google Sheets spreadsheet ID (game mode) | `17ZW0hl3x2A56zrWRH67SZOraqAYSTWSPNnpXWJF1CEg` |
| `BGG_WATCHLIST_RANGE` | Range in spreadsheet for watchlist (game mode) | `Watchlist!A2:A` |
| `BGG_SPREADSHEET_DATA_RANGE` | Range in spreadsheet for game data (game mode) | `Data!A2:D1000` |
| `BGG_SPREADSHEET_TIMESTAMP_RANGE` | Range in spreadsheet for timestamp (game mode) | `Data!F1` |
| `BGG_HTTP_TIMEOUT` | HTTP request timeout in seconds | `10` |
| `BGG_BADGE_POLL_INTERVAL` | Badge polling interval in seconds | `10` |
| `BGG_GAME_POLL_INTERVAL` | Game polling interval in seconds (also initial backoff) | `10` |
| `BGG_BADGE_STATUS_UPDATE_INTERVAL` | Interval between status updates in badge mode (seconds) | `10800` (3 hours) |
| `BGG_GAME_MAX_BACKOFF` | Maximum backoff time for game mode on errors (seconds) | `300` (5 minutes) |

### Docker Usage

Build the Docker image:

```bash
docker build -t bgg-tickets .
```

Run the container:

```bash
docker run -d \
  -e WEBHOOK_URL="https://discord.com/api/webhooks/YOUR_WEBHOOK_URL" \
  -e BGG_GAME_MODE=true \
  -e BGG_CONVENTION_UUID="YOUR_CONVENTION_UUID" \
  -e BGG_LIBRARY_UUID="YOUR_LIBRARY_UUID" \
  -e BGG_SPREADSHEET_ID="YOUR_SPREADSHEET_ID" \
  -v $(pwd)/credentials.json:/app/credentials.json \
  -v $(pwd)/token.json:/app/token.json \
  --name bgg-tickets \
  bgg-tickets
```

**Note**: 
- Only include the environment variables you need to override. The defaults will work for the original BGG.CON setup.
- The Dockerfile sets the working directory to `/app`, so files are expected at `/app/credentials.json` and `/app/token.json`
- When using volume mounts, mount the files to `/app/` (as shown above)
- Alternatively, you can use `GOOGLE_CREDENTIALS_FILE` and `GOOGLE_TOKEN_FILE` environment variables to specify custom paths
- Make sure to mount `credentials.json` and `token.json` as volumes if using game mode

## Configuration

All configuration is done via environment variables. The defaults work for the original BGG.CON setup, but you can override them for other conventions or custom configurations.

### Updating Convention UUID

To monitor a different convention, set the `BGG_CONVENTION_UUID` environment variable:

```bash
export BGG_CONVENTION_UUID="YOUR_CONVENTION_UUID"
```

### Updating Library UUID (Game Mode)

To monitor games from a different library, set the `BGG_LIBRARY_UUID` environment variable:

```bash
export BGG_LIBRARY_UUID="YOUR_LIBRARY_UUID"
```

### Updating Google Sheets Configuration (Game Mode)

Update the spreadsheet configuration via environment variables:

```bash
export BGG_SPREADSHEET_ID="YOUR_SPREADSHEET_ID"
export BGG_WATCHLIST_RANGE="Watchlist!A2:A"  # Range for reading watchlist
export BGG_SPREADSHEET_DATA_RANGE="Data!A2:D1000"  # Range for game data
export BGG_SPREADSHEET_TIMESTAMP_RANGE="Data!F1"  # Range for timestamp
```

The spreadsheet should have:
- A "Watchlist" sheet with game names in column A (starting from row 2) - or whatever range you configure
- A "Data" sheet that will be updated with game availability information - or whatever sheet/range you configure

### Adjusting Polling Intervals

You can customize how frequently the bot checks for availability:

```bash
# Badge mode: check every 5 seconds instead of 10
export BGG_BADGE_POLL_INTERVAL="5"

# Game mode: check every 30 seconds instead of 10
export BGG_GAME_POLL_INTERVAL="30"

# Badge mode: send status updates every hour instead of every 3 hours
export BGG_BADGE_STATUS_UPDATE_INTERVAL="3600"
```

## Troubleshooting

### Authentication Issues

If you encounter Google Sheets authentication errors:
1. Delete `token.json` and re-authenticate
2. Ensure `credentials.json` is valid and in the project root
3. Verify the Google Sheets API is enabled in your Google Cloud project

### Discord Notifications Not Working

- Verify the `WEBHOOK_URL` environment variable is set correctly
- Test the webhook URL manually with a curl command:
  ```bash
  curl -H "Content-Type: application/json" -d '{"content":"Test"}' $WEBHOOK_URL
  ```

### Game Mode Not Finding Games

- Ensure game names in the watchlist exactly match names in the tabletop.events library
- Check that the library UUID is correct
- Verify the Google Sheets API has access to your spreadsheet

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
