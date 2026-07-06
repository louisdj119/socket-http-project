# TCP 기반 소켓 프로그래밍 HTTP Server/Client 과제 보고서

## 1. 과제 개요

본 과제는 Python을 사용하여 TCP 기반 소켓 프로그래밍으로 Server와 Client 프로그램을 작성하는 것을 목표로 한다. 일반적인 웹 프레임워크나 Python의 내장 HTTP 서버 기능을 사용하지 않고, `socket` 모듈의 TCP 통신 기능을 직접 사용하여 HTTP 형식의 Request와 Response 메시지를 구성한다.

Client는 사용자가 입력한 Method와 Path를 바탕으로 HTTP/1.1 Request 문자열을 직접 생성한 뒤 Server로 전송한다. Server는 Client가 보낸 Request 메시지를 수신하고, request line을 파싱하여 Method, Path, Version을 분리한다. 이후 Method와 Path에 따라 알맞은 HTTP Response를 직접 만들어 Client에게 전송한다.

실행 환경은 macOS, localhost 주소인 `127.0.0.1`, port `8080`을 기준으로 작성하였다. 같은 PC에서 Server와 Client를 각각 다른 터미널에 실행하여 테스트할 수 있으며, Wireshark에서는 loopback 인터페이스를 선택하여 HTTP 형식 메시지를 확인할 수 있다.

## 2. 구현 목적

이 프로그램의 구현 목적은 TCP 소켓 통신의 기본 흐름과 HTTP 메시지 구조를 직접 이해하는 것이다. 브라우저나 웹 서버 라이브러리를 사용하면 HTTP 처리 과정이 자동으로 숨겨지지만, 본 과제에서는 HTTP 메시지의 각 줄을 직접 작성하고 파싱함으로써 네트워크 계층 위에서 응용 계층 프로토콜이 어떻게 동작하는지 확인할 수 있다.

특히 다음 내용을 학습하는 데 목적이 있다.

- TCP Server Socket 생성 과정 이해
- TCP Client Socket 접속 과정 이해
- `bind()`, `listen()`, `accept()`, `recv()`, `sendall()` 함수 사용법 이해
- HTTP Request Line 구조 이해
- HTTP Response Status Line 구조 이해
- Header와 Body를 구분하는 blank line의 의미 이해
- GET, HEAD, POST, PUT Method의 차이 이해
- Wireshark를 활용한 패킷 캡처 및 HTTP 메시지 확인

## 3. 개발 환경

| 항목 | 내용 |
|---|---|
| 운영체제 | macOS |
| 프로그래밍 언어 | Python 3 |
| 통신 방식 | TCP Socket |
| IP 주소 | 127.0.0.1 |
| Port | 8080 |
| Server 파일 | `server.py` |
| Client 파일 | `client.py` |
| HTML 테스트 파일 | `index.html` |
| 캡처 도구 | Wireshark |

## 4. 사용 기술

본 과제에서 사용한 핵심 기술은 Python의 표준 라이브러리인 `socket`이다. `socket.AF_INET`은 IPv4 주소 체계를 의미하고, `socket.SOCK_STREAM`은 TCP 통신을 의미한다. Server는 TCP 연결을 기다리고 Client는 Server에 접속하여 문자열 기반 HTTP 메시지를 전송한다.

또한 파일 입출력을 사용하여 POST, PUT, DELETE 요청의 결과를 실제 파일에 반영하였다. **POST `/post.txt` 요청은 파일이 없으면 새 파일을 만들고, 이미 있으면 기존 내용 뒤에 append한다. PUT `/put.txt` 요청은 파일 내용을 덮어쓴다. DELETE `/post.txt` 또는 DELETE `/put.txt` 요청은 파일을 삭제한다.** PUT 또는 DELETE `/readonly.txt` 요청은 수정 금지 대상으로 가정하여 403 Forbidden을 응답한다.

## 5. 전체 프로그램 구조

```text
socket_http_project/
├── README/
│   └── CAPTURE_GUIDE.md
├── server.py
├── client.py
├── index.html
├── README.md
├── README.docx
└── README.pdf
```

