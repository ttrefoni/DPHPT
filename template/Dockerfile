#FROM rocker/rstudio:4.3.2
FROM python:3.9

#LABEL org.opencontainers.image.licenses="GPL-2.0-or-later" \
#      org.opencontainers.image.source="https://github.com/rocker-org/rocker-versioned2" \
#      org.opencontainers.image.vendor="Rocker Project" \
#      org.opencontainers.image.authors="Carl Boettiger <cboettig@ropensci.org>"

#RUN /rocker_scripts/install_tidyverse.sh
ENV DEBIAN_FRONTEND=noninteractive

# Update the package list, install Python and python3-venv, and clean up afterwards
#RUN apt-get update && \
#    apt-get install -y --no-install-recommends \
#    vim \
#    python3.10 \
#    python3.10-venv \
#    python3.10-dev \
#    python3-pip && \
#    apt-get clean && \
#    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY data /data
COPY LSTM_model_fit.py /LSTM_model_fit.py
COPY LSTM_model_fit_ES.py /LSTM_model_fit_ES.py
