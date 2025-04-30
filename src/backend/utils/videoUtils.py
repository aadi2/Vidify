import os
import ffmpeg
import re
from ultralytics import YOLO
from PIL import Image
from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection
import torch


class videoUtils:

    """Class constructor

    Args: None

    Returns: None
    """

    def __init__(self):
        self.video_file = ""
        self.frame_dir = ""

        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.model = YOLO("yolov8l.pt")
        self.conf_thresh = 0.3

        self.DINOprocessor = AutoProcessor.from_pretrained("IDEA-Research/grounding-dino-base")
        self.DINOmodel = AutoModelForZeroShotObjectDetection.from_pretrained("IDEA-Research/grounding-dino-base").to(self.device)

    """Extract video frames from a video based on how much they differ.
    The function selects only the frames that differ from the previous ones by more than 30%.
    First frame is always selected. Frames are saved to temp/frames directory.

    Args:
        video_file (str): The path to the downloaded YouTube video.

    Returns: None
    """

    def __get_frames__(self):
        # Extract frames
        out = (
            ffmpeg.input(self.video_file)
            .output(
                f"{self.frame_dir}/frame_%03d.jpg",
                vf="select='eq(n\\,0)+gt(scene\\,0.3)',showinfo",
                fps_mode="vfr",
            )
            .run(capture_stdout=True, capture_stderr=True)
        )

        # Rename frames' filenames to include timestamps in seconds
        p = re.compile(r"pts_time:([\d\.]+)")
        timestamps = p.findall(out[1].decode("utf-8", errors="ignore"))

        for i, timestamp in enumerate(timestamps):
            old = f"{self.frame_dir}/frame_{i:03d}.jpg"
            new = f"{self.frame_dir}/frame_{float(timestamp):.3f}.jpg"
            if os.path.exists(old):
                os.rename(old, new)

    """Find all possible objects in the video to create a table of contents.
    Limited by the pretraining data of the model.
    The function uses YOLOv8 (large).

    Args:
        video_file (str): The path to the downloaded YouTube video.

    Returns:
        toc ( {obj_name (str), [timestamp (str) ] } ): A dictionary with found objects, 
            with timestamps listed for each.
    """

    def find_objects(self, video_file):
        self.video_file = video_file
        self.frame_dir = (
            "temp/frames/" + os.path.splitext(os.path.basename(self.video_file))[0]
        )
        os.makedirs(f"{self.frame_dir}", exist_ok=True)
        self.__get_frames__()
        toc = {}

        # Scan all .jpg frames
        for filename in sorted(os.listdir(self.frame_dir)):
            if not filename.endswith(".jpg"):
                continue

            match = re.match(r"frame_([\d\.]+)\.jpg", filename)
            if not match:
                continue  # Skip files like 'frame_001.jpg'

            timestamp = float(match.group(1))
            frame_path = os.path.join(self.frame_dir, filename)

            results = self.model(frame_path)[0]
            for box in results.boxes:
                conf = float(box.conf[0])
                if conf >= self.conf_thresh:
                    cls_id = int(box.cls[0])
                    obj_name = self.model.names[cls_id]
                    toc.setdefault(obj_name, []).append(timestamp)

        # Save TOC to JSON
        '''
        os.makedirs("temp", exist_ok=True)
        with open("temp/object_toc.json", "w") as f:
            json.dump(toc, f, indent=2)
        '''

        return toc

    """Search the video for an object.
    The function uses Grounding DINO open-set object detection model.

    Args:
        video_file (str): The path to the downloaded YouTube video.
        search (str): The object a user is looking for.

    Returns: self.results ([str]): A list of timestamps at which an object occurs.
    """

    def search_video(self, video_file, search):
        self.video_file = video_file
        self.frame_dir = (
            "temp/frames/" + os.path.splitext(os.path.basename(self.video_file))[0]
        )
        os.makedirs(f"{self.frame_dir}", exist_ok=True)
        self.__get_frames__()

        self.text_labels = [[search]]
        self.results = []

        for filename in os.listdir(self.frame_dir):
            filepath = os.path.join(self.frame_dir, filename)
            image = Image.open(filepath).convert("RGB")
            inputs = self.DINOprocessor(images=image, text=self.text_labels, return_tensors="pt").to(self.device)

            with torch.no_grad():
                outputs = self.DINOmodel(**inputs)

            results = self.DINOprocessor.post_process_grounded_object_detection(
                outputs,
                inputs.input_ids,
                box_threshold=0.4,
                text_threshold=0.3,
                target_sizes=[image.size[::-1]]
            )

            result = results[0]
            for score in result["scores"]:
                if round(score.item(), 3) >= 0.600:
                    match = re.match(r"frame_([\d\.]+)\.jpg", filename)
                    timestamp = float(match.group(1))
                    self.results.append(timestamp)

        return self.results
