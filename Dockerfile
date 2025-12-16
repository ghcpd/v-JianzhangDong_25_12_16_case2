FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
# Example env variables should be set at runtime; do not bake secrets into images
ENV FLASK_APP=input.py
EXPOSE 5000
CMD ["python", "input.py"]
