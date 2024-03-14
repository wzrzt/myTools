

"""


从这个网址进 https://bing.gifposter.com/

中国区Bing壁纸 https://bing.gifposter.com/cn
美区Bing壁纸 https://bing.gifposter.com/

中国区Bing壁纸列表页 https://bing.gifposter.com/cn/list/new/desc/classic.html
美区列表页 https://bing.gifposter.com/list/new/desc/classic.html
美区列表页第2页 https://bing.gifposter.com/list/new/desc/classic.html?p=2

预览地址 src="https://h2.gifposter.com/bingImages/BryceSnow_1920x1080.jpg_sm"
下载地址
UHD https://bing.gifposter.com/bingImages/BeaumontClock_uhd.jpg
1080 https://bing.gifposter.com/bingImages/BeaumontClock_1920x1080.jpg


备选网站 https://bing.wallpaper.pics
"""


import os
import re
import requests
import configparser
import pandas as pd
from tqdm import tqdm
from lxml import etree
from retrying import retry
from pathvalidate import sanitize_filename
from PIL import Image
from _utils import set_logger
from dateutil import parser


def _retry_if_exception(exception):
    return isinstance(exception, Exception)


class BingWallpaperDownloader:
    def __init__(self, resolution='4k', log_dir='.'):
        """
        resolution '4k' or '1080'
        4k   --> _uhd suffix in download url
        1080 --> _1920x1080 suffix in download url
        """
        self.resolution = resolution
        self.base_url = 'https://bing.gifposter.com/cn/list/new/desc/classic.html'
        self.logger = set_logger('WallpaperDownloader', log_dir)
        self.download_dir = self.set_default_dir()
        self.history_date = self.get_downloaded()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        }

    def set_download_dir(self, download_dir):
        if os.path.isdir(download_dir):
            pass
        else:
            os.makedirs(download_dir)
        self.download_dir = download_dir
        self.logger.info(f"Download dir set to {download_dir}")
        self.history_date = self.get_downloaded()
    
    def set_default_dir(self, config_filepath='config.ini'):
        try:
            config = configparser.ConfigParser()
            config.read(config_filepath)
            output_path = config.get('wallpaper', 'outpath')
        except Exception as e:
            # print(e)
            self.logger.error(e)
            self.logger.error(f"{config_filepath} not found or wrong structure, will use default dir")
            output_path = 'WallPapers'
        
        # self.download_dir = output_path
        # print(f"Download dir set to {output_path}")
        self.logger.info(f"Download dir set to {output_path}")
        return output_path
        
    def _img_file_check(self, path, width=1920, height=1080):
        try:
            im = Image.open(path)
            print('%s Width: %d, Height: %d' % (path, im.size[0], im.size[1]))
            if im.size[0] < width or im.size[1] < height:
                print('%s Width: %d, Height: %d, incorrect dimensions' % (path, im.size[0], im.size[1]))
                return False
            else:
                return True
        except Exception as e:
            print(e)
            return False

    def _get_page_source(self, page_no):
        url = f"{self.base_url}/?p={page_no}"
        res = requests.get(url, headers=self.headers)
        page_html = etree.HTML(res.text)
        return page_html

    def _get_all_pages(self, page_cnt):
        page_sources = []
        for page_no in tqdm(range(1, 1 + page_cnt)):
            page_sources.append(self._get_page_source(page_no))
        return page_sources

    def _extract_page_num(self, page_html):
        xpath_page_no = "/html/body/div[2]/div[3]/div/ul/li/a/text()"
        page_nos = page_html.xpath(xpath_page_no)
        page_nos_int = [int(x) for x in filter(lambda x: re.match('\\d+', x), page_nos)]
        page_no_max = max(page_nos_int)
        return page_no_max

    def _extract_img_source(self, page_html_list):
        # 20230821更新 原网址抓取不到了，估计是接口调整了，改网址，页面排版也有变动
        xpath_img_div = """/html/body/main/section/ul/li"""
        # xpath_img_url_1080p = """div[@class="card progressive"]/div[@class="options"]/a[2]/@href"""
        # xpath_img_url_4k = """div[@class="card progressive"]/div[@class="options"]/a[3]/@href"""
        # xpath_img_title = """div[@class="card progressive"]/div[@class="description"]/h3/text()"""
        # xpath_img_subtitle = """div/div[1]/div[2]/h3/text()"""
        # xpath_img_date = """div[@class="card progressive"]/div[@class="description"]/p[1]/em/text()"""

        # xpath_list = "/html/body/main/section/ul/li"
        xpath_img_url_thumb = "a/img/@src"
        xpath_img_title = "div/span/text()"  # 标题需要用路径修复函数修复一下，避免特殊符号导致失败
        xpath_img_date = "div/time/text()"

        urls = []
        for page_html in tqdm(page_html_list):
            img_divs = page_html.xpath(xpath_img_div)
            for img_div in img_divs:

                title = img_div.xpath(xpath_img_title)
                if title:
                    title = title[0].strip()
                    title = re.sub('\(.+\)', '', title)
                    title = title.strip()
                else:
                    title = ''

                date = img_div.xpath(xpath_img_date)
                if date:
                    date_string = date[0].strip()
                    date_parsed = parser.parse(date_string)
                    date = date_parsed.strftime("%Y-%m-%d")
                else:
                    date = ''

                url_thumb = img_div.xpath(xpath_img_url_thumb)
                if url_thumb:
                    url_thumb = url_thumb[0].strip()
                else:
                    url_thumb = ''
                
                if url_thumb:
                    url_1080 = url_thumb.replace("https://h2", "https://bing").replace("1920x1080.jpg_sm", "1920x1080.jpg")
                    url_4k = url_thumb.replace("https://h2", "https://bing").replace("1920x1080.jpg_sm", "uhd.jpg")
                    title_en = url_thumb.replace("https://h2.gifposter.com/bingImages/", "").replace("_1920x1080.jpg_sm", "")
                
                    url_one = {
                        'title': title,
                        'title_en': title_en,
                        'url_1080': url_1080,
                        'url_4k': url_4k,
                        'date': date
                    }
                    
                    urls.append(url_one)

                else:
                    pass

        url_df = pd.DataFrame(urls)

        return url_df

    @retry(retry_on_exception=_retry_if_exception,
        wait_random_min=1000,
        wait_random_max=5000,
        stop_max_attempt_number=5)
    def _download_wallpaper(self, url, path):
        response = requests.get(url, headers=self.headers, stream=True)
        if response.status_code == 200:
            total_size = int(response.headers.get("content-length", 0))
            # with open(path, 'wb') as f:
            #     f.write(r.content)
            output_filename = os.path.basename(path)
            file_tag = output_filename.split('.')[0]
            # Create a progress bar
            progress_bar = tqdm(total=total_size, unit="B", unit_scale=True)
            progress_bar.set_description(file_tag)
            # Write the downloaded content to a file
            with open(path, "wb") as file:
                for data in response.iter_content(chunk_size=4096):
                    file.write(data)
                    progress_bar.update(len(data))
            # Close the progress bar
            progress_bar.close()

    def download_wallpapers(self, page_cnt=5):
        """
        default download recent 5 pages
        """
        page_html_list = self._get_all_pages(page_cnt)
        url_df = self._extract_img_source(page_html_list)
        url_df = url_df.loc[url_df[f'url_{self.resolution}'].str.startswith('http')]
        # url_df['file_basename'] = url_df[f'url_{self.resolution}'].apply(lambda x: sanitize_filename(os.path.basename(x)))
        # url_df['file_basename'] = url_df['file_basename'].str.replace('&qlt=100', '').str.replace('thid=', '')
        # url_df['filename'] = url_df['file_basename']
        # url_df['filename'] = 'date_' + url_df['date'].str.replace('-', '') + '.' + url_df['filename']
        # url_df['filename'] = url_df['filename'].apply(lambda x: sanitize_filename(x))
        url_df['filename'] = url_df[f'url_{self.resolution}'].apply(lambda x: os.path.basename(x))
        url_df['filename'] = 'date_' + url_df['date'].str.replace('-', '') + '.' + url_df['title'] + '.OHR.' + url_df['filename'].str.replace('uhd', 'UHD')
        url_df['filename'] = url_df['filename'].apply(lambda x: sanitize_filename(x))
        # dates_downloaded = self.get_downloaded()
        if self.history_date:
            url_df = url_df.loc[~url_df['date'].isin(self.history_date)]

        if url_df.empty:
            self.logger.info("All wallpaper exists or no url crawled, can try to change date")
        
        else:
            for _, row in tqdm(url_df.iterrows(), total=url_df.shape[0]):
                img_url = row[f'url_{self.resolution}']
                if img_url:
                    save_path = os.path.join(self.download_dir, row['filename'])
                    self._download_wallpaper(img_url, save_path)
                    if os.path.isfile(save_path):
                        if self._img_file_check(save_path):
                            self.logger.info(f"Downloaded {save_path}")
                        else:
                            os.remove(save_path)
                            self.logger.info(f"Deleted {save_path}")
                    else:
                        self.logger.info("Failed to download wallpaper.")
                else:
                    self.logger.info("Invalid image URL.")


    def get_downloaded(self):
        """
        获取已下载的壁纸
        """

        filenames = os.listdir(self.download_dir)

        wp_files = list(filter(lambda x: x.startswith('date_'), filenames))
        
        dates = [x.split('.')[0].replace('date_', '') for x in wp_files]
        dates = ['-'.join( [x[:4], x[4:6], x[6:]] ) for x in dates]
        return dates


if __name__=="__main__":

    # 示例用法
    downloader = BingWallpaperDownloader()
    # downloader.set_download_dir('TestOut/bing.gifposter.com')
    downloader.download_wallpapers(page_cnt=5)

