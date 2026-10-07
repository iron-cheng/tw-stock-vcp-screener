# ============================================================
# 台股 VCP Stage 2 選股系統 Dockerfile
# ============================================================
FROM python:3.11-slim

# 設定環境變數：關閉輸出緩衝、停用 bytecode 產生、設定台灣時區
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Taipei \
    DEBIAN_FRONTEND=noninteractive

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴：
# 1. tzdata: 精確時區設定 (Asia/Taipei)，確保每日 17:00 排程無時差
# 2. fonts-noto-cjk: Google 思源黑體，解決 Matplotlib 產出圖表時繁體中文豆腐字 (□□□) 問題
# 3. ca-certificates: 確保 TWSE / TPEx / Yahoo Finance 之 SSL 憑證信任
# 4. curl: 網路診斷與容器狀態檢查
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    fonts-noto-cjk \
    ca-certificates \
    curl \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴清單並安裝 Python 套件（利用 Docker cache 加速後續 build）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案原始程式碼
COPY . .

# 確保資料與日誌目錄存在
RUN mkdir -p data logs

# 預設常駐啟動主服務（包含 Telegram 互動指令 Bot 與定時掃描排程）
CMD ["python", "main.py"]
