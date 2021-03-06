
from requests.api import head
from tqdm import tqdm
import requests
from lxml import etree
from retrying import retry
import re
import pandas as pd
from PIL import Image
import os
from pathvalidate import sanitize_filename


"""
基于 http://bingimg.cn 抓取bing壁纸，有1080，4k两版本可选  
图片位于 http://bingimg.cn/list1 中，切换页面改 url后的数字即可，最新的在最前面  
本脚本将抓取前x页壁纸信息，包括标题，副标题，日期，文件名等，拼成pd.DataFrame，再保存至文件夹中  

"""




def _retry_if_exception(exception):
    return isinstance(exception, Exception)


@retry(retry_on_exception=_retry_if_exception,
       wait_random_min=1000,
       wait_random_max=5000,
       stop_max_attempt_number=5)
def get_img_url(url_base, params, headers):
    res = requests.get(url_base, params=params, headers=headers)
    return res


def img_file_check(path, width=1920, height=1080):
    """
    检测文件大小是否正常，如果文件没传输完，这里出错
    """
    try:
        im = Image.open(path) 
        print('%s 宽：%d,高：%d' % (path, im.size[0], im.size[1]))
        if im.size[0] >= width or im.size[1] >= height:
            print('%s 宽：%d,高：%d, 尺寸不对' % (path, im.size[0], im.size[1]))
            return False
        else:
            return True

    except Exception as e:
        print(e)
        return False


def list_wallpapers(path):
    """
    检查现有的图片，以日期为检查依据, pattern后面按实际情况再调整
    """
    pattern = re.compile('20\\d{2}[01]\\d[0123]\d')
    
    files = os.listdir(path)
    dates = []
    for filename in files:
        dates.extend(re.findall(pattern, filename))
    
    return dates


base_url = """http://bingimg.cn/list1"""


# # 先到 图片模块那一层div
# xpath_img_div = """/html/body/div[@class="container"]/div[2]/div"""

# xpath_img_url_1080p = """div/div[@class="card_date_div"]/span[3]/a/@href"""
# xpath_img_url_4k = """div/div[@class="card_date_div"]/span[5]/a/@href"""
# xpath_img_title = """div/div[1]/div[1]/a/h2/text()"""
# xpath_img_subtitle = """div/div[1]/div[2]/h3/text()"""
# xpath_img_date = """div/div[2]/span[1]/text()"""


# # 到 li 那一层，找所有页码中最大的一个
# xpath_page_no = """/html/body/div[2]/div[3]/div/ul/li/a/text()"""

# xpath_img_url_1080p = """/html/body/div[@class="container"]/div[2]/div/div/div[@class="card_date_div"]/span[3]/a/@href"""
# xpath_img_url_4k = """/html/body/div[@class="container"]/div[2]/div/div/div[@class="card_date_div"]/span[5]/a/@href"""
# xpath_img_title = """/html/body/div[@class="container"]/div[2]/div/div/div[1]/div[1]/a/h2/text()"""
# xpath_img_subtitle = """/html/body/div[@class="container"]/div[2]/div/div/div[1]/div[2]/h3/text()"""
# xpath_img_date = """/html/body/div[@class="container"]/div[2]/div/div/div[2]/span[1]/text()"""


# res = requests.get(base_url)
# page_source = etree.HTML(res.text)

# img_divs = page_source.xpath(xpath_img_div)

# page_nos = page_source.xpath(xpath_page_no)
# page_nos_int = [ int(x) for x in filter(lambda x: re.match('\\d+', x), page_nos)]
# page_no_max = max(page_nos_int)

# for img_div in img_divs:

#     print(img_div.xpath(xpath_page_no))
#     print(img_div.xpath(xpath_img_url_1080p))
#     print(img_div.xpath(xpath_img_url_4k))
#     print(img_div.xpath(xpath_img_title))
#     print(img_div.xpath(xpath_img_subtitle))
#     print(img_div.xpath(xpath_img_date))


def get_page_source(page_no):
    base_url = f"""http://bingimg.cn/list{page_no}"""
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36'}
    res = requests.get(base_url, headers = headers)
    html = etree.HTML(res.text)
    return html


