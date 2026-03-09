#!/bin/bash

# Build Windows EXE using Docker with Wine
echo "Building Windows EXE using Docker..."

# Create Dockerfile for Windows build
cat > Dockerfile.windows << 'EOF'
FROM ubuntu:22.04

# Install Wine and dependencies
RUN dpkg --add-architecture i386 && \
    apt-get update && \
    apt-get install -y wine32 wine64 libwine wine-development && \
    apt-get install -y python3 python3-pip && \
    apt-get clean

# Install Python 3.12 in Wine
RUN wine python -m pip install --upgrade pip

WORKDIR /app
COPY requirements.txt .
COPY main.py .
COPY "Vertex Browser.icns" .

# Install dependencies in Wine
RUN wine python -m pip install -r requirements.txt

# Build EXE
RUN wine pyinstaller --onefile --windowed --name="Vertex Browser" --icon="Vertex Browser.icns" main.py
EOF

# Build and run Docker container
docker build -f Dockerfile.windows -t vertex-windows-builder .
docker run --rm -v "$(pwd)/dist":/output vertex-windows-builder cp dist/Vertex\ Browser.exe /output/

echo "Windows EXE built successfully in dist/Vertex Browser.exe"
