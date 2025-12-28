# syntax=docker/dockerfile:1.4
ARG BASE_IMAGE=ubuntu:22.04
FROM --platform=linux/arm64 ${BASE_IMAGE} AS loader

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# 1. Install Base Build Tools (Always needed)
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    build-essential \
    python3-dev \
    python3-numpy \
    python3-pip \
    rsync \
    && apt-get clean

# 2. Dynamic Dependency Installation
# We copy a config file (requirements.txt or similar) and install from it.
# This allows changing dependencies without editing the Dockerfile structure.

# A. System Packages (apt)
COPY dependencies/apt_packages_generated.txt /tmp/apt_packages.txt
RUN apt-get update && \
    xargs -a /tmp/apt_packages.txt apt-get install -y && \
    apt-get clean

# B. Python Packages (pip) - Optional
# COPY dependencies/requirements.txt /tmp/requirements.txt
# RUN pip3 install -r /tmp/requirements.txt

# 3. Generate a manifest for debugging
RUN dpkg -l > /sysroot_manifest.txt
