"""
TCP 메시지 클라이언트 - Windows 호스트에서 실행
"""
import socket

SERVER_IP = "192.168.x.x"  # Ubuntu VM의 IP 주소로 변경 (VM에서 `ip addr` 명령으로 확인)
PORT = 9000


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER_IP, PORT))
        print(f"서버 {SERVER_IP}:{PORT} 에 연결됨")
        print("메시지 입력 후 Enter (종료: 'quit')\n")

        while True:
            message = input("클라이언트 메시지: ")
            if message.lower() == "quit":
                break

            s.sendall(message.encode("utf-8"))

            reply = s.recv(4096).decode("utf-8")
            print(f"[서버 응답] {reply}\n")


if __name__ == "__main__":
    main()
