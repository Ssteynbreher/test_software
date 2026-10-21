FROM jenkins/jenkins:lts-jdk17

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    qemu-system-arm \
    python3 \
    python3-pip \
    python3-venv \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

USER jenkins
