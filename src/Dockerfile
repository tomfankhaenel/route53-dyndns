FROM python:3.13-alpine

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py /app/
CMD ["python","-u","main.py"]
