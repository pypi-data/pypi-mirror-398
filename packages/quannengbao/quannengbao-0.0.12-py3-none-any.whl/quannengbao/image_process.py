import requests
from PIL import Image
from io import BytesIO


class ImageProcess:
    def __init__(self):
        pass

    def get_image_binary(self, image_url):
        try:
            response = requests.get(image_url)
        except Exception:
            print(f"Request error from {image_url}")
            return None

        if response.status_code == 200:
            # 打开图像文件
            image = Image.open(BytesIO(response.content))
            # 将图像转换为PNG格式的二进制数据
            with BytesIO() as f:
                image.save(f, format="JPEG")
                return list(f.getvalue())
        else:
            print(f"Failed to fetch image from {image_url}")
            return None

    def batch_get_image_binary(self, image_dct):
        for item in image_dct:
            url = image_dct[item]["url"]
            image_binary = self.get_image_binary(url)

            if image_binary:
                image_dct[item]["image_binary"] = image_binary
                print(image_dct[item]["url"])
            else:
                image_dct[item]["image_binary"] = None
                print("Failed to fetch image binary.")
        return image_dct



