# Use Python 3.11 slim image for better compatibility
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for PDF and document processing
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p knowledge_base chroma_db static templates

# Set environment variables with defaults
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Build the vector database if knowledge base files exist
# This will use the GOOGLE_API_KEY_1 provided during the build process
ARG GOOGLE_API_KEY_1
ARG GOOGLE_API_KEY_2
ARG GOOGLE_API_KEY_3
ARG GOOGLE_API_KEY_4
ARG GOOGLE_API_KEY_5
ARG SECRET_KEY

ENV GOOGLE_API_KEY_1=$GOOGLE_API_KEY_1
ENV GOOGLE_API_KEY_2=$GOOGLE_API_KEY_2
ENV GOOGLE_API_KEY_3=$GOOGLE_API_KEY_3
ENV GOOGLE_API_KEY_4=$GOOGLE_API_KEY_4
ENV GOOGLE_API_KEY_5=$GOOGLE_API_KEY_5
ENV SECRET_KEY=$SECRET_KEY

# Only build DB if knowledge base files exist
RUN if [ -n "$(ls -A knowledge_base/ 2>/dev/null)" ]; then python build_db.py; fi

# Expose port 8000 for FastAPI
EXPOSE 8000

# Health check for FastAPI - updated endpoint
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run multi-org FastAPI application with uvicorn
CMD ["uvicorn", "run:app", "--host", "0.0.0.0", "--port", "8000"]