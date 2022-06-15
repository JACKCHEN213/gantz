# -*- coding: utf-8 -*-
import os
import json
import bs4
from bs4 import BeautifulSoup
import requests
from lxml import html
import re
import threading
import math


def main_page():
    base_url = "https://www.100fanwo.com"
    url = "https://www.100fanwo.com/riman/shaludushi/"
    response = requests.get(url)
    formatter = bs4.BeautifulSoup(response.content, 'html.parser')
    chapter = formatter.select('#chapters').pop()
    titles = chapter.select('.comic-chapters').pop().find_all('a')

    page_url_list = {}
    for title in titles:
        name = title.find('span').get_text()
        title_url = base_url + title.attrs['href']
        page_url_list[name] = title_url
    return page_url_list


def load_json(filename):
    if not os.path.isfile(filename):
        fid = open(filename, 'w')
        fid.close()
    with open(filename, 'r+', encoding='utf-8') as fp:
        content = fp.read()
        if not content:
            return []
        return json.loads(content)


def picture_pages(page_list):
    finish_list = load_json('url_finish_list.json')
    if not os.path.isdir('images_url'):
        os.mkdir('images_url')
    index = 0
    failed_list = {}
    for name, page in page_list.items():
        try:
            index += 1
            if name in finish_list:
                print(f'\r完成：{index}/{len(page_list)}', end='')
                continue
            filename = f'images_url/{name}.json'
            if os.path.isfile(filename):
                print(f'\r完成：{index}/{len(page_list)}', end='')
                continue
            response = requests.get(url=page, timeout=30)
            soup = bs4.BeautifulSoup(response.content, 'html.parser')
            script = soup.find_all('script')[2].get_text()
            image_var = re.findall(r';var chapterImages.*\[(.*?)\];', script)
            if not image_var:
                print('匹配失败')
                failed_list[name] = page
                continue
            images = ['https://res6.myleemo.com' + eval(image.replace('\\', '')) for image in image_var[0].split(',')]
            with open(filename, 'w+', encoding='utf-8') as fp:
                fp.write(json.dumps(images, indent=2, ensure_ascii=False))
            print(f'\r完成：{index}/{len(page_list)}', end='')
            finish_list.append(name)
        except Exception:
            failed_list[name] = page
    if failed_list:
        with open('url_failed_list.json', 'w+', encoding='utf-8') as fp:
            fp.write(json.dumps(failed_list, indent=2, ensure_ascii=False))
    if finish_list:
        with open('url_finish_list.json', 'w+', encoding='utf-8') as fp:
            fp.write(json.dumps(finish_list, indent=2, ensure_ascii=False))


def save_all_pictures(chapter_list, chapter_count):
    if not os.path.isdir('threading'):
        os.mkdir('threading')
    current_threading = threading.currentThread()
    finish_list = load_json(f'threading/images_finish_list_{current_threading.getName()}.json')
    url_path = 'images_url'
    image_path = 'images'
    if not os.path.isdir(image_path):
        os.mkdir(image_path)
    failed_list = []
    headers = {
        "authority": "res4.w13k.com",
        "method": "GET",
        "path": "/images/cache/39/5b/d9940d2d3c1133cf5f4c3152566d.jpg",
        "scheme": "https",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9",
        "cache-control": "max-age=0",
        "cookie": "__yjs_duid=1_39ebf718588f4c192577c2a025339bbb1653450602601",
        "if-modified-since": "Sun, 14 Mar 2021 04:47:33 GMT",
        "if-none-match": "\"604d9565-657b\"",
        "sec-ch-ua": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"101\", \"Google Chrome\";v=\"101\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36"
    }
    for index, chapter in enumerate(chapter_list):
        index += 1
        if chapter in finish_list:
            continue
        filename = url_path + '/' + chapter + '.json'
        if not os.path.isfile(filename):
            print(f'文件不存在: {filename}')
            failed_list.append(chapter)
            continue
        url_list = load_json(filename)
        if not os.path.isdir(image_path + '/' + chapter):
            os.mkdir(image_path + '/' + chapter)
        try:
            index_1 = 0
            for image_url in url_list:
                index_1 += 1
                image_name = image_path + '/' + chapter + '/' + str(index_1) + os.path.splitext(image_url)[-1]
                if os.path.isfile(image_name):
                    continue
                response = requests.get(image_url, timeout=30, headers=headers)
                with open(image_name, 'wb+') as fp:
                    fp.write(response.content)
                print(f'\r完成: {index_1}/{len(url_list)} {index}/{chapter_count}', end='')
        except Exception as e:
            print(e)
            failed_list.append(chapter)
        finish_list.append(chapter)
        print(f'\r完成: {index}/{chapter_count}', end='')
    if failed_list:
        with open(f'threading/images_failed_list_{current_threading.getName()}.json', 'w+', encoding='utf-8') as fp:
            fp.write(json.dumps(failed_list, indent=2, ensure_ascii=False))
    if finish_list:
        with open(f'threading/images_finish_list_{current_threading.getName()}.json', 'w+', encoding='utf-8') as fp:
            fp.write(json.dumps(finish_list, indent=2, ensure_ascii=False))
    print(f'\n线程{current_threading.getName()}已退出')


if __name__ == '__main__':
    page_url_list = main_page()
    picture_pages(page_list=page_url_list)
    print()
    chapter_list = load_json('url_finish_list.json')
    chapter_count = len(chapter_list)
    gap = math.ceil(len(chapter_list) / 10)
    threading_list = []
    for i in range(10):
        start = i * gap
        end = (i + 1) * gap
        if end > len(chapter_list):
            thread = threading.Thread(
                target=save_all_pictures,
                kwargs={'chapter_list': chapter_list[start:], 'chapter_count': chapter_count}
            )
        else:
            thread = threading.Thread(
                target=save_all_pictures,
                kwargs={'chapter_list': chapter_list[start:end], 'chapter_count': chapter_count}
            )
        thread.start()
        threading_list.append(thread)
    for thread in threading_list:
        thread.join()
    print('\n完成')
    pass
