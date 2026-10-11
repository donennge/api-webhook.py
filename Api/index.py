
import os
import json
import urllib.request
from http.server import BaseHTTPRequestHandler

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("FEEDBACK_CHANNEL_ID", "")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")


def telegram(method, payload):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        result = json.loads(response.read().decode("utf-8"))

    if not result.get("ok"):
        raise RuntimeError("Telegram API request failed")


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot webhook is ready")

    def do_POST(self):
        if (
            not WEBHOOK_SECRET
            or self.headers.get("X-Telegram-Bot-Api-Secret-Token")
            != WEBHOOK_SECRET
        ):
            self.send_error(403)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            update = json.loads(self.rfile.read(length))
            msg = update.get("message")

            if msg and CHANNEL_ID and BOT_TOKEN:
                sender = msg.get("from", {})
                username = sender.get("username")
                name = " ".join(filter(None, [
                    sender.get("first_name"),
                    sender.get("last_name")
                ])) or "Unknown"

                caption = (
                    f"Feedback by - @{username}"
                    if username else f"Feedback by - {name}"
                )

                if msg.get("photo"):
                    telegram("sendPhoto", {
                        "chat_id": CHANNEL_ID,
                        "photo": msg["photo"][-1]["file_id"],
                        "caption": caption
                    })

                elif msg.get("video"):
                    telegram("sendVideo", {
                        "chat_id": CHANNEL_ID,
                        "video": msg["video"]["file_id"],
                        "caption": caption
                    })

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

        except Exception:
            self.send_error(500)

