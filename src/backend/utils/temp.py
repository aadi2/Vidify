from backend.utils.videoUtils import yolo
import json

v = yolo("temp/videos/coffeevideo.mp4")
v.get_frames()
toc = v.find_objects()

print(json.dumps(toc, indent=2))
