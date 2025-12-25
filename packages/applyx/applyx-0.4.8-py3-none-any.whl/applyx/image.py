# coding=utf-8

import os
import shlex
import datetime
import tempfile
import subprocess
from io import BytesIO

from loguru import logger
from PIL import Image
from bson import ObjectId

from applyx.storage import init_storage


class ImageProcessor:

    scene = ''
    image = None
    origin = {}

    def __init__(self):
        self.storage = init_storage()

    def load(self, scene: str, content: BytesIO, name=''):
        self.scene = scene.replace('.', os.sep)

        try:
            self.image = Image.open(content)
        except Exception as e:
            # PIL can not process highly compressed image
            logger.error('image type unknown')
            raise e

        file = tempfile.NamedTemporaryFile()
        self.image.save(file, self.image.format, quality=100)
        if self.image.format not in ('JPEG', 'PNG', 'BMP', 'GIF'):
            logger.error('image type unknown')
            raise Exception('image type unknown')

        image_id = str(ObjectId())
        image_path = self.get_image_path(image_id)
        headers = {
            'Content-Type': f'image/{self.image.format.lower()}',
            'Content-Disposition': f'inline;filename={name}',
            # 'Content-Disposition': f'attachment;filename={name}',
        }
        self.storage.save(image_path, file, headers=headers)

        width, height = self.image.size
        self.origin = {
            'url': self.storage.url(image_path),
            'width': width,
            'height': height,
        }

        return {
            'id': image_id,
            'name': name,
            'type': self.image.format,
            'origin': self.origin,
        }

    def resize(self, dimension: tuple[int, int], name=''):
        if self.image is None:
            return None

        if dimension[0] > self.image.size[0] or dimension[1] > self.image.size[1]:
            (width, height) = self.image.size
        else:
            ratio = max(
                dimension[0] / self.image.size[0], dimension[1] / self.image.size[1]
            )
            width = int(self.image.size[0] * ratio)
            height = int(self.image.size[1] * ratio)

        file = tempfile.NamedTemporaryFile()
        if self.image.format == 'GIF':
            # http://www.lcdf.org/gifsicle/man.html
            # gifsicle --no-warnings --resize 150x150 -o out.gif in.gif
            cmd = f'gifsicle --no-warnings --resize {width}x{height} -o {file.name} {self.origin_path}'
            process = subprocess.Popen(
                shlex.split(cmd),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            _, stderr = process.communicate()
            stderr = stderr.decode('utf8')
            if stderr:
                logger.info(stderr)

            if process.poll() != 0:
                file.close()
                return None

        elif self.image.format in ('JPEG', 'PNG'):
            image_copy = self.image.resize((width, height), Image.ANTIALIAS)
            image_copy.save(file, self.image.format, quality=100)

            if self.image.format == 'JPEG':
                cmd = f'jpegoptim {file.name}'
            elif self.image.format == 'PNG':
                cmd = f'optipng {file.name}'

            process = subprocess.Popen(
                shlex.split(cmd),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            _, stderr = process.communicate()
            stderr = stderr.decode('utf8')
            if stderr:
                logger.info(stderr)

            if process.poll() != 0:
                file.close()
                return None

        elif self.image.format == 'BMP':
            image_copy = self.image.resize((width, height), Image.ANTIALIAS)
            image_copy.save(file, self.image.format, quality=100)

        else:
            file.close()
            return None

        file.seek(0)
        image_id = str(ObjectId())
        image_path = self.get_image_path(image_id)
        filename, extension = os.path.splitext(name)
        headers = {
            'Content-Type': f'image/{self.image.format.lower()}',
            'Content-Disposition': f'inline;filename={filename}_{dimension[0]}x{dimension[1]}.{extension}',
            # 'Content-Disposition': f'attachment;filename={filename}_{dimension[0]}x{dimension[1]}.{extension}',
        }
        self.storage.save(image_path, file, headers=headers)
        file.close()

        return {
            'url': self.storage.url(image_path),
            'width': width,
            'height': height,
        }

    def get_image_path(self, image_id: str):
        now = datetime.datetime.now()
        datetime_path = os.path.join(
            now.strftime('%Y'), now.strftime('%m%d'), now.strftime('%H%M')
        )
        image_filename = f'{image_id }.{self.image.format.lower()}'
        return os.path.join(self.scene, datetime_path, image_filename)
