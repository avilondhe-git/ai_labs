FROM mcr.microsoft.com/azure-functions/python:4-python3.11

COPY requirements.txt /
RUN pip install --no-cache-dir -r /requirements.txt

COPY . /home/site/wwwroot

WORKDIR /home/site/wwwroot
