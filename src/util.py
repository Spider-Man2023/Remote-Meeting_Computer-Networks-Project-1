'''
Simple util implementation for video conference
Including data capture, image compression and image overlap
Note that you can use your own implementation as well :)
'''
from io import BytesIO
import pyaudio
import cv2
import pyautogui
import numpy as np
from PIL import Image, ImageGrab, UnidentifiedImageError
from config import *
import mss
import mss.tools


# audio setting
# FORMAT = pyaudio.paInt16
# audio = pyaudio.PyAudio()
# streamin = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
# streamout = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)

# print warning if no available camera
cap = cv2.VideoCapture(0)
if cap.isOpened():
    can_capture_camera = True
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_height)
else:
    can_capture_camera = False

my_screen_size = pyautogui.size()


def resize_image_to_fit_screen(image, my_screen_size):
    screen_width, screen_height = my_screen_size

    original_width, original_height = image.size

    aspect_ratio = original_width / original_height

    if screen_width / screen_height > aspect_ratio:
        # resize according to height
        new_height = screen_height
        new_width = int(new_height * aspect_ratio)
    else:
        # resize according to width
        new_width = screen_width
        new_height = int(new_width / aspect_ratio)

    # resize the image
    resized_image = image.resize((new_width, new_height), Image.LANCZOS)

    return resized_image


def overlay_camera_images(screen_image, camera_images):
    """
    screen_image: cv2 frame
    camera_images: list[PIL.Image]
    """
    if screen_image is None and camera_images is None:
        print('[Warn]: cannot display when screen and camera are both None')
        return None
    if screen_image is not None:
        screen_image = resize_image_to_fit_screen(screen_image, my_screen_size)

    if camera_images is not None:
        # make sure same camera images
        if not all(img.size == camera_images[0].size for img in camera_images):
            raise ValueError("All camera images must have the same size")

        screen_width, screen_height = my_screen_size if screen_image is None else screen_image.size
        camera_width, camera_height = camera_images[0].size

        # calculate num_cameras_per_row
        num_cameras_per_row = screen_width // camera_width

        # adjust camera_imgs
        if len(camera_images) > num_cameras_per_row:
            adjusted_camera_width = screen_width // len(camera_images)
            adjusted_camera_height = (adjusted_camera_width * camera_height) // camera_width
            camera_images = [img.resize((adjusted_camera_width, adjusted_camera_height), Image.LANCZOS) for img in
                                camera_images]
            camera_width, camera_height = adjusted_camera_width, adjusted_camera_height
            num_cameras_per_row = len(camera_images)

        # if no screen_img, create a container
        if screen_image is None:
            display_image = Image.fromarray(np.zeros((camera_width, my_screen_size[1], 3), dtype=np.uint8))
        else:
            display_image = screen_image
        # cover screen_img using camera_images
        for i, camera_image in enumerate(camera_images):
            row = i // num_cameras_per_row
            col = i % num_cameras_per_row
            x = col * camera_width
            y = row * camera_height
            display_image.paste(camera_image, (x, y))

        return display_image
    else:
        return screen_image


def capture_screen():
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        frame = np.array(sct.grab(monitor))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
    return frame


def capture_camera():
    # capture frame of camera
    ret, frame = cap.read()
    if not ret:
        raise Exception('Fail to capture frame from camera')
    return frame


def capture_voice():
    return streamin.read(CHUNK)

def play_audio(audio_data):
    streamout.write(audio_data)


def compress_image(frame):
    # buffer = BytesIO()
    # # Save the image to the buffer in the desired format and quality
    # image.save(buffer, format=format, quality=quality)
    # buffer.seek(0)  # Reset buffer position
    # compressed_image_data = buffer.getvalue()
    # buffer.close()
    # return compressed_image_data
    _, encoded_frame = cv2.imencode('.jpg', frame)
    payload = encoded_frame.tobytes()
    return payload


def decompress_image(payload):
    # img_byte_arr = BytesIO(image_bytes)
    # try:
    #     image = Image.open(img_byte_arr)
    #     image.load()  # Force loading the image to check if it's valid
    # except UnidentifiedImageError:
    #     print("The image file could not be identified.")
    #     return None
    # return image
    np_arr = np.frombuffer(payload, dtype=np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return frame
