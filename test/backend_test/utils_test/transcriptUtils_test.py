from backend.utils.transcriptUtils import transcriptUtils


def test_transcript_search():

    # Instantiate the utility class
    transcript_util = transcriptUtils()

    transcript = "test_transcript.vtt"
    

    keyword = "cat"
    results = transcript_util.search_transcript(transcript, keyword)
    print("HELLO")
    for timestamp, text in results:
        # assert(False)
        print(f"Found at {timestamp}: {text}")
        