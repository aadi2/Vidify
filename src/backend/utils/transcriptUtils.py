import yt_dlp
import os
import webvtt
import tempfile
import shutil
import json

COOKIES_FILE = "cookies.txt"
CACHE_DIR = "temp/cache"


class transcriptUtils:
    """Class constructor

    Args: None

    Returns: None
    """

    def __init__(self):
        # Create a temp file manager for this instance
        self.temp_dirs = []

        # Create audio directory as a temp directory
        self.audio_dir = tempfile.mkdtemp(prefix="audio_")
        self.temp_dirs.append(self.audio_dir)
        self.audio_file = os.path.join(self.audio_dir, "temp_audio.mp3")

        # Create subtitles directory as a temp directory
        self.subtitle_dir = tempfile.mkdtemp(prefix="subtitles_")
        self.temp_dirs.append(self.subtitle_dir)

        self.filename = ""
        self.transcript_file = ""

        # Ensure cache directory exists
        os.makedirs(CACHE_DIR, exist_ok=True)

    def __del__(self):
        """Clean up resources when the object is destroyed"""
        self.cleanup()

    def cleanup(self):
        """Clean up all temporary resources"""
        for directory in self.temp_dirs:
            if os.path.exists(directory):
                try:
                    shutil.rmtree(directory)
                except Exception as e:
                    print(f"Error cleaning up directory {directory}: {e}")
        self.temp_dirs = []

    """Download an audio file of the YouTube video to create transcript.

    Args:
        yt_url (str): The YouTube video URL.

    Returns: None
    """

    def __get_audio__(self, yt_url):
        try:
            ydl_opts = {
                "format": "bestaudio/best",
                "extract_audio": True,
                "audio_format": "mp3",
                "outtmpl": self.audio_file,
                "noplaylist": True,
                "cookiefile": COOKIES_FILE,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([yt_url])

            return True
        except Exception as e:
            print(f"Error downloading audio: {e}")
            return False

    """Create a transcript if it is not available.

    Args:
        yt_url (str): The YouTube video URL.
        filename (str): title of the video used for the filename of the transcript file.
        model: openai-whisper model ("small") for transcript creation from audio, initialized on app startup.

    Returns:
        self.transcript_file (str): path to the transcript file.
    """

    def create_transcript(self, yt_url, filename, model):
        # Check if transcript is cached
        cache_path = os.path.join(CACHE_DIR, f"{filename}.json")
        if os.path.exists(cache_path):
            try:
                # Load from cache and write to VTT
                with open(cache_path, "r") as f:
                    result = json.load(f)

                self.filename = filename
                self.transcript_file = os.path.join(
                    self.subtitle_dir, f"{filename}.vtt"
                )

                # Write cached result to VTT file
                self._write_vtt_from_segments(result.get("segments", []))

                print("Transcript loaded from cache.")
                return self.transcript_file
            except Exception as e:
                print(f"Error loading from cache: {e}")
                # Continue with normal processing if cache fails

        # No cache or cache failed, create transcript
        if not self.__get_audio__(yt_url):
            return None

        try:
            # Use a context manager to ensure model is released after use
            result = model.transcribe(self.audio_file)

            if not result:
                return None

            self.filename = filename
            self.transcript_file = os.path.join(self.subtitle_dir, f"{filename}.vtt")

            # Write to VTT file
            self._write_vtt_from_segments(result.get("segments", []))

            # Cache the result
            try:
                with open(cache_path, "w") as f:
                    json.dump(result, f)
            except Exception as e:
                print(f"Error caching transcript: {e}")

            # Clean up audio file
            if os.path.exists(self.audio_file):
                os.remove(self.audio_file)

            print("Transcript created.")
            return self.transcript_file
        except Exception as e:
            print(f"Error creating transcript: {e}")
            # Clean up audio file on error
            if os.path.exists(self.audio_file):
                os.remove(self.audio_file)
            return None

    def _write_vtt_from_segments(self, segments):
        """Write segments to a WebVTT file"""
        with open(self.transcript_file, "w", encoding="utf-8") as file:
            file.write("WEBVTT\n\n")
            for segment in segments:
                start = segment["start"]
                end = segment["end"]
                text = segment["text"]

                h_s = int(start // 3600)
                m_s = int((start % 3600) // 60)
                s_s = start % 60
                h_e = int(end // 3600)
                m_e = int((end % 3600) // 60)
                s_e = end % 60

                start_vtt = f"{h_s:02}:{m_s:02}:{s_s:.3f}"
                end_vtt = f"{h_e:02}:{m_e:02}:{s_e:.3f}"

                file.write(f"{start_vtt} --> {end_vtt}\n{text}\n\n")

    """Search the transcript for the keywords.

    Args: None

    Returns: None
    """

    def search_transcript(self, transcript, keyword):
        if not transcript or not keyword:
            return []

        transcript_path = os.path.join("temp/subtitles", transcript)

        if not os.path.exists(transcript_path):
            print(f"Transcript file not found: {transcript_path}")
            return []

        keyword = keyword.lower()
        matches = []

        # Process one caption at a time using generator to reduce memory usage
        for caption in self._caption_generator(transcript_path):
            caption_text = caption.text.lower()

            if keyword in caption_text:
                matches.append((caption.start, caption.text.strip()))

        return matches

    def _caption_generator(self, transcript_path):
        """Generator that yields captions one at a time to reduce memory usage"""
        try:
            for caption in webvtt.read(transcript_path):
                yield caption
        except Exception as e:
            print(f"Error reading captions: {e}")
            return

    # Cache management functions
    def get_cached_transcript(self, video_id):
        """Get a transcript from cache if it exists"""
        cache_path = os.path.join(CACHE_DIR, f"{video_id}.json")
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error reading cache: {e}")
        return None

    def cache_transcript(self, video_id, transcript_data):
        """Cache a transcript for future use"""
        os.makedirs(CACHE_DIR, exist_ok=True)
        try:
            cache_path = os.path.join(CACHE_DIR, f"{video_id}.json")
            with open(cache_path, "w") as f:
                json.dump(transcript_data, f)
            return True
        except Exception as e:
            print(f"Error caching transcript: {e}")
            return False
