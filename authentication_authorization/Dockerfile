FROM python:3.9-slim
WORKDIR /app
RUN pip install --upgrade pip
COPY ../requirements.txt .
RUN pip install -r requirements.txt
COPY authentication_authorization/ .

CMD ["python3", "app.py"]