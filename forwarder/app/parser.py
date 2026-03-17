def base_event(raw_event: dict, event_type: str) -> dict:
    return {
        "event_source": "cowrie",
        "event_type": event_type,
        "source_ip": raw_event.get("src_ip", "unknown"),
        "timestamp": raw_event.get("timestamp"),
        "session_id": raw_event.get("session", "unknown"),
        "username": raw_event.get("username"),
        "password": raw_event.get("password"),
        "success": False,
        "command": None,
        "duration": None,
        "raw_event": raw_event,
    }


def parse_cowrie_event(raw_event: dict) -> dict | None:
    eventid = raw_event.get("eventid")

    if eventid == "cowrie.session.connect":
        event = base_event(raw_event, "session_started")
        return event

    if eventid == "cowrie.login.success":
        event = base_event(raw_event, "ssh_login_attempt")
        event["success"] = True
        return event

    if eventid == "cowrie.command.input":
        event = base_event(raw_event, "ssh_command_input")
        event["command"] = raw_event.get("input")
        return event

    if eventid == "cowrie.command.failed":
        event = base_event(raw_event, "ssh_command_failed")
        event["command"] = raw_event.get("input")
        return event

    if eventid == "cowrie.session.closed":
        event = base_event(raw_event, "session_closed")
        event["duration"] = raw_event.get("duration")
        return event

    return None