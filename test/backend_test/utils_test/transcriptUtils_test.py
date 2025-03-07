from backend.utils.transcriptUtils import transcriptUtils

# Instantiate the utility class
transcript_util = transcriptUtils()

# Path to the test .vtt file
transcript = "src/backend/utils/test_transcript.vtt"

keyword = "cat"
results = transcript_util.search_transcript(transcript, keyword)

for timestamp, text in results:
    print(f"Found at {timestamp}: {text}")
