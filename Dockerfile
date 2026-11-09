FROM python:3.11-slim

ENV USER=username
ENV HOME=/home/$USER
ENV PYTHONUNBUFFERED=1

RUN useradd -m -u 1000 $USER

WORKDIR $HOME/app

RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt $HOME/app/requirements.txt
COPY app.py $HOME/app/app.py
COPY start-script.sh $HOME/app/start-script.sh

RUN pip install --no-cache-dir -r requirements.txt \
    && chmod +x start-script.sh \
    && chown -R $USER:$USER $HOME

USER $USER

EXPOSE 8501

ENTRYPOINT ["./start-script.sh"]
