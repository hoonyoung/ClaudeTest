# TCP 텍스트 메시지 예제

VMware Ubuntu VM(서버) ↔ Windows 호스트(클라이언트) 간 텍스트 메시지 교환

## 구성

```
Windows 호스트 (client.py)  ←→  Ubuntu VM (server.py)
```

## 실행 방법

### 1단계: Ubuntu VM IP 확인

Ubuntu VM 터미널에서:
```bash
ip addr show
# 또는
hostname -I
```
`192.168.x.x` 형태의 IP를 메모해둔다.

### 2단계: Ubuntu VM - 방화벽 허용 (필요 시)

```bash
sudo ufw allow 9000/tcp
```

### 3단계: Ubuntu VM에서 서버 실행

```bash
python3 server.py
```

### 4단계: client.py 수정

`client.py` 파일에서 `SERVER_IP`를 Ubuntu VM의 실제 IP로 변경:
```python
SERVER_IP = "192.168.x.x"  # 실제 IP로 변경
```

### 5단계: Windows에서 클라이언트 실행

```cmd
python client.py
```

## 동작 흐름

1. 클라이언트가 메시지를 입력하여 서버로 전송
2. 서버가 메시지를 출력하고 응답을 입력
3. 클라이언트가 서버 응답을 수신하여 출력
4. 반복 (`quit` 입력 시 클라이언트 종료)
