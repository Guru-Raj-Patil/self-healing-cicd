FROM jenkins/jenkins:lts
USER root
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv curl nano \
    && rm -rf /var/lib/apt/lists/*
# Install Docker CLI just in case we need to run docker from within jenkins
RUN curl -fsSL https://get.docker.com | sh
USER jenkins
