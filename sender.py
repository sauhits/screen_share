# sender.py
import cv2
import mss
import numpy as np
import socket
import time
import struct

# --- 設定項目 ---
HOST = '192.168.0.5' # 送信先のIPアドレス（必ずお使いの環境に合わせて変更してください）
PORT = 9999
JPEG_QUALITY = 50
MAX_CHUNK_SIZE = 60000  # 1チャンクの最大サイズ (UDPの上限より小さく)
# ----------------

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            print(f"キャプチャ対象: {monitor['width']}x{monitor['height']}")
            print(f"{HOST}:{PORT} へ送信を開始します。Ctrl+Cで停止します。")
            
            frame_id = 0 # フレームを識別するためのID

            while True:
                try:
                    img_mss = sct.grab(monitor)
                    img_np = np.array(img_mss)
                    img_bgr = cv2.cvtColor(img_np, cv2.COLOR_BGRA2BGR)
                    
                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
                    _, encoded_img = cv2.imencode('.jpg', img_bgr, encode_param)
                    
                    data = encoded_img.tobytes()
                    data_size = len(data)

                    # データの分割
                    total_chunks = (data_size // MAX_CHUNK_SIZE) + 1
                    
                    # 各チャンクをヘッダ付きで送信
                    for i in range(total_chunks):
                        start = i * MAX_CHUNK_SIZE
                        end = start + MAX_CHUNK_SIZE
                        chunk = data[start:end]

                        # ヘッダ: [フレームID, 総チャンク数, 現在のチャンク番号]
                        header = struct.pack('QII', frame_id, total_chunks, i)
                        
                        # ヘッダとチャンクを結合して送信
                        sock.sendto(header + chunk, (HOST, PORT))

                    frame_id += 1
                    time.sleep(1/30) # 30fps程度に制限

                except KeyboardInterrupt:
                    print("\n送信を停止しました。")
                    break
                except Exception as e:
                    print(f"エラー: {e}")
                    pass

if __name__ == "__main__":
    main()