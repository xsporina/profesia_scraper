FROM python:3.11-slim

USER root

# Update and install Chrome with NEW method (no apt-key)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    xvfb \
    ca-certificates \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV DISPLAY=:99
ENV PYTHONUNBUFFERED=1

CMD ["bash", "-c", "rm -f /tmp/.X99-lock && Xvfb :99 -screen 0 1920x1080x24 & sleep 5 && python app/run.py"]