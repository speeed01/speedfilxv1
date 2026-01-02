name: Build APK

on:
  push:
    branches: [ "main" ]
  workflow_dispatch:

jobs:
  build:
    # ⬅️ هذا هو الحل الحقيقي
    runs-on: ubuntu-22.04

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.10"

    - name: Install system dependencies
      run: |
        sudo apt update
        sudo apt install -y \
          build-essential \
          git \
          zip \
          unzip \
          openjdk-17-jdk \
          libffi-dev \
          libssl-dev \
          libsqlite3-dev \
          zlib1g-dev \
          libncurses5 \
          libtinfo5

    - name: Install Buildozer
      run: |
        python -m pip install --upgrade pip
        pip install buildozer cython==0.29.36

    - name: Clean build cache
      run: |
        rm -rf ~/.buildozer
        rm -rf .buildozer

    - name: Build APK
      env:
        JAVA_HOME: /usr/lib/jvm/java-17-openjdk-amd64
      run: |
        buildozer android debug

    - name: Upload APK
      uses: actions/upload-artifact@v4
      with:
        name: SpeedFlix-APK
        path: bin/*.apk
