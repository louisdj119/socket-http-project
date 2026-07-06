import datetime as dt
import socket
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.parse import unquote


HOST = "127.0.0.1"
PORT = 8080
BUFFER_SIZE = 4096
SERVER_NAME = "PythonSocketHTTPServer/1.0"
BASE_DIR = Path(__file__).resolve().parent


def make_http_date() -> str:
    """HTTP Response의 Date 헤더에 들어갈 GMT 시간 문자열을 만든다."""
    return dt.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")


def guess_content_type(path: str) -> str:
    """요청 경로의 확장자에 따라 간단한 Content-Type을 결정한다."""
    if path.endswith(".html"):
        return "text/html; charset=utf-8"
    if path.endswith(".txt"):
        return "text/plain; charset=utf-8"
    return "text/plain; charset=utf-8"


def parse_http_request(raw_data: bytes) -> Tuple[str, str, str, Dict[str, str], str]:
    """
    TCP로 받은 HTTP Request 메시지를 직접 파싱한다.

    Request는 request line, headers, blank line, body 구조를 가진다.
    이 함수는 request line에서 method, path, version을 분리하고,
    header는 딕셔너리로 저장하며, blank line 뒤의 body를 문자열로 반환한다.
    """
    request_text = raw_data.decode("utf-8", errors="replace")
    header_part, _, body = request_text.partition("\r\n\r\n")
    lines = header_part.split("\r\n")

    if not lines or len(lines[0].split()) != 3:
        return "", "", "", {}, body

    method, path, version = lines[0].split()
    headers: Dict[str, str] = {}

    for line in lines[1:]:
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip().lower()] = value.strip()

    return method.upper(), path, version, headers, body


def build_http_response(
    status_code: int,
    reason: str,
    body: str = "",
    content_type: str = "text/plain; charset=utf-8",
    send_body: bool = True,
) -> bytes:
    """
    HTTP Response 메시지를 직접 구성한다.

    Response 구조:
    1. Status line
    2. Header lines
    3. Blank line
    4. Body
    """
    body_bytes = body.encode("utf-8")
    response_lines = [
        f"HTTP/1.1 {status_code} {reason}",
        f"Date: {make_http_date()}",
        f"Server: {SERVER_NAME}",
        f"Content-Type: {content_type}",
        f"Content-Length: {len(body_bytes)}",
        "Connection: close",
        "",
        "",
    ]

    header_bytes = "\r\n".join(response_lines).encode("utf-8")
    if send_body:
        return header_bytes + body_bytes
    return header_bytes


def safe_file_path(request_path: str) -> Optional[Path]:
    """
    요청 경로를 프로젝트 폴더 내부의 파일 경로로 변환한다.

    /index.html -> index.html
    /post.txt -> post.txt
    """
    clean_path = unquote(request_path).lstrip("/")
    target_path = (BASE_DIR / clean_path).resolve()

    # ../ 같은 경로 이동 공격을 막기 위해 프로젝트 폴더 내부 파일만 허용한다.
    try:
        target_path.relative_to(BASE_DIR)
    except ValueError:
        return None

    return target_path


def handle_get(path: str) -> bytes:
    """GET 요청 처리: 파일이 있으면 200 OK, 없으면 404 Not Found."""
    file_path = safe_file_path(path)
    if file_path is None:
        return build_http_response(400, "Bad Request", "Invalid file path.")

    if file_path.exists() and file_path.is_file():
        body = file_path.read_text(encoding="utf-8")
        return build_http_response(200, "OK", body, guess_content_type(path))

    body = f"404 Not Found: {path} does not exist on this server."
    return build_http_response(404, "Not Found", body)


def handle_head(path: str) -> bytes:
    """
    HEAD 요청 처리: GET과 같은 상태 코드를 만들지만 Body는 전송하지 않는다.

    HTTP에서 HEAD는 응답 헤더만 확인할 때 사용한다. 따라서 Content-Length는
    실제 Body 길이를 알려주되, blank line 뒤의 Body 데이터는 보내지 않는다.
    """
    file_path = safe_file_path(path)
    if file_path is None:
        return build_http_response(400, "Bad Request", "Invalid file path.", send_body=False)

    if file_path.exists() and file_path.is_file():
        body = file_path.read_text(encoding="utf-8")
        return build_http_response(200, "OK", body, guess_content_type(path), send_body=False)

    body = f"404 Not Found: {path} does not exist on this server."
    return build_http_response(404, "Not Found", body, send_body=False)


def handle_post(path: str, body: str) -> bytes:
    """
    POST 요청 처리.

    /post.txt 파일이 없으면 새로 만들고 201 Created를 응답한다.
    /post.txt 파일이 이미 있으면 기존 내용 뒤에 append하고 200 OK를 응답한다.
    """
    if path != "/post.txt":
        return build_http_response(404, "Not Found", "POST target path is not supported.")

    file_path = safe_file_path(path)
    if file_path is None:
        return build_http_response(400, "Bad Request", "Invalid file path.")

    file_exists = file_path.exists()
    file_path.parent.mkdir(parents=True, exist_ok=True)

    mode = "a" if file_exists else "w"
    with file_path.open(mode, encoding="utf-8") as file:
        if file_exists:
            file.write("\n")
        file.write(body)

    if file_exists:
        response_body = "POST success: post.txt already existed, so the body was appended."
        return build_http_response(200, "OK", response_body)

    response_body = "POST success: post.txt was created."
    return build_http_response(201, "Created", response_body)


