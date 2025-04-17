import yt_dlp
import os
import webvtt

COOKIES_FILE = "cookies.txt"


class transcriptUtils():

    """Class constructor

    Args: None

    Returns: None
    """
    def __init__(self):
        os.makedirs("temp/audio", exist_ok=True)
        self.audio_file = "temp/audio/temp_audio.mp3"
        self.filename = ""
        os.makedirs("temp/subtitles", exist_ok=True)
        self.transcript_file = f'temp/subtitles/{self.filename}.vtt'

    """Download an audio file of the YouTube video to create transcript.

    Args:
        yt_url (str): The YouTube video URL.

    Returns: None
    """
    def __get_audio__(self, yt_url):
        ydl_opts = {
            "format": "bestaudio/best",
            "extract_audio": True,
            "audio_format": "mp3",
            "outtmpl": self.audio_file,
            "noplaylist": True,
            "cookiefile": COOKIES_FILE
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([yt_url])

    """Create a transcript if it is not available.

    Args:
        yt_url (str): The YouTube video URL.
        filename (str): title of the video used for the filename of the transcript file.
        model: openai-whisper model ("small") for transcript creation from audio, initialized on app startup.

    Returns:
        self.transcript_file (str): path to the transcript file.
    """
    def create_transcript(self, yt_url, filename, model):
        self.__get_audio__(yt_url)
        if not self.audio_file:
            return None
        
        result = model.transcribe(self.audio_file)
        self.filename = filename

        if not result:
            return None

        with open(self.transcript_file, "w", encoding="utf-8") as file:
            file.write("WEBVTT\n\n")
            for i, segment in enumerate(result["segments"]):
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

        os.remove(self.audio_file)
        print("Transcript created.")
        return self.transcript_file

    """Search the transcript for the keywords.

    Args: None

    Returns: None
    """
    def search_transcript(self, transcript, keyword):
        if not transcript or not keyword:
            return []

        transcript = "temp/subtitles/" + transcript

        keyword = keyword.lower()
        matches = []

        for caption in webvtt.read(transcript):
            caption_text = caption.text.lower()

            if keyword in caption_text:
                matches.append((caption.start, caption.text.strip()))

        return matches
