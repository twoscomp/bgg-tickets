"""
A small program to check tabletop.events for badge availability to BGG.CON 2023.
Poll the API every 10 seconds and send a message to Discord if badges are available.
"""

import datetime
import sys
import time
import os
import requests

WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
GAME_QUERY_URL = 'https://tabletop.events/api/library/0AEB11DA-2B7D-11EC-B400-855F800FD618/librarygames'

DEBUG = os.environ.get("BGG_DEBUG", False)
GAME_MODE = os.environ.get("BGG_GAME_MODE", False)
GAME_WATCHLIST = os.environ.get("BGG_WATCHLIST", "").split(",")

def send_discord_message(message, dry=False):
    """
    Send a messiage to Discord using a webhoom URL.
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

    query = {"query": game, "is_in_circulation": 1}
    resp = requests.get(GAME_QUERY_URL, params=query)
    data = resp.json()

    # Parse JSON for availabe games
    games = data["result"]["items"]
    matches = []
    for g in games:
        if g["custom_fields"]["ItemType"] == "Standalone" and g["custom_fields"]["Location"] != "HOT GAMES":
            matches.append(g)
    return matches

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

def format_watchlist_details(games):
    now = datetime.datetime.now()
    watchlist = """
( ⌐■_■) WATCHLIST
================="""
    for g in games:
        if g["is_checked_out"] == 0: 
            watchlist += f"\n'{g['name']}: Avaliable.'"
        else:
            checkout_time = datetime.datetime.strptime(g['last_checkout_date'], "%Y-%m-%d %H:%M:%S")
            delta = now - checkout_time
            total_s = delta.total_seconds()
            h = abs(total_s // 3600)
            m = abs((total_s%3600) // 60)
            watchlist += f"\n'{g['name']}: Checked out {h} hour(s) and {m} minutes ago."
    return watchlist 
    
def get_attendee_badge_availablity():
    """
    Query the tabletop.events API for badge availability.
    """

    # Make request to tabletop.events
    resp = requests.get(
        "https://tabletop.events/api/convention/C50E2390-C43D-11ED-AB2B-20397E91607B/badgetypes?_include_relationships=1&_items_per_page=10&_order_by=sequence_number&_page_number=1",
        timeout=5,
    )
    data = resp.json()

    # Parse JSON for available badges
    item_name = data["result"]["items"][0]["name"]
    available_quantity = data["result"]["items"][0]["available_quantity"]
    max_available_count = data["result"]["items"][0]["max_available_count"]

    return item_name, available_quantity, max_available_count

# pylint: disable=C0103
if __name__ == "__main__":
    # Check every 10 seconds if badges are available. If so, then send a message to Discord.
    prev_available = 10000
    last_update = 0

    if GAME_MODE:
        prev = {}
        while True:
            cur = {}
            if len(GAME_WATCHLIST) == 0:
                exit("ERR: Watchlist is empty.")

            copies = []
            # Get the current state of games
            for n in GAME_WATCHLIST:
                copies += get_game(n)
            
            # Print a summary of every game copy
            if time.time() - last_update > 60 * 60:
                send_discord_message(format_watchlist_details(copies))        
                last_update = time.time()

            # Aggregate game by 'name'.
            cur = get_game_availablity(copies)

            # Compare to previous state of games. Send a discord message if changed.
            for name, c in cur.items():
                p = prev.get(name, {"avail": -1, "total": -1})
                if p["avail"] == 0 and c["avail"] > 0:
                    send_discord_message(f"(ʘ言ʘ╬) @everyone '{name}' is available!!!")
                elif p["avail"] > 0 and c["avail"] == 0:
                    send_discord_message(f" ( ಥ╭╮ಥ)\" '{name}' is all checked out...")
            prev = cur
            time.sleep(10)
    

    while True:
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
        elif time.time() - last_update > 60 * 180:
            msg = f"({now}) 🤖 Still checking for {name} badges..."
            send_discord_message(msg)
            last_update = time.time()
        prev_available = available
        time.sleep(10)
