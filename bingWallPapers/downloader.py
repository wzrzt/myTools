
import os 
import requests
import re
import datetime
import time
import numpy as np
from PIL import Image


def getPageImgUrl(url):
    headers = {
        # 'Accept' :'*/*',
        # 'Cache-Control': 'no-cache',
        'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36',
        # 'Accept-Encoding': 'gzip, deflate',
        # 'Host': 'bing.ioliu.cn',
        # 'Postman-Token': 'f61ba919-fe7d-4dab-baf1-e267b59eda7e'
    }
    res = requests.get(url,headers=headers).content
    pattern = re.compile(r'data-progressive="(.*?)"')
    urls = re.findall(pattern, str(res))
    return urls


def getAllUrl(page_cnt):
    l = []
    for i in range(1,1+page_cnt):
        url = 'https://bing.ioliu.cn/?p={}'.format(i)
        u = getPageImgUrl(url)
        l += u
        time.sleep(1 + np.random.randint(1, 1000)/1000)
    return l



def DownloadImg(url, dir):
    headers = {
        'use_agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:66.0) Gecko/20100101 Firefox/66.0',
    }
    r = requests.get(url, headers=headers)
    pattern = re.compile(r'/bing/(.*?)_1920')
    filename_raw = re.findall(pattern, url)
    if filename_raw:

        filename = str(filename_raw[0]) + '.jpg'
    
        # while not filename in os.listdir(dir):
        with open(os.path.join(dir, filename), 'wb') as f:
            f.write(r.content)
    else:
        pass


if __name__ == "__main__":
    output_dir = 'Wallpapers'
    try:
        os.makedirs(output_dir)
    except:
        pass

    # urls = getAllUrl(10)
    # for page_no, page_url in enumerate(urls):
    #     print("Processing page: %s of %s. %s" % (page_no, 10, datetime.datetime.now()))
    #     img_urls = getPageImgUrl(page_url)
    #     for img_no, img_url in enumerate(img_urls):
    #         print("Processing page: %s of %s, pic_no: %s. %s" % (page_no, 10, img_no, datetime.datetime.now()))
    #         DownloadImg(img_url, output_dir)

    def parse_img_name(url):
        pattern = re.compile(r'/bing/(.*?)_1920')
        filename_raw = re.findall(pattern, url)
        if filename_raw:
            filename = str(filename_raw[0]) + '.jpg'
            return filename
        else:
            return None

    # page_cnt = int(input("输入要"))
    page_cnt = 10 
    img_urls_raw = getAllUrl(page_cnt)
    img_urls = list(filter(lambda x: parse_img_name(x) not in os.listdir(output_dir), img_urls_raw))

    img_cnt = len(img_urls)

    if img_cnt == 0:
        print("已经无壁纸可以下载, 可以尝试往前下载一些往期的壁纸")

    for img_no, img_url in enumerate(img_urls):
        print("Processing pic_no: %s of %s. %s" % (img_no + 1, img_cnt, datetime.datetime.now()))
        img_filename = parse_img_name(img_url)
        DownloadImg(img_url, output_dir)
        im = Image.open(os.path.join(output_dir, img_filename)) 
        print('%s 宽：%d,高：%d' % (img_filename, im.size[0],im.size[1]))
        if im.size[0] < 1920 or im.size[1] < 1080:
            print('%s 宽：%d,高：%d, 尺寸不对，将删除' % (img_filename, im.size[0], im.size[1]))
            os.remove(os.path.join(output_dir, img_filename))
