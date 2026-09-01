FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir .
EXPOSE 8080
CMD ["gunicorn", "-c", "gunicorn.conf.py", "agent.main:app"]
