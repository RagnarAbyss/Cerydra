import requests
import os
import time
from datetime import datetime

PLACE_IDS = [pid.strip() for pid in os.environ.get("PLACE_IDS", "").split(",") if pid.strip()]
ALERT_ENDPOINT = os.environ.get("NOTIF_URL", "")

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})

RETRY = 3
BASE_DELAY = 0.5


def safe_get(url):
    for i in range(RETRY):
        try:
            res = session.get(url, timeout=10)

            if res.status_code == 200:
                return res.json()

            elif res.status_code == 429:
                wait = 2 * (i + 1)
                print(f"⏳ Rate limit, tunggu {wait}s...")
                time.sleep(wait)

            else:
                print(f"⚠️ Status {res.status_code}")

        except Exception as e:
            print(f"⚠️ Error attempt {i+1}: {e}")

        time.sleep(1)

    return None


def get_universe_id(place_id):
    url = f"https://apis.roblox.com/universes/v1/places/{place_id}/universe"
    data = safe_get(url)
    if data and data.get("universeId"):
        return str(data["universeId"])
    print(f"❌ Gagal universe: {place_id}")
    return None


def get_game_info(universe_id):
    url = f"https://games.roblox.com/v1/games?universeIds={universe_id}"
    data = safe_get(url)
    if data and data.get("data"):
        return data["data"][0]
    print(f"❌ Gagal game info: {universe_id}")
    return None


def get_game_thumbnail(universe_id):
    url = f"https://thumbnails.roblox.com/v1/games/icons?universeIds={universe_id}&size=512x512&format=Png"
    data = safe_get(url)
    if data and data.get("data"):
        return data["data"][0].get("imageUrl", "")
    return ""


def send_discord_notification(place_id, game_name, thumbnail_url, updated_time):
    if not ALERT_ENDPOINT:
        print("❌ Webhook kosong")
        return

    try:
        if updated_time:
            dt = datetime.fromisoformat(updated_time.replace("Z", "+00:00"))
            updated_time = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except:
        pass

    embed = {
        "title": "Meow",
        "description": f"**{game_name}**\nhttps://www.roblox.com/games/{place_id}/",
        "color": 0x00ff00,
        "fields": [
            {"name": "Game", "value": game_name, "inline": True},
            {"name": "Place ID", "value": place_id, "inline": True},
            {"name": "Updated", "value": updated_time or "Unknown", "inline": True},
        ],
        "timestamp": datetime.utcnow().isoformat()
    }

    if thumbnail_url:
        embed["thumbnail"] = {"url": thumbnail_url}

    try:
        res = session.post(ALERT_ENDPOINT, json={"embeds": [embed]}, timeout=10)
        print(f"✅ Sent: {game_name}")
    except Exception as e:
        print(f"❌ Send error: {e}")


def main():
    print(f"\n🚀 DAILY RUN @ {datetime.utcnow()}")
    print(f"📦 Total: {len(PLACE_IDS)}")

    for place_id in PLACE_IDS:
        print(f"\n🔍 {place_id}")

        universe_id = get_universe_id(place_id)
        if not universe_id:
            continue

        time.sleep(BASE_DELAY)

        game = get_game_info(universe_id)
        if not game:
            continue

        time.sleep(BASE_DELAY)

        name = game.get("name", place_id)
        updated = game.get("updated", "")
        thumb = get_game_thumbnail(universe_id)

        time.sleep(BASE_DELAY)

        send_discord_notification(place_id, name, thumb, updated)

        time.sleep(BASE_DELAY)

    print("\n✅ DONE")


if __name__ == "__main__":
    main()
