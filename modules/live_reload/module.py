import os

LIVE_RELOAD_JS = """
<script>
(function() {
    let lastMtime = null;
    setInterval(() => {
        fetch('/_live_reload')
            .then(res => res.text())
            .then(mtime => {
                if (lastMtime === null) {
                    lastMtime = mtime;
                } else if (lastMtime !== mtime) {
                    window.location.reload();
                }
            })
            .catch(() => {});
    }, 1000);
})();
</script>
</body>
"""


def get_latest_mtime(directory="src"):
    """Scans src/ and returns the newest file modification timestamp."""
    latest = 0
    if not os.path.exists(directory):
        return 0
    for root, _, files in os.walk(directory):
        for file in files:
            mtime = os.path.getmtime(os.path.join(root, file))
            if mtime > latest:
                latest = mtime
    return latest


def handle_request(path, raw_request=None, address=None):
    if path == "/_live_reload":
        latest = str(get_latest_mtime())
        return (
            b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n"
            + latest.encode()
        )
    return None



def transform_response(content):
    """Injects auto-reload JS script into served HTML."""
    if b"</body>" in content:
        return content.replace(b"</body>", LIVE_RELOAD_JS.encode())
    return content + LIVE_RELOAD_JS.encode()