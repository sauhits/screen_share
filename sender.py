# sender.py
import cv2
import mss
import numpy as np
import socket
import time
import struct
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import os

# --- 設定項目 ---
HOST = '192.168.0.5' # 送信先のIPアドレス
PORT = 9999
JPEG_QUALITY = 50
MAX_CHUNK_SIZE = 60000

# ステップ2で生成した秘密鍵をここに貼り付けてください
load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')

def main():
    # --- 暗号化関連 ---
    cipher = Fernet(SECRET_KEY) 

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            print(f"キャプチャ対象: {monitor['width']}x{monitor['height']}")
            print(f"{HOST}:{PORT} へ暗号化通信を開始します。Ctrl+Cで停止します。")
            
            frame_id = 0

            while True:
                try:
                    img_mss = sct.grab(monitor)
                    img_np = np.array(img_mss)
                    img_bgr = cv2.cvtColor(img_np, cv2.COLOR_BGRA2BGR)
                    
                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
                    _, encoded_img = cv2.imencode('.jpg', img_bgr, encode_param)
                    
                    # --- ★ 暗号化処理 ---
                    encrypted_data = cipher.encrypt(encoded_img.tobytes())
                    data_size = len(encrypted_data)
                    # --------------------
                    
                    total_chunks = (data_size // MAX_CHUNK_SIZE) + 1
                    
                    for i in range(total_chunks):
                        start = i * MAX_CHUNK_SIZE
                        end = start + MAX_CHUNK_SIZE
                        chunk = encrypted_data[start:end]

                        header = struct.pack('QII', frame_id, total_chunks, i)
                        sock.sendto(header + chunk, (HOST, PORT))

                    frame_id += 1
                    time.sleep(1/30)

                except KeyboardInterrupt:
                    print("\n送信を停止しました。")
                    break
                except Exception as e:
                    print(f"エラー: {e}")
                    pass

if __name__ == "__main__":
    main()