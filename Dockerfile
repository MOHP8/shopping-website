# 使用官方 Python 映像作為基本映像
FROM python:3.11.4

# 將工作目錄設置為應用程序代碼所在的目錄
WORKDIR /demo

# 複製 requirements.txt 到容器中
COPY requirements.txt .

# 安裝應用程序依賴項
RUN pip install --no-cache-dir -r requirements.txt

# 複製所有代碼到容器中
COPY demo .

# 將 Flask 應用程序運行在端口 5000
EXPOSE 5000
# CMD ["gunicorn", "-b", "0.0.0.0:5000", "wsgi_app:app"]
CMD ["gunicorn", "-k", "gevent", "-b", "0.0.0.0:5000", "wsgi_app:app"]

