
"""

备选网站 https://bing.wallpaper.pics
当前面的网站不再更新维护时，走这个网站

某个日期的壁纸： "https://bing.wallpaper.pics/CN/20240312.html"
缺点是一页只有一个壁纸，优点是直接按日期下载，而且获取到的下载链接也是bing原始的链接，可以与最早的全名保持一致

下载链接需要转换
https://www.bing.com/th?id=OHR.MagadiFlamingos_ZH-CN7888437841_1920x1080.jpg&rf=LaDigue_1920x1080.jpg&pid=hp

1920x1080: https://www.bing.com/th?id=OHR.MagadiFlamingos_ZH-CN7888437841_1920x1080.jpg&qlt=100
4k: https://www.bing.com/th?id=OHR.MagadiFlamingos_ZH-CN7888437841_UHD.jpg&qlt=100


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
import datetime


def _retry_if_exception(exception):
    return isinstance(exception, Exception)


class BingWallpaperDownloader:
    def __init__(self, resolution='4k', log_dir='.'):
        """
        resolution '4k' or '1080'
        """
        self.resolution = resolution
        self.base_url = 'https://bing.wallpaper.pics'
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

    def generate_date_list(self, start_date, end_date):
        """
        date format must be 'YYYY-MM-DD'
        start_date: '2021-01-01' 
        end_date: '2021-12-31'
        """
        start_date_time = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end_date_time = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        if start_date_time > end_date_time:
            raise ValueError("start_date must be earlier than end_date")
        days_diff = (end_date_time - start_date_time).days
        date_list = []
        # date_list.append(start_date)
        for i in range(days_diff + 1):
            date_i = start_date_time + datetime.timedelta(days=i)
            date_str = date_i.strftime('%Y-%m-%d')
            date_list.append(date_str)
        
        return date_list
    
    def recent_date_list(self, recent_days=5):
        """
        date format must be 'YYYY-MM-DD'
        start_date: '2021-01-01' 
        end_date: '2021-12-31'
        """
        # start_date_time = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end_date_time = datetime.datetime.now()
        date_list = []
        for i in range(recent_days):
            date_i = end_date_time - datetime.timedelta(days=i)
            date_str = date_i.strftime('%Y-%m-%d')
            date_list.append(date_str)
        
        return date_list
    
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

    # def _get_page_source(self, page_no):
    #     url = f"{self.base_url}/?p={page_no}"
    #     res = requests.get(url, headers=self.headers)
    #     page_html = etree.HTML(res.text)
    #     return page_html
        
    def _get_page_source(self, date_str):
        date_str = date_str.replace('-', '')
        url = f"{self.base_url}/CN/{date_str}.html"
        res = requests.get(url, headers=self.headers)
        page_html = etree.HTML(res.text)
        return page_html

    def _get_all_pages(self, date_list):
        page_sources = []
        for date_str in date_list:
            page_sources.append({'date': date_str, 'html': self._get_page_source(date_str)})
        return page_sources

    # def _extract_page_num(self, page_html):
    #     xpath_page_no = "/html/body/div[2]/div[3]/div/ul/li/a/text()"
    #     page_nos = page_html.xpath(xpath_page_no)
    #     page_nos_int = [int(x) for x in filter(lambda x: re.match('\\d+', x), page_nos)]
    #     page_no_max = max(page_nos_int)
    #     return page_no_max

    def _extract_img_source(self, page_html_list):

        xpath_img_div = '//*[@id="photos"]/div/div[1]/img'

        urls = []
        for each_page_html in tqdm(page_html_list):
            
            page_html = each_page_html['html']
            date = each_page_html['date']

            img_divs = page_html.xpath(xpath_img_div)
            if img_divs:
                img_div = img_divs[0]

                img_url = img_div.get('src')
                title = img_div.get('title')
                
                if title:
                    title = title.strip()
                    title = re.sub('\(.+\)', '', title)
                    title = title.strip()
                else:
                    title = ''

                if img_url:
                    img_url_base = img_url.split('&')[0]
                    url_1080 = 'https:' + img_url_base + "&qlt=100"
                    url_4k = 'https:' + img_url_base.replace('1920x1080', 'UHD') + "&qlt=100"

                url_one = {
                    'title': title, 
                    # 'subtitle': subtitle,
                    'url_1080': url_1080,
                    'url_4k': url_4k,
                    'date': date
                }
                
                urls.append(url_one)

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

    def download_wallpapers(self, date_list):
        """
        default download recent 5 pages
        """
        page_html_list = self._get_all_pages(date_list)
        url_df = self._extract_img_source(page_html_list)
        url_df = url_df.loc[url_df[f'url_{self.resolution}'].str.startswith('http')]
        url_df['file_basename'] = url_df[f'url_{self.resolution}'].apply(lambda x: sanitize_filename(os.path.basename(x)))
        url_df['file_basename'] = url_df['file_basename'].str.replace('&qlt=100', '').str.replace('thid=', '')
        url_df['filename'] = url_df['file_basename']
        url_df['filename'] = 'date_' + url_df['date'].str.replace('-', '') + '.' + url_df['filename']
        url_df['filename'] = url_df['filename'].apply(lambda x: sanitize_filename(x))
        
        url_df['filename'] = url_df['title'] + '.' + url_df['file_basename']
        url_df['filename'] = 'date_' + url_df['date'].str.replace('-', '') + '.' + url_df['filename']
        
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


class BingWallpaperDownloader_backup:
    def __init__(self, resolution='4k'):
        self.resolution = resolution
        self.base_url = 'https://bing.wallpaper.pics'

    def _get_image_url(self, page_url):
        response = requests.get(page_url)
        if response.status_code == 200:
            image_url = response.json()[self.resolution]
            return image_url
        return None

    def _download_wallpaper(self, url, download_dir):
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            filename = url.split("/")[-1]
            save_path = os.path.join(download_dir, filename)
            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            return save_path
        return None

    def _img_file_check(self, path, width=1920, height=1080):
        try:
            im = Image.open(path)
            print(f'{path} Width: {im.size[0]}, Height: {im.size[1]}')
            if im.size[0] >= width or im.size[1] >= height:
                print(f'{path} Width: {im.size[0]}, Height: {im.size[1]}, incorrect dimensions')
                return False
            else:
                return True
        except Exception as e:
            print(e)
            return False

    def download_wallpapers(self, download_dir, start_date, end_date):
        url_template = f"{self.base_url}/api/bing-wallpapers/{start_date}/{end_date}"
        for date in tqdm(pd.date_range(start_date, end_date)):
            date_str = date.strftime("%Y-%m-%d")
            url = url_template.format(date_str)
            image_url = self._get_image_url(url)
            if image_url:
                save_path = self._download_wallpaper(image_url, download_dir)
                if save_path:
                    if not self.resolution == '4k' or self._img_file_check(save_path, width=3840, height=2160):
                        print(f"Downloaded {save_path}")
                    else:
                        os.remove(save_path)
                        print(f"Deleted {save_path}")
                else:
                    print("Failed to download wallpaper.")
            else:
                print(f"No wallpaper available for {date_str}.")


if __name__ == '__main__':

    # 示例用法
    downloader = BingWallpaperDownloader()
    # downloader.set_download_dir('TestOut/bing.wallpaper.pics')
    # date_list = downloader.generate_date_list('2023-11-01', '2023-12-31')
    date_list = downloader.recent_date_list(recent_days=10)
    downloader.download_wallpapers(date_list)

