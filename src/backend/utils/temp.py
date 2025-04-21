import os
import ffmpeg
import re


class temp:

    """Class constructor

    Args: None

    Returns: None
    """

    def __init__(self, video_file):
        self.video_file = video_file
        self.frame_dir = "temp/frames/" + os.path.splitext(os.path.basename(self.video_file))[0]
        os.makedirs(f"{self.frame_dir}", exist_ok=True)

    """Extract video frames from a video based on how much they differ.
    The function selects only the frames that differ from the previous ones by more than 30%.
    First frame is always selected. Frames are saved to temp/frames directory.

    Args:
        video_file (str): The path to the downloaded YouTube video.

    Returns: None
    """

    def get_frames(self):
        # Extract frames
        out = ffmpeg.input(self.video_file).output(
            f'{self.frame_dir}/frame_%03d.jpg',
            vf="select='eq(n\\,0)+gt(scene\\,0.3)',showinfo",
            fps_mode='vfr').run(capture_stdout=True, capture_stderr=True)

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
        pass
