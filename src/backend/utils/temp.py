import os
import ffmpeg
import re
import tempfile
import shutil


class temp:
    """Class constructor

    Args: None

    Returns: None
    """

    def __init__(self, video_file):
        self.video_file = video_file

        # Create a unique temp directory instead of using a fixed path
        self.base_dir = tempfile.mkdtemp(prefix="vidify_frames_")
        self.frame_dir = os.path.join(
            self.base_dir, os.path.splitext(os.path.basename(self.video_file))[0]
        )
        os.makedirs(self.frame_dir, exist_ok=True)

    def __del__(self):
        """Clean up resources when the object is destroyed"""
        self.cleanup()

    def cleanup(self):
        """Clean up temporary resources"""
        if hasattr(self, "base_dir") and os.path.exists(self.base_dir):
            try:
                shutil.rmtree(self.base_dir)
            except Exception as e:
                print(f"Error cleaning up directory {self.base_dir}: {e}")

    """Extract video frames from a video based on how much they differ.
    The function selects only the frames that differ from the previous ones by more than 30%.
    First frame is always selected. Frames are saved to temp/frames directory.

    Args:
        video_file (str): The path to the downloaded YouTube video.

    Returns: None
    """

    def get_frames(self, batch_size=10):
        """Extract frames with memory-efficient batch processing"""
        try:
            # Extract frame information but not the frames yet
            out = (
                ffmpeg.input(self.video_file)
                .output(
                    "-", format="null", vf="select='eq(n\\,0)+gt(scene\\,0.3)',showinfo"
                )
                .run(capture_stdout=True, capture_stderr=True)
            )

            # Parse timestamps
            p = re.compile(r"pts_time:([\d\.]+)")
            timestamps = p.findall(out[1].decode("utf-8", errors="ignore"))

            # Process frames in batches to reduce memory usage
            for i in range(0, len(timestamps), batch_size):
                batch = timestamps[i : min(i + batch_size, len(timestamps))]
                self._process_frame_batch(batch)

            return len(timestamps)
        except Exception as e:
            print(f"Error extracting frames: {e}")
            return 0

    def _process_frame_batch(self, timestamps):
        """Process a batch of frames by timestamp"""
        for timestamp in timestamps:
            output_file = os.path.join(
                self.frame_dir, f"frame_{float(timestamp):.3f}.jpg"
            )
            try:
                ffmpeg.input(self.video_file, ss=float(timestamp)).output(
                    output_file, vframes=1
                ).run(quiet=True)
            except Exception as e:
                print(f"Error extracting frame at {timestamp}: {e}")

    def get_frame_paths(self):
        """Get paths of all extracted frames"""
        if not os.path.exists(self.frame_dir):
            return []

        return [
            os.path.join(self.frame_dir, f)
            for f in os.listdir(self.frame_dir)
            if f.startswith("frame_") and f.endswith(".jpg")
        ]

    # TODO: Trent - Object Detection
    def find_objects(self):
        pass
