"""
A small program to check tabletop.events for badge availability to BGG.CON.
Poll the API every 10 seconds and send a message to Discord if badges are available.
"""

import datetime
import os
import sys
import time

import pytz
import requests
from requests.exceptions import SSLError, ConnectionError, Timeout, RequestException
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

DEBUG = os.environ.get("BGG_DEBUG", False)

# Set to True to check for game availability instead of badges.
GAME_MODE = os.environ.get("BGG_GAME_MODE", False)

# Notification Webhook URL
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")

# For game availability.
LIBRARY_UUID = os.environ.get("BGG_LIBRARY_UUID", "0AEB11DA-2B7D-11EC-B400-855F800FD618")
GAME_QUERY_URL = f"https://tabletop.events/api/library/{LIBRARY_UUID}/librarygames"
GAME_WATCHLIST = os.environ.get("BGG_WATCHLIST", "").split(",")

# For badge availability.
CONVENTION_UUID = os.environ.get("BGG_CONVENTION_UUID", "C50E2390-C43D-11ED-AB2B-20397E91607B")

# Google Sheets for loading watchlist
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# The ID and range of a watchlist spreadsheet.
SPREADSHEET_ID = os.environ.get("BGG_SPREADSHEET_ID", "17ZW0hl3x2A56zrWRH67SZOraqAYSTWSPNnpXWJF1CEg")
WATCHLIST_RANGE = os.environ.get("BGG_WATCHLIST_RANGE", "Watchlist!A2:A")
SPREADSHEET_DATA_RANGE = os.environ.get("BGG_SPREADSHEET_DATA_RANGE", "Data!A2:D1000")
SPREADSHEET_TIMESTAMP_RANGE = os.environ.get("BGG_SPREADSHEET_TIMESTAMP_RANGE", "Data!F1")

# HTTP request timeout in seconds
HTTP_TIMEOUT = int(os.environ.get("BGG_HTTP_TIMEOUT", "10"))

# Polling intervals (in seconds)
BADGE_POLL_INTERVAL = int(os.environ.get("BGG_BADGE_POLL_INTERVAL", "10"))
GAME_POLL_INTERVAL = int(os.environ.get("BGG_GAME_POLL_INTERVAL", "10"))
BADGE_STATUS_UPDATE_INTERVAL = int(os.environ.get("BGG_BADGE_STATUS_UPDATE_INTERVAL", "10800"))  # 3 hours in seconds
GAME_MAX_BACKOFF = int(os.environ.get("BGG_GAME_MAX_BACKOFF", "300"))  # 5 minutes in seconds

# Google OAuth credentials file paths (configurable via environment variables)
# Defaults to current directory for local use, or /app for Docker
CREDENTIALS_FILE = os.environ.get("GOOGLE_CREDENTIALS_FILE", "credentials.json")
TOKEN_FILE = os.environ.get("GOOGLE_TOKEN_FILE", "token.json")


def send_discord_message(message, dry=False):
    """
    Send a messiage to Discord using a webhook URL.
    """

    if DEBUG:
        print(message)
    if not dry and len(WEBHOOK_URL) > 0:
        data = {"content": message}
        requests.post(WEBHOOK_URL, json=data, timeout=5)


def get_game(game):
    """
    Query the tabletop.events Library API for games by name. Return the total number and the number available.
    """
    try:
        query = {"query": game, "is_in_circulation": 1}
        resp = requests.get(GAME_QUERY_URL, params=query, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()  # Raise an exception for bad status codes
        data = resp.json()

        # Parse JSON for availabe games
        games = data["result"]["items"]
        matches = []
        for g in games:
            if (
                g["custom_fields"]["ItemType"] == "Standalone"
                and g["custom_fields"]["Location"] != "HOT GAMES"
            ):
                matches.append(g)
        return matches
    except (SSLError, ConnectionError) as e:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"({now}) HTTPS/Connection error when checking tabletop.events API for game '{game}': {e}", file=sys.stderr)
        raise
    except Timeout as e:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"({now}) Timeout error when checking tabletop.events API for game '{game}': {e}", file=sys.stderr)
        raise
    except RequestException as e:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"({now}) Request error when checking tabletop.events API for game '{game}': {e}", file=sys.stderr)
        raise


