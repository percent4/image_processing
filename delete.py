# -*- coding: utf-8 -*-

# 载入必要的模块
import wx
import time
import urllib.request
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException

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

        time.sleep(3)
        browser.find_element_by_id('j-input').send_keys(self.song_name)
        browser.find_element_by_id("j-submit").click()
        time.sleep(3)

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

        print("%.2f%%已经下载的大小:%ld\t文件大小:%ld\n" % (per, a * b, c))

    # 下载歌曲到指定文件夹
    def download_song(self):
        page_source = self.get_page_source()
        song_link = self.get_song_link(page_source)
        # print(song_link)
        song_name = self.save_directory+self.song_name+'.mp3'
        # print(song_name)
        urllib.request.urlretrieve(song_link, song_name, reporthook=self.Schedule)

#利用WxPython创建GUI
class Example(wx.Frame):
    def __init__(self, parent, title):
        #继承父类wx.Frame的初始化方法，并设置窗口大小为320*220
        super(Example, self).__init__(parent, title = title, size=(320, 260))
        self.InitUI()
        self.Centre()
        self.Show()

    def InitUI(self):

        #利用wxpython的GridBagSizer()进行页面布局
        panel = wx.Panel(self)
        sizer = wx.GridBagSizer(10, 20) #列间隔为10，行间隔为20

        # 第一行为空
        title = wx.StaticText(panel, label="")
        sizer.Add(title, pos=(0, 1), flag=wx.ALL, border=5)

        #添加账号字段，并加入页面布局，为第二行，第一列
        text = wx.StaticText(panel, label="歌曲名称")
        sizer.Add(text, pos=(1, 0), flag=wx.ALL, border=5)

        #添加文本框字段，并加入页面布局，为第二行，第2,3列
        self.tc = wx.TextCtrl(panel)
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
        btn2 = wx.Button(panel, -1, "清空")
        sizer.Add(btn2, pos=(3, 1), flag=wx.ALL, border=5)

        #为开始下载按钮绑定login_process事件
        self.Bind(wx.EVT_BUTTON, self.login_process, btn1)
        #为清空按钮绑定clear事件
        self.Bind(wx.EVT_BUTTON, self.clear, btn2)

        gauge = wx.Gauge(panel, size = (250, 25), style =  wx.GA_HORIZONTAL)
        gauge.SetBezelFace(3)
        gauge.SetShadowWidth(3)
        sizer.Add(gauge, pos=(4, 0), span=(0,2), flag=wx.ALL, border=5)
        self.Bind(wx.EVT_BUTTON, self.OnStart, btn1)

        #将Panmel适应GridBagSizer()放置
        panel.SetSizerAndFit(sizer)

    #事件处理，开始下载歌曲到指定保存目录
    def login_process(self, event):
        url = 'http://www.qmdai.cn/yinyuesou/'
        song_name = self.tc.GetValue()
        save_directory = self.tc1.GetValue()
        # print(song_name, save_directory)
        if song_name and save_directory:
            air = Download_Songs(url, save_directory, song_name)
            try:
                air.download_song()
                wx.MessageBox("歌曲%s下载成功！"%song_name)
            except Exception as e:
                print("错误原因：")
                print(e)
                wx.MessageBox("歌曲%s下载失败，请重试~"%song_name)
        else:
            wx.MessageBox("您的输入为空，请输入歌曲名称和保存目录！")

    # 清空输入框
    def clear(self, event):
        self.tc.SetValue("")
        self.tc1.SetValue("")

    # 进度条时间
    def OnStart(self, event):
        while True:
            time.sleep(1);
            self.count = self.count + 1
            self.gauge.SetValue(self.count)

            if self.count >= 20:
                print("end")

#主函数
def main():
    app = wx.App()
    Example(None, title = '简易歌曲下载APP')
    app.MainLoop()

main()

