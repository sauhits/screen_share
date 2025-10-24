# sender.py
import cv2
import mss
import numpy as np
import socket
import time
import struct
from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

load_dotenv()

# --- 設定項目 ---
HOST = os.getenv('HOST', '192.168.1.10')
PORT = int(os.getenv('PORT', 9999))
JPEG_QUALITY = int(os.getenv('JPEG_QUALITY', 50))
MAX_CHUNK_SIZE = 60000
TARGET_FPS = 20
SECRET_KEY = os.getenv('SECRET_KEY').encode()
END_STREAM_MSG = b'--STREAM_END--' # 終了通知メッセージ

def main():
    cipher = Fernet(SECRET_KEY)
    
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            print(f"キャプチャ対象: {monitor['width']}x{monitor['height']}")
            print(f"{HOST}:{PORT} へ全画面エンコードでの送信を開始します。")

            frame_id = 0
            
            try:
                while True:
                    # 1. 画面キャプチャと変換
                    img_mss = sct.grab(monitor)
                    current_frame = cv2.cvtColor(np.array(img_mss), cv2.COLOR_BGRA2BGR)
                    
                    # 2. JPEGにエンコード
                    ret, jpeg_data = cv2.imencode('.jpg', current_frame, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
                    if not ret:
                        continue
                    
                    payload = jpeg_data.tobytes()

                    # 3. 暗号化とチャンク分割
                    encrypted_data = cipher.encrypt(payload)
                    data_size = len(encrypted_data)
                    total_chunks = (data_size // MAX_CHUNK_SIZE) + 1
                    
                    # 4. 各チャンクを送信
                    for i in range(total_chunks):
                        start = i * MAX_CHUNK_SIZE
                        end = start + MAX_CHUNK_SIZE
                        header = struct.pack('QII', frame_id, total_chunks, i)
                        sock.sendto(header + encrypted_data[start:end], (HOST, PORT))

                    frame_id = (frame_id + 1) % 1000000
                    
                    # 5. FPS制御
                    time.sleep(1 / TARGET_FPS)

            except KeyboardInterrupt:
                print("\n送信を停止します。終了通知を送信中...")
                # --- ★ 修正点：終了通知を送信 ---
                for _ in range(5):
                    sock.sendto(END_STREAM_MSG, (HOST, PORT))
                    time.sleep(0.01)
                print("終了通知を送信しました。")
                # ---------------------------------
            except Exception as e:
                print(f"エラー: {e}")

if __name__ == "__main__":
    main()