import os
import ffmpeg
import re
import json
from ultralytics import YOLO


class yolo:

    """Class constructor

    Args: None

    Returns: None
    """

    def __init__(self, video_file):
        self.video_file = video_file
        self.frame_dir = (
            "temp/frames/" + os.path.splitext(os.path.basename(self.video_file))[0]
        )
        os.makedirs(f"{self.frame_dir}", exist_ok=True)

        self.model = YOLO("yolov8l.pt")
        self.conf_thresh = 0.05

    """Extract video frames from a video based on how much they differ.
    The function selects only the frames that differ from the previous ones by more than 30%.
    First frame is always selected. Frames are saved to temp/frames directory.

    Args:
        video_file (str): The path to the downloaded YouTube video.

    Returns: None
    """

    def get_frames(self):
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

    # TODO: Trent - Object Detection
    def find_objects(self):
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
        os.makedirs("temp", exist_ok=True)
        with open("temp/object_toc.json", "w") as f:
            json.dump(toc, f, indent=2)

        return toc
