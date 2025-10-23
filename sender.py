# sender.py
import cv2
import mss
import numpy as np
import socket
import time

# --- 設定項目 ---
HOST = '192.168.0.5' # 送信先のIPアドレス（receiver.pyを動かすPCのIP）
PORT = 9999           # 送信先のポート番号
WIDTH = 640           # キャプチャする幅
HEIGHT = 480          # キャプチャする高さ
JPEG_QUALITY = 40     # JPEGの品質 (0-100)
# ----------------

def main():
    """
    画面をキャプチャし、UDPで送信するメイン関数
    """
    # ソケットを作成
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        # mssを初期化
        with mss.mss() as sct:
            monitor = {"top": 40, "left": 0, "width": WIDTH, "height": HEIGHT}

            print(f"{HOST}:{PORT} へ送信を開始します。Ctrl+Cで停止します。")
            
            # FPS計算用
            last_time = time.time()
            frame_count = 0
            
            while True:
                try:
                    # 画面キャプチャ
                    img_mss = sct.grab(monitor)
                    img_np = np.frombuffer(img_mss.rgb, dtype=np.uint8).reshape((HEIGHT, WIDTH, 3))
                    
                    # JPEGにエンコード
                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
                    _, encoded_img = cv2.imencode('.jpg', img_np, encode_param)

                    # データを送信
                    sock.sendto(encoded_img.tobytes(), (HOST, PORT))
                    
                    # FPS計算と表示
                    frame_count += 1
                    current_time = time.time()
                    if current_time - last_time > 1.0:
                        fps = frame_count / (current_time - last_time)
                        print(f"FPS: {fps:.2f}")
                        frame_count = 0
                        last_time = current_time

                except KeyboardInterrupt:
                    print("\n送信を停止しました。")
                    break

if __name__ == "__main__":
    main()