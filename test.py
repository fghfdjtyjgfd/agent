import os
from typing import List
import datetime
import time

# print(os.path.join(os.path.dirname(__file__), "images", "image1.jpg"))
# print(os.listdir("./images"))

def get_images_by_room(root_dir: str) -> List[List[str]]:
    rooms_images = []
    
    for room_number in sorted(os.listdir(root_dir)):
        room_path = os.path.join(root_dir, room_number)
        if not os.path.isdir(room_path):
            continue
        
        images_path = []
        for image_name in sorted(os.listdir(room_path)):
            if dir == '.DS_Store':
                continue
            image_path = os.path.join(room_path, image_name)
            images_path.append(image_path)

        rooms_images.append(images_path)

    return rooms_images

def get_rooms_name(img_dir_path: str) -> List:
    images_dir = []
    for dir in os.listdir(img_dir_path):
        if dir == ".DS_Store":
            continue
        images_dir.append(dir)
    return images_dir

def format_time(timedelta):
    total_seconds = int(timedelta.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    formatted = f"{hours}:{minutes:02}:{seconds:02}"
    return formatted
# for i in range(len(f)):
#     # dir = (get_images_path("./images"))
#     print(get_rooms_name("./images")[i])

start = datetime.datetime.now()
time.sleep(3)
duration = datetime.datetime.now() - start

print(f"duration = {format_time(duration)} hour")