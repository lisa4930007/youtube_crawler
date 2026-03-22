import os
import time
import logging
from dotenv import load_dotenv
from youtube_crawler import YouTubeStatsCrawler
from gcs_uploader import GCSUploader
from line_notifier import LineNotifier

# 設定全域 Logger 格式
logging.basicConfig(
    level=logging.INFO, # 可以改成 logging.DEBUG 看更詳細的資訊
    format='%(asctime)s | %(levelname)-8s | %(module)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def main():
    # 載入 .env 環境變數
    load_dotenv()
    
    api_key = os.getenv("YOUTUBE_API_KEY")
    channel_id = os.getenv("TARGET_CHANNEL_ID")
    bucket_name = os.getenv("TARGET_BUCKET")
    line_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN") 
    line_user_id = os.getenv("LINE_USER_ID")

    # 檢查變數是否齊全 (如果漏了任何一個，程式會提早結束並報錯)
    if not all([api_key, channel_id, bucket_name, line_token, line_user_id]):
        logger.error("環境變數設定不完整 (.env 漏了某些值)")
        return

    logger.info("🚀 啟動 YouTube 數據爬蟲應用程式...")
    
    try:
        # 1. 實例化三個工作類別
        crawler = YouTubeStatsCrawler(api_key=api_key)
        uploader = GCSUploader(bucket_name=bucket_name)
        notifier = LineNotifier(channel_access_token=line_token, user_id=line_user_id) 
        
        # 2. 執行爬蟲
        df = crawler.run(channel_id=channel_id, max_results=10)
        
        # 3. 執行上傳與通知
        if not df.empty:
            filename = f"video_stats_{int(time.time())}.csv"

            # 呼叫 GCS 上傳
            is_uploaded = uploader.upload_dataframe(df, filename)
            
            if is_uploaded:
                success_msg = (
                    f"✅ YouTube 爬蟲任務完成！\n"
                    f"📁 已存入 GCS: {filename}\n"
                    f"📊 本次共抓取了 {len(df)} 筆數據。"
                )
                notifier.send_message(success_msg)
            else:
                notifier.send_message(f"⚠️ 爬蟲警告！資料抓取成功，但上傳 GCS 失敗。")
                
        else:
            logger.warning("因為沒有抓到資料，跳過上傳與通知流程。")
            
    except Exception as e:
        logger.error("❌ 應用程式執行時發生未預期錯誤", exc_info=True)
        # 如果程式崩潰，嘗試發送錯誤通知給 LINE
        if 'notifier' in locals():
            try:
                notifier.send_message(f"🚨 YouTube 爬蟲發生嚴重錯誤！\n請檢查系統 Log。")
            except Exception as notify_e:
                logger.error(f"錯誤通知發送失敗: {notify_e}")

if __name__ == "__main__":
    main()