import json
import os
from datetime import datetime

TELEMETRY_JS = """
<script>
(function() {
    function sendEvent(type, details) {
        fetch('/_telemetry_event', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                type: type,
                screen: window.screen.width + 'x' + window.screen.height,
                userAgent: navigator.userAgent,
                details: details
            })
        }).catch(() => {});
    }

    window.addEventListener('DOMContentLoaded', () => {
        sendEvent('session_start', {});
    });
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('button, input[type="button"], input[type="submit"], .btn');
        if (btn) {
            sendEvent('button_click', {
                id: btn.id || null,
                class: btn.className || null,
                text: (btn.innerText || btn.value || '').trim().substring(0, 50)
            });
        }
    });
})();
</script>
</body>
"""


def parse_user_agent(ua):
    browser = "Unknown"
    if "Chrome" in ua and "Edg" not in ua:
        browser = "Chrome"
    elif "Safari" in ua and "Chrome" not in ua:
        browser = "Safari"
    elif "Firefox" in ua:
        browser = "Firefox"
    elif "Edg" in ua:
        browser = "Edge"

    mobile_indicators = ["Mobile", "Android", "iPhone", "iPad", "iPod", "Windows Phone"]
    desktop_indicators = ["Windows NT", "Macintosh", "X11", "Linux", "CrOS"]
    
    if any(term in ua for term in mobile_indicators):
        device = "Mobile"
    elif any(term in ua for term in desktop_indicators):
        device = "Desktop"
    else:
        device = "Other"
    return browser, device


def handle_request(path, raw_request, address):
    if path == "/_telemetry_event":
        try:
            # Extract JSON from POST
            _, body = raw_request.split("\r\n\r\n", 1)
            data = json.loads(body)

            browser, device = parse_user_agent(data.get("userAgent", ""))

            entry = {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "ip": address[0],
                "event": data.get("type"),
                "device": device,
                "browser": browser,
                "screen": data.get("screen"),
                "details": data.get("details"),
            }

            # Write to /modules/telemetry/logs/[YYYY-MM-DD].json
            base_dir = os.path.dirname(os.path.abspath(__file__))
            logs_dir = os.path.join(base_dir, "logs")
            os.makedirs(logs_dir, exist_ok=True)

            date_str = datetime.now().strftime("%Y-%m-%d")
            log_file = os.path.join(logs_dir, f"{date_str}.json")

            with open(log_file, "a") as f:
                f.write(json.dumps(entry) + "\n")

        except Exception:
            pass

        return b"HTTP/1.1 204 No Content\r\n\r\n"

    return None


def transform_response(content):
    if b"</body>" in content:
        return content.replace(b"</body>", TELEMETRY_JS.encode())
    return content + TELEMETRY_JS.encode()