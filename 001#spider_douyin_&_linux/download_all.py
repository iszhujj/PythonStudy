# -*- coding: utf-8 -*-
'''
    @Author: zhujj
    @Time: 2024/2/29 15:12
'''
import threading, requests, os, zipfile
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from pyvirtualdisplay import Display
from time import sleep
from bs4 import BeautifulSoup
from selenium.common.exceptions import WebDriverException

display = Display(visible=0, size=(1980, 1440))
display.start()

firefox_options = Options()
firefox_options.headless = True
firefox_options.binary_location = '/home/lighthouse/firefox/firefox'


# 获取当前时间
def get_current_time():
    now = datetime.now()
    format_time = now.strftime("_%Y-%m-%d__%H-%M-%S-%f__")
    return format_time


# 设置一个根路径，作品文件以及日志文件都保留在此
ABS_PATH = f'/home/resources/{get_current_time()}'


# 创建目录，dir_name 是作品的发布时间，格式为：2024-02-26 16:59，需要进行处理
def create_dir(dir_name):
    dir_name = dir_name.replace(' ', '-').replace(':', '-')
    path = f'{ABS_PATH}/{dir_name}'
    try:
        os.makedirs(path)
    except FileExistsError:
        print(f'试图创建已存在的文件， 失败（{path}）')
    else:
        print(f'创建目录成功  {path}')
    finally:
        return path


# 下载    目录名称，当前文件的命名，下载的地址
def download_works(dir_name, work_name, src):
    response = requests.get(src, stream=True)
    if response.status_code == 200:
        with open(f'{dir_name}/{work_name}', mode='wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)


# 判断作品是否已经下载过
def test_work_exist(dir_name):
    dir_name = dir_name.replace(' ', '-').replace(':', '-')
    path = f'{ABS_PATH}/{dir_name}'
    if os.path.exists(path) and os.path.isdir(path):
        if os.listdir(path):
            return True
    return False


def get_all_works(target):
    try:
        driver = webdriver.Firefox(options=firefox_options)
        driver.set_page_load_timeout(6)
        # 目标博主页面
        driver.get(target)
        WebDriverWait(driver, 6).until(EC.presence_of_element_located((By.CLASS_NAME, 'e6wsjNLL')))
        WebDriverWait(driver, 6).until(EC.presence_of_element_located((By.CLASS_NAME, 'niBfRBgX')))

        driver.execute_script('document.querySelector(".wcHSRAj6").scrollIntoView()')
        sleep(1)

        html = BeautifulSoup(driver.page_source, 'lxml')
        driver.quit()
        # 作品列表
        ul = html.find(class_='e6wsjNLL')
        # 每一个作品
        lis = ul.findAll(class_='niBfRBgX')

        for li in lis:
            element_a = li.find('a')
            is_pictures = element_a.find(class_='TQTCdYql')

            if (not is_pictures) or (not is_pictures.svg):
                href = f'https://www.douyin.com{element_a["href"]}'

                temp_driver = webdriver.Firefox(options=firefox_options)
                temp_driver.set_page_load_timeout(6)
                temp_driver.get(href)

                WebDriverWait(temp_driver, 6).until(EC.presence_of_element_located((By.CLASS_NAME, 'D8UdT9V8')))

                # 不是必须，剩余内容webdriver也能胜任
                html_v = BeautifulSoup(temp_driver.page_source, 'lxml')
                temp_driver.quit()

                # 获取该作品的发布时间
                publish_time = html_v.find(class_='D8UdT9V8').string[5:]

                # if test_work_exist(f'{publish_time}_video'):
                #     continue

                video = html_v.find(class_='xg-video-container').video
                source = video.find('source')

                # 为该作品创建文件夹
                path = create_dir(f'{publish_time}_video')

                # 下载作品
                download_works(path, f'{get_current_time()}.mp4', f'https:{source["src"]}')
            else:
                href = f'https:{element_a["href"]}'

                temp_driver = webdriver.Firefox(options=firefox_options)
                temp_driver.set_page_load_timeout(6)
                temp_driver.get(href)
                WebDriverWait(temp_driver, 6).until(EC.presence_of_element_located((By.CLASS_NAME, 'YWeXsAGK')))

                # 使用 beautifulsoup 不是必须
                html_p = BeautifulSoup(temp_driver.page_source, 'lxml')
                temp_driver.quit()

                publish_time = f'{html_p.find(class_="YWeXsAGK")}'[-23:-7]

                # 图片列表
                img_ul = html_p.find(class_='KiGtXxLr')
                imgs = img_ul.findAll('img')

                # if test_work_exist(f'{publish_time}_pictures_{len(imgs)}'):
                #     continue

                path = create_dir(f'{publish_time}_pictures_{len(imgs)}')
                for img in imgs:
                    download_works(path, f'{get_current_time()}.webp', f'{img["src"]}')

        display.stop()
        print('##### finish #####')
    except WebDriverException as e:
        print(f"捕获到 WebDriverException: {e}")
    except Exception as err:
        print("捕获到其他错误 get_all_works 末尾")
        print(err)
    finally:
        driver.quit()
        display.stop()


# 将目录进行压缩
def zipdir(path, ziph):
    # ziph 是 zipfile.ZipFile 对象
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file),
                       os.path.relpath(os.path.join(root, file), os.path.join(path, '..')))


def dy_download_all(target_url):
    get_all_works(target_url)

    directory_to_zip = ABS_PATH  # 目录路径
    output_filename = f'{ABS_PATH}.zip'  # 输出ZIP文件的名称

    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipdir(directory_to_zip, zipf)

    return f'{ABS_PATH}.zip'  # 返回下载地址


if __name__ == '__main__':
    # 简单测试
    url = input('请输入博主主页url：')
    path = dy_download_all(url)
    print('下载完成')
    print(f'地址：{path}')