`server.py`는 TCP Server 역할을 담당한다. Client 접속을 기다린 후 Request를 수신하고, HTTP 메시지를 파싱한 뒤 Response를 생성한다.

`client.py`는 TCP Client 역할을 담당한다. 사용자가 Method와 Path를 입력하면 HTTP Request 문자열을 만들고 Server에 전송한다.

`index.html`은 GET과 HEAD 요청을 테스트하기 위한 정적 HTML 파일이다.

`README.md`는 GitHub에서 확인할 수 있는 기본 설명 문서이다. `README.docx`와 `README.pdf`는 과제 제출용 상세 보고서이며, 10장 이상 분량의 설명을 포함한다.

`README/` 폴더는 선배 예시처럼 Wireshark 캡처 PNG를 저장하기 위한 폴더이다. 실제 캡처 이미지는 본인 PC에서 Wireshark로 직접 촬영한 뒤 `GET_OK.png`, `POST_1_CREATED.png`, `PUT_OK.png` 같은 이름으로 저장하면 된다.

## 6. TCP Socket 통신 흐름

Server는 먼저 소켓을 생성한다. 이때 `socket.socket(socket.AF_INET, socket.SOCK_STREAM)`을 사용한다. 이후 `bind()`로 `127.0.0.1:8080` 주소에 소켓을 연결하고, `listen()`으로 Client 접속 대기 상태에 들어간다.

Client가 접속하면 Server는 `accept()`로 Client와 통신할 새로운 소켓을 얻는다. 이후 `recv()`를 사용해 Client가 보낸 HTTP Request 데이터를 읽고, 처리 결과를 `sendall()`로 Client에게 전송한다.

Client는 Server 주소로 TCP 연결을 생성하고, `sendall()`로 Request를 보낸다. 그 후 Server가 연결을 종료할 때까지 `recv()`를 반복하여 Response 전체를 수신한다.

## 7. HTTP Request 메시지 구조

HTTP Request는 다음 구조를 가진다.

```text
METHOD PATH HTTP/1.1
Host: 127.0.0.1:8080
User-Agent: PythonSocketHTTPClient/1.0
Content-Type: text/plain; charset=utf-8
Content-Length: body길이
Connection: close

Body 내용
```

첫 번째 줄은 request line이다. 예를 들어 `GET /index.html HTTP/1.1`은 Method가 GET이고 Path가 `/index.html`이며 Version이 HTTP/1.1임을 의미한다.

Header는 Request에 대한 부가 정보를 담는다. Host는 접속 대상 서버를 나타내고, Content-Length는 Body의 byte 길이를 나타낸다. blank line은 Header와 Body를 구분한다.

## 8. HTTP Response 메시지 구조

HTTP Response는 다음 구조를 가진다.

```text
HTTP/1.1 200 OK
Date: Mon, 06 Jul 2026 00:00:00 GMT
Server: PythonSocketHTTPServer/1.0
Content-Type: text/html; charset=utf-8
Content-Length: 100
Connection: close

Body 내용
```

첫 번째 줄은 status line이다. Version, status code, reason phrase로 구성된다. Header에는 Date, Server, Content-Type, Content-Length, Connection을 포함하였다. 이 구조를 직접 만들기 때문에 Wireshark에서 HTTP format으로 확인할 수 있다.

## 9. 구현한 Method-Response Case 표

| 번호 | 요청 | 응답 | 설명 |
|---|---|---|---|
| 1 | GET `/index.html` | 200 OK | HTML 파일이 존재하므로 Body와 함께 응답 |
| 2 | GET `/notfound.html` | 404 Not Found | 파일이 없으므로 오류 응답 |
| 3 | HEAD `/index.html` | 200 OK | 파일은 존재하지만 Body 없이 Header만 응답 |
| 4 | HEAD `/missing.html` | 404 Not Found | 파일이 없고 Body 없이 Header만 응답 |
| 5 | POST `/post.txt` | 201 Created | 파일이 없으면 새 파일 생성 |
| 6 | POST `/post.txt` | 200 OK | 파일이 이미 있으면 기존 내용 뒤에 append |
| 7 | PUT `/put.txt` | 204 No Content | 파일 내용을 덮어쓰고 Body 없이 응답 |
| 8 | PUT `/readonly.txt` | 403 Forbidden | 수정 금지 파일로 가정하여 거부 |
| 9 | DELETE `/post.txt` | 200 OK | 생성된 파일 삭제 |
| 10 | DELETE `/readonly.txt` | 403 Forbidden | 삭제 금지 파일로 가정하여 거부 |
| 11 | PATCH `/index.html` | 400 Bad Request | 지원하지 않는 Method 처리 |

