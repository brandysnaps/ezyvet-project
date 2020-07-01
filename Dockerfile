FROM python:3.8-slim

WORKDIR /ezyvet

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . .

ENTRYPOINT [ "python", "launch_instance.py" ]
