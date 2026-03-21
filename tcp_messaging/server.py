"""
TCP 메시지 서버 - Ubuntu VM에서 실행

수신된 파일은 'received_files/' 디렉토리에 저장됩니다.
"""
import socket
import threading
import os

HOST = "0.0.0.0"  # 모든 네트워크 인터페이스에서 수신
PORT = 9000
SAVE_DIR = "received_files"


def handle_file(conn, filename, filesize):
    os.makedirs(SAVE_DIR, exist_ok=True)
    save_path = os.path.join(SAVE_DIR, filename)

    conn.sendall(b"READY\n")

    received = 0
    with open(save_path, "wb") as f:
        while received < filesize:
            chunk = conn.recv(min(4096, filesize - received))
            if not chunk:
                break
            f.write(chunk)
            received += len(chunk)

    if received == filesize:
        print(f"[파일 저장 완료] {save_path} ({filesize} bytes)")
        conn.sendall(f"OK:{filename} 저장 완료 ({filesize} bytes)".encode("utf-8"))
    else:
        print(f"[파일 오류] {filename}: {received}/{filesize} bytes 수신")
        conn.sendall(b"ERROR:전송 불완전")


def handle_client(conn, addr):
    print(f"[연결됨] {addr}")
    try:
        # 헤더 수신 (한 줄)
        header_buf = b""
        while b"\n" not in header_buf:
            chunk = conn.recv(1)
            if not chunk:
                return
            header_buf += chunk

        header = header_buf.decode("utf-8").strip()

        if header.startswith("FILE:"):
            # "FILE:<파일명>:<파일크기>"
            _, filename, filesize_str = header.split(":", 2)
            filesize = int(filesize_str)
            print(f"[파일 수신 시작] {filename} ({filesize} bytes)")
            handle_file(conn, filename, filesize)

        elif header.startswith("MSG:"):
            message = header[4:]
            print(f"[클라이언트] {message}")
            reply = input("서버 응답 입력: ")
            conn.sendall(reply.encode("utf-8"))

        else:
            print(f"[알 수 없는 헤더] {header}")

    except (ConnectionResetError, ValueError) as e:
        print(f"[오류] {addr}: {e}")
    finally:
        conn.close()
        print(f"[연결 종료] {addr}")


def main():
    os.makedirs(SAVE_DIR, exist_ok=True)
    print(f"파일 저장 경로: {os.path.abspath(SAVE_DIR)}")

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
