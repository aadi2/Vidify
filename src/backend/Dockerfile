FROM python:3.9-slim

ENV APP_HOME=/app

WORKDIR $APP_HOME

# copy all files
COPY . .

# install system dependencies
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# download Whisper model
RUN python3 -c "import whisper; whisper.load_model('tiny')"

# download YOLOv8 model
RUN python3 -c "from ultralytics import YOLO; YOLO('yolov8l.pt')"

# download Grounding DINO
RUN python3 -c "from transformers import AutoProcessor, AutoModel; \
    AutoProcessor.from_pretrained('IDEA-Research/grounding-dino-base'); \
    AutoModel.from_pretrained('IDEA-Research/grounding-dino-base')"


# the port Flask/FastAPI runs on
EXPOSE 8080

# Run 
CMD ["flask", "--app", "app", "run", "--host=0.0.0.0", "--port=8080"]
