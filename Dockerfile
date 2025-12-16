# Use an official lightweight Python image
FROM python:3.11-slim

# Install build dependencies (if needed) and set workdir
WORKDIR /app

# Copy project files
COPY requirements.txt setup.sh run_test.sh run_test.bat auto_test.py input.py input_backup.py /app/
COPY tests/ /app/tests/

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Ensure scripts are executable (for Linux)
RUN chmod +x setup.sh run_test.sh

# Default command runs the auto test script so CI/containers can validate quickly
CMD ["python", "auto_test.py"]
