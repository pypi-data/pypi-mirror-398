from PIL import Image
import requests
from urllib.parse import urlparse
from aibridgecore.exceptions import ImageException, AIBridgeException
from io import BytesIO
import base64
import sys


class ImageOptimise:
    TARGET_SIZE = 4 * 1024 * 1024

    @classmethod
    def image_resize(self, image, buf):
        current_size = len(buf.getvalue())
        width = image.width
        height = image.height
        bytes_im = None
        print(current_size, self.TARGET_SIZE)
        while current_size > self.TARGET_SIZE:
            width = int(width * 0.75)
            height = int(height * 0.75)
            resized_image = image.resize((width, height), Image.Resampling.LANCZOS)
            temp_file = BytesIO()
            resized_image.save(temp_file, format="PNG", quality=80)
            print("Original image size:", sys.getsizeof(temp_file) / (1 << 20), "MB")
            current_size = len(temp_file.getvalue())
            bytes_im = temp_file.getvalue()
            temp_file.seek(0)
            temp_file.close
        if not bytes_im:
            temp_file = BytesIO()
            image.save(temp_file, format="PNG", quality=80)
            print("xxxxxxxxxxxxxxxxxx:", sys.getsizeof(temp_file) / (1 << 20), "MB")
            bytes_im = temp_file.getvalue()
            temp_file.seek(0)
            temp_file.close

        return bytes_im

    @classmethod
    def get_image(self, image_data):
        image_obj = []
        try:
            for index, image in enumerate(image_data):
                result = urlparse(image)
                if all([result.scheme, result.netloc]):
                    response = requests.get(image)
                    if response.status_code == 200:
                        image_data = BytesIO(response.content)
                        image = Image.open(image_data)
                elif "base64" in image:
                    image = image.split(",")[1]
                    image = BytesIO(base64.b64decode(image))
                    image = Image.open(image)
                else:
                    with open(image, "rb") as image_file:
                        binary_data = image_file.read()
                    image_buffer = BytesIO(binary_data)
                    image = Image.open(image_buffer)
                if image.mode != "RGBA":
                    image = image.convert("RGBA")
                image_obj.append(image)
            return image_obj
        except Exception as e:
            raise ImageException(f"Error in reading the the image {e}")

    @classmethod
    def get_bytes_io(self, image_data):
        image_obj = []
        for image in image_data:
            buf = BytesIO()
            image.save(buf, save_all=True, format="PNG", quality=100)
            buf_size = len(buf.getvalue())
            print("buffer image size:", sys.getsizeof(buf) / (1 << 20), "MB")
            if buf_size > self.TARGET_SIZE:
                bytes_im = self.image_resize(image, buf)
            else:
                bytes_im = buf.getvalue()
            buf.close()
            image_obj.append(bytes_im)
        return image_obj

    @classmethod
    def set_dimension(self, image_data, mask_data):
        for index, image in enumerate(image_data):
            if image.size != mask_data[index].size:
                mask = mask_data[index].resize(image.size)
                print(image.size)
                mask_data[index] = mask
                print(mask_data[index].size)
        return mask_data
