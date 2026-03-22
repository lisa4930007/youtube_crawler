# 使用輕量級的 Python 3.11 映像檔
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 先複製 requirements.txt 以利用 Docker 快取機制
# 這樣只要套件清單沒變，Docker 就不會每次都重新下載套件
COPY requirements.txt .

# 安裝套件
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案內的所有檔案到容器中
COPY . .

# 預設執行的指令
CMD ["python", "main.py"]