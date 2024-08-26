# Use the official Debian slim image as a base
FROM debian:bookworm-slim

# Install Tesseract OCR and necessary dependencies
RUN apt-get update && \
    apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/alt-desc/

ENV VIRTUAL_ENV=venv


# Create a virtual environment and install dependencies
RUN python3 -m venv venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"


# Copy the source code and requirements.txt into the container
COPY src/ /usr/alt-desc/src/
COPY requirements.txt /usr/alt-desc/
COPY download_models.py /usr/alt-desc/

RUN pip install --no-cache-dir -r requirements.txt 

RUN venv/bin/python3 download_models.py

ENTRYPOINT ["venv/bin/python3", "src/main.py"]
