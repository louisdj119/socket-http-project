# Wireshark Capture Image Guide

이 폴더는 Wireshark 캡처 PNG를 저장하는 위치입니다.

선배 예시처럼 GitHub에 캡처 화면까지 같이 올리려면, macOS Wireshark에서 `lo0` 인터페이스를 선택하고 Display Filter에 `tcp.port == 8080`을 적용한 뒤 아래 이름으로 저장하면 됩니다.

권장 캡처 파일:

- `GET_OK.png`: `GET /index.html` 요청과 `HTTP/1.1 200 OK` 응답
- `GET_NO.png`: `GET /notfound.html` 요청과 `HTTP/1.1 404 Not Found` 응답
- `HEAD_OK.png`: `HEAD /index.html` 요청과 `HTTP/1.1 200 OK` 응답
- `POST_1_CREATED.png`: 첫 번째 `POST /post.txt` 요청과 `HTTP/1.1 201 Created` 응답
- `POST_2_OK.png`: 두 번째 `POST /post.txt` 요청과 `HTTP/1.1 200 OK` 응답
- `GET_POST_RESULT.png`: `GET /post.txt` 요청으로 POST append 결과 확인
- `PUT_OK.png`: `PUT /put.txt` 요청과 `HTTP/1.1 204 No Content` 응답
- `GET_PUT_RESULT.png`: `GET /put.txt` 요청으로 PUT 덮어쓰기 결과 확인
- `DELETE_OK.png`: `DELETE /post.txt` 요청과 `HTTP/1.1 200 OK` 응답
- `BAD_REQUEST.png`: `PATCH /index.html` 요청과 `HTTP/1.1 400 Bad Request` 응답

캡처할 때 화면에 보이면 좋은 부분:

1. 상단 Display Filter: `tcp.port == 8080`
2. 패킷 목록의 Protocol: `HTTP`
3. Info 열의 Method 또는 Status: `GET /index.html HTTP/1.1`, `HTTP/1.1 200 OK` 등
4. 하단 상세 영역의 Request Line 또는 Status Line

주의: 다른 사람의 캡처 이미지는 제출하지 말고, 본인 PC에서 직접 실행한 패킷 캡처 화면을 저장해야 합니다.
