from datetime import datetime, UTC
import requests

def main():

    event = {
        "event_type": "ssh_login_attempt",
        "source_ip": "127.0.0.1",
        "timestamp": datetime.now(UTC).isoformat(),
        "session_id": "session-local-001",
        "username": "root",
        "password": "123456",
        "success": False,
    }

    try:
        response = requests.post("http://collector-api:8000/events", json=event, timeout=5)
        print("Event sent:", response.status_code, response.text)
    except Exception as exc:
        print("Error sending event:", exc)

    if __name__ == "__main__":
        main()