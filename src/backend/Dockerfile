FROM python:3.9-slim

ENV APP_HOME=/app

WORKDIR $APP_H ME

# copy all files
COPY . .

# install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# the port Flask/FastAPI runs on
EXPOSE 8080

# Run 
CMD ["flask", "--app", "app", "run", "--host=0.0.0.0", "--port=8080"]
