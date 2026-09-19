import importlib
import json
import mimetypes
import os
import socket
import threading


def get_active_modules():
    try:
        with open("settings.json", "r") as f:
            settings = json.load(f)
    except FileNotFoundError:
        return []

    active = []
    for mod_name, enabled in settings.get("modules", {}).items():
        if enabled:
            try:
                module = importlib.import_module(f"modules.{mod_name}.module")
                active.append(module)
            except ModuleNotFoundError:
                print(f"[WARN] Could not find modules/{mod_name}/module.py")
    return active


def handle_client(client, address):
    active_modules = get_active_modules()


    for module in active_modules:
        if hasattr(module, "run"):
            module.run(address[0])

    raw_request = client.recv(1024).decode("utf-8", errors="ignore")
    first_line = raw_request.split("\r\n")[0] if raw_request else ""
    parts = first_line.split(" ")
    path = parts[1] if len(parts) > 1 else "/"

    # Check if a module handles this specific request path 
    for module in active_modules:
        if hasattr(module, "handle_request"):
            module_response = module.handle_request(path, raw_request, address)
            if module_response:
                client.sendall(module_response)
                client.close()
                return

    # default file serving logic
    requested = path.split("?")[0].split("#")[0]
    if requested in ("", "/"):
        requested = "/index.html"
    rel = os.path.normpath(requested.lstrip("/"))
    status = 200
    if rel.startswith("..") or os.path.isabs(rel):
        content = b"File not found."
        content_type = "text/plain; charset=utf-8"
        status = 404
    else:
        file_path = os.path.join("src", rel)
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
            if content_type.startswith("text/"):
                content_type += "; charset=utf-8"
            if content_type.startswith("text/html"):
                for module in active_modules:
                    if hasattr(module, "transform_response"):
                        content = module.transform_response(content)
        except (FileNotFoundError, IsADirectoryError, PermissionError):
            content = b"File not found."
            content_type = "text/plain; charset=utf-8"
            status = 404

    response = (
        f"HTTP/1.1 {status} {'OK' if status == 200 else 'Not Found'}\r\n"
        f"Content-Type: {content_type}\r\n\r\n".encode() + content
    )

    client.sendall(response)
    client.close()


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(("0.0.0.0", 8000))
server.listen(5)

print("Server started on port 8000")

while True:
    client, address = server.accept()
    threading.Thread(
        target=handle_client, args=(client, address), daemon=True
    ).start()