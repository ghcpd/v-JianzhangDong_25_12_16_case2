FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PAYMENT_TOKEN=tok_production_998877
ENV MAIL_SERVER_KEY=mail_srv_key_ABCDEFG
ENV INTERNAL_AUTH=admin_internal_5566

EXPOSE 5000

CMD ["python", "input.py"]