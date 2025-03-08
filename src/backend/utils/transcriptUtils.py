import webvtt

class transcriptUtils():

    """Class constructor

    Args: None

    Returns: None
    """
    def __init__(self):
        pass

    """Create a transcript if it is not available.

    Args: None

    Returns: None
    """
    def create_transcript(self):
        # Owner: Ola
        pass

    """Search the transcript for the keywords.

    Args: None

    Returns: None
    """
    def search_transcript(self, transcript, keyword):
        # Owner: Trent

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