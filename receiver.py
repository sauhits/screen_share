# receiver.py
import cv2
import numpy as np
import socket
import struct
from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

load_dotenv()

# --- 設定項目 ---
HOST = '0.0.0.0'
PORT = int(os.getenv('PORT', 9999))
BUFFER_SIZE = 65536
SECRET_KEY = os.getenv('SECRET_KEY').encode()
END_STREAM_MSG = b'--STREAM_END--' # 終了通知メッセージ

def main():
    cipher = Fernet(SECRET_KEY)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((HOST, PORT))
        print(f"{HOST}:{PORT} で全画面データを受信待機中...")
        
        buffers = {}
        current_screen = None

        while True:
            try:
                data, _ = sock.recvfrom(BUFFER_SıZE)

                # --- ★ 修正点：終了通知をチェック ---
                if data == END_STREAM_MSG:
                    print("送信側が終了しました。受信を停止します。")
                    break # ループを抜けて終了
                # ------------------------------------

                # 1. チャンク受信と再構築 (通常の処理)
                header = data[:16]
                chunk_data = data[16:]
                frame_id, total_chunks, chunk_id = struct.unpack('QII', header)

                if frame_id not in buffers:
                    if len(buffers) > 5:
                        oldest_frame = min(buffers.keys())
                        del buffers[oldest_frame]
                    buffers[frame_id] = [None] * total_chunks
                
                if frame_id in buffers:
                    buffers[frame_id][chunk_id] = chunk_data
                
                # 2. 全チャンクが揃ったら処理
                if frame_id in buffers and all(c is not None for c in buffers[frame_id]):
                    full_encrypted_data = b''.join(buffers[frame_id])
                    del buffers[frame_id]

                    # 3. 復号
                    try:
                        payload = cipher.decrypt(full_encrypted_data)
                    except Exception:
                        continue
                    
                    # 4. 全画面としてデコード
                    img_np = np.frombuffer(payload, dtype=np.uint8)
                    current_screen = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

                # 5. 画面表示
                if current_screen is not None:
                    cv2.imshow("Receiver", current_screen)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            except Exception:
                pass

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()