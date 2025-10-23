# receiver.py
import cv2
import numpy as np
import socket
import struct

# --- 設定項目 ---
HOST = '0.0.0.0'
PORT = 9999
BUFFER_SIZE = 65536
# ----------------

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((HOST, PORT))
        print(f"{HOST}:{PORT} で受信待機中...'q'キーで終了します。")
        
        buffers = {} # フレームごとにチャンクを保存する辞書
        current_frame_id = -1

        while True:
            try:
                data, addr = sock.recvfrom(BUFFER_SIZE)
                
                # ヘッダを解析 [フレームID, 総チャンク数, 現在のチャンク番号]
                header = data[:16]
                chunk_data = data[16:]
                frame_id, total_chunks, chunk_id = struct.unpack('QII', header)

                # 新しいフレームが来たらバッファを初期化
                if frame_id not in buffers:
                    buffers[frame_id] = [None] * total_chunks
                
                # バッファにチャンクを格納
                buffers[frame_id][chunk_id] = chunk_data
                
                # 古いフレームのバッファを削除（メモリリーク対策）
                if frame_id > current_frame_id:
                    if current_frame_id in buffers:
                        del buffers[current_frame_id]
                    current_frame_id = frame_id

                # すべてのチャンクが揃ったかチェック
                if all(c is not None for c in buffers[frame_id]):
                    # チャンクを結合して完全な画像データにする
                    full_data = b''.join(buffers[frame_id])
                    
                    img_np = np.frombuffer(full_data, dtype=np.uint8)
                    img_decode = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

                    if img_decode is not None:
                        cv2.imshow("Receiver", img_decode)
                    
                    # 処理済みのフレームをバッファから削除
                    del buffers[frame_id]

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            except Exception as e:
                # print(f"エラー: {e}")
                pass

    cv2.destroyAllWindows()
    print("受信を終了しました。")

if __name__ == "__main__":
    main()