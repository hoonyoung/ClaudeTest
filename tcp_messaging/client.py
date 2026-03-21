"""
TCP 메시지 클라이언트 - Windows 호스트에서 실행

사용법:
  메시지 모드: python client.py
  파일 전송:   python client.py <파일명>
"""
import socket
import sys
import os
import struct

SERVER_IP = "192.168.x.x"  # Ubuntu VM의 IP 주소로 변경 (VM에서 `ip addr` 명령으로 확인)
PORT = 9000


def send_file(filepath):
    if not os.path.isfile(filepath):
        print(f"오류: 파일을 찾을 수 없습니다 - {filepath}")
        sys.exit(1)

    filename = os.path.basename(filepath)
    filesize = os.path.getsize(filepath)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER_IP, PORT))
        print(f"서버 {SERVER_IP}:{PORT} 에 연결됨")

        # 파일 전송 요청 헤더: "FILE:<파일명>:<파일크기>\n"
        header = f"FILE:{filename}:{filesize}\n"
        s.sendall(header.encode("utf-8"))

        # 서버 준비 응답 대기
        response = s.recv(16).decode("utf-8").strip()
        if response != "READY":
            print(f"서버 오류: {response}")
            return

        # 파일 데이터 전송
        with open(filepath, "rb") as f:
            sent = 0
            while sent < filesize:
                chunk = f.read(4096)
                if not chunk:
                    break
                s.sendall(chunk)
                sent += len(chunk)
                print(f"\r전송 중: {sent}/{filesize} bytes ({sent*100//filesize}%)", end="")

        print()

        # 완료 응답 수신
        result = s.recv(64).decode("utf-8").strip()
        print(f"[서버 응답] {result}")


def send_messages():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER_IP, PORT))
        print(f"서버 {SERVER_IP}:{PORT} 에 연결됨")
        print("메시지 입력 후 Enter (종료: 'quit')\n")

        while True:
            message = input("클라이언트 메시지: ")
            if message.lower() == "quit":
                break

            # 일반 메시지 헤더: "MSG:<내용>\n"
            header = f"MSG:{message}\n"
            s.sendall(header.encode("utf-8"))

            reply = s.recv(4096).decode("utf-8")
            print(f"[서버 응답] {reply}\n")


if __name__ == "__main__":
    if len(sys.argv) == 2:
        send_file(sys.argv[1])
    else:
        send_messages()
