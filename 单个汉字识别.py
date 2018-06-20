# 备注： 并发模块进行识别
#       识别过程中，出现次数最多的那个，即为识别结果
#       若次数一样，则选择第一个

import os
import time
import pytesseract
from PIL import Image
from collections import Counter
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED


# tesseract.exe所在的文件路径
pytesseract.pytesseract.tesseract_cmd = 'C://Program Files (x86)/Tesseract-OCR/tesseract.exe'


# 获取图片中像素点数量最多的像素
def get_threshold(image):

    # 创建像素字典
    pixel_dict = defaultdict(int)

    rows, cols = image.size
    for i in range(rows):
        for j in range(cols):
            pixel = image.getpixel((i, j))
            pixel_dict[pixel] += 1

    count_max = max(pixel_dict.values()) # 获取像素出现出多的次数
    pixel_dict_reverse = {v:k for k,v in pixel_dict.items()}
    threshold = pixel_dict_reverse[count_max] # 获取出现次数最多的像素点

    return threshold # 返回阈值


# 按照阈值进行二值化处理
# 输入为： 图片像素的阈值
def get_bin_table(threshold):

    # 获取灰度转二值的映射table
    table = []
    for i in range(256):
        rate = 0.1 # 在threshold的适当范围内进行处理
        if threshold*(1-rate)<= i <= threshold*(1+rate):
            table.append(1)
        else:
            table.append(0)
    return table


# 去掉二值化处理后的图片的噪声点
def cut_noise(image):

    rows, cols = image.size
    change_pos = [] # 记录噪声点位置

    # 遍历图片中的每个点，除掉边缘
    for i in range(1, rows-1):
        for j in range(1, cols-1):
            # pixel_set用来记录该店附近的黑色像素的数量
            pixel_set = []
            # 取该点的邻域为以该点为中心的九宫格
            for m in range(i-1, i+2):
                for n in range(j-1, j+2):
                    if image.getpixel((m, n)) != 1: # 1为白色,0位黑色
                        pixel_set.append(image.getpixel((m, n)))

            # 如果该位置的九宫内的黑色数量小于等于4，则判断为噪声
            if len(pixel_set) <= 2:
                change_pos.append((i,j))

    # 对相应位置进行像素修改，将噪声处的像素置为1（白色）
    for pos in change_pos:
        image.putpixel(pos, 1)

    # 将左右的黑边框变为白色
    for i in range(rows):
        image.putpixel((0, i), 1)
        image.putpixel((cols-1, i), 1)

    # 将上下的黑边框变为白色
    for j in range(rows):
        image.putpixel((j, 0), 1)
        image.putpixel((j, cols-1), 1)

    return image # 返回修改后的图片


# 改变图片格式， 将gif格式的图片改成png格式的图片
def change_picture_form(img_path):

    image = Image.open(img_path)
    save_path = img_path.replace('gif', 'png')
    image.save(save_path) # 保存图片为png格式

    return save_path


# 图片旋转前, 主要工作为： 图片去掉干扰，转化为灰度图，转化为黑白图片，去掉噪声
# 返回值： out
def before_rorate(img_path):

    # 打开png格式的图片
    image = Image.open(img_path)

    # 去掉灰色线条（即图片中的干扰项）
    rows, cols = image.size
    for i in range(rows):
        for j in range(cols):
            pixel = image.getpixel((i, j))
            if pixel == 202: # 202 为png格式下的灰色像素的值
                image.putpixel((i, j), 251)

    imgry = image.convert('L')  # 转化为灰度图

    # 获取图片中的出现次数最多的像素，即为该图片的背景
    max_pixel = get_threshold(imgry)

    # 将图片进行二值化处理
    table = get_bin_table(threshold=max_pixel)
    out = imgry.point(table, '1')

    # 去掉图片中的噪声（孤立点）
    # 重复去噪声3次
    for _ in range(3):
        out = cut_noise(out)

    # 去掉上边部分的黑色

    return out


# 识别图片中的数字
# 传入参数为out, angle(旋转角度), 返回结果为：识别结果
def OCR_lmj(out, angle, image_path):

    # 将图片顺时针旋转angle度, 并将旋转后的图片背景置为白色
    dst_im = Image.new("RGBA", (50, 50), "white")
    im = out.convert('RGBA')
    rot = im.rotate(angle, expand=0).resize((50, 50))
    dst_im.paste(rot, (0, 0), rot)

    # 文件保存路径
    save_path = image_path.split('.')[0][0:-2]

    # 保存图片
    dst_im.save("%s/test.png"%save_path)

    # 仅识别图片中的数字
    # text = pytesseract.image_to_string(out, config='--oem 0 digits')
    # 仅识别图片中的数字和字母
    #text = pytesseract.image_to_string(out)#, lang='eng', config='--oem 0 yours')
    # 识别图片中的中文
    text = pytesseract.image_to_string(dst_im, config='--psm 6 -l chi_sim')

    white_list = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmjopqrstuvwxyz0123456789【】，。；：‘’“”！？-[]{}<>:/\\;\'\"'

    with open('%s/recognize.txt'%save_path, 'a') as f:
        if (len(text) == 1 and text not in white_list):
            f.write(text+' ')

    return text

# 列表中出现次数最多的那个元素
# arr: 列表(list)
def counter_most(arr):

    # 返回出现频率最高的两个数
    element = Counter(arr).most_common(1)[0][0]
    return  element

# 识别单个汉字
def recongnize_single_character(image_path):

    image_path = change_picture_form(image_path)  # 读取png格式的图片
    out = before_rorate(image_path)  # 获取out值

    # 并发模块进行识别
    executor = ThreadPoolExecutor(5)  # 可以根据自己的需要调整线程的数量
    # 旋转角度从-50度到50度，每次旋转1度
    future_tasks = [executor.submit(OCR_lmj, out, angle, image_path) for angle in range(-50, 51, 1)]
    wait(future_tasks, return_when=ALL_COMPLETED)

    # 文件保存路径
    save_path = image_path.split('.')[0][0:-2]
    # 返回识别后的结果
    with open('%s/recognize.txt'%save_path, 'r') as f:
        words = f.readline()

    return counter_most(words.split())


def main():

    # 开始计时
    t1 = time.time()

    # 单张图片识别
    image_path = 'E://figures/hanzi/注.gif'    #图片的完整目录，图片格式为gif

    save_path = image_path.split('.')[0][0:-1] # 文件保存路径

    answer = image_path.split('/')[-1].split('.')[0] # 图片中的文字
    print('答案：%s'%answer)

    word = recongnize_single_character(image_path) # 图片识别后的汉子
    print('识别后的答案：%s'%word)

    t2 = time.time() # 结束计时
    print('耗时：%s'%(t2-t1))


    # 文件保存路径
    save_path = image_path.split('.')[0][0:-2]
    # 识别完文字后，需要删除txt文件, test.png文件
    if os.path.exists('%s/recognize.txt'%save_path):
        os.remove('%s/recognize.txt'%save_path)

    if os.path.exists('%s/test.png'%save_path):
        os.remove('%s/test.png'%save_path)

main()
