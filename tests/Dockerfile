FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt requirements-test.txt ./
RUN pip install --no-cache-dir -r requirements-test.txt
COPY pytest.ini .env.example ./
COPY src ./src
COPY tests ./tests
ENV PYTHONPATH=/app
CMD ["pytest", "-v", "--junitxml=/app/test-results/results.xml"]
