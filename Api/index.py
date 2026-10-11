import os
import json
import urllib.request
import urllib.error
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

    with urllib.request.urlopen(request, timeout=15) as response:
        result = json.loads(response.read().decode("utf-8"))

    if not result.get("ok"):
        raise RuntimeError("Telegram API request failed")

    return result


class handler(BaseHTTPRequestHandler):

    def respond(self, status, message):
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(message.encode("utf-8"))

    def do_GET(self):
        self.respond(200, "Bot webhook is ready")

    def do_POST(self):
        if not BOT_TOKEN or not CHANNEL_ID or not WEBHOOK_SECRET:
            self.respond(500, "Missing environment variables")
            return

        if self.headers.get(
            "X-Telegram-Bot-Api-Secret-Token"
        ) != WEBHOOK_SECRET:
            self.respond(403, "Forbidden")
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            update = json.loads(self.rfile.read(length))
            msg = update.get("message")

            if not msg:
                self.respond(200, "OK")
                return

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

            self.respond(200, "OK")

        except urllib.error.HTTPError as error:
            print("Telegram API HTTP error:", error.code)
            self.respond(502, "Telegram API rejected the request")

        except Exception as error:
            print("Webhook error:", str(error))
            self.respond(500, "Webhook failed")
