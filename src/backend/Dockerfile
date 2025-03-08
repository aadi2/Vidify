FROM python:3.9-slim

WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# all files
COPY . .

# the port Flask/FastAPI runs on
EXPOSE 8080

# Run 
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]
