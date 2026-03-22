import time
import logging
import pandas as pd
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

class YouTubeStatsCrawler:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("必須提供 YouTube API Key")
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        logger.info("📺 YouTube API Client 初始化成功。")

    def fetch_latest_videos(self, channel_id: str, max_results: int = 10) -> dict:
        """第一步：抓取最新影片基本資訊"""
        # 👉 加入這行，把底層吃到的數字印出來看！
        logger.info(f"🕵️ 抓漏雷達：準備向 API 請求，目前的 max_results 變數值是 => {max_results}")

        request = self.youtube.search().list(
            part="snippet",
            channelId=channel_id,
            maxResults=max_results,
            order="date",
            type="video"
        )
        response = request.execute()
        
        video_dict = {}
        for item in response.get('items', []):
            vid = item['id']['videoId']
            video_dict[vid] = {
                'id': vid,
                'title': item['snippet']['title'],
                'published': item['snippet']['publishedAt']
            }
        return video_dict

    def fetch_video_stats(self, video_dict: dict) -> pd.DataFrame:
        """第二步：批次抓取影片統計數據"""
        if not video_dict:
            return pd.DataFrame()

        video_ids = list(video_dict.keys())
        ids_string = ",".join(video_ids)
        
        request = self.youtube.videos().list(
            part="statistics",
            id=ids_string
        )
        response = request.execute()
        
        ts = int(time.time())

        for item in response.get('items', []):
            vid = item['id']
            stats = item.get('statistics', {})
            
            video_dict[vid]['viewCount'] = stats.get('viewCount', '0')
            video_dict[vid]['likeCount'] = stats.get('likeCount', '0')
            video_dict[vid]['commentCount'] = stats.get('commentCount', '0')
            video_dict[vid]['timestamp'] = ts

        return pd.DataFrame(list(video_dict.values()))

    def run(self, channel_id: str, max_results: int = 10) -> pd.DataFrame:
        """執行完整爬蟲流程"""
        logger.info(f"🔍 開始抓取頻道 {channel_id} 的影片資料...")
        video_dict = self.fetch_latest_videos(channel_id, max_results)
        
        if not video_dict:
            logger.warning("⚠️ 找不到任何影片。")
            return pd.DataFrame()
            
        df = self.fetch_video_stats(video_dict)
        logger.info(f"📊 成功完成資料抓取，共 {len(df)} 筆記錄。")
        return df