import os
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageOps

MAX_SIZE = (300, 300)
SMALL_QUALITY = 85
FORMAT = 'JPEG'
BG_COLOR = (255, 255, 255)

def compress_image(image, max_size=MAX_SIZE, quality=SMALL_QUALITY, format=FORMAT, bg_color=BG_COLOR):
    image_obj = Image.open(image)
    image_obj = ImageOps.exif_transpose(image_obj)
    if image_obj.mode in ('RGBA', 'LA'):
        bg = Image.new('RGB', image_obj.size, bg_color)
        bg.paste(image_obj, mask=image_obj.split()[-1])
        image_obj = bg
    elif image_obj.mode != 'RGB':
        image_obj = image_obj.convert('RGB')
    image_obj.thumbnail(max_size, Image.Resampling.LANCZOS)
    buf = BytesIO()
    image_obj.save(buf, format=format, optimize=True, progressive=True, quality=quality)
    buf.seek(0)
    return ContentFile(buf.read())
