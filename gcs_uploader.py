import os
import tempfile
import logging
import pandas as pd
from google.cloud import storage

# 建立這個模組的 logger
logger = logging.getLogger(__name__)

class GCSUploader:
    def __init__(self, bucket_name: str):
        if not bucket_name:
            raise ValueError("必須提供目標 GCS Bucket 名稱")
        
        self.bucket_name = bucket_name
        
        try:
            # 初始化 Storage Client (會自動使用 WIF 或本地的 ADC 權限)
            self.client = storage.Client()
            self.bucket = self.client.bucket(self.bucket_name)
            logger.info(f"☁️ 成功連線至 GCS，目標 Bucket: {self.bucket_name}")
        except Exception as e:
            logger.error(f"❌ 初始化 GCS Client 失敗: {e}")
            raise

    def upload_dataframe(self, df: pd.DataFrame, filename: str) -> bool:
        """將 DataFrame 暫存為 CSV 並上傳至 GCS"""
        if df.empty:
            logger.warning("⚠️ 沒有資料可供上傳。")
            return False

        # 使用 tempfile 建立跨平台的暫存檔案
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as tmp_file:
            df.to_csv(tmp_file.name, index=False)
            tmp_path = tmp_file.name

        try:
            logger.info(f"⬆️ 準備上傳檔案: {filename} ...")
            blob = self.bucket.blob(filename)
            blob.upload_from_filename(tmp_path)
            logger.info(f"✅ 已成功上傳至: gs://{self.bucket_name}/{filename}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 上傳 GCS 失敗: {e}", exc_info=True)
            return False
            
        finally:
            # 無論上傳成功或失敗，都必須清理暫存檔釋放空間
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                logger.debug(f"🗑️ 暫存檔 {tmp_path} 已清理。")