def get_game_availablity(games):
    sorted = {}
    for g in games:
        matched_name = g["name"]
        entry = sorted.get(matched_name, {"avail": 0, "total": 0})
        if g["is_checked_out"] == 0:
            entry.update({"avail": entry.get("avail") + 1})
        entry.update({"total": entry.get("total") + 1})
        sorted.update({matched_name: entry})
    return sorted


def calculate_timedelta(last_date):
    if last_date.tzinfo is None:
        last_date = pytz.utc.localize(last_date)
    now = datetime.datetime.now(pytz.utc)
    delta = now - last_date
    hours, remainder = divmod(delta.total_seconds(), 3600)
    minutes = remainder // 60
    return f"{int(hours)}h {int(minutes)}m"


def format_spreadsheet_update(copies):
    body = []
    for c in copies:
        row = [c["name"]]
        if c["is_checked_out"] == 0:
            row.append(True)
            last_date = datetime.datetime.strptime(
                c["last_checkin_date"], "%Y-%m-%d %H:%M:%S"
            )
            row.append(convert_to_cst(c["last_checkin_date"]))
        else:
            row.append(False)
            last_date = datetime.datetime.strptime(
                c["last_checkout_date"], "%Y-%m-%d %H:%M:%S"
            )
            row.append(convert_to_cst(c["last_checkout_date"]))

        # Calculate timedelta and append to row
        row.append(calculate_timedelta(last_date))

        body.append(row)
    return body


def get_attendee_badge_availablity():
    """
    Query the tabletop.events API for badge availability.

    """
    try:
        # Make request to tabletop.events
        resp = requests.get(
            f"https://tabletop.events/api/convention/{CONVENTION_UUID}/badgetypes?_include_relationships=1&_items_per_page=10&_order_by=sequence_number&_page_number=1",
            timeout=HTTP_TIMEOUT,
        )
        resp.raise_for_status()  # Raise an exception for bad status codes
        data = resp.json()

        # Parse JSON for available badges
        item_name = data["result"]["items"][0]["name"]
        available_quantity = data["result"]["items"][0]["available_quantity"]
        max_available_count = data["result"]["items"][0]["max_available_count"]

        return item_name, available_quantity, max_available_count
    except (SSLError, ConnectionError) as e:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"({now}) HTTPS/Connection error when checking tabletop.events API: {e}", file=sys.stderr)
        raise
    except Timeout as e:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"({now}) Timeout error when checking tabletop.events API: {e}", file=sys.stderr)
        raise
    except RequestException as e:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"({now}) Request error when checking tabletop.events API: {e}", file=sys.stderr)
        raise


def get_sheets_service():
    """
    Get the Google Sheets service.
    """
    # Set up the credentials
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"Google credentials file not found: {CREDENTIALS_FILE}. "
                    f"Please set GOOGLE_CREDENTIALS_FILE environment variable or "
                    f"place credentials.json in the current directory."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    # Build the service
    service = build("sheets", "v4", credentials=creds)
    return service


def get_watchlist(sheets_service):
    """
    Get the watchlist from Google Sheets.
    """
    # Call the Sheets API
    sheet = sheets_service.spreadsheets()
    result = (
        sheet.values()
        .get(spreadsheetId=SPREADSHEET_ID, range=WATCHLIST_RANGE)
        .execute()
    )
    values = result.get("values", [])
    return values


def convert_to_cst(time_str):
    """
    Convert a time string to CST.
    """
    central = pytz.timezone("US/Central")
    dt = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    dt = pytz.utc.localize(dt)
    dt = dt.astimezone(central)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def update_spreadsheet_data(sheets_service, body):
    """
    Update the Google Sheets with the current state of games.
    """
    sheet = sheets_service.spreadsheets()
    result = (
        sheet.values()
        .update(
            spreadsheetId=SPREADSHEET_ID,
            range=SPREADSHEET_DATA_RANGE,
            valueInputOption="USER_ENTERED",
            body={"values": body},
        )
        .execute()
    )
    return result


