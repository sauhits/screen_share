# receiver.py
import cv2
import numpy as np
import socket
import struct
from cryptography.fernet import Fernet 
from dotenv import load_dotenv
import os

# --- 設定項目 ---
HOST = '0.0.0.0'
PORT = 9999
BUFFER_SIZE = 65536

# sender.pyと全く同じ秘密鍵をここに貼り付けてください
load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')

def main():
    # --- 復号関連 ---
    cipher = Fernet(SECRET_KEY) # ★ 復号器を初期化

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((HOST, PORT))
        print(f"{HOST}:{PORT} で暗号化通信を受信待機中...'q'キーで終了します。")
        
        buffers = {}
        current_frame_id = -1

        while True:
            try:
                data, addr = sock.recvfrom(BUFFER_SIZE)
                
                header = data[:16]
                chunk_data = data[16:]
                frame_id, total_chunks, chunk_id = struct.unpack('QII', header)

                if frame_id not in buffers:
                    buffers[frame_id] = [None] * total_chunks
                
                buffers[frame_id][chunk_id] = chunk_data
                
                if frame_id > current_frame_id:
                    if current_frame_id in buffers:
                        del buffers[current_frame_id]
                    current_frame_id = frame_id

                if all(c is not None for c in buffers[frame_id]):
                    full_data = b''.join(buffers[frame_id])
                    
                    # --- ★ 復号処理 ---
                    try:
                        decrypted_data = cipher.decrypt(full_data)
                    except Exception:
                        # 復号に失敗したデータは無視
                        print("復号エラー、パケットを破棄します。")
                        del buffers[frame_id]
                        continue
                    # --------------------

                    img_np = np.frombuffer(decrypted_data, dtype=np.uint8)
                    img_decode = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

                    if img_decode is not None:
                        cv2.imshow("Receiver (Encrypted)", img_decode)
                    
                    del buffers[frame_id]

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            except Exception as e:
                pass

    cv2.destroyAllWindows()
    print("受信を終了しました。")

if __name__ == "__main__":
    main()