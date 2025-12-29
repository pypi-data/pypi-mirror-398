FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir fastapi uvicorn httpx starlette

# Copy package
COPY py_observatory/ py_observatory/
COPY examples/ examples/

# Set PYTHONPATH to include the app directory
ENV PYTHONPATH=/app

EXPOSE 8001

CMD ["uvicorn", "examples.sample_app:app", "--host", "0.0.0.0", "--port", "8001"]
