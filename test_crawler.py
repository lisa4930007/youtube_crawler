import pytest
import pandas as pd
import requests
from unittest.mock import patch, MagicMock

# 引入我們寫好的三個核心模組
from youtube_crawler import YouTubeStatsCrawler
from gcs_uploader import GCSUploader
from line_notifier import LineNotifier

# ==========================================
# 1. YouTubeStatsCrawler 測試
# ==========================================
@pytest.fixture
def mock_crawler():
    # 攔截 Google API Client 的 build 方法
    with patch('youtube_crawler.build'):
        return YouTubeStatsCrawler(api_key="FAKE_KEY")

def test_crawler_init_without_key():
    with pytest.raises(ValueError):
        YouTubeStatsCrawler(api_key="")

def test_fetch_latest_videos(mock_crawler):
    # 模擬 YouTube API 的回傳結構
    mock_response = {
        "items": [
            {"id": {"videoId": "vid_1"}, "snippet": {"title": "Test Video", "publishedAt": "2026-03-21T00:00:00Z"}}
        ]
    }
    mock_crawler.youtube.search().list().execute.return_value = mock_response
    
    result = mock_crawler.fetch_latest_videos("FAKE_CHANNEL")
    
    assert "vid_1" in result
    assert result["vid_1"]["title"] == "Test Video"

# ==========================================
# 2. GCSUploader 測試
# ==========================================
def test_uploader_init_without_bucket():
    with pytest.raises(ValueError):
        GCSUploader(bucket_name="")

@patch('gcs_uploader.storage.Client')
def test_upload_dataframe_success(mock_storage_client):
    # 設定 mock GCS 的行為
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    mock_storage_client.return_value.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob

    uploader = GCSUploader("FAKE_BUCKET")
    df = pd.DataFrame([{"id": "vid_1", "viewCount": 100}])
    
    result = uploader.upload_dataframe(df, "test.csv")

    # 驗證上傳成功且 API 被正確呼叫
    assert result is True
    mock_storage_client.assert_called_once()
    mock_bucket.blob.assert_called_with("test.csv")
    mock_blob.upload_from_filename.assert_called_once()

@patch('gcs_uploader.storage.Client')
def test_upload_dataframe_empty(mock_storage_client):
    uploader = GCSUploader("FAKE_BUCKET")
    df = pd.DataFrame() # 空資料表
    
    result = uploader.upload_dataframe(df, "test.csv")
    
    # 驗證空資料時會直接回傳 False，且不觸發上傳
    assert result is False
    uploader.bucket.blob.assert_not_called()

# ==========================================
# 3. LineNotifier 測試 (新增)
# ==========================================
def test_notifier_init_missing_args():
    # 測試缺少 token 或 user_id 時是否會報錯
    with pytest.raises(ValueError):
        LineNotifier(channel_access_token="", user_id="U123456")
    with pytest.raises(ValueError):
        LineNotifier(channel_access_token="FAKE_TOKEN", user_id="")

@patch('line_notifier.requests.post')
def test_send_message_success(mock_post):
    # 模擬 requests.post 成功回傳 HTTP 200，且 raise_for_status 不報錯
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    notifier = LineNotifier(channel_access_token="FAKE_TOKEN", user_id="FAKE_USER")
    result = notifier.send_message("測試推播訊息")

    # 驗證
    assert result is True
    mock_post.assert_called_once()
    
    # 檢查 payload 結構是否符合 LINE Messaging API 規範
    called_kwargs = mock_post.call_args.kwargs
    assert called_kwargs['json']['to'] == "FAKE_USER"
    assert called_kwargs['json']['messages'][0]['text'] == "測試推播訊息"

@patch('line_notifier.requests.post')
def test_send_message_failure(mock_post):
    # 模擬網路異常或 LINE API 拒絕請求 (例如 Token 錯誤)
    mock_post.side_effect = requests.exceptions.RequestException("Simulated Network Error")

    notifier = LineNotifier(channel_access_token="FAKE_TOKEN", user_id="FAKE_USER")
    result = notifier.send_message("測試推播訊息")

    # 驗證在發生 Exception 時，程式會攔截並回傳 False，而不是整個崩潰
    assert result is False