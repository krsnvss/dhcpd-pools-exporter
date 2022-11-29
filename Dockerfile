FROM --platform=amd64 python:3.9.15-slim
RUN mkdir /app
WORKDIR /app
COPY . /app/
RUN pip install -r requirements.txt
ENTRYPOINT [ "python3", "main.py" ]