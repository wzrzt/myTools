from PIL import Image
from tqdm import tqdm
import os

# 指定图片文件夹的路径
IMAGE_FOLDER = '/Users/wzr/Tools/WallPapers'
THUMBNAIL_FOLDER = '/Users/wzr/temp/temp_thumbnail'



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


filepaths = os.listdir(IMAGE_FOLDER)
pbar = tqdm(filepaths)
for filepath in tqdm(filepaths):
    if filepath.endswith('jpg'):
        pbar.set_description(filepath)
        img_path = os.path.join(IMAGE_FOLDER, filepath)
        generate_thumbnail(img_path)