## 10. server.py 코드 설명

`server.py`는 Server Socket을 생성하고 Client의 HTTP Request를 처리한다. `run_server()` 함수는 전체 Server 실행 흐름을 담당한다. 내부에서 TCP 소켓을 만들고, `bind()`, `listen()`, `accept()`를 순서대로 호출한다.

`receive_full_request()` 함수는 TCP로 들어오는 데이터를 읽는다. TCP는 스트림 방식이므로 한 번의 `recv()`만으로 전체 메시지가 들어온다고 보장할 수 없다. 따라서 Header의 끝을 의미하는 `\r\n\r\n`이 올 때까지 먼저 수신하고, Content-Length 값이 있으면 Body 길이만큼 추가로 수신한다.

`parse_http_request()` 함수는 Request 메시지를 문자열로 변환한 뒤 request line을 분리한다. request line에서 Method, Path, Version을 얻고, Header는 딕셔너리 형태로 저장한다.

`route_request()` 함수는 Method에 따라 GET, HEAD, POST, PUT, DELETE 처리 함수로 분기한다. 지원하지 않는 Method가 들어오면 400 Bad Request를 응답한다.

## 11. client.py 코드 설명

`client.py`는 사용자 입력을 받아 HTTP Request 문자열을 직접 만든다. 사용자는 Method와 Path를 입력하고, POST 또는 PUT인 경우 Body도 입력한다.

`build_request()` 함수는 request line, header, blank line, body 순서로 메시지를 만든다. 이때 Content-Length는 Body를 UTF-8로 인코딩한 byte 길이를 계산하여 넣는다.

`send_request()` 함수는 TCP 소켓을 생성하고 Server에 접속한다. 이후 `sendall()`로 Request를 보내고, `recv()`를 반복하여 Response 전체를 수신한다.

## 12. 실행 방법

터미널 1에서 Server를 실행한다.

```bash
python3 server.py
```

터미널 2에서 Client를 실행한다.

```bash
python3 client.py
```

Client 실행 후 Method와 Path를 입력한다. POST와 PUT은 Body 입력도 진행한다.

## 13. GET 실행 결과 설명

GET `/index.html`은 서버의 프로젝트 폴더에 있는 `index.html` 파일을 찾는다. 파일이 존재하면 Server는 HTML 내용을 Body에 담아 200 OK 응답을 보낸다.

GET `/notfound.html`은 존재하지 않는 파일을 요청하는 경우이다. Server는 파일을 찾을 수 없으므로 404 Not Found를 응답한다.

## 14. HEAD 실행 결과 설명

HEAD `/index.html`은 GET과 같은 상태 판단을 수행하지만 Body를 전송하지 않는다. 따라서 Response Header에는 Content-Length가 포함되지만, blank line 뒤에 HTML 내용은 오지 않는다.

HEAD `/missing.html`은 존재하지 않는 파일에 대한 HEAD 요청이다. Server는 404 Not Found 상태를 응답하지만, HEAD Method의 특성에 따라 Body는 보내지 않는다.

## 15. POST 실행 결과 설명

POST `/post.txt`는 Body 내용을 서버의 프로젝트 폴더에 `post.txt` 파일로 저장한다. 처음 실행할 때 파일이 없으면 새 파일을 만들고 201 Created를 응답한다.

같은 요청을 다시 실행하면 `post.txt`가 이미 존재한다. 이때 Server는 기존 내용을 지우지 않고 Body를 파일 뒤에 추가한 뒤 200 OK를 응답한다.

## 16. PUT 실행 결과 설명

