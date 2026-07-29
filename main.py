import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from supabase import create_client
from datetime import datetime

supabase = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_SERVICE_KEY")
)


class SignalHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path == "/webhook/indicator-signal":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length))
                record = {
                    "instrument": body.get("instrument"),
                    "timeframe": body.get("timeframe"),
                    "signal_type": body.get("signal_type"),
                    "price_at_signal": body.get("price_at_signal"),
                    "created_at": body.get("timestamp") or datetime.now().isoformat(),
                }
                result = supabase.table("signal_log").insert(record).execute()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "saved", "data": record}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return
        self.send_response(404)
        self.end_headers()


def main():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SignalHandler)
    print(f"📡 Signal ingestion service running on port {port}")
    server.serve_forever()


if __name__ == "__main__":
    main()