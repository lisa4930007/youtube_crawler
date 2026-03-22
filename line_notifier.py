import requests
import logging

logger = logging.getLogger(__name__)

class LineNotifier:
    def __init__(self, channel_access_token: str, user_id: str):
        if not channel_access_token or not user_id:
            raise ValueError("必須提供 LINE Channel Access Token 與 User ID")
            
        self.channel_access_token = channel_access_token
        self.user_id = user_id
        self.api_url = "https://api.line.me/v2/bot/message/push"

    def send_message(self, text: str) -> bool:
        """使用 LINE Messaging API 發送推播訊息給指定使用者"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.channel_access_token}"
        }
        
        # Messaging API 的 Payload 格式
        payload = {
            "to": self.user_id,
            "messages": [
                {
                    "type": "text",
                    "text": text
                }
            ]
        }
        
        try:
            logger.info("💬 準備發送 LINE Messaging API 通知...")
            # 注意這裡是用 json=payload 而不是 data=payload
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=10)
            
            # 檢查 HTTP 狀態碼
            response.raise_for_status()
            
            logger.info("🟢 LINE 通知發送成功！")
            return True
            
        except requests.exceptions.RequestException as e:
            # 如果發生錯誤，印出 API 回傳的詳細錯誤訊息幫助 Debug
            error_detail = e.response.text if e.response else "無詳細回應"
            logger.error(f"🔴 LINE 通知發送失敗: {e} \n詳細原因: {error_detail}", exc_info=True)
            return False