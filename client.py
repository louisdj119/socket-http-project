import socket


HOST = "127.0.0.1"
PORT = 8080
BUFFER_SIZE = 4096


def build_request(method: str, path: str, body: str) -> bytes:
    """
    사용자 입력값을 바탕으로 HTTP/1.1 Request 문자열을 직접 구성한다.

    Request 구조:
    1. Request line
    2. Header lines
    3. Blank line
    4. Body
    """
    method = method.upper()
    body_bytes = body.encode("utf-8")

    request_lines = [
        f"{method} {path} HTTP/1.1",
        f"Host: {HOST}:{PORT}",
        "User-Agent: PythonSocketHTTPClient/1.0",
        "Content-Type: text/plain; charset=utf-8",
        f"Content-Length: {len(body_bytes)}",
        "Connection: close",
        "",
        "",
    ]

    request_header = "\r\n".join(request_lines).encode("utf-8")
    return request_header + body_bytes


def send_request(request_bytes: bytes) -> bytes:
    """TCP 소켓으로 Server에 접속하여 Request를 보내고 Response 전체를 수신한다."""
    response = b""

    # socket.AF_INET: IPv4, socket.SOCK_STREAM: TCP
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((HOST, PORT))
        client_socket.sendall(request_bytes)

        while True:
            chunk = client_socket.recv(BUFFER_SIZE)
            if not chunk:
                break
            response += chunk

    return response


def main() -> None:
    """사용자로부터 Method, Path, Body를 입력받아 HTTP 요청을 전송한다."""
    print("[CLIENT] TCP Socket HTTP Client")
    print("[CLIENT] Server:", f"{HOST}:{PORT}")
    print("[CLIENT] Example methods: GET, HEAD, POST, PUT, DELETE, PATCH")
    print("[CLIENT] Example paths: /index.html, /notfound.html, /post.txt, /put.txt, /readonly.txt")

    method = input("\nMethod 입력: ").strip().upper()
    path = input("Path 입력: ").strip()

    if not path.startswith("/"):
        path = "/" + path

    body = ""
    if method in ("POST", "PUT"):
        body = input("Body 입력: ")

    request_bytes = build_request(method, path, body)
    response_bytes = send_request(request_bytes)

    print("\n" + "=" * 70)
    print("[CLIENT] Sent Request")
    print(request_bytes.decode("utf-8", errors="replace"))
    print("=" * 70)
    print("[CLIENT] Received Response")
    print(response_bytes.decode("utf-8", errors="replace"))


if __name__ == "__main__":
    main()
