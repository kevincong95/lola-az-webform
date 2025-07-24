# Use an official slim Python image as base
FROM python:3.11-slim

# Install Java (OpenJDK)
RUN apt-get update && \
    apt-get install -y openjdk-17-jdk && \
    rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME (optional but good practice)
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your Streamlit app code
COPY . /lola-az-webform
WORKDIR /lola-az-webform

# Expose the port Streamlit uses
EXPOSE 8501

# Command to run Streamlit on container start
CMD ["streamlit", "run", "landing_page.py", "--server.port=8501", "--server.address=0.0.0.0"]