def handle_put(path: str, body: str) -> bytes:
    """
    PUT 요청 처리.

    /put.txt는 파일 내용을 덮어쓰고 204 No Content를 응답한다.
    /readonly.txt는 수정할 수 없는 파일로 가정하고 403 Forbidden을 응답한다.
    """
    if path == "/readonly.txt":
        return build_http_response(403, "Forbidden", "PUT denied: readonly.txt cannot be modified.")

    if path == "/put.txt":
        file_path = safe_file_path(path)
        if file_path is None:
            return build_http_response(400, "Bad Request", "Invalid file path.")

        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(body, encoding="utf-8")
        return build_http_response(204, "No Content", "", send_body=False)

    return build_http_response(404, "Not Found", "PUT target path is not supported.")


def handle_delete(path: str) -> bytes:
    """
    DELETE 요청 처리.

    /post.txt 또는 /put.txt가 존재하면 파일을 삭제하고 200 OK를 응답한다.
    파일이 없으면 404 Not Found를 응답한다. /readonly.txt는 삭제 금지 대상으로
    가정하여 403 Forbidden을 응답한다.
    """
    if path == "/readonly.txt":
        return build_http_response(403, "Forbidden", "DELETE denied: readonly.txt cannot be removed.")

    if path not in ("/post.txt", "/put.txt"):
        return build_http_response(404, "Not Found", "DELETE target path is not supported.")

    file_path = safe_file_path(path)
    if file_path is None:
        return build_http_response(400, "Bad Request", "Invalid file path.")

    if file_path.exists() and file_path.is_file():
        file_path.unlink()
        return build_http_response(200, "OK", f"DELETE success: {path} was removed.")

    return build_http_response(404, "Not Found", f"DELETE failed: {path} does not exist.")


def route_request(method: str, path: str, version: str, body: str) -> bytes:
    """파싱된 Method와 Path에 따라 알맞은 HTTP Response를 선택한다."""
    if version != "HTTP/1.1":
        return build_http_response(400, "Bad Request", "Only HTTP/1.1 is supported.")

    if method == "GET":
        return handle_get(path)
    if method == "HEAD":
        return handle_head(path)
    if method == "POST":
        return handle_post(path, body)
    if method == "PUT":
        return handle_put(path, body)
    if method == "DELETE":
        return handle_delete(path)

    return build_http_response(400, "Bad Request", f"Unsupported method: {method}")


def receive_full_request(client_socket: socket.socket) -> bytes:
    """
    recv()를 사용하여 HTTP Request 전체를 수신한다.

    TCP는 스트림 방식이므로 한 번의 recv()로 전체 메시지가 온다는 보장이 없다.
    먼저 header의 끝인 CRLF CRLF를 찾고, Content-Length가 있으면 Body 길이만큼
    추가로 수신한다.
    """
    raw_data = b""
    client_socket.settimeout(3)

    while b"\r\n\r\n" not in raw_data:
        chunk = client_socket.recv(BUFFER_SIZE)
        if not chunk:
            return raw_data
        raw_data += chunk

    header_bytes, _, body_bytes = raw_data.partition(b"\r\n\r\n")
    header_text = header_bytes.decode("utf-8", errors="replace")
    content_length = 0

    for line in header_text.split("\r\n"):
        if line.lower().startswith("content-length:"):
            try:
                content_length = int(line.split(":", 1)[1].strip())
            except ValueError:
                content_length = 0
            break

    while len(body_bytes) < content_length:
        chunk = client_socket.recv(BUFFER_SIZE)
        if not chunk:
            break
        body_bytes += chunk

    return header_bytes + b"\r\n\r\n" + body_bytes


def run_server() -> None:
    """TCP 기반 HTTP Server를 실행한다."""
    # socket.AF_INET: IPv4, socket.SOCK_STREAM: TCP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        print(f"[SERVER] Listening on http://{HOST}:{PORT}")
        print("[SERVER] Press Ctrl+C to stop.")

        while True:
            client_socket, client_address = server_socket.accept()
            with client_socket:
                raw_request = receive_full_request(client_socket)
                request_text = raw_request.decode("utf-8", errors="replace")
                method, path, version, headers, body = parse_http_request(raw_request)

                print("\n" + "=" * 70)
                print(f"[SERVER] Client address: {client_address}")
                print("[SERVER] Raw request message:")
                print(request_text)
                print(f"[SERVER] Parsed method: {method}")
                print(f"[SERVER] Parsed path: {path}")
                print(f"[SERVER] Parsed version: {version}")
                print(f"[SERVER] Header count: {len(headers)}")
                print(f"[SERVER] Body length: {len(body.encode('utf-8'))} bytes")

                response = route_request(method, path, version, body)
                status_line = response.decode("utf-8", errors="replace").split("\r\n", 1)[0]
                print(f"[SERVER] Response status: {status_line}")
                client_socket.sendall(response)

    except KeyboardInterrupt:
        print("\n[SERVER] KeyboardInterrupt received. Server stopped.")
    finally:
        server_socket.close()


if __name__ == "__main__":
    run_server()
