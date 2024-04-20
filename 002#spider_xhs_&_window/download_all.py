'''
    @Author: zhujj
    @Time: 2024/3/3 23:38
'''

import json
import threading
import requests, os
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from datetime import datetime
from selenium import webdriver
from time import sleep
from bs4 import BeautifulSoup


# 获取当前时间
def get_current_time():
    now = datetime.now()
    format_time = now.strftime("_%Y-%m-%d__%H-%M-%S-%f__")
    return format_time


# 下载的作品保存的路径，以作者主页的 id 号命名
ABS_BASE_URL = f'G:\\wordId'


# 检查作品是否已经下载过
def check_download_or_not(work_id, is_pictures):
    end_str = 'pictures' if is_pictures else 'video'
    # work_id 是每一个作品的目录，检查目录是否存在并且是否有内容，则能判断对应的作品是否被下载过
    path = f'{ABS_BASE_URL}/{work_id}-{end_str}'
    if os.path.exists(path) and os.path.isdir(path):
        if os.listdir(path):
            return True
    return False


# 下载资源
def download_resource(url, save_path):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)


# 处理图片类型作品的一系列操作
def download_pictures_prepare(res_links, path, date):
    # 下载作品到目录
    index = 0
    for src in res_links:
        download_resource(src, f'{path}/{date}-{index}.webp')
        index += 1


# 处理图片类型的作品
def deal_pictures(work_id):
    # 直接 requests 请求回来，style 是空的，使用 webdriver 获取当前界面的源代码
    temp_driver = webdriver.Chrome()
    temp_driver.set_page_load_timeout(5)
    temp_driver.get(f'https://www.xiaohongshu.com/explore/{work_id}')
    sleep(1)
    try:
        temp_driver.find_element(By.CLASS_NAME, 'feedback-btn')
    except NoSuchElementException:
        WebDriverWait(temp_driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'swiper-wrapper')))
        source_code = temp_driver.page_source
        temp_driver.quit()

        html = BeautifulSoup(source_code, 'lxml')
        swiper_sliders = html.find_all(class_='swiper-slide')
        # 当前作品的发表日期
        date = html.find(class_='bottom-container').span.string.split(' ')[0].strip()

        # 图片路径
        res_links = []
        for item in swiper_sliders:
            url = item['style'].split('url(')[1].split(')')[0].replace('&quot;', '').replace('"', '')
            if url not in res_links:
                res_links.append(url)

        # 为图片集创建目录
        path = f'{ABS_BASE_URL}/{work_id}-pictures'
        try:
            os.makedirs(path)
        except FileExistsError:
            # 目录已经存在，则直接下载到该目录下
            download_pictures_prepare(res_links, path, date)
        except Exception as err:
            print(f'deal_pictures 捕获到其他错误：{err}')
        else:
            download_pictures_prepare(res_links, path, date)
        finally:
            return 1
    except Exception as err:
        print(f'下载图片类型作品 捕获到错误：{err}')
        return 1
    else:
        print(f'访问作品页面被阻断，下次再试')
        return 0


# 处理视频类型的作品
def deal_video(work_id):
    temp_driver = webdriver.Chrome()
    temp_driver.set_page_load_timeout(5)
    temp_driver.get(f'https://www.xiaohongshu.com/explore/{work_id}')
    sleep(1)
    try:
        # 访问不到正常内容的标准元素
        temp_driver.find_element(By.CLASS_NAME, 'feedback-btn')
    except NoSuchElementException:
        WebDriverWait(temp_driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'player-container')))
        source_code = temp_driver.page_source
        temp_driver.quit()

        html = BeautifulSoup(source_code, 'lxml')
        video_src = html.find(class_='player-el').video['src']
        # 作品发布日期
        date = html.find(class_='bottom-container').span.string.split(' ')[0].strip()

        # 为视频作品创建目录
        path = f'{ABS_BASE_URL}/{work_id}-video'
        try:
            os.makedirs(path)
        except FileExistsError:
            download_resource(video_src, f'{path}/{date}.mp4')
        except Exception as err:
            print(f'deal_video 捕获到其他错误：{err}')
        else:
            download_resource(video_src, f'{path}/{date}.mp4')
        finally:
            return 1
    except Exception as err:
        print(f'下载视频类型作品 捕获到错误：{err}')
        return 1
    else:
        print(f'访问视频作品界面被阻断，下次再试')
        return 0


# 检查作品是否已经下载，如果没有下载则去下载
def work_task(href, is_pictures):
    work_id = href.split('/')[-1]
    has_downloaded = check_download_or_not(work_id, is_pictures)
    # 没有下载，则去下载
    if not has_downloaded:
        if not is_pictures:
            res = deal_video(work_id)
        else:
            res = deal_pictures(work_id)
        if res == 0:
            return 0  # 受到阻断
    else:
        print('当前作品已被下载')
        return 2
    return 1


def thread_task(ul):
    for item in ul:
        href = item[0]
        is_pictures = (True if item[1] == 0 else False)
        res = work_task(href, is_pictures)
        if res == 0:  # 被阻止正常访问
            break


if __name__ == '__main__':
    content = ''
    with open('xhs_works.txt', mode='r', encoding='utf-8') as f:
        content = json.load(f)
    url_list = [list(pair) for pair in content.items()]
    length = len(url_list)
    if length > 3:
        ul = [url_list[0: int(length / 3) + 1], url_list[int(length / 3) + 1: int(length / 3) * 2 + 1],
              url_list[int(length / 3) * 2 + 1: length]]
        for child_ul in ul:
            thread = threading.Thread(target=thread_task, args=(child_ul,))
            thread.start()
    else:
        thread_task(url_list)