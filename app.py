import os
import re
import time
import requests

BASE_URL = "https://www.clubhouseapi.com/api/"


def get_channel_code(room_link):
    match = re.search(r"/room/([A-Za-z0-9:_-]+)", room_link)
    return match.group(1) if match else None


def get_headers(token):
    return {
        "CH-Languages": "en-US",
        "CH-Locale": "en_US",
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Token {token}",
        "User-Agent": "clubhouse/android",
    }


def join_room(token, channel_code):
    url = BASE_URL + "join_channel"

    response = requests.post(
        url,
        headers=get_headers(token),
        data={"channel": channel_code},
        timeout=20,
    )

    print("Join response:", response.status_code)
    print(response.text)


def main():
    print("=== Clubhouse Room Tool ===")

    token = os.getenv("CLUBHOUSE_TOKEN")

    if not token:
        token = input("Enter your authorized Clubhouse token: ").strip()

    room_link = input("Enter Clubhouse room link: ").strip()

    channel_code = get_channel_code(room_link)

    if not channel_code:
        print("Invalid Clubhouse room link.")
        return

    print("Room code:", channel_code)
    print("Joining room...")

    try:
        join_room(token, channel_code)
    except requests.RequestException as e:
        print("Request failed:", e)
        return

    print("Finished.")


if __name__ == "__main__":
    main()
