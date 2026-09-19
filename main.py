import socket

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(("0.0.0.0", 8000))
server.listen(1)

print("Server started on port 8000")

while True:
    client, _ = server.accept()
    client.recv(1024)  

    try:
        with open("src/index.html", "rb") as f:
            content = f.read()
        response = b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + content
    except FileNotFoundError:
        response = b"HTTP/1.1 404 Not Found\r\n\r\nFile not found."

    client.sendall(response)
    client.close()