PUT `/put.txt`는 Body 내용으로 프로젝트 폴더의 `put.txt` 파일을 덮어쓴다. PUT은 리소스를 생성하거나 교체하는 의미를 가지므로, 본 프로그램에서는 기존 내용이 있더라도 새 Body로 교체한다. 응답은 204 No Content이며 Body는 보내지 않는다.

**주의:** 204 No Content는 실패가 아니라 HTTP 표준에서 "요청은 성공했지만 응답 Body는 없다"는 의미이다. 영상에서는 PUT 실행 직후 Server 터미널의 `Response status: HTTP/1.1 204 No Content` 로그를 보여주고, 이어서 GET `/put.txt`를 실행하여 실제 파일 내용이 변경되었음을 확인하면 된다.

PUT `/readonly.txt`는 수정할 수 없는 파일로 가정한다. Server는 파일을 변경하지 않고 403 Forbidden을 응답한다.

## 17. 잘못된 요청 처리 결과 설명

PATCH `/index.html`처럼 지원하지 않는 Method가 들어오면 Server는 400 Bad Request를 응답한다. 이 과제에서는 GET, HEAD, POST, PUT, DELETE를 정상 Method로 처리하고 나머지 Method는 잘못된 요청으로 분류하였다.

DELETE `/post.txt` 또는 DELETE `/put.txt`는 파일 삭제 기능을 확인하기 위한 요청이다. 파일이 존재하면 삭제 후 200 OK를 응답하고, 파일이 없으면 404 Not Found를 응답한다. DELETE `/readonly.txt`는 삭제 금지 파일로 가정하여 403 Forbidden을 응답한다.

## 18. Wireshark 캡처 방법

macOS에서 localhost 통신을 캡처할 때는 Wireshark에서 `lo0` 인터페이스를 선택한다. 캡처를 시작한 뒤 Client를 실행하고 요청을 전송한다. Display Filter에는 다음 값을 입력한다.

```text
tcp.port == 8080
```

HTTP로 자동 표시되지 않으면 패킷을 우클릭하고 `Decode As...` 메뉴에서 TCP port 8080을 HTTP로 지정한다. 이후 패킷 상세 영역에서 Request Line, Header, Response Status Line을 확인할 수 있다.

## 19. 영상 녹화 시나리오

영상은 5분 이상으로 녹화하고, 화면에 날짜가 보이도록 한다. 먼저 프로젝트 폴더와 `server.py`, `client.py`, `index.html`, `README.md` 파일을 보여준다. 다음으로 Server 터미널에서 `python3 server.py`를 실행한다.

그 후 Client 터미널에서 `python3 client.py`를 여러 번 실행하면서 GET, POST, PUT, DELETE, PATCH 요청을 차례로 입력한다. HEAD는 과제 요구사항 확인용으로 짧게만 보여주고, 영상 설명은 파일 제어가 잘 보이는 GET/POST/PUT/DELETE에 집중한다. 각 요청마다 Client 화면에는 보낸 Request와 받은 Response가 출력되고, Server 화면에는 Client 주소, 원본 Request, 파싱된 Method/Path/Version, 응답 상태 코드가 출력된다.

마지막으로 Wireshark 화면에서 `tcp.port == 8080` 필터를 적용하고, GET, POST, PUT, DELETE 요청 패킷과 응답 패킷을 확인한다. POST와 PUT은 Body가 보이는지도 확인한다.

## 20. 전체 결과 요약

본 프로그램은 Python TCP Socket을 직접 사용하여 HTTP 형식의 Request와 Response를 구현하였다. Server는 `bind()`, `listen()`, `accept()`, `recv()`, `sendall()`을 사용하고, Client는 사용자 입력을 바탕으로 HTTP Request 문자열을 직접 생성한다.

총 11개의 Method-Response case를 구현하였으며, GET, HEAD, POST, PUT, DELETE와 잘못된 Method 처리까지 포함하였다. 또한 HTTP 메시지의 status line, header, blank line, body 구조를 직접 작성하였으므로 Wireshark에서 HTTP format으로 캡처하고 분석할 수 있다.
