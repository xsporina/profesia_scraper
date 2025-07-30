FROM python:3.11-slim

USER root

# Update and install python
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    xvfb \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV DISPLAY=:99
ENV PYTHONUNBUFFERED=1

CMD ["bash", "-c", "rm -f /tmp/.X99-lock && Xvfb :99 -screen 0 1920x1080x24 & sleep 5 && python app/run.py"]