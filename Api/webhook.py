
import os
import json
import urllib.request
from http.server import BaseHTTPRequestHandler

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
FEEDBACK_CHANNEL_ID = os.environ.get("FEEDBACK_CHANNEL_ID", "")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")


def telegram(method, payload):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if not WEBHOOK_SECRET or self.headers.get(
            "X-Telegram-Bot-Api-Secret-Token"
        ) != WEBHOOK_SECRET:
            self.send_error(403)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            update = json.loads(self.rfile.read(length))
            message = update.get("message") or update.get("channel_post")

            if message and FEEDBACK_CHANNEL_ID:
                user = message.get("from", {})
                username = user.get("username")
                display_name = " ".join(
                    filter(None, [
                        user.get("first_name"),
                        user.get("last_name"),
                    ])
                ) or "Unknown"
                attribution = (
                    f"Feedback by - @{username}"
                    if username else f"Feedback by - {display_name}"
                )

                media = None
                if message.get("photo"):
                    media = {
                        "type": "photo",
                        "media": message["photo"][-1]["file_id"],
                    }
                elif message.get("video"):
                    media = {
                        "type": "video",
                        "media": message["video"]["file_id"],
                    }

                if media:
                    media["caption"] = attribution
                    telegram("sendMedia", {
                        "chat_id": FEEDBACK_CHANNEL_ID,
                        "media": media,
                    })

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

        except Exception:
            self.send_error(500, "Webhook processing failed")
