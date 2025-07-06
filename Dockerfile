FROM python:3.12.11-alpine

WORKDIR /app

COPY wut-login.py /app/wut-login.py

RUN adduser -S whut && \
    addgroup -S whut && \
    chown -R whut:whut /app && \
    pip install --no-cache-dir requests

# Run as non-root user
USER whut

CMD ["python", "wut-login.py"]