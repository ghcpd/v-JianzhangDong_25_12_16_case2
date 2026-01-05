FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY input.py .
COPY input_backup.py .

# Create necessary directories
RUN mkdir -p configs logs

# Set environment variables
ENV FLASK_ENV=production
ENV PAYMENT_TOKEN=${PAYMENT_TOKEN}
ENV MAIL_SERVER_KEY=${MAIL_SERVER_KEY}
ENV INTERNAL_AUTH=${INTERNAL_AUTH}

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health', timeout=5)" || exit 1

# Run application
CMD ["python", "-u", "input.py"]
