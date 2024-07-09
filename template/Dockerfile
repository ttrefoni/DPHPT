FROM python:3.9

ENV DEBIAN_FRONTEND=noninteractive

#installs requirment packages
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY sample_data /data
COPY LSTM_model_fit.py /LSTM_model_fit.py
COPY LSTM_model_fit_ES.py /LSTM_model_fit_ES.py
