import os
from flask import Flask, render_template, send_from_directory, request
from PIL import Image
import numpy as np


app = Flask(__name__)

# 指定图片文件夹的路径
IMAGE_FOLDER = '/Users/wzr/Tools/WallPapers'
THUMBNAIL_FOLDER = '/Users/wzr/temp/temp_thumbnail'
IMAGES_PER_PAGE = 12
IMAGES_PER_ROW = 3


def count_images():
    image_files = os.listdir(IMAGE_FOLDER)
    # 过滤出图片文件
    image_files = [filename for filename in image_files if filename.endswith(('.jpg', '.jpeg', '.png', '.gif'))]

    return len(image_files)


def generate_thumbnail2(image_path):
    # 生成缩略图并保存到缩略图文件夹
    thumbnail_path = os.path.join(THUMBNAIL_FOLDER, os.path.basename(image_path))
    image = Image.open(image_path)
    image.thumbnail((200, 200))  # 设置缩略图的大小
    image.save(thumbnail_path)
    return thumbnail_path


def generate_thumbnail(image_path):
    # 生成缩略图并保存到缩略图文件夹
    thumbnail_path = os.path.join(THUMBNAIL_FOLDER, os.path.basename(image_path))
    if os.path.isfile(thumbnail_path):
        return os.path.basename(thumbnail_path)
    else:
        image = Image.open(image_path)
        image.thumbnail((800, 450))  # 设置缩略图的大小
        image.save(thumbnail_path)
        return os.path.basename(thumbnail_path)
    

def get_images(page=1):
    # 获取当前页需要显示的图片
    start_index = (page - 1) * IMAGES_PER_PAGE
    end_index = start_index + IMAGES_PER_PAGE

    image_files = os.listdir(IMAGE_FOLDER)
    # 过滤出图片文件
    image_files = [filename for filename in image_files if filename.endswith(('.jpg', '.jpeg', '.png', '.gif'))]

    thumbnails = []
    for image_file in image_files[start_index:end_index]:
        image_path = os.path.join(IMAGE_FOLDER, image_file)
        thumbnail_path = generate_thumbnail(image_path)
        thumbnails.append((image_file, thumbnail_path))

    return thumbnails

def get_images_multi_rows(page=1):
    # 获取当前页需要显示的图片
    start_index = (page - 1) * IMAGES_PER_PAGE
    end_index = start_index + IMAGES_PER_PAGE

    image_files = os.listdir(IMAGE_FOLDER)
    # 过滤出图片文件
    image_files = [filename for filename in image_files if filename.endswith(('.jpg', '.jpeg', '.png', '.gif'))]

    thumbnails = []
    for image_file in image_files[start_index:end_index]:
        image_path = os.path.join(IMAGE_FOLDER, image_file)
        thumbnail_path = generate_thumbnail(image_path)
        thumbnails.append((image_file, thumbnail_path))

    thumbnail_rows = [thumbnails[i:i+IMAGES_PER_ROW] for i in range(0, len(thumbnails), IMAGES_PER_ROW)]

    return thumbnail_rows


@app.route('/')
def index():
    page_cnt = np.ceil(count_images() / IMAGES_PER_PAGE)
    page = request.args.get('page', default=1, type=int)
    thumbnails = get_images_multi_rows(page=page)
    return render_template('index.html', thumbnails=thumbnails, page=page, IMAGES_PER_PAGE=IMAGES_PER_PAGE, 
                           page_cnt = page_cnt)


@app.route('/images/<path:filename>')
def download(filename):
    # 从指定文件夹中发送图片文件
    return send_from_directory(IMAGE_FOLDER, filename)


@app.route('/thumbnails/<path:filename>')
def thumbnail(filename):
    # 从缩略图文件夹中发送缩略图文件
    return send_from_directory(THUMBNAIL_FOLDER, filename)


if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=5001)
    app.run(port=5001)