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
HOST = os.getenv('HOST', '192.168.0.5')
PORT = int(os.getenv('PORT', 9999))
JPEG_QUALITY = int(os.getenv('JPEG_QUALITY', 60))
MAX_CHUNK_SIZE = 60000
KEYFRAME_INTERVAL = 5
TARGET_FPS = 30
SECRET_KEY = os.getenv('SECRET_KEY').encode()

# --- Packet Types ---
TYPE_KEYFRAME = 0
TYPE_DIFF = 1

def main():
    cipher = Fernet(SECRET_KEY)
    
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            print(f"キャプチャ対象: {monitor['width']}x{monitor['height']}")
            print(f"{HOST}:{PORT} へ差分エンコードでの送信を開始します。")

            frame_id = 0
            previous_frame = None
            last_keyframe_time = 0
            
            while True:
                try:
                    now = time.time()
                    img_mss = sct.grab(monitor)
                    current_frame = cv2.cvtColor(np.array(img_mss), cv2.COLOR_BGRA2BGR)
                    
                    payload = b''
                    
                    # --- ★ 修正点 ★ ---
                    # キーフレームを送信するか、差分を送信するかを決定
                    is_keyframe_time = (now - last_keyframe_time) > KEYFRAME_INTERVAL
                    
                    if previous_frame is None or is_keyframe_time:
                        # 全画面（キーフレーム）を送信
                        print(">>> Sending KEYFRAME (full update)") # ★デバッグ表示を追加
                        ret, jpeg_data = cv2.imencode('.jpg', current_frame, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
                        if not ret: continue
                        payload = struct.pack('>B', TYPE_KEYFRAME) + jpeg_data.tobytes()
                        last_keyframe_time = now
                    else:
                        # 差分を送信
                        diff = cv2.absdiff(current_frame, previous_frame)
                        is_changed = np.any(diff > 15, axis=2)
                        
                        changed_y, changed_x = np.where(is_changed)
                        
                        if len(changed_y) == 0:
                            time.sleep(1 / TARGET_FPS)
                            continue
                        
                        x, y = np.min(changed_x), np.min(changed_y)
                        w, h = np.max(changed_x) - x + 1, np.max(changed_y) - y + 1
                        
                        cropped_diff = current_frame[y:y+h, x:x+w]
                        
                        ret, jpeg_data = cv2.imencode('.jpg', cropped_diff, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
                        if not ret: continue
                        
                        header = struct.pack('>BHH', TYPE_DIFF, x, y)
                        payload = header + jpeg_data.tobytes()

                    # 送信処理
                    encrypted_data = cipher.encrypt(payload)
                    data_size = len(encrypted_data)
                    total_chunks = (data_size // MAX_CHUNK_SIZE) + 1
                    
                    for i in range(total_chunks):
                        start = i * MAX_CHUNK_SIZE
                        end = start + MAX_CHUNK_SIZE
                        header = struct.pack('QII', frame_id, total_chunks, i)
                        sock.sendto(header + encrypted_data[start:end], (HOST, PORT))

                    previous_frame = current_frame
                    frame_id = (frame_id + 1) % 1000000
                    
                    time.sleep(1 / TARGET_FPS)

                except KeyboardInterrupt:
                    print("\n送信を停止しました。")
                    break
                except Exception as e:
                    pass

if __name__ == "__main__":
    main()