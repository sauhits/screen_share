# receiver.py
import cv2
import numpy as np
import socket

# --- 設定項目 ---
HOST = '0.0.0.0'      # 待ち受けるIPアドレス（0.0.0.0は全てのネットワークから）
PORT = 9999           # 待ち受けるポート番号
BUFFER_SIZE = 65536   # 一度に受信するバッファサイズ
# ----------------

def main():
    """
    UDPでデータを受信し、画面に表示するメイン関数
    """
    # ソケットを作成
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        # IPアドレスとポートを紐付け
        sock.bind((HOST, PORT))
        print(f"{HOST}:{PORT} で受信待機中...'q'キーで終了します。")

        while True:
            try:
                # データを受信
                data, addr = sock.recvfrom(BUFFER_SIZE)
                
                # 受信したバイナリデータをnumpy配列に変換
                img_np = np.frombuffer(data, dtype=np.uint8)
                
                # numpy配列を画像にデコード
                img_decode = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

                # 画像が表示可能かチェック
                if img_decode is not None:
                    # ウィンドウに表示
                    cv2.imshow("Receiver", img_decode)
                
                # 'q'キーで終了
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            except Exception as e:
                print(f"エラーが発生しました: {e}")

    cv2.destroyAllWindows()
    print("受信を終了しました。")

if __name__ == "__main__":
    main()