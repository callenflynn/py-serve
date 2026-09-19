import importlib
import json
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
    try:
        with open("src/index.html", "rb") as f:
            content = f.read()

        # let modules modify content
        for module in active_modules:
            if hasattr(module, "transform_response"):
                content = module.transform_response(content)

        response = (
            b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + content
        )
    except FileNotFoundError:
        response = b"HTTP/1.1 404 Not Found\r\n\r\nFile not found."

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