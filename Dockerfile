FROM openjdk:17-slim

RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

RUN python3 --version && pip3 --version && javac -version

RUN ln -s /usr/bin/python3 /usr/bin/python

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
WORKDIR /app

EXPOSE 8501

CMD ["bash", "-c", "streamlit run landing_page.py --server.port=${PORT:-8501} --server.address=0.0.0.0"]
