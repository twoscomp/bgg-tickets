"""
A small program to check tabletop.events for badge availability to BGG.CON 2023.
Poll the API every 10 seconds and send a message to Discord if badges are available.
"""

import datetime
import sys
import time
import os
import requests

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")


def send_discord_message(message):
    """
    Send a messiage to Discord using a webhoom URL.
    """

    data = {"content": message}
    requests.post(WEBHOOK_URL, json=data, timeout=5)


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

    while True:
        name, available, num_badges = get_attendee_badge_availablity()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(
            f"({now}) {available} of {num_badges} {name} badges available.",
            file=sys.stdout,
        )
        if available > 0 and prev_available != available:
            msg = (
                f"({now}) 🔔🔔🔔 {available} of {num_badges} {name} badges available: "
                "https://tabletop.events/conventions/bgg.con-2023/badgetypes"
            )
            send_discord_message(msg)
        elif prev_available > 0 and available == 0:
            msg = f"({now}) 😢 {name} badges are sold out, {available} of {num_badges} available."
            send_discord_message(msg)
        elif time.time() - last_update > 60 * 30:
            msg = f"({now}) 🤖 Still checking for {name} badges..."
            send_discord_message(msg)
        last_update = time.time()
        prev_available = available
        time.sleep(10)
