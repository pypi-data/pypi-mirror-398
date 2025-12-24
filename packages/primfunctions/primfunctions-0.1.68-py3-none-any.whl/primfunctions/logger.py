import json

from datetime import datetime


class Logger:
    def __init__(self, session_id: str):
        self.session_id = session_id

    def log(self, level: str, message: str):
        payload = {
            "level": level,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
        }

        print(json.dumps(payload), flush=True)

    def debug(self, message: str):
        self.log("debug", message)

    def info(self, message: str):
        self.log("info", message)

    def warning(self, message: str):
        self.log("warning", message)

    def error(self, message: str):
        self.log("error", message)
