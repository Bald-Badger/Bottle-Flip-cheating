# @Author 技术帅 shuaige19981012@163.com
# encode: utf-8

import os
from PIL import Image, ImageEnhance
import cv2
import math
import sys
import time


def cut():
    # 加载原始图片
    img = Image.open('screencap.png')

    img2 = img.crop((0, 640, 1440, 1920))
    img2.save("cutted.png")
    # 剪切出适合识别的图片


def cir_pos():
    # 输入一个图像，找到左右的圆并返回坐标
    # 参考http://m.blog.csdn.net/haofan_/article/details/77625843
    # 会找到所有的圆，所以别忘记滤掉圆们
    im = Image.open(r"cutted.png")
    bg = Image.new("RGB", im.size, (255, 255, 255))
    bg.paste(im, im)
    bg.save(r"cutted_cir.jpg")
    bg.save(r"cutted_top.jpg")
    # 转码，识别貌似只支持jpg格式

    # 载入并显示图片
    img = cv2.imread('cutted_cir.jpg')

    # cv2.imshow('img', img)
    # 灰度化

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 输出图像大小，方便根据图像大小调节minRadius和maxRadius

    # print(img.shape)
    # 霍夫变换圆检测

    circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 1000, param1=30, param2=26, minRadius=30, maxRadius=50)
    # 这些参数调整起来真的麻烦。。。还不是最准确的，不过good enough。 移植的时候主要要改minRadius 和 maxRadius这两个参数，适配自己的手机

    # 输出返回值，方便查看类型
    # print(circles)

    # 输出检测到圆的个数
    # print(len(circles[0]))

    # print('-------------我是条分割线-----------------')
    # 根据检测到圆的信息，画出每一个圆
    for circle in circles[0]:
        # 坐标行列
        x = int(circle[0])
        y = int(circle[1])

        # 半径
        r = int(circle[2])
        # 在原图用指定颜色标记出圆的位置
        img = cv2.circle(img, (x, y), r, (0, 0, 255), -1)

    # 显示新图像
    # cv2.imshow('res', img)

    # 按任意键退出
    # cv2.waitKey(0)
    # time.sleep(1)
    # cv2.destroyAllWindows()

    print('cir[x, y, r] = %s' % str([x, y, r]))
    return [x, y, r]


def top_pos():
    # 输入一个图片，返回最上层边界位置
    image = Image.open('cutted_top.jpg')
    enh_con = ImageEnhance.Contrast(image)
    contrast = 2  # 增加对比度，方便识别
    image_contrasted = enh_con.enhance(contrast)
    image_contrasted.save('cutted_top.jpg')
    img = cv2.imread('cutted_top.jpg', 0)
    img = cv2.GaussianBlur(img, (3, 3), 0)
    canny = cv2.Canny(img, 13, 43)  # 上下阈值，具体建议百度

    # cv2.imshow('Canny', canny)
    # cv2.waitKey(0)
    # time.sleep(1)
    # cv2.destroyAllWindows()

    find = False
    for i in range(1400):  # 如果要移植代码，别忘了该这个参数 数值=截图的高的像素数
        if find:
            break
        for ele in canny[i]:
            if ele > 0:
                y = i
                x = list(canny[i]).index(ele)
                find = True
    print('top[x, y] = %s' % str([x,y]))
    return [x, y]


def distance():
    # 算圆要走的距离
    cir = cir_pos()
    top = top_pos()  # 顺序很重要 先cir再top， 因为top()需要cir()的转码后的文件
    if abs(top[1] <= 150):  # 检测游戏结束,150是随便写的，还没有调过
        print('seems that the game have ended')
        sys.exit(0)
    dx = abs(cir[0] - top[0])
    dy = abs(cir[1] - top[1])
    length = math.sqrt(dx * dx + dy * dy)

    if length > 900:  # 一般不会这么远
        print(length)
        return 'far & unbounded'

    if length < 300:  # 一般不会这么进
        print(length)
        return 'too close'

    if length <= 500:
        print(length)
        print("\nseems that it's too near, auto-adjusting...\n")
        dy += 80  # 检测两个跳板是不是太近了
        print(math.sqrt(dx * dx + dy * dy))
    print('[dx, dy] = %s' % str([dx, dy]))
    if dx / dy >= 5.5:  # 比例异常，比如没有识别边界
        length = 'far & unbounded'
    elif dx <= 70 and dy <= 70:  # 顶点是否为球本身
        length = 'too close'
    else:
        length = math.sqrt(dx * dx + dy * dy)
        if length <= 333:  # 这么近多半是出bug了，直接上手动
            length = 'too close'
        elif length >= 866:  # 这么远少半是出bug了，直接上手动
            print('length = %d' % length)
            length = 'far & unbounded'
    return length


def push_file(speed):  # 参数speed，
    # 三星galaxyS6的经验值约为1-1.1，其他机型需要自己摸索
    # 如果感觉走的太近就调高一些，感觉跳的太远就调低一些
    # 估计怎么改也都是0.8-1.2这个区间

    # 修改push.bat，使其走该走的那么长的路
    result = distance()
    if str(result) == 'far & unbounded':
        far_unbounded()
    elif str(result) == 'too close':
        too_close()
    else:
        file = open('push.bat', 'w')
        word = 'adb shell input swipe 300 300 600 400 '+str(int(speed*result))
        file.write(word)
        file.close()
        print('jumping, distance = %s' % str(int(speed*result)))


def loop(speed):
    while 1:
        os.system('wtf.bat')  # 加载图片并储存在当前文件夹
        time.sleep(0.5)
        cut()  # 剪切图片，保存容易识别的图片
        time.sleep(0.1)
        push_file(speed)  # 修改push.bat
        os.system('push.bat')  # 执行push.bat，等效于按压屏幕
        time.sleep(1.3)  # 等待动画特效结束


def far_unbounded():
    print('error, far or unbounded')
    prompt = input('please confirm your order\n')
    if prompt == 'abort':
        print('confirmed, aborting')
        sys.exit(0)
    file = open('push.bat', 'w')
    word = 'adb shell input swipe 300 300 400 600 ' + str(prompt)
    file.write(word)
    file.close()
    print('confirmed, jumping %s millisecond' % str(prompt))


def too_close():  # 太近的时候，手动输入该跳多少
    print('error, too close')
    prompt = input('please confirm your order\n')
    if prompt == 'abort':
        print('confirmed, aborting')
        sys.exit(0)
    file = open('push.bat', 'w')
    word = 'adb shell input swipe 300 300 300 600 ' + str(prompt)
    file.write(word)
    file.close()
    print('confirmed, jumping %s millisecond' % str(prompt))


if __name__ == '__main__':
    os.system('adb devices')  # 连手机
    time.sleep(3)  # 等adb连接手机
    path = os.getcwd()
    os.system(path[0] + ': && cd ' + path)  # 修改cmd路径至当前位置
    loop(speed=1.06)  # speed

