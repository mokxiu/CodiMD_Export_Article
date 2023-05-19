#!/usr/bin/python
# -*- coding: UTF-8 -*-
# by Mokxiu
'''
注意不要有重名的文章，不然会覆盖
2:40 可能是因为爬的太快了

'''

import re
import json
import requests
import time
import os

session = requests.Session()

# host 后面需要加一个 / ,如：http://127.0.0.1/
host = "http://127.0.0.1/"
email = "xxx"
password = "xxx"


class Codimd():
    def __init__(self, host, email, password):
        self.num = 0
        self.success = 0
        self.host = host
        self.email = email
        self.password = password
        self.heareds = {
            "Content-Length": "36",
            "Cache-Control": "max-age=0",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,ja;q=0.7",
            "Cookie": "connect.sid=s%3A7leM07AimNozqgM-CMOW7aaEO6D1B8BP.mqpI9QtHrpePEM5wCvRrD4FefBZFeNceaO7RwNvQy8E; loginstate=true; userid=ebe80950-73a8-43bf-8bc7-ca82c1576780; indent_type=space; space_units=4; keymap=sublime; io=p5kFV2GzbREi2NHDAAQw",
            "Connection": "close",
        }
        self.object()

    # 请求页面
    def spider(self, mode, url, data='', retry=0):
        proxies = {
            # "http": "http://127.0.0.1:8080"
        }
        # time.sleep(1)
        # print(url)
        try:
            if mode == 'get':
                res = session.get(url=url, headers=self.heareds, proxies=proxies, timeout=2)
                # res = session.get(url=url, headers=self.heareds,timeout=2)

            elif mode == 'post':
                res = session.post(url=url, headers=self.heareds, data=data, proxies=proxies, timeout=2)
                # res = session.post(url=url, headers=self.heareds, data=data,timeout=2)
        except:
            if retry >= 3:
                exit(f'请求url: {url} 时出错，程序退出')
            else:
                print(f'请求url: {url} 时出错，正在第{retry + 1}次尝试')
                self.spider(mode, url, data, retry + 1)
        if res.text == "I'm busy right now, try again later.":
            print("I'm busy right now, try again later.")
            time.sleep(10)
            self.spider(mode, url, data)
        # print(res.text)
        return res

    # 登录
    def login(self):
        data = f"email={self.email}&password={self.password}"
        url = self.host + 'login'
        res = self.spider('post', url, data)
        url = self.host + 'me'
        try:
            res = self.spider('get', url)
            print(f"用户 {res.json()['name']} 登录成功")
        except:
            exit('登陆失败')

    # 导出页面和图片
    def export(self, links):
        for link in links:

            # 获取sid
            url = self.host + f"socket.io/?noteId={link}&EIO=3&transport=polling"
            res = self.spider('get', url)
            sid_re = re.search('\"sid\":\"(.*?)\"', res.text)
            sid = sid_re.group(1)

            dirname, pics = self.export_mk(link, sid)
            if dirname == None:
                continue
            self.export_pic(dirname, pics)
            print(f'{dirname} 项目全部内容导出成功')
            self.success += 1

    # 导出 markdown文件
    def export_mk(self, link, sid):
        #  下载文档
        url = host + f'socket.io/?noteId={link}&EIO=3&transport=polling&sid={sid}'
        res = self.spider('get', url)

        if '["info",{"code":403}]' in res.text:
            print('----------------------')
            print(f'{self.object_dic[link]} 项目导出失败,请检查是否有权限')
            return None, None
        elif '["info",{"code":404}]' in res.text:
            print('----------------------')
            print(f'{self.object_dic[link]} 项目不存在')
            return None, None
        elif res.text == '2:40':
            # 有时会出现导出失败的情况，等待3秒后重试
            # print('超时,等待3秒')
            time.sleep(3)
            links = [link]
            self.export(links)
            return None, None
        # 通过正则取出文章内容
        # 对文件内容进行修饰,换行，使用相对路径
        try:
            document_re = re.search('\"str\":\"(.*?)\",\"revision\"', res.text)
            # 对文件内容进行修饰,换行，使用相对路径
            document = document_re.group(1).replace(r'\n', '\n').replace('![](/uploads', '![](./uploads')
        except:
            print(f'导出文章 {self.object_dic[link]} 时出错')
            print(f'出错URL：{url}')
            print(f'出错resbonse:{res.text}')
            return None, None

        # print(document)
        # 保存图片地址
        pics = re.findall('!\[\]\(\.(.*?)\)', document)

        # 保存到md文件
        dirname = self.object_dic[link].strip()
        name_rule = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        for i in name_rule:
            dirname = dirname.replace(i, '')
        filename = dirname + '.md'

        # 创建项目主文件夹
        if os.path.exists(f'./downloads/{dirname}') == False:
            os.mkdir(f'./downloads/{dirname}')
        with open(f'./downloads/{dirname}/' + filename, mode='w+', encoding='utf-8') as f:
            f.write(document)
        print('----------------------')
        self.num += 1
        print(f'正在导出第 {self.num} 个项目 {filename} ')
        return dirname, pics

    # 导出图片
    def export_pic(self, dirname, pics):
        # 创建图片文件夹
        if os.path.exists(f'./downloads/{dirname}/uploads') == False:
            os.mkdir(f'./downloads/{dirname}/uploads')
        for pic in pics:
            url = self.host + pic
            res = self.spider('get', url)
            pic_name = os.path.basename(pic)
            with open(f'./downloads/{dirname}/uploads/{pic_name}', 'wb') as f:
                f.write(res.content)
            # print(f'{pic_name} 图片保存成功。')

    # 查看所有项目
    def object(self):
        self.object_dic = {}
        url = host + 'history'
        res = self.spider('get', url)
        # print(res.json()['history'])
        for obj in res.json()['history']:
            self.object_dic[obj['id']] = obj['text']

    # 获取全部的列表
    def find_all(self):
        links = []
        for k in self.object_dic.keys():
            # 按时间顺序
            links.append(k)
            # links.insert(0,k)
        return links


if __name__ == '__main__':
    links = []
    # 登录
    mm = Codimd(host, email, password)
    mm.login()

    if os.path.exists('downloads') == False:
        os.mkdir('./downloads')

    key = str(input("导出全部文档还是指定文档？请输入序号数字\n1.导出全部\n2.导出指定，请输入url\n:"))
    if key == "1":
        links = mm.find_all()
        print(f'共 {len(links)} 个项目')
        mm.export(links)
        print('----------------------')
        print(f"导出 {mm.success} 个项目成功， {len(links) - mm.success} 个项目失败。程序结束！")
    elif key == "2":
        link_url = input('请输入完整URL：')
        index = link_url.rfind('/') + 1
        link = link_url[index:]
        links.append(link)
        mm.export(links)
        print("全部内容导出成功，程序结束！")
