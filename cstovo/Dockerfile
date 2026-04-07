FROM python:3.10

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY . .

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

CMD ["gunicorn", "cstovo.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]