def update_spreadsheet_timestamp(sheets_service):
    """
    Update the Google Sheets with the current timestamp.
    """

    central = pytz.timezone("US/Central")
    now = datetime.datetime.now(central).strftime("%Y-%m-%d %H:%M:%S")
    sheet = sheets_service.spreadsheets()
    result = (
        sheet.values()
        .update(
            spreadsheetId=SPREADSHEET_ID,
            range=SPREADSHEET_TIMESTAMP_RANGE,
            valueInputOption="USER_ENTERED",
            body={"values": [[now]]},
        )
        .execute()
    )
    return result


def clear_spreadsheet_data(sheets_service):
    """
    Clear the Google Sheets with the current state of games.
    """
    sheet = sheets_service.spreadsheets()
    result = (
        sheet.values()
        .clear(
            spreadsheetId=SPREADSHEET_ID,
            range=SPREADSHEET_DATA_RANGE,
        )
        .execute()
    )
    return result


def game_mode():
    prev = {}
    backoff = GAME_POLL_INTERVAL  # Initial backoff time in seconds

    # send_discord_message("🤖 Starting BGG.CON Game Availability Bot...")
    while True:
        cur = {}
        copies = []

        try:
            # Read the watchlist from Google Sheets
            sheets = get_sheets_service()
            watchlist = get_watchlist(sheets)
            # Get the current state of games
            for n in watchlist:
                copies += get_game(n)

            # Update the spreadsheet with the current state of games
            body = format_spreadsheet_update(copies)
            clear_spreadsheet_data(sheets)
            update_spreadsheet_data(sheets, body)
            update_spreadsheet_timestamp(sheets)

            # Aggregate game by 'name'.
            cur = get_game_availablity(copies)

            # Compare to previous state of games. Send a discord message if changed.
            for name, c in cur.items():
                p = prev.get(name, {"avail": -1, "total": -1})
                if p["avail"] == 0 and c["avail"] > 0:
                    send_discord_message(f"✅ @everyone '{name}' is available!!!")
                elif p["avail"] > 0 and c["avail"] == 0:
                    send_discord_message(f"🚫 '{name}' is all checked out...")
            prev = cur
            backoff = GAME_POLL_INTERVAL
        except Exception as error:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"({now}) An error occurred: {error}", file=sys.stderr)
            # Log errors instead of spamming Discord
            backoff = min(backoff * 2, GAME_MAX_BACKOFF)  # Exponential backoff up to max backoff

        time.sleep(backoff)


def badge_mode():
    # Check for badge availability at configured intervals and send messages to Discord.
    prev_available = 10000
    last_update = 0
    while True:
        try:
            name, available, num_badges = get_attendee_badge_availablity()
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(
                f"({now}) {available} of {num_badges} {name} badges available.",
                file=sys.stdout,
            )
            if available > 0 and prev_available == 0:
                msg = (
                    f"({now}) 🔔 @everyone 🔔 {available} of {num_badges} {name} badges available: "
                    "https://tabletop.events/conventions/bgg.con-2023/badgetypes"
                )
                send_discord_message(msg)
            elif available > 0 and prev_available != available:
                msg = (
                    f"({now}) 🎟️ {available} of {num_badges} {name} badges available: "
                    "https://tabletop.events/conventions/bgg.con-2023/badgetypes"
                )
                send_discord_message(msg)
            elif prev_available > 0 and available == 0:
                msg = f"({now}) 😢 {name} badges are sold out, {available} of {num_badges} available."
                send_discord_message(msg)
                last_update = time.time()
            elif time.time() - last_update > BADGE_STATUS_UPDATE_INTERVAL:
                msg = f"({now}) 🤖 Still checking for {name} badges..."
                send_discord_message(msg)
                last_update = time.time()
            prev_available = available
        except Exception as error:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"({now}) An error occurred: {error}", file=sys.stderr)
            # Log errors instead of spamming Discord
        time.sleep(BADGE_POLL_INTERVAL)


# pylint: disable=C0103
if __name__ == "__main__":
    if not WEBHOOK_URL:
        print(
            "Warning: WEBHOOK_URL environment variable is not set. "
            "Discord notifications will not be sent.",
            file=sys.stderr,
        )

    if GAME_MODE:
        game_mode()
    else:
        badge_mode()
