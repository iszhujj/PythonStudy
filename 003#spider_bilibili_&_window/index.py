'''
    @Author: zhujj
    @Time: 2024/3/28 12:12
'''

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import requests, os
from datetime import datetime

# 创建一个Chrome选项对象
chrome_options = Options()
chrome_options.add_argument("--headless")  # 启用无头模式,不显示用户界面
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")

headers = {
    'Accept': f'*/*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Origin': 'https://www.bilibili.com',
    'Referer': '',
    'User-Agent': f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Sec-Ch-Ua': f'"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
    'Sec-Ch-Ua-Mobile': f'?0',
    'Sec-Ch-Ua-Platform': f'"Windows"',
    'Sec-Fetch_Dest': 'empty',
    'Sec-Fetch_Mode': 'cors',
    'Sec-Fetch_Site': 'cross-site',
    'Accept-Encoding': 'identity',
}

# 获取视频的相关信息（视频地址、音频地址、音频标题）
def get_play_info(target):
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(target)
    print('浏览器打开成功')
    WebDriverWait(driver, 6).until(EC.presence_of_element_located((By.CLASS_NAME, 'bpx-player-video-wrap')))
    # 注入 JavaScript 获取 音频 和 视频 的源地址
    res = driver.execute_script('''
        let dash = __playinfo__.data.dash;
        let video = dash.video[1].base_url;
        let audio = dash.audio[1].base_url;
        return {"video_url":video, "audio_url":audio}
    ''')
    video_url = res['video_url']
    audio_url = res['audio_url']
    # 获取当前视频的标题
    title = driver.find_element(By.CLASS_NAME, 'video-title').text

    print(f'video_url: {video_url} \n audio: {audio_url} \n title: {title}')
    driver.quit()
    return video_url, audio_url, title

# 下载资源
def download_resource(url, title):
    res = requests.get(url, stream=True, headers=headers)
    total = int(res.headers.get('content-length', 0))
    has_download = 0
    size = 20480                 # 每次下载的字节数，当前 20480 字节即 20KB
    if res.status_code == 200:
        with open(f'{title}.m4s', mode='wb') as f:
            for trunk in res.iter_content(size):
                f.write(trunk)
                has_download += size if has_download + size < total else total - has_download
                if has_download != size:
                    print('\r', end='')
                print(f'{has_download} / {total} , {round(has_download / total * 100, 2)}%', end='')
        print('\n', end='')
        return True
    else:
        print(f"状态码：{res.status_code}")
        return False

# 将音频和视频进行合成
def combine(video_name, audio_name, output_name):
    os.system(f'ffmpeg -i {video_name}.m4s -i {audio_name}.m4s -c copy {output_name}.mp4')
    # 删除无用的 m4s 文件
    os.remove(f'{video_name}.m4s')
    os.remove(f'{audio_name}.m4s')

# 获取完整的资源，视频和音频一起
def get_whole(target, output_title):
    # 修改请求头中的 Referer 为当前作品页地址
    headers['Referer'] = target
    print('start')
    video_url, audio_url, title = get_play_info(target)

    current_time = datetime.now()
    output_file_name = f'{output_title if output_title else ""}{current_time.strftime("%Y_%m_%d_%H_%M_%S")}'

    # 下载视频
    print('视频下载中')
    v_res = download_resource(video_url, f'{output_file_name}-video')
    if v_res:
        print('视频下载完成')
    else:
        print('发生错误，退出程序')
        exit()

    # 下载音频
    print('音频下载中')
    v_res = download_resource(audio_url, f'{output_file_name}-audio')
    if v_res:
        print('音频下载完成')
    else:
        print('发生错误，退出程序')
        exit()

    print('音频视频组合中')
    # .m4s 和最后的文件都下载到当前的项目目录下
    combine(f'{output_file_name}-video', f'{output_file_name}-audio', f'{output_file_name}')
    print('finish')

# 下载音频为并转换为mp3
def download_audio_to_mp3(target, output_title):
    headers['Referer'] = target
    print('start')
    video_url, audio_url, title = get_play_info(target)

    current_time = datetime.now()
    output_file_name = f'{output_title if output_title else ""}{current_time.strftime("%Y_%m_%d_%H_%M_%S")}'

    # 下载音频
    print('音频下载中')
    v_res = download_resource(audio_url, f'{output_file_name}-audio')
    if v_res:
        print('音频下载完成')
    else:
        print('发生错误，退出程序')
        exit()

    print('.m4s 转换为 .mp3')
    os.system(f'ffmpeg -i {output_file_name}-audio.m4s -vn -acodec libmp3lame {output_file_name}.mp3')
    os.remove(f'{output_file_name}-audio.m4s')
    print('finish')


if __name__ == '__main__':
    # 作品页地址格式
    # target = 'https://www.bilibili.com/video/${work_id}'

    target_arr = [
        ['https://www.bilibili.com/video/BV1cg41127ZB/','去年夏天'],
        ['https://www.bilibili.com/video/BV1wJ4m1a7tX/','方圆几里'],
        ['https://www.bilibili.com/video/BV1UZ4y1F7RM/','岁月如歌'],
        ['https://www.bilibili.com/video/BV1xc411N7mT/','无条件'],
        ['https://www.bilibili.com/video/BV1VC4y1K75o/','飞鸟与蝉'],
    ]

    for item in target_arr:
        get_whole(item[0], item[1])
        download_audio_to_mp3(item[0], item[1])



