"""
TCP 메시지 서버 - Ubuntu VM에서 실행
"""
import socket
import threading

HOST = "0.0.0.0"  # 모든 네트워크 인터페이스에서 수신
PORT = 9000


def handle_client(conn, addr):
    print(f"[연결됨] {addr}")
    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break
            message = data.decode("utf-8")
            print(f"[클라이언트] {message}")

            reply = input("서버 응답 입력: ")
            conn.sendall(reply.encode("utf-8"))
    except ConnectionResetError:
        pass
    finally:
        conn.close()
        print(f"[연결 종료] {addr}")


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"서버 시작 - {HOST}:{PORT} 대기 중...")

        while True:
            conn, addr = s.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            thread.start()


if __name__ == "__main__":
    main()
