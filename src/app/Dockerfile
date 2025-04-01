# Build stage
FROM python:3.12-slim as builder

WORKDIR /app

# Install poetry
RUN pip install poetry

# Copy pyproject.toml
COPY pyproject.toml ./

# Configure poetry and generate lock file
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "main.py"] 