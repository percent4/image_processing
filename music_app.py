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
    # 初始化，传入参数为: url-> 网址， save_directory: 保存目录， song_name: 歌曲名称， platform: 音乐平台，默认为网易
    def __init__(self, url, save_directory, song_name, platform = 'netease'):
        self.url = url
        self.save_directory = save_directory
        self.song_name = song_name
        self.platform = platform

    # 获取歌曲的下载地址
    # 传入参数化为该网页的源代码: page_source
    def get_song_link(self, page_source):
        #print("正在解析页面!")
        soup = BeautifulSoup(page_source, "lxml")
        song_link = soup.find('a', id="j-src-btn")['href']
        #print(song_link)
        print("已获取歌曲的下载地址！")

        return song_link

    # 获取歌曲所在页面的源代码
    # 利用webdriver操作页面
    def get_page_source(self):
        # 设置Chrome浏览器，并启动
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
        # 操作页面，输入歌曲名称，选择音乐平台，点击获取下载地址
        browser.find_element_by_id('j-input').send_keys(self.song_name)
        browser.find_element_by_xpath('//input[@value="%s"]'%self.platform).click()  # click
        browser.find_element_by_id("j-submit").click()
        time.sleep(10)

        page_source = browser.page_source # 获取网页源代码
        browser.close() # 关闭浏览器

        return page_source

    '''
    显示下载进度函数
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
        page_source = self.get_page_source() # 获取歌曲所在网页的源代码
        song_link = self.get_song_link(page_source) # 解析网页，获取歌曲的下载地址
        # print(song_link)
        song_name = self.save_directory+self.song_name+'.mp3' # 歌曲所在完整路径
        # print(song_name)
        # 利用urllib.request.urlretrieve下载歌曲
        urllib.request.urlretrieve(song_link, song_name)#, reporthook=self.Schedule)

#事件处理，开始下载歌曲到指定保存目录
def login_process(save_directory, song, platform):
    url = 'http://www.qmdai.cn/yinyuesou/'
    # 初始化Download_Songs类
    air = Download_Songs(url, save_directory, song, platform)

    # 下载歌曲，并给出相应的提示信息
    try:
        air.download_song()  # 开始歌曲下载
        print("歌曲%s下载成功！" % song)
    except Exception as e:
        print("歌曲%s下载失败，请重试~" % song)
        print("错误原因：")
        print(e)
    finally:
        return 'ok'

#利用WxPython创建GUI
class Example(wx.Frame):
    def __init__(self, parent, title):
        #继承父类wx.Frame的初始化方法，并设置窗口大小为420*360
        super(Example, self).__init__(parent, title = title, size=(420, 360))
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
        text = wx.StaticText(panel, label="歌曲名称")
        sizer.Add(text, pos=(1, 0), flag=wx.ALL, border=5)

        #添加文本框字段，并加入页面布局，为第二行，第2,3列
        self.tc =  wx.TextCtrl(panel, -1, size = (150,100), style = wx.TE_MULTILINE)
        sizer.Add(self.tc, pos=(1, 1), span=(1,3), flag=wx.EXPAND|wx.ALL, border=5)

        #添加密码字段，并加入页面布局，为第三行，第一列
        text1 = wx.StaticText(panel, label="保存目录")
        sizer.Add(text1, pos=(2,0), flag=wx.ALL, border=5)

        #添加文本框字段，以星号掩盖,并加入页面布局，为第三行，第2,3列
        self.tc1 = wx.TextCtrl(panel)
        sizer.Add(self.tc1, pos=(2,1), span=(1,3), flag=wx.EXPAND|wx.ALL, border=5)

        # 添加音乐平台及单选框组，并加入页面布局，为第三行
        platform_list = ["网易", "QQ", "酷狗", "酷我", "虾米", "百度"]
        self.radiobox = wx.RadioBox(panel, -1, "音乐平台", (150, 80), (310, 50), platform_list, 6, wx.RA_SPECIFY_COLS)
        sizer.Add(self.radiobox, pos=(3, 0), span=(0,3), flag=wx.ALL, border=5)

        #添加开始下载按钮，并加入页面布局，为第四行，第0,1列
        btn1 = wx.Button(panel, -1, "开始下载")
        sizer.Add(btn1, pos=(4,0), span=(0,1), flag=wx.ALL, border=5)

        # 添加清空按钮，并加入页面布局，为第四行，第2,3列
        btn2 = wx.Button(panel, -1, "清空输入")
        sizer.Add(btn2, pos=(4,2), span=(2,3), flag=wx.ALL, border=5)

        #为开始下载按钮绑定concurrency事件
        self.Bind(wx.EVT_BUTTON, self.concurrency, btn1)
        #为清空按钮绑定clear事件
        self.Bind(wx.EVT_BUTTON, self.clear, btn2)

        #将Panel适应GridBagSizer()放置
        panel.SetSizerAndFit(sizer)

    # 并发下载歌曲
    def concurrency(self, event):

        song_list = self.tc.GetValue().split('\n')  # 获取输入框中的歌曲名称
        save_directory = self.tc1.GetValue()  # 获取输入框中的保存目录
        platform_choice = self.radiobox.GetStringSelection() # 获取下载的音乐平台

        if not platform_choice: # 默认选择为'网易'
            platform_choice = '网易'

        # 音乐平台及其对应的网页中input的value
        platform_dict = {'网易': 'netease',
                         'QQ':   'qq',
                         '酷狗': 'kugou',
                         '酷我': 'kuwo',
                         '虾米': 'xiami',
                         '百度': 'baidu'
        }

        platform = platform_dict[platform_choice]

        if song_list and save_directory:  # 输入歌曲名称和保存目录不为空
            # 如果保存目录不存在，则新建目录
            if not os.path.exists(save_directory):
                os.mkdir(save_directory)

            print('\n'+'*'*60+'\n并发下载歌曲中...')
            # concurrent.futures模块进行并发下载
            executor = ThreadPoolExecutor(len(song_list))
            future_tasks = [executor.submit(login_process, save_directory, song, platform) for song in song_list]
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

