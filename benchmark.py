import cv2
import mss
import numpy as np
import time

# --- 設定項目 ---
WIDTH = 640
HEIGHT = 480
# ----------------

def main():
    print("ベンチマークを開始します。ウィンドウ上で 'q' キーを押すと終了します。")

    # mssを初期化
    with mss.mss(display=":0.0") as sct:
        # キャプチャする領域を指定
        monitor = {"top": 40, "left": 0, "width": WIDTH, "height": HEIGHT}

        # FPS計算用の変数を初期化
        last_time = time.time()
        frame_count = 0

        while True:
            # 指定した領域のスクリーンショットを取得
            img_mss = sct.grab(monitor)

            # mssの画像データをnumpy配列に変換
            img_np = np.frombuffer(img_mss.rgb, dtype=np.uint8).reshape((img_mss.height, img_mss.width, 3))

            # OpenCVでウィンドウに画像を表示
            cv2.imshow("Screen Capture Benchmark", img_np)

            # FPSを計算してコンソールに表示
            frame_count += 1
            current_time = time.time()
            elapsed_time = current_time - last_time
            if elapsed_time > 1.0: # 1秒ごとにFPSを更新
                fps = frame_count / elapsed_time
                print(f"FPS: {fps:.2f}")
                # 変数をリセット
                last_time = current_time
                frame_count = 0

            # 'q'キーが押されたらループを抜ける
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    # すべてのウィンドウを閉じる
    cv2.destroyAllWindows()
    print("ベンチマークを終了しました。")

if __name__ == '__main__':
    main()