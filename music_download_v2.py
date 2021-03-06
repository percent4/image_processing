# -*- coding: utf-8 -*-

# 载入必要的模块
import os
import wx
import time
import urllib.request
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED

# 创建歌曲下载类
class Download_Songs(object):
    # 初始化，传入参数为: url-> 网址， save_directory: 保存目录， song_name: 歌曲名称
    def __init__(self, url, save_directory, song_name):
        self.url = url
        self.save_directory = save_directory
        self.song_name = song_name

    # 获取歌曲的下载地址
    # 传入参数化为该网页的源代码: page_source
    def get_song_link(self, page_source):
        print("正在解析页面!")
        soup = BeautifulSoup(page_source, "lxml")
        song_link = soup.find('a', id="j-src-btn")['href']
        print("已获取歌曲的下载地址！")

        return song_link

    # 获取歌曲所在页面的源代码
    # 利用webdriver操作页面
    def get_page_source(self):
        #设置Chrome浏览器，并启动
        #chrome_options = webdriver.ChromeOptions()
        # 不加载图片(提升加载速度)
        #prefs = {"profile.managed_default_content_settings.images":2}
        #chrome_options.add_argument('headless')
        #chrome_options.add_experimental_option("prefs",prefs)

        #browser = webdriver.Chrome(chrome_options=chrome_options) #启动浏览器
        browser = webdriver.PhantomJS()
        print("浏览器已启动")
        #browser.maximize_window() #窗口最大化
        browser.set_page_load_timeout(30) # 最大等待时间为30s

        #当加载时间超过30秒后，自动停止加载该页面
        try:
            browser.get(self.url)
        except TimeoutException:
            browser.execute_script('window.stop()')

        time.sleep(2)
        browser.find_element_by_id('j-input').send_keys(self.song_name)
        browser.find_element_by_id("j-submit").click()
        time.sleep(2)

        page_source = browser.page_source # 获取网页源代码
        browser.close()

        return page_source

    '''
    传入参数：
        - a:已经下载的数据块
        - b:数据块的大小
        - c:远程文件的大小
    '''
    def Schedule(self, a, b, c):
        per = 100.0 * a * b / c

        if per > 100:
            per = 100

        if int(per) % 10 == 0:
            print("%2.f%% 已经下载的大小:%ld\t文件大小:%ld\n" % (per, a * b, c))

    # 下载歌曲到指定文件夹
    def download_song(self):
        page_source = self.get_page_source()
        song_link = self.get_song_link(page_source)
        # print(song_link)
        song_name = self.save_directory+self.song_name+'.mp3'
        # print(song_name)
        urllib.request.urlretrieve(song_link, song_name, reporthook=self.Schedule)

        return 'ok'

#事件处理，开始下载歌曲到指定保存目录
def login_process(save_directory, song):
    url = 'http://www.qmdai.cn/yinyuesou/'
    air = Download_Songs(url, save_directory, song)

    try:
        air.download_song()  # 开始歌曲下载
        print("歌曲%s下载成功！" % song)
    except Exception as e:
        print("错误原因：")
        print(e)
        print("歌曲%s下载失败，请重试~" % song)

#利用WxPython创建GUI
class Example(wx.Frame):
    def __init__(self, parent, title):
        #继承父类wx.Frame的初始化方法，并设置窗口大小为320*220
        super(Example, self).__init__(parent, title = title, size=(320, 300))
        self.InitUI()
        self.Centre()
        self.Show()

    def InitUI(self):

        #利用wxpython的GridBagSizer()进行页面布局
        panel = wx.Panel(self)
        sizer = wx.GridBagSizer(10, 20) #列间隔为10，行间隔为20

        # 第一行为空
        #title = wx.StaticText(panel, label="")
        #sizer.Add(title, pos=(0, 1), flag=wx.ALL, border=5)

        #添加账号字段，并加入页面布局，为第二行，第一列
        #text = wx.StaticText(panel, label="歌曲名称")
        # 设置普通文本
        text = wx.StaticText(panel, label="歌曲名称")
        sizer.Add(text, pos=(1, 0), flag=wx.ALL, border=5)

        #添加文本框字段，并加入页面布局，为第二行，第2,3列
        self.tc =  wx.TextCtrl(panel, -1, size = (150,100), style = wx.TE_MULTILINE)
        sizer.Add(self.tc, pos=(1, 1), span=(1,2), flag=wx.EXPAND|wx.ALL, border=5)

        #添加密码字段，并加入页面布局，为第三行，第一列
        text1 = wx.StaticText(panel, label="保存目录")
        sizer.Add(text1, pos=(2,0), flag=wx.ALL, border=5)

        #添加文本框字段，以星号掩盖,并加入页面布局，为第三行，第2,3列
        self.tc1 = wx.TextCtrl(panel)
        sizer.Add(self.tc1, pos=(2,1), span=(1,2), flag=wx.EXPAND|wx.ALL, border=5)

        #添加开始下载按钮，并加入页面布局，为第四行，第1列
        btn1 = wx.Button(panel, -1, "开始下载")
        sizer.Add(btn1, pos=(3,0), flag=wx.ALL, border=5)

        # 添加清空按钮，并加入页面布局，为第四行，第2列
        btn2 = wx.Button(panel, -1, "清空输入")
        sizer.Add(btn2, pos=(3,1), flag=wx.ALL, border=5)

        #为开始下载按钮绑定login_process事件
        self.Bind(wx.EVT_BUTTON, self.concurrency, btn1)
        #为清空按钮绑定clear事件
        self.Bind(wx.EVT_BUTTON, self.clear, btn2)

        #将Panmel适应GridBagSizer()放置
        panel.SetSizerAndFit(sizer)


    def concurrency(self, event):

        song_list = self.tc.GetValue().split('\n')  # 获取输入框中的歌曲名称
        save_directory = self.tc1.GetValue()  # 获取输入框中的保存目录
        #print(save_directory)
        #print(song_list)

        if song_list and save_directory:  # 输入歌曲名称和保存目录不为空
            # 如果保存目录不存在，则新建目录
            if not os.path.exists(save_directory):
                os.mkdir(save_directory)

            print('并发下载歌曲中...')
            executor = ThreadPoolExecutor(len(song_list))
            future_tasks = [executor.submit(login_process, save_directory, song) for song in song_list]
            wait(future_tasks, return_when=ALL_COMPLETED)
            wx.MessageBox("全部歌曲下载完毕,请前往文件夹中查看！")
        else:  # 输入歌曲名称或保存目录为空
            wx.MessageBox("您的输入为空，请输入歌曲名称和保存目录！")

    # 清空输入框
    def clear(self, event):
        self.tc.SetValue("")
        self.tc1.SetValue("")

#主函数
def main():
    app = wx.App()
    Example(None, title = '简易歌曲下载APP')
    app.MainLoop()

main()