def get_all_pages(page_cnt):
    page_sources = []
    for page_no in tqdm(range(1, 1+page_cnt)):
        page_sources.append(get_page_source(page_no))

    return page_sources


def extract_page_num(page_html):
    xpath_page_no = """/html/body/div[2]/div[3]/div/ul/li/a/text()"""
    page_nos = page_html.xpath(xpath_page_no)
    page_nos_int = [ int(x) for x in filter(lambda x: re.match('\\d+', x), page_nos)]
    page_no_max = max(page_nos_int)
    return page_no_max


def extrac_img_source(page_html_list:list):
    # 先到 图片模块那一层div
    xpath_img_div = """/html/body/div[@class="container"]/div[2]/div"""
    xpath_img_url_1080p = """div/div[@class="card_date_div"]/span[3]/a/@href"""
    xpath_img_url_4k = """div/div[@class="card_date_div"]/span[5]/a/@href"""
    xpath_img_title = """div/div[1]/div[1]/a/h2/text()"""
    xpath_img_subtitle = """div/div[1]/div[2]/h3/text()"""
    xpath_img_date = """div/div[2]/span[1]/text()"""

    urls = []
    for page_html in tqdm(page_html_list):

        img_divs = page_html.xpath(xpath_img_div)

        for img_div in img_divs:

            title = img_div.xpath(xpath_img_title)
            if title:
                title = title[0].strip()
            else:
                title = ''

            subtitle = img_div.xpath(xpath_img_subtitle)
            if subtitle:
                subtitle = subtitle[0].strip()
            else:
                subtitle = ''

            url_1080 = img_div.xpath(xpath_img_url_1080p)
            if url_1080:
                url_1080 = url_1080[0].strip()
            else:
                url_1080 = ''
            
            url_4k = img_div.xpath(xpath_img_url_4k)
            if url_4k:
                url_4k = url_4k[0].strip()
            else:
                url_4k = ''
            
            date = img_div.xpath(xpath_img_date)
            if date:
                date = date[0].strip()
            else:
                date = ''

            url_one = {
                'title': title, 
                'subtitle': subtitle,
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
def DownloadImg(url, dir):
    headers = {
        'use_agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:66.0) Gecko/20100101 Firefox/66.0',
    }
    r = requests.get(url, headers=headers)
    filename_raw = os.path.basename(url)
    filename = sanitize_filename(filename_raw)

    with open(os.path.join(dir, filename), 'wb') as f:
        f.write(r.content)


@retry(retry_on_exception=_retry_if_exception,
       wait_random_min=1000,
       wait_random_max=5000,
       stop_max_attempt_number=5)
def DownloadOneImg(url, path):
    headers = {
        'use_agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:66.0) Gecko/20100101 Firefox/66.0',
    }
    r = requests.get(url, headers=headers)

    with open(path, 'wb') as f:
        f.write(r.content)


def DownloadImgs(url_df, dir, type='4k', with_title=False, with_date=False):

    if os.path.isdir(dir):
        pass
    else:
        os.makedirs(dir)

    if type.lower() == '1080p':
        tag = 'url_1080'
    else:
        # default 4k
        tag = 'url_4k'
    
    url_df['file_basename'] = url_df[tag].apply(lambda x: sanitize_filename(os.path.basename(x)))
    url_df['filename'] = url_df['file_basename']
    if with_title:
        url_df['filename'] = url_df['title'] + '.' + url_df['file_basename']
    if with_date:
        url_df['filename'] = 'date_' + url_df['date'].str.replace('-', '') + '.' + url_df['filename']
    
    url_df['filename'] = url_df['filename'].apply(lambda x: sanitize_filename(x))
    for i, row in tqdm(url_df.iterrows(), total=url_df.shape):
        DownloadOneImg(row[tag], os.path.join(dir, row['filename']))




if __name__=="__main__":

    page_htmls = get_all_pages(5)
    url_df = extrac_img_source(page_htmls)

    # for i, row in tqdm(url_df.iterrows(), total = url_df.shape[0]):
    #     DownloadImg(row['url_1080'], 'wallPapers')

    DownloadImgs(url_df, 'wallPapers', with_date=True, with_title=True)

    print(1)