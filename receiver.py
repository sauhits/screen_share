# receiver.py
import cv2
import numpy as np
import socket
import struct
from cryptography.fernet import Fernet
import os 
from dotenv import load_dotenv 

# .envファイルから環境変数を読み込む
load_dotenv()

# --- 設定項目 ---
HOST = '0.0.0.0'
PORT = int(os.getenv('PORT', 9999))
BUFFER_SIZE = 65536
SECRET_KEY = os.getenv('SECRET_KEY').encode() 

# --- Packet Types ---
TYPE_KEYFRAME = 0
TYPE_DIFF = 1
# --------------------

def main():
    cipher = Fernet(SECRET_KEY)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((HOST, PORT))
        print(f"{HOST}:{PORT} で差分データを受信待機中...")
        
        buffers = {}
        current_screen = None

        while True:
            try:
                data, _ = sock.recvfrom(BUFFER_SIZE)
                header = data[:16]
                chunk_data = data[16:]
                frame_id, total_chunks, chunk_id = struct.unpack('QII', header)

                if frame_id not in buffers:
                    if len(buffers) > 5: # バッファが溜まりすぎないように
                        oldest_frame = min(buffers.keys())
                        del buffers[oldest_frame]
                    buffers[frame_id] = [None] * total_chunks
                
                if frame_id in buffers:
                    buffers[frame_id][chunk_id] = chunk_data
                
                if frame_id in buffers and all(c is not None for c in buffers[frame_id]):
                    full_encrypted_data = b''.join(buffers[frame_id])
                    del buffers[frame_id]

                    try:
                        payload = cipher.decrypt(full_encrypted_data)
                    except Exception:
                        continue
                    
                    packet_type = struct.unpack('>B', payload[:1])[0]

                    if packet_type == TYPE_KEYFRAME:
                        jpeg_data = payload[1:]
                        img_np = np.frombuffer(jpeg_data, dtype=np.uint8)
                        current_screen = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

                    elif packet_type == TYPE_DIFF and current_screen is not None:
                        header = payload[1:5]
                        x, y = struct.unpack('>HH', header)
                        jpeg_data = payload[5:]
                        
                        img_np = np.frombuffer(jpeg_data, dtype=np.uint8)
                        patch = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
                        
                        if patch is not None:
                            h, w, _ = patch.shape
                            if y + h <= current_screen.shape[0] and x + w <= current_screen.shape[1]:
                                current_screen[y:y+h, x:x+w] = patch
                
                if current_screen is not None:
                    cv2.imshow("Receiver", current_screen)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            except Exception as e:
                # print(f"エラー: {e}") # デバッグ時以外はコメントアウト推奨
                pass